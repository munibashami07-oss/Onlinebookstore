"""Repository for Inventory database operations."""

from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory


class InventoryRepository:
    """Data access layer for the Inventory model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, inventory: Inventory) -> Inventory:
        """Insert a new inventory record."""
        self.db.add(inventory)
        await self.db.flush()
        await self.db.refresh(inventory)
        return inventory

    async def get_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Fetch inventory record by primary key."""
        stmt = select(Inventory).where(Inventory.id == inventory_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_stock(self, book_id: int) -> Optional[Inventory]:
        """Fetch inventory record for a specific book."""
        stmt = select(Inventory).where(Inventory.book_id == book_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def increase_stock(self, book_id: int, quantity: int) -> Optional[Inventory]:
        """Increase stock_quantity for a given book."""
        stmt = (
            update(Inventory)
            .where(Inventory.book_id == book_id)
            .values(stock_quantity=Inventory.stock_quantity + quantity)
            .returning(Inventory)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        row = result.scalars().first()
        if row:
            await self.db.refresh(row)
        return row

    async def decrease_stock(self, book_id: int, quantity: int) -> Optional[Inventory]:
        """Decrease stock_quantity for a given book."""
        stmt = (
            update(Inventory)
            .where(Inventory.book_id == book_id)
            .values(stock_quantity=Inventory.stock_quantity - quantity)
            .returning(Inventory)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        row = result.scalars().first()
        if row:
            await self.db.refresh(row)
        return row
