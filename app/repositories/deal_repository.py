"""Repository for Deal database operations."""

from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal import Deal


class DealRepository:
    """Data access layer for the Deal model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, deal: Deal) -> Deal:
        """Insert a new deal record."""
        self.db.add(deal)
        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def get_by_id(self, deal_id: int) -> Optional[Deal]:
        """Fetch a single deal by primary key with related books and stationary."""
        stmt = (
            select(Deal)
            .options(
                selectinload(Deal.books),
                selectinload(Deal.stationary_items),
            )
            .where(Deal.id == deal_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[Deal]:
        """Fetch a paginated list of deals."""
        stmt = (
            select(Deal)
            .offset(skip)
            .limit(limit)
            .order_by(Deal.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_active(
        self, skip: int = 0, limit: int = 100
    ) -> List[Deal]:
        """Fetch only active deals."""
        stmt = (
            select(Deal)
            .where(Deal.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Deal.end_date.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, deal: Deal) -> Deal:
        """Persist changes to an existing deal."""
        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def delete(self, deal_id: int) -> None:
        """Delete a deal by primary key."""
        stmt = delete(Deal).where(Deal.id == deal_id)
        await self.db.execute(stmt)
        await self.db.flush()
