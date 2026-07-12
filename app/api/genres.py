"""API Router for Genre catalog management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.genre import Genre
from app.models.user import User
from app.repositories.genre_repository import GenreRepository
from app.schemas.genre import GenreCreate, GenreResponse, GenreUpdate

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get(
    "",
    response_model=List[GenreResponse],
    summary="List all genres",
)
async def list_genres(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> List[GenreResponse]:
    """Retrieve paginated list of genres."""
    genre_repo = GenreRepository(db)
    skip = (page - 1) * page_size
    return await genre_repo.list_all(skip=skip, limit=page_size)


@router.get(
    "/{genre_id}",
    response_model=GenreResponse,
    summary="Get genre details by ID",
)
async def get_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
) -> GenreResponse:
    """Retrieve details of a single genre by ID."""
    genre_repo = GenreRepository(db)
    genre = await genre_repo.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found.")
    return genre


@router.post(
    "",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new genre (Admin only)",
)
async def create_genre(
    payload: GenreCreate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GenreResponse:
    """Create a new genre (Admin privilege required)."""
    genre_repo = GenreRepository(db)
    existing = await genre_repo.get_by_name(payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A genre with this name already exists.",
        )
    genre = Genre(name=payload.name, description=payload.description)
    return await genre_repo.create(genre)


@router.put(
    "/{genre_id}",
    response_model=GenreResponse,
    summary="Update a genre (Admin only)",
)
async def update_genre(
    genre_id: int,
    payload: GenreUpdate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GenreResponse:
    """Update an existing genre (Admin privilege required)."""
    genre_repo = GenreRepository(db)
    genre = await genre_repo.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found.")

    if payload.name is not None:
        genre.name = payload.name
    if payload.description is not None:
        genre.description = payload.description

    return await genre_repo.update(genre)


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a genre (Admin only)",
)
async def delete_genre(
    genre_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a genre by ID (Admin privilege required)."""
    genre_repo = GenreRepository(db)
    genre = await genre_repo.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found.")
    await genre_repo.delete(genre_id)
