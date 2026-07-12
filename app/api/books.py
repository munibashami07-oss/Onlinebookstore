"""API Router for Book Catalog browsing, search, and admin management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.user import User
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService, BookServiceError

router = APIRouter(prefix="/books", tags=["Books"])


@router.get(
    "",
    response_model=List[BookResponse],
    summary="Browse and filter books catalog",
)
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    genre_id: Optional[int] = Query(None, description="Filter by Genre ID"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter available stock only"),
    sort_by: Optional[str] = Query(
    None,
    pattern="^(price_asc|price_desc|newest)$",
    description="Sort by: price_asc, price_desc, newest",
    ),
    db: AsyncSession = Depends(get_db),
) -> List[BookResponse]:
    """Retrieve catalog books supporting pagination, filtering, and sorting."""
    book_service = BookService(db)
    skip = (page - 1) * page_size

    if genre_id is not None:
        books = await book_service.get_books_by_genre(genre_id, skip=skip, limit=page_size)
    else:
        books = await book_service.list_books(skip=skip, limit=page_size)

    # In-memory filtering for price and availability if provided
    if min_price is not None:
        books = [b for b in books if float(b.price) >= min_price]
    if max_price is not None:
        books = [b for b in books if float(b.price) <= max_price]
    if in_stock is True:
        books = [b for b in books if b.inventory and b.inventory.stock_quantity > 0]

    # Sorting options
    if sort_by == "price_asc":
        books = sorted(books, key=lambda b: float(b.price))
    elif sort_by == "price_desc":
        books = sorted(books, key=lambda b: float(b.price), reverse=True)
    elif sort_by == "newest":
        books = sorted(books, key=lambda b: b.created_at, reverse=True)

    return books


@router.get(
    "/search",
    response_model=List[BookResponse],
    summary="Search books by title, author, or ISBN",
)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query term"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> List[BookResponse]:
    """Search book catalog by title, author name, or ISBN number."""
    book_service = BookService(db)
    skip = (page - 1) * page_size
    return await book_service.search_books(query=q, skip=skip, limit=page_size)


@router.get(
    "/genre/{genre_id}",
    response_model=List[BookResponse],
    summary="Get books by genre ID",
)
async def get_books_by_genre(
    genre_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> List[BookResponse]:
    """Retrieve books belonging to a specific genre."""
    book_service = BookService(db)
    skip = (page - 1) * page_size
    try:
        return await book_service.get_books_by_genre(genre_id, skip=skip, limit=page_size)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get book details by ID",
)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Retrieve details of a single book."""
    book_service = BookService(db)
    try:
        return await book_service.get_book_details(book_id)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book (Admin only)",
)
async def create_book(
    payload: BookCreate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Add a new book to the catalog (Admin privilege required)."""
    book_service = BookService(db)
    try:
        return await book_service.create_book(payload)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update a book (Admin only)",
)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Update an existing book record (Admin privilege required)."""
    book_service = BookService(db)
    try:
        return await book_service.update_book(book_id, payload)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book (Admin only)",
)
async def delete_book(
    book_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a book record from the catalog (Admin privilege required)."""
    book_service = BookService(db)
    try:
        await book_service.delete_book(book_id)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
