"""Service layer for book reviews and ratings."""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.book_repository import BookRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewServiceError(Exception):
    """Base exception for ReviewService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ReviewService:
    """Business logic for book reviews and aggregate ratings."""

    def __init__(self, db: AsyncSession) -> None:
        self.review_repo = ReviewRepository(db)
        self.book_repo = BookRepository(db)

    async def create_review(self, user_id: int, payload: ReviewCreate) -> Review:
        """Create a new book review.

        Args:
            user_id: Primary key of the reviewing user.
            payload: Validated ReviewCreate payload.

        Returns:
            Newly created Review ORM instance.

        Raises:
            ReviewServiceError: If book does not exist or user has already reviewed it.
        """
        book = await self.book_repo.get_book(payload.book_id)
        if not book:
            raise ReviewServiceError("Book not found.", status_code=404)

        existing = await self.review_repo.get_user_book_review(user_id, payload.book_id)
        if existing:
            raise ReviewServiceError(
                "You have already submitted a review for this book.", status_code=409
            )

        review = Review(
            user_id=user_id,
            book_id=payload.book_id,
            rating=payload.rating,
            review_text=payload.review_text,
        )
        return await self.review_repo.create_review(review)

    async def update_review(
        self, user_id: int, review_id: int, payload: ReviewUpdate
    ) -> Review:
        """Update an existing review owned by the user.

        Args:
            user_id: Primary key of the user.
            review_id: Primary key of the review.
            payload: Validated ReviewUpdate payload.

        Returns:
            Updated Review ORM instance.

        Raises:
            ReviewServiceError: If review not found or owned by another user.
        """
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewServiceError("Review not found.", status_code=404)
        if review.user_id != user_id:
            raise ReviewServiceError("Not authorized to update this review.", status_code=403)

        if payload.rating is not None:
            review.rating = payload.rating
        if payload.review_text is not None:
            review.review_text = payload.review_text

        return await self.review_repo.update_review(review)

    async def delete_review(self, user_id: int, review_id: int) -> None:
        """Delete a review owned by the user.

        Args:
            user_id: Primary key of the user.
            review_id: Primary key of the review.

        Raises:
            ReviewServiceError: If review not found or owned by another user.
        """
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewServiceError("Review not found.", status_code=404)
        if review.user_id != user_id:
            raise ReviewServiceError("Not authorized to delete this review.", status_code=403)

        await self.review_repo.delete_review(review_id)

    async def get_book_reviews(
        self, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        """Fetch paginated reviews for a book.

        Args:
            book_id: Primary key of the book.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Review ORM instances.
        """
        return await self.review_repo.get_book_reviews(book_id, skip=skip, limit=limit)

    async def get_average_rating_for_book(self, book_id: int) -> Dict[str, Any]:
        """Calculate average star rating and review count for a book.

        Args:
            book_id: Primary key of the book.

        Returns:
            Dict containing book_id, average_rating, and total_reviews.
        """
        reviews = await self.review_repo.get_book_reviews(book_id, skip=0, limit=1000)
        total_count = len(reviews)
        if total_count == 0:
            return {"book_id": book_id, "average_rating": 0.0, "total_reviews": 0}

        avg = sum(r.rating for r in reviews) / float(total_count)
        return {
            "book_id": book_id,
            "average_rating": round(avg, 2),
            "total_reviews": total_count,
        }
