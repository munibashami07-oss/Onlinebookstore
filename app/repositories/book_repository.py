"""Repository for Book database operations."""

from typing import List, Optional
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book


class BookRepository:
    """Data access layer for the Book model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_book(self, book: Book) -> Book:
        """Insert a new book record."""
        self.db.add(book)
        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def get_book(self, book_id: int) -> Optional[Book]:
        """Fetch a single book by primary key with eager-loaded genre."""
        stmt = (
            select(Book)
            .options(selectinload(Book.genre), selectinload(Book.inventory))
            .where(Book.id == book_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Fetch a single book by ISBN."""
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_books(
        self, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Fetch a paginated list of books."""
        stmt = (
            select(Book)
            .options(selectinload(Book.genre), selectinload(Book.inventory))
            .offset(skip)
            .limit(limit)
            .order_by(Book.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_books(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Search books by title, author, or ISBN partial match."""
        search_term = f"%{query}%"
        stmt = (
            select(Book)
            .options(selectinload(Book.genre), selectinload(Book.inventory))
            .where(
                or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term),
                    Book.isbn.ilike(search_term),
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Book.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_books_by_genre(
        self, genre_id: int, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Fetch books filtered by genre foreign key."""
        stmt = (
            select(Book)
            .options(selectinload(Book.genre), selectinload(Book.inventory))
            .where(Book.genre_id == genre_id)
            .offset(skip)
            .limit(limit)
            .order_by(Book.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_book(self, book: Book) -> Book:
        """Persist changes to an existing book instance."""
        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def delete_book(self, book_id: int) -> None:
        """Delete a book by primary key."""
        stmt = delete(Book).where(Book.id == book_id)
        await self.db.execute(stmt)
        await self.db.flush()