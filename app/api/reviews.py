"""API Router for Book Reviews and Ratings."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review_service import ReviewService, ReviewServiceError

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "/book/{book_id}",
    response_model=List[ReviewResponse],
    summary="Get all reviews for a book",
)
async def get_book_reviews(
    book_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewResponse]:
    """Retrieve paginated list of reviews for a specific book."""
    review_service = ReviewService(db)
    skip = (page - 1) * page_size
    reviews = await review_service.get_book_reviews(book_id, skip=skip, limit=page_size)
    return reviews


@router.get(
    "/book/{book_id}/rating",
    summary="Get average rating and review count for a book",
)
async def get_book_average_rating(
    book_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Calculate average star rating and total review count for a book."""
    review_service = ReviewService(db)
    return await review_service.get_average_rating_for_book(book_id)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for a book (Authenticated user)",
)
async def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Submit a star rating and text review for a book."""
    review_service = ReviewService(db)
    try:
        return await review_service.create_review(current_user.id, payload)
    except ReviewServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Update a review (Authenticated owner only)",
)
async def update_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Update an existing review owned by the authenticated user."""
    review_service = ReviewService(db)
    try:
        return await review_service.update_review(current_user.id, review_id, payload)
    except ReviewServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review (Authenticated owner only)",
)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a review owned by the authenticated user."""
    review_service = ReviewService(db)
    try:
        await review_service.delete_review(current_user.id, review_id)
    except ReviewServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
