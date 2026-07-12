"""Service layer for shopping cart operations and subtotal, tax, and discount calculations."""

from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.repositories.book_repository import BookRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CartServiceError(Exception):
    """Base exception for CartService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CartService:
    """Business logic for shopping cart management and financial calculations."""

    TAX_RATE = 0.05  # 5% tax rate
    SHIPPING_FEE = 5.00  # Flat shipping rate

    def __init__(self, db: AsyncSession) -> None:
        self.cart_repo = CartRepository(db)
        self.book_repo = BookRepository(db)
        self.inventory_repo = InventoryRepository(db)

    async def get_or_create_user_cart(self, user_id: int) -> Cart:
        """Fetch existing user cart or create a new one."""
        cart = await self.cart_repo.get_cart(user_id)
        if not cart:
            cart = Cart(user_id=user_id)
            cart = await self.cart_repo.create_cart(cart)
            cart = await self.cart_repo.get_cart(user_id)
        return cart

    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """Get cart details and calculate Subtotal, Discount, Tax, and Estimated Total."""
        cart = await self.get_or_create_user_cart(user_id)
        subtotal = 0.0
        items_detail = []

        for item in cart.items:
            item_subtotal = float(item.price_at_add_time) * item.quantity
            subtotal += item_subtotal
            items_detail.append({
                "id": item.id,
                "book_id": item.book_id,
                "book_title": item.book.title if item.book else f"Book #{item.book_id}",
                "quantity": item.quantity,
                "price_at_add_time": float(item.price_at_add_time),
                "subtotal": round(item_subtotal, 2),
            })

        discount = 0.0  # Placeholder for active deals/promos
        taxable_amount = max(0.0, subtotal - discount)
        tax = round(taxable_amount * self.TAX_RATE, 2)
        shipping = self.SHIPPING_FEE if subtotal > 0 else 0.0
        estimated_total = round(subtotal - discount + tax + shipping, 2)

        return {
            "cart_id": cart.id,
            "user_id": user_id,
            "items": items_detail,
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "tax": tax,
            "shipping": shipping,
            "estimated_total": estimated_total,
        }

    async def add_item(self, user_id: int, payload: CartItemCreate) -> CartItem:
        """Add an item to cart or increase quantity if already present after stock validation."""
        book = await self.book_repo.get_book(payload.book_id)
        if not book:
            raise CartServiceError("Book not found.", status_code=404)

        # Validate inventory stock before adding
        inventory = await self.inventory_repo.get_stock(payload.book_id)
        available_stock = inventory.stock_quantity if inventory else 0

        cart = await self.get_or_create_user_cart(user_id)
        existing_item = await self.cart_repo.get_item(cart.id, payload.book_id)

        target_quantity = payload.quantity
        if existing_item:
            target_quantity += existing_item.quantity

        if available_stock < target_quantity:
            raise CartServiceError(
                f"Insufficient inventory stock for '{book.title}'. Available: {available_stock}, Requested: {target_quantity}.",
                status_code=400,
            )

        if existing_item:
            existing_item.quantity = target_quantity
            existing_item.price_at_add_time = float(book.price)
            return await self.cart_repo.update_item(existing_item)

        new_item = CartItem(
            cart_id=cart.id,
            book_id=payload.book_id,
            quantity=payload.quantity,
            price_at_add_time=float(book.price),
        )
        return await self.cart_repo.add_item(new_item)

    async def update_quantity(
        self, user_id: int, item_id: int, payload: CartItemUpdate
    ) -> CartItem:
        """Update item quantity in user cart after stock validation."""
        cart = await self.get_or_create_user_cart(user_id)
        item = await self.cart_repo.get_item_by_id(item_id)

        if not item or item.cart_id != cart.id:
            raise CartServiceError("Cart item not found.", status_code=404)

        inventory = await self.inventory_repo.get_stock(item.book_id)
        available_stock = inventory.stock_quantity if inventory else 0

        if available_stock < payload.quantity:
            raise CartServiceError(
                f"Insufficient inventory stock. Available: {available_stock}, Requested: {payload.quantity}.",
                status_code=400,
            )

        item.quantity = payload.quantity
        return await self.cart_repo.update_item(item)

    async def remove_item(self, user_id: int, item_id: int) -> None:
        """Remove item from user cart."""
        cart = await self.get_or_create_user_cart(user_id)
        item = await self.cart_repo.get_item_by_id(item_id)

        if not item or item.cart_id != cart.id:
            raise CartServiceError("Cart item not found.", status_code=404)

        await self.cart_repo.remove_item(item_id)

    async def clear_cart(self, user_id: int) -> None:
        """Clear all items from user cart."""
        cart = await self.get_or_create_user_cart(user_id)
        await self.cart_repo.clear_cart(cart.id)
