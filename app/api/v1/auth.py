"""Authentication API Router for registration, login, refresh, and profile endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new customer account."""
    auth_service = AuthService(db)
    new_user = await auth_service.register_user(user_in)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="User Login for JWT Token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """OAuth2 compatible token login, returning access and refresh tokens."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    return auth_service.generate_token_pair(user.id)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh JWT Access Token",
)
async def refresh_token(
    payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> Token:
    """Get new token pair using a valid refresh token."""
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile of authenticated user."""
    return current_user
