"""Repository for Genre database operations."""

from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.genre import Genre


class GenreRepository:
    """Data access layer for the Genre model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, genre: Genre) -> Genre:
        """Insert a new genre record."""
        self.db.add(genre)
        await self.db.flush()
        await self.db.refresh(genre)
        return genre

    async def get_by_id(self, genre_id: int) -> Optional[Genre]:
        """Fetch a single genre by primary key."""
        stmt = select(Genre).where(Genre.id == genre_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Genre]:
        """Fetch a single genre by name."""
        stmt = select(Genre).where(Genre.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[Genre]:
        """Fetch a paginated list of genres."""
        stmt = select(Genre).offset(skip).limit(limit).order_by(Genre.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, genre: Genre) -> Genre:
        """Persist changes to an existing genre."""
        await self.db.flush()
        await self.db.refresh(genre)
        return genre

    async def delete(self, genre_id: int) -> None:
        """Delete a genre by primary key."""
        stmt = delete(Genre).where(Genre.id == genre_id)
        await self.db.execute(stmt)
        await self.db.flush()
