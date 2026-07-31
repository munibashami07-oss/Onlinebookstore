"""Service layer for authentication workflows."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_registration_confirmation_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


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
        created_user = await self.user_repo.create_user(user)
        await send_registration_confirmation_email(created_user.email, created_user.full_name)
        return created_user

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