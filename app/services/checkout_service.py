"""Service layer orchestrating atomic multi-step checkout workflow."""

from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.repositories.cart_repository import CartRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate


class CheckoutServiceError(Exception):
    """Base exception for CheckoutService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CheckoutService:
    """Business logic for atomic checkout validation, order creation, stock reservation, and cart clearance."""

    TAX_RATE = 0.05
    SHIPPING_FEE = 5.00

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.cart_repo = CartRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.order_repo = OrderRepository(db)

    async def process_checkout(self, user_id: int, payload: OrderCreate) -> Dict[str, Any]:
        """Execute atomic checkout transaction:
        1. Validate cart is not empty.
        2. Validate stock availability for each item (prevent overselling).
        3. Calculate subtotal, discount, tax, shipping, and grand total.
        4. Create Order & OrderItems.
        5. Reserve inventory / decrease stock.
        6. Empty shopping cart.
        7. Return Order Summary prepared for payment.

        Transaction rolls back automatically on any exception.
        """
        cart = await self.cart_repo.get_cart(user_id)
        if not cart or not cart.items:
            raise CheckoutServiceError("Cannot checkout with an empty cart.", status_code=400)

        subtotal = 0.0
        purchased_items = []

        # Validate inventory stock & calculate prices
        for item in cart.items:
            inventory = await self.inventory_repo.get_stock(item.book_id)
            if not inventory or inventory.stock_quantity < item.quantity:
                book_title = item.book.title if item.book else f"Book #{item.book_id}"
                available = inventory.stock_quantity if inventory else 0
                raise CheckoutServiceError(
                    f"Insufficient inventory for '{book_title}'. Available: {available}, Requested: {item.quantity}.",
                    status_code=400,
                )
            item_price = float(item.price_at_add_time)
            item_total = item_price * item.quantity
            subtotal += item_total

            purchased_items.append({
                "book_id": item.book_id,
                "title": item.book.title if item.book else f"Book #{item.book_id}",
                "quantity": item.quantity,
                "unit_price": item_price,
                "total_price": round(item_total, 2),
            })

        discount = 0.0
        taxable_amount = max(0.0, subtotal - discount)
        tax = round(taxable_amount * self.TAX_RATE, 2)
        shipping = self.SHIPPING_FEE
        grand_total = round(subtotal - discount + tax + shipping, 2)

        # Atomic Transaction execution block
        try:
            # Step 1: Create Order
            order = Order(
                user_id=user_id,
                total_amount=grand_total,
                status=OrderStatus.PENDING,
                shipping_address=payload.shipping_address,
            )
            order = await self.order_repo.create_order(order)

            # Step 2: Create OrderItems and decrease inventory stock
            for item in cart.items:
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    purchase_price=item.price_at_add_time,
                )
                await self.order_repo.add_order_item(order_item)
                await self.inventory_repo.decrease_stock(item.book_id, item.quantity)

            # Step 3: Clear user cart
            await self.cart_repo.clear_cart(cart.id)

            # Prepare Order Summary
            order_summary = {
                "order_number": f"ORD-{order.id:06d}",
                "order_id": order.id,
                "status": order.status.value,
                "payment_status": "pending",
                "purchased_items": purchased_items,
                "subtotal": round(subtotal, 2),
                "discount": round(discount, 2),
                "tax": tax,
                "shipping": shipping,
                "grand_total": grand_total,
                "shipping_address": payload.shipping_address,
                "message": "Order created successfully. Ready for payment processing.",
            }

            return order_summary

        except Exception as e:
            await self.db.rollback()
            raise CheckoutServiceError(
                f"Checkout failed due to system error: {str(e)}", status_code=500
            )
