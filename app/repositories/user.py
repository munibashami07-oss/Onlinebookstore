"""User repository implementation for database operations on enrolled_users."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository specializing in User database interactions."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()
