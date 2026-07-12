"""Repository for Cart and CartItem database operations."""

from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem


class CartRepository:
    """Data access layer for the Cart and CartItem models."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_cart(self, user_id: int) -> Optional[Cart]:
        """Fetch the cart for a given user, with items and their books eagerly loaded."""
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.book)
            )
            .where(Cart.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_cart(self, cart: Cart) -> Cart:
        """Create a new cart for a user."""
        self.db.add(cart)
        await self.db.flush()
        await self.db.refresh(cart)
        return cart

    async def add_item(self, item: CartItem) -> CartItem:
        """Insert a new item into the cart."""
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_item(self, cart_id: int, book_id: int) -> Optional[CartItem]:
        """Fetch a specific cart item by cart and book."""
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.book_id == book_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_item_by_id(self, item_id: int) -> Optional[CartItem]:
        """Fetch a cart item by its primary key."""
        stmt = select(CartItem).where(CartItem.id == item_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_item(self, item: CartItem) -> CartItem:
        """Persist changes to an existing cart item."""
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def remove_item(self, item_id: int) -> None:
        """Remove a single item from the cart."""
        stmt = delete(CartItem).where(CartItem.id == item_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def clear_cart(self, cart_id: int) -> None:
        """Remove all items from a cart."""
        stmt = delete(CartItem).where(CartItem.cart_id == cart_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_cart_items(self, cart_id: int) -> List[CartItem]:
        """Fetch all items in a cart."""
        stmt = (
            select(CartItem)
            .options(selectinload(CartItem.book))
            .where(CartItem.cart_id == cart_id)
            .order_by(CartItem.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
