"""Base repository pattern implementation using SQLAlchemy 2.0 async session."""

from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base class providing standard CRUD operations."""

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Fetch single record by primary key."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch paginated records."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, instance: ModelType) -> ModelType:
        """Add and persist a new model instance."""
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Save updates to an existing instance."""
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete instance from database."""
        await self.db.delete(instance)
        await self.db.flush()
