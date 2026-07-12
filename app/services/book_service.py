"""Service layer for Book catalog browsing, search, and management."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.inventory import Inventory
from app.repositories.book_repository import BookRepository
from app.repositories.genre_repository import GenreRepository
from app.schemas.book import BookCreate, BookUpdate


class BookServiceError(Exception):
    """Base exception for BookService errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BookService:
    """Business logic for book catalog management, search, and filtering."""

    def __init__(self, db: AsyncSession) -> None:
        self.book_repo = BookRepository(db)
        self.genre_repo = GenreRepository(db)

    async def get_book_details(self, book_id: int) -> Book:
        """Fetch details of a single book by ID.

        Args:
            book_id: Primary key of the book.

        Returns:
            Book ORM instance with loaded relationships.

        Raises:
            BookServiceError: If book is not found.
        """
        book = await self.book_repo.get_book(book_id)
        if not book:
            raise BookServiceError("Book not found.", status_code=404)
        return book

    async def list_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """Browse paginated book list.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Book ORM instances.
        """
        return await self.book_repo.list_books(skip=skip, limit=limit)

    async def search_books(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Search books by title, author, or ISBN.

        Args:
            query: Search query string.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching Book ORM instances.
        """
        if not query.strip():
            return await self.list_books(skip=skip, limit=limit)
        return await self.book_repo.search_books(query=query, skip=skip, limit=limit)

    async def get_books_by_genre(
        self, genre_id: int, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """Filter books by genre ID.

        Args:
            genre_id: Primary key of the genre.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Book ORM instances in the specified genre.

        Raises:
            BookServiceError: If genre is not found.
        """
        genre = await self.genre_repo.get_by_id(genre_id)
        if not genre:
            raise BookServiceError("Genre not found.", status_code=404)
        return await self.book_repo.get_books_by_genre(
            genre_id=genre_id, skip=skip, limit=limit
        )

    async def create_book(self, payload: BookCreate) -> Book:
        """Create a new book record.

        Args:
            payload: Validated BookCreate payload.

        Returns:
            Newly created Book ORM instance.

        Raises:
            BookServiceError: If genre does not exist or ISBN already exists.
        """
        genre = await self.genre_repo.get_by_id(payload.genre_id)
        if not genre:
            raise BookServiceError("Specified genre does not exist.", status_code=404)

        existing_isbn = await self.book_repo.get_by_isbn(payload.isbn)
        if existing_isbn:
            raise BookServiceError(
                "A book with this ISBN already exists.", status_code=409
            )

        book = Book(
            title=payload.title,
            author=payload.author,
            isbn=payload.isbn,
            price=payload.price,
            description=payload.description,
            cover_image_url=payload.cover_image_url,
            genre_id=payload.genre_id,
        )
        created_book = await self.book_repo.create_book(book)

    # Ensure every new book has a matching inventory row so stock
    # can be managed via the Inventory Stock admin panel right away.
        inventory = Inventory(book_id=created_book.id, stock_quantity=0, low_stock_threshold=5)
        self.book_repo.db.add(inventory)
        await self.book_repo.db.flush()
        await self.book_repo.db.refresh(inventory)

    # Attach it directly so response serialization doesn't need to
    # lazy-load the relationship on an async session.
        created_book.inventory = inventory

        return created_book
        

    async def update_book(self, book_id: int, payload: BookUpdate) -> Book:
        """Update an existing book record.

        Args:
            book_id: Primary key of the book.
            payload: Validated BookUpdate payload.

        Returns:
            Updated Book ORM instance.

        Raises:
            BookServiceError: If book or target genre is not found.
        """
        book = await self.book_repo.get_book(book_id)
        if not book:
            raise BookServiceError("Book not found.", status_code=404)

        if payload.genre_id is not None:
            genre = await self.genre_repo.get_by_id(payload.genre_id)
            if not genre:
                raise BookServiceError("Target genre does not exist.", status_code=404)
            book.genre_id = payload.genre_id

        if payload.title is not None:
            book.title = payload.title
        if payload.author is not None:
            book.author = payload.author
        if payload.isbn is not None:
            book.isbn = payload.isbn
        if payload.price is not None:
            book.price = payload.price
        if payload.description is not None:
            book.description = payload.description
        if payload.cover_image_url is not None:
            book.cover_image_url = payload.cover_image_url

        return await self.book_repo.update_book(book)

    async def delete_book(self, book_id: int) -> None:
        """Delete a book record by ID.

        Args:
            book_id: Primary key of the book.

        Raises:
            BookServiceError: If book is not found.
        """
        book = await self.book_repo.get_book(book_id)
        if not book:
            raise BookServiceError("Book not found.", status_code=404)

        await self.book_repo.delete_book(book_id)
