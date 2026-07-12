"""FastAPI Router serving public-facing HTML views powered by Jinja2 templates."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.repositories.deal_repository import DealRepository
from app.repositories.genre_repository import GenreRepository
from app.repositories.stationary_repository import StationaryRepository
from app.services.book_service import BookService, BookServiceError
from app.services.review_service import ReviewService

router = APIRouter(tags=["Public Website Views"])
templates = Jinja2Templates(directory="app/templates")


# ── Home Page ────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse, summary="Homepage")
async def home_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render public bookstore home page with hero, featured books, deals, and genres."""
    book_service = BookService(db)
    genre_repo = GenreRepository(db)
    deal_repo = DealRepository(db)

    books = await book_service.list_books(skip=0, limit=12)
    genres = await genre_repo.list_all(skip=0, limit=10)
    deals = await deal_repo.list_active_deals()

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "active_page": "home",
            "books": books,
            "genres": genres,
            "deals": deals,
        },
    )


# ── Books Catalog ─────────────────────────────────────────────────────────────
@router.get("/books", response_class=HTMLResponse, summary="Books Catalog Page")
async def books_page(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Render paginated public book catalog."""
    book_service = BookService(db)
    skip = (page - 1) * page_size
    books = await book_service.list_books(skip=skip, limit=page_size)

    return templates.TemplateResponse(
        "books.html",
        {
            "request": request,
            "active_page": "books",
            "books": books,
            "page": page,
        },
    )


# ── Book Detail Page ──────────────────────────────────────────────────────────
@router.get("/books/{book_id}", response_class=HTMLResponse, summary="Book Details Page")
async def book_detail_page(
    request: Request,
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Render detailed view of a single book with synopsis and reviews."""
    book_service = BookService(db)
    review_service = ReviewService(db)

    try:
        book = await book_service.get_book_details(book_id)
        reviews = await review_service.get_book_reviews(book_id)
    except BookServiceError:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND
        )

    return templates.TemplateResponse(
        "book_detail.html",
        {
            "request": request,
            "active_page": "books",
            "book": book,
            "reviews": reviews,
        },
    )


# ── Genres List Page ──────────────────────────────────────────────────────────
@router.get("/genres", response_class=HTMLResponse, summary="Genres Overview Page")
async def genres_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render list of available book genres."""
    genre_repo = GenreRepository(db)
    genres = await genre_repo.list_all(skip=0, limit=100)

    return templates.TemplateResponse(
        "genres.html",
        {
            "request": request,
            "active_page": "genres",
            "genres": genres,
        },
    )


# ── Genre Books Page ──────────────────────────────────────────────────────────
@router.get("/genres/{genre_id}", response_class=HTMLResponse, summary="Genre Books Page")
async def genre_books_page(
    request: Request,
    genre_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Render books filtered by specific genre ID."""
    genre_repo = GenreRepository(db)
    book_service = BookService(db)

    genre = await genre_repo.get_by_id(genre_id)
    if not genre:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND
        )

    books = await book_service.get_books_by_genre(genre_id)

    return templates.TemplateResponse(
        "genre_books.html",
        {
            "request": request,
            "active_page": "genres",
            "genre": genre,
            "books": books,
        },
    )


# ── Stationary Page ───────────────────────────────────────────────────────────
@router.get("/stationary", response_class=HTMLResponse, summary="Stationary Page")
async def stationary_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render stationary merchandise showcase page."""
    stat_repo = StationaryRepository(db)
    items = await stat_repo.list_all(skip=0, limit=100)

    return templates.TemplateResponse(
        "stationary.html",
        {
            "request": request,
            "active_page": "stationary",
            "items": items,
        },
    )


# ── Deals Page ────────────────────────────────────────────────────────────────
@router.get("/deals", response_class=HTMLResponse, summary="Deals Page")
async def deals_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render active promotions and special offers page."""
    deal_repo = DealRepository(db)
    deals = await deal_repo.list_active_deals()

    return templates.TemplateResponse(
        "deals.html",
        {
            "request": request,
            "active_page": "deals",
            "deals": deals,
        },
    )


# ── Search Page ───────────────────────────────────────────────────────────────
@router.get("/search", response_class=HTMLResponse, summary="Search Results Page")
async def search_page(
    request: Request,
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Render search results for books matching title, author, or ISBN."""
    book_service = BookService(db)
    query_str = q.strip() if q else ""
    books = await book_service.search_books(query_str) if query_str else []

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "active_page": "",
            "query": query_str,
            "books": books,
        },
    )
