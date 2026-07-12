"""Repository for Stationary database operations."""

from typing import List, Optional
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stationary import Stationary


class StationaryRepository:
    """Data access layer for the Stationary model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, item: Stationary) -> Stationary:
        """Insert a new stationary record."""
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> Optional[Stationary]:
        """Fetch a single stationary item by primary key."""
        stmt = select(Stationary).where(Stationary.id == item_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[Stationary]:
        """Fetch a paginated list of stationary items."""
        stmt = (
            select(Stationary)
            .offset(skip)
            .limit(limit)
            .order_by(Stationary.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Stationary]:
        """Search stationary items by name or description."""
        search_term = f"%{query}%"
        stmt = (
            select(Stationary)
            .where(
                or_(
                    Stationary.name.ilike(search_term),
                    Stationary.description.ilike(search_term),
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Stationary.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, item: Stationary) -> Stationary:
        """Persist changes to an existing stationary item."""
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item_id: int) -> None:
        """Delete a stationary item by primary key."""
        stmt = delete(Stationary).where(Stationary.id == item_id)
        await self.db.execute(stmt)
        await self.db.flush()
