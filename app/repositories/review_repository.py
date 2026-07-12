"""Repository for Review database operations."""

from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review


class ReviewRepository:
    """Data access layer for the Review model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_review(self, review: Review) -> Review:
        """Insert a new review record."""
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_by_id(self, review_id: int) -> Optional[Review]:
        """Fetch a single review by primary key."""
        stmt = select(Review).where(Review.id == review_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_book_reviews(
        self, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        """Fetch paginated reviews for a specific book."""
        stmt = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.book_id == book_id)
            .offset(skip)
            .limit(limit)
            .order_by(Review.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_reviews(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        """Fetch paginated reviews written by a specific user."""
        stmt = (
            select(Review)
            .options(selectinload(Review.book))
            .where(Review.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Review.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_book_review(
        self, user_id: int, book_id: int
    ) -> Optional[Review]:
        """Fetch a specific review by user and book composite."""
        stmt = select(Review).where(
            Review.user_id == user_id,
            Review.book_id == book_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_review(self, review: Review) -> Review:
        """Persist changes to an existing review."""
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def delete_review(self, review_id: int) -> None:
        """Delete a review by primary key."""
        stmt = delete(Review).where(Review.id == review_id)
        await self.db.execute(stmt)
        await self.db.flush()
