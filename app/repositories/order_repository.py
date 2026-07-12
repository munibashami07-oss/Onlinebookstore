"""Repository for Order and OrderItem database operations."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:
    """Data access layer for the Order and OrderItem models."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_order(self, order: Order) -> Order:
        """Insert a new order record."""
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def add_order_item(self, item: OrderItem) -> OrderItem:
        """Insert a new order item record."""
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_order(self, order_id: int) -> Optional[Order]:
        """Fetch a single order by primary key with items and payment eagerly loaded."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.inventory),
                selectinload(Order.payment),
            )
            .where(Order.id == order_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_orders(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Fetch paginated orders for a specific user."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.inventory),
                selectinload(Order.payment),
            )
            .where(Order.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Order.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_order(self, order: Order) -> Order:
        """Persist changes to an existing order."""
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def list_all_orders(
        self, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Fetch paginated list of all orders (admin use)."""
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.inventory),
                selectinload(Order.payment),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Order.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())