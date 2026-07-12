"""Repository for User database operations on enrolled_users table."""

from typing import List, Optional
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """Data access layer for the User (enrolled_users) model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, user: User) -> User:
        """Insert a new user record."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a single user by primary key."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a single user by email address."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, full_name: str) -> Optional[User]:
        """Fetch a single user by full_name (username proxy)."""
        stmt = select(User).where(User.full_name == full_name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Fetch a paginated list of users."""
        stmt = select(User).offset(skip).limit(limit).order_by(User.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_user(self, user: User) -> User:
        """Persist changes to an existing user instance."""
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> None:
        """Delete a user by primary key."""
        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        await self.db.flush()
