"""Repository for User database operations on enrolled_users table."""

from typing import List, Optional
from sqlalchemy import delete, or_, select, update
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

    async def search_users(
        self,
        exclude_user_id: int,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[User]:
        """Fetch active users other than `exclude_user_id`, optionally
        filtered by a case-insensitive match on full_name or email.

        Backs the chat "start a new conversation" contact search. Under
        the open messaging model any active registered user (customer or
        admin) is a valid target, so unlike `list_users` this is safe to
        expose to non-admin callers -- it deliberately never returns
        email/password/role details beyond what `UserPublic` already
        allows through the router's response_model.
        """
        stmt = select(User).where(
            User.id != exclude_user_id, User.is_active.is_(True)
        )
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(User.full_name.ilike(like), User.email.ilike(like))
            )
        stmt = stmt.order_by(User.full_name.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_first_admin(self) -> Optional[User]:
        """Fetch the lowest-id admin user, used as the fixed customer-support
        contact for the chat feature (single-admin support model)."""
        stmt = (
            select(User)
            .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
            .order_by(User.id.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

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