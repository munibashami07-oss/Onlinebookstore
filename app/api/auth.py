# force-rebuild-marker
"""Authentication API router endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new customer account using AuthService.

    Args:
        payload: Registration request body.
        db: Injected database session.

    Returns:
        Created UserResponse model (excluding password hashes).
    """
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(payload)
        return user
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user credentials for JWT token pair",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth2 compatible password login endpoint returning JWT access & refresh tokens.

    Args:
        form_data: Standard OAuth2 form data containing username (email) and password.
        db: Injected database session.

    Returns:
        TokenResponse containing access_token, refresh_token, and token_type.
    """
    auth_service = AuthService(db)
    try:
        login_payload = LoginRequest(
            email=form_data.username,
            password=form_data.password,
        )
        tokens = await auth_service.login(login_payload)
        return tokens
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Obtain a new access token using a valid refresh token",
)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """Validate refresh token and issue a new access token.

    Args:
        payload: Refresh token request body.
        db: Injected database session.

    Returns:
        RefreshTokenResponse containing new access_token.
    """
    auth_service = AuthService(db)
    try:
        tokens = await auth_service.refresh_token(payload.refresh_token)
        return RefreshTokenResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout endpoint (Token revocation architecture)",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Logout current user.
    
    NOTE: Prepared architecture for token blocklist / Redis revocation.
    Client should drop tokens on client-side.
    """
    return {
        "status": "success",
        "message": f"Successfully logged out user '{current_user.email}'. Client should discard stored tokens.",
    }


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request a password reset email",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a password reset link to the given email, if an account exists.

    Always returns the same generic success message regardless of whether
    the email is registered, so this endpoint can't be used to enumerate
    accounts.
    """
    auth_service = AuthService(db)
    await auth_service.forgot_password(payload.email)
    return {
        "status": "success",
        "message": "If an account exists for that email, a reset link is on its way.",
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset a password using a token from the reset email",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Redeem a reset token and set a new password."""
    auth_service = AuthService(db)
    try:
        await auth_service.reset_password(payload.token, payload.new_password)
        return {"status": "success", "message": "Password has been reset. You can now sign in."}
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Retrieve profile data of the currently authenticated active user.

    Args:
        current_user: Injected authenticated active user.

    Returns:
        UserResponse model of the current user.
    """
    return current_user