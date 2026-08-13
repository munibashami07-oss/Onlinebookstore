"""Service layer for authentication workflows."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email_verification import create_email_verification_token
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User, UserRole
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.email_service import send_password_reset_email, send_verification_email

logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    """Base exception for AuthService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthService:
    """Business logic for user registration, login, and token management."""

    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)
        self.reset_repo = PasswordResetRepository(db)

    async def register(self, payload: RegisterRequest) -> User:
        """Register a new customer account.

        Args:
            payload: Validated registration request data.

        Returns:
            Newly created User instance.

        Raises:
            AuthServiceError: If email is already registered.
        """
        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise AuthServiceError(
                "A user with this email address already exists.", status_code=409
            )

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_superuser=False,
        )
        user = await self.user_repo.create_user(user)

        # Send the confirmation email, but never let a mail failure block
        # registration -- the account is already created at this point.
        try:
            token = create_email_verification_token(user.email)
            verify_url = (
                f"{settings.BACKEND_BASE_URL}{settings.API_V1_STR}"
                f"/verify-email?token={token}"
            )
            await send_verification_email(user.email, user.full_name, verify_url)
        except Exception:
            logger.exception(
                "Failed to send verification email during registration for %s",
                user.email,
            )

        return user

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue token pair.

        Args:
            payload: Validated login request data.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthServiceError: If credentials are invalid or account is inactive.
        """
        user = await self.user_repo.get_by_email(payload.email)
        if not user:
            raise AuthServiceError(
                "Incorrect email or password.", status_code=401
            )

        if not verify_password(payload.password, user.hashed_password):
            raise AuthServiceError(
                "Incorrect email or password.", status_code=401
            )

        if not user.is_active:
            raise AuthServiceError(
                "User account is deactivated.", status_code=403
            )

        return self._generate_token_pair(user.id)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token.

        Args:
            refresh_token: JWT refresh token string.

        Returns:
            New TokenResponse pair.

        Raises:
            AuthServiceError: If refresh token is invalid or user not found.
        """
        payload = decode_token(refresh_token, settings.REFRESH_SECRET_KEY)
        if payload is None or payload.get("type") != "refresh":
            raise AuthServiceError(
                "Invalid or expired refresh token.", status_code=401
            )

        user_id = payload.get("sub")
        if not user_id:
            raise AuthServiceError("Invalid token payload.", status_code=401)

        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise AuthServiceError(
                "User not found or account deactivated.", status_code=401
            )

        return self._generate_token_pair(user.id)

    async def forgot_password(self, email: str) -> None:
        """Issue a password reset token and email it, if the account exists.

        Always succeeds from the caller's perspective regardless of
        whether `email` belongs to a real account -- this prevents the
        endpoint from being used to enumerate registered emails. Only a
        real, existing user actually gets a token generated and an email
        sent; for anyone else this is a silent no-op.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            return

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
        )

        await self.reset_repo.create_token(
            PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        )

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        try:
            await send_password_reset_email(user.email, reset_url)
        except Exception:
            # Don't leak email-delivery failures to the client -- the
            # token still exists in the DB either way; log-and-swallow
            # is handled inside email_service. Re-raising here would
            # reveal "this email exists but sending failed", which is
            # itself an enumeration signal.
            pass

    async def reset_password(self, token: str, new_password: str) -> None:
        """Redeem a password reset token and set the account's new password.

        Raises:
            AuthServiceError: if the token is missing, expired, or already used.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = await self.reset_repo.get_valid_token(token_hash)
        if not reset_token:
            raise AuthServiceError(
                "This reset link is invalid or has expired. Please request a new one.",
                status_code=400,
            )

        user = await self.user_repo.get_by_id(reset_token.user_id)
        if not user or not user.is_active:
            raise AuthServiceError(
                "This reset link is invalid or has expired. Please request a new one.",
                status_code=400,
            )

        user.hashed_password = get_password_hash(new_password)
        await self.user_repo.update_user(user)
        await self.reset_repo.mark_used(reset_token)

    def _generate_token_pair(self, user_id: int) -> TokenResponse:
        """Generate access and refresh JWT token pair.

        Args:
            user_id: The user's primary key.

        Returns:
            TokenResponse containing both tokens.
        """
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )