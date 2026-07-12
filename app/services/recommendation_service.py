"""Service layer defining book recommendation system architecture."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository


class RecommendationServiceError(Exception):
    """Base exception for RecommendationService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RecommendationService:
    """Business logic for book recommendations architecture (rule-based pre-AI setup)."""

    def __init__(self, db: AsyncSession) -> None:
        self.book_repo = BookRepository(db)
        self.order_repo = OrderRepository(db)
        self.review_repo = ReviewRepository(db)

    async def get_recommended_books_for_user(
        self, user_id: int, limit: int = 5
    ) -> List[Book]:
        """Fetch personalized book recommendations for a user.
        
        NOTE: Architecture placeholder for vector-search / RAG recommendation engine (Phase 13).
        Currently falls back to popular catalog items.

        Args:
            user_id: Primary key of the user.
            limit: Maximum number of recommended books.

        Returns:
            List of recommended Book ORM instances.
        """
        # Fallback heuristic: Return top catalog books
        return await self.book_repo.list_books(skip=0, limit=limit)

    async def get_similar_books(self, book_id: int, limit: int = 5) -> List[Book]:
        """Fetch books similar to a given book based on genre.

        Args:
            book_id: Primary key of the target book.
            limit: Maximum number of similar books.

        Returns:
            List of similar Book ORM instances.

        Raises:
            RecommendationServiceError: If target book does not exist.
        """
        target_book = await self.book_repo.get_book(book_id)
        if not target_book:
            raise RecommendationServiceError("Target book not found.", status_code=404)

        genre_books = await self.book_repo.get_books_by_genre(
            target_book.genre_id, skip=0, limit=limit + 1
        )
        # Exclude current book
        similar = [b for b in genre_books if b.id != book_id][:limit]
        return similar
