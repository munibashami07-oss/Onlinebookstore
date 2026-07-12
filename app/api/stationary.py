"""API Router for Stationary merchandise catalog management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.stationary import Stationary
from app.models.user import User
from app.repositories.stationary_repository import StationaryRepository
from app.schemas.stationary import (
    StationaryCreate,
    StationaryResponse,
    StationaryUpdate,
)

router = APIRouter(prefix="/stationary", tags=["Stationary"])


@router.get(
    "",
    response_model=List[StationaryResponse],
    summary="List all stationary items",
)
async def list_stationary(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> List[StationaryResponse]:
    """Retrieve paginated list of stationary items."""
    stationary_repo = StationaryRepository(db)
    skip = (page - 1) * page_size
    return await stationary_repo.list_all(skip=skip, limit=page_size)


@router.get(
    "/{stationary_id}",
    response_model=StationaryResponse,
    summary="Get stationary item details by ID",
)
async def get_stationary_item(
    stationary_id: int,
    db: AsyncSession = Depends(get_db),
) -> StationaryResponse:
    """Retrieve details of a single stationary item by ID."""
    stationary_repo = StationaryRepository(db)
    item = await stationary_repo.get_by_id(stationary_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stationary item not found."
        )
    return item


@router.post(
    "",
    response_model=StationaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new stationary product (Admin only)",
)
async def create_stationary_item(
    payload: StationaryCreate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StationaryResponse:
    """Create a new stationary product (Admin privilege required)."""
    stationary_repo = StationaryRepository(db)
    item = Stationary(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        cover_image_url=payload.cover_image_url,
    )
    return await stationary_repo.create(item)


@router.put(
    "/{stationary_id}",
    response_model=StationaryResponse,
    summary="Update a stationary product (Admin only)",
)
async def update_stationary_item(
    stationary_id: int,
    payload: StationaryUpdate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StationaryResponse:
    """Update an existing stationary product (Admin privilege required)."""
    stationary_repo = StationaryRepository(db)
    item = await stationary_repo.get_by_id(stationary_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stationary item not found."
        )

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.price is not None:
        item.price = payload.price
    if payload.stock is not None:
        item.stock = payload.stock
    if payload.cover_image_url is not None:
        item.cover_image_url = payload.cover_image_url

    return await stationary_repo.update(item)


@router.delete(
    "/{stationary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stationary product (Admin only)",
)
async def delete_stationary_item(
    stationary_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a stationary product by ID (Admin privilege required)."""
    stationary_repo = StationaryRepository(db)
    item = await stationary_repo.get_by_id(stationary_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stationary item not found."
        )
    await stationary_repo.delete(stationary_id)
