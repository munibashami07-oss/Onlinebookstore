"""Service layer for User profile and account management workflows."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserServiceError(Exception):
    """Base exception for UserService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserService:
    """Business logic for User profiles and account management."""

    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: int) -> User:
        """Retrieve user profile by user ID.

        Args:
            user_id: Primary key of the user.

        Returns:
            User ORM instance.

        Raises:
            UserServiceError: If user is not found.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserServiceError("User profile not found.", status_code=404)
        return user

    async def update_profile(self, user_id: int, payload: UserUpdate) -> User:
        """Update profile information of a user.

        Args:
            user_id: Primary key of the user.
            payload: Validated UserUpdate schema.

        Returns:
            Updated User ORM instance.

        Raises:
            UserServiceError: If user not found or email conflict occurs.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserServiceError("User profile not found.", status_code=404)

        if payload.email and payload.email != user.email:
            existing_user = await self.user_repo.get_by_email(payload.email)
            if existing_user:
                raise UserServiceError(
                    "This email address is already in use by another account.",
                    status_code=409,
                )
            user.email = payload.email

        if payload.full_name is not None:
            user.full_name = payload.full_name

        if payload.password:
            user.hashed_password = get_password_hash(payload.password)

        if payload.is_active is not None:
            user.is_active = payload.is_active

        if payload.role is not None:
            user.role = payload.role

        return await self.user_repo.update_user(user)

    async def delete_account(self, user_id: int) -> None:
        """Delete user account by user ID.

        Args:
            user_id: Primary key of the user.

        Raises:
            UserServiceError: If user not found.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserServiceError("User profile not found.", status_code=404)

        await self.user_repo.delete_user(user_id)
