"""OAuth2 Bearer authentication dependencies."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.security.jwt import verify_token
from app.security.permissions import RoleChecker

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# `auto_error=False` is the key difference from `oauth2_scheme` above: if no
# Authorization header is present, FastAPI passes `None` through instead of
# raising a 401 itself. This lets endpoints that should work for BOTH guests
# and logged-in users (like the public chatbot) tell the two cases apart
# without an anonymous visitor ever hitting an auth error / triggering the
# frontend's token-refresh flow.
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and authenticate user from Bearer JWT Access Token.

    Args:
        token: Bearer JWT token string.
        db: Async DB session.

    Returns:
        Authenticated User instance.

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, token_type="access")
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id_str))
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that currently authenticated user is active.

    Args:
        current_user: User obtained from get_current_user dependency.

    Returns:
        Active User instance.

    Raises:
        HTTPException 403: If user account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Enforce that currently authenticated active user has admin privileges.

    Args:
        current_user: Active User obtained from get_current_active_user.

    Returns:
        Admin User instance.

    Raises:
        HTTPException 403: If user lacks admin role.
    """
    admin_checker = RoleChecker([UserRole.ADMIN])
    return admin_checker(current_user)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Best-effort authentication for endpoints usable by guests AND users.

    Unlike `get_current_user`, this NEVER raises on a missing/invalid/expired
    token -- it simply returns None, so the endpoint can treat the caller as
    an anonymous guest. Use this (not `Optional[User] = Depends(get_current_active_user)`)
    anywhere guests must be able to call the endpoint, since `get_current_user`
    raises 401 unconditionally via `oauth2_scheme` the moment no bearer token
    is present, regardless of how the return type is annotated.

    Args:
        token: Bearer JWT token string, or None if no Authorization header.
        db: Async DB session.

    Returns:
        Authenticated + active User instance, or None for guests / invalid tokens.
    """
    if not token:
        return None

    payload = verify_token(token, token_type="access")
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id_str))
    if not user or not user.is_active:
        return None

    return user