"""Service layer managing user authentication and account workflows."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_verification_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import Token, UserCreate


class AuthService:
    """Service providing user authentication and authorization logic."""

    def __init__(self, db_session: AsyncSession):
        self.user_repo = UserRepository(db_session)

    async def register_user(self, user_in: UserCreate) -> User:
        """Register a new user after verifying unique email."""
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        hashed_pw = get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_pw,
            role=user_in.role,
            is_active=True,
            is_superuser=False,
        )
        new_user = await self.user_repo.create(new_user)

        # Fire-and-forget: failures are logged inside send_verification_email
        # and never raised, so a broken mail server can't block registration.
        await send_verification_email(new_user.email, new_user.full_name)

        return new_user

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account.",
            )
        return user

    def generate_token_pair(self, user_id: int) -> Token:
        """Generate JWT access and refresh token pair."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh JWT access token using a valid refresh token."""
        payload = decode_token(refresh_token, settings.REFRESH_SECRET_KEY)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject.",
            )

        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or no longer exists.",
            )

        return self.generate_token_pair(user.id)