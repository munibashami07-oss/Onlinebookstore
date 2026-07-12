"""API Router for User Profile and User Management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_current_admin, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService, UserServiceError

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Retrieve profile data for the authenticated active user."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current authenticated user profile",
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update profile data for the authenticated active user."""
    user_service = UserService(db)
    try:
        updated_user = await user_service.update_profile(current_user.id, payload)
        return updated_user
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete the account of the currently authenticated active user."""
    user_service = UserService(db)
    try:
        await user_service.delete_account(current_user.id)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List all users (Admin only)",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """Retrieve paginated list of users (Admin privilege required)."""
    user_service = UserService(db)
    skip = (page - 1) * page_size
    users = await user_service.user_repo.list_users(skip=skip, limit=page_size)
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details by ID (Admin only)",
)
async def get_user_by_id(
    user_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve details of a specific user by ID (Admin privilege required)."""
    user_service = UserService(db)
    try:
        user = await user_service.get_profile(user_id)
        return user
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
