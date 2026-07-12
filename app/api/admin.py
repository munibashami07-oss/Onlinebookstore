"""API Router for Admin Operations, Management CRUD, Dashboard, and Analytics."""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.deal import Deal
from app.models.genre import Genre
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.models.stationary import Stationary
from app.models.user import User
from app.repositories.deal_repository import DealRepository
from app.repositories.genre_repository import GenreRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.stationary_repository import StationaryRepository
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.genre import GenreCreate, GenreResponse, GenreUpdate
from app.schemas.inventory import InventoryResponse, InventoryUpdate
from app.schemas.order import OrderResponse
from app.schemas.payment import PaymentResponse
from app.schemas.stationary import StationaryCreate, StationaryResponse, StationaryUpdate
from app.schemas.user import UserResponse
from app.services.admin_service import AdminService
from app.services.book_service import BookService, BookServiceError
from app.services.inventory_service import InventoryService, InventoryServiceError
from app.services.order_service import OrderService, OrderServiceError
from app.services.user_service import UserService, UserServiceError

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin)],
)


# ==========================================
# 0. File Upload Endpoint
# ==========================================

@router.post(
    "/upload",
    summary="Upload image file to static storage (Admin only)",
)
async def upload_image_file(
    file: UploadFile = File(...),
) -> Dict[str, str]:
    """Upload an image file (jpg, png, webp, gif, svg) and return its static URL."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed.",
        )

    extension = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if extension not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
        extension = ".jpg"

    filename = f"{uuid.uuid4().hex}{extension}"

    target_dir = os.path.join("app", "static", "uploads")
    if not os.path.exists("app/static") and os.path.exists("static"):
        target_dir = os.path.join("static", "uploads")

    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"url": f"/static/uploads/{filename}"}


# ==========================================
# 1. Dashboard
# ==========================================


@router.get(
    "/dashboard",
    summary="Get high-level admin dashboard metrics",
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve aggregate statistics for admin dashboard."""
    admin_service = AdminService(db)
    return await admin_service.get_dashboard_statistics()


# ==========================================
# 2. Users Management
# ==========================================

@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
)
async def list_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """List all registered users with pagination."""
    user_service = UserService(db)
    skip = (page - 1) * page_size
    return await user_service.user_repo.list_users(skip=skip, limit=page_size)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user profile details by ID",
)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve user details by primary key."""
    user_service = UserService(db)
    try:
        return await user_service.get_profile(user_id)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user account",
)
async def delete_user_account(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user account by primary key."""
    user_service = UserService(db)
    try:
        await user_service.delete_account(user_id)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==========================================
# 3. Books Admin CRUD
# ==========================================

@router.get("/books", response_model=List[BookResponse], summary="List books (Admin)")
async def admin_list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[BookResponse]:
    """Retrieve catalog books for admin."""
    book_service = BookService(db)
    skip = (page - 1) * page_size
    return await book_service.list_books(skip=skip, limit=page_size)


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED, summary="Create book")
async def admin_create_book(
    payload: BookCreate,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Add a new book to catalog."""
    book_service = BookService(db)
    try:
        return await book_service.create_book(payload)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/books/{book_id}", response_model=BookResponse, summary="Update book")
async def admin_update_book(
    book_id: int,
    payload: BookUpdate,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Update existing book record."""
    book_service = BookService(db)
    try:
        return await book_service.update_book(book_id, payload)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete book")
async def admin_delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete book record."""
    book_service = BookService(db)
    try:
        await book_service.delete_book(book_id)
    except BookServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==========================================
# 4. Genres Admin CRUD
# ==========================================

@router.get("/genres", response_model=List[GenreResponse], summary="List genres")
async def admin_list_genres(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[GenreResponse]:
    genre_repo = GenreRepository(db)
    return await genre_repo.list_all(skip=skip, limit=limit)


@router.post("/genres", response_model=GenreResponse, status_code=status.HTTP_201_CREATED, summary="Create genre")
async def admin_create_genre(
    payload: GenreCreate,
    db: AsyncSession = Depends(get_db),
) -> GenreResponse:
    genre_repo = GenreRepository(db)
    genre = Genre(name=payload.name, description=payload.description)
    return await genre_repo.create(genre)


@router.put("/genres/{genre_id}", response_model=GenreResponse, summary="Update genre")
async def admin_update_genre(
    genre_id: int,
    payload: GenreUpdate,
    db: AsyncSession = Depends(get_db),
) -> GenreResponse:
    genre_repo = GenreRepository(db)
    genre = await genre_repo.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found.")
    if payload.name:
        genre.name = payload.name
    if payload.description is not None:
        genre.description = payload.description
    return await genre_repo.update(genre)


@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete genre")
async def admin_delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    genre_repo = GenreRepository(db)
    await genre_repo.delete(genre_id)


# ==========================================
# 5. Stationary Admin CRUD
# ==========================================

@router.get("/stationary", response_model=List[StationaryResponse], summary="List stationary")
async def admin_list_stationary(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[StationaryResponse]:
    repo = StationaryRepository(db)
    return await repo.list_all(skip=skip, limit=limit)


@router.post("/stationary", response_model=StationaryResponse, status_code=status.HTTP_201_CREATED, summary="Create stationary")
async def admin_create_stationary(
    payload: StationaryCreate,
    db: AsyncSession = Depends(get_db),
) -> StationaryResponse:
    repo = StationaryRepository(db)
    item = Stationary(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        cover_image_url=payload.cover_image_url,
    )
    return await repo.create(item)


@router.put("/stationary/{stationary_id}", response_model=StationaryResponse, summary="Update stationary")
async def admin_update_stationary(
    stationary_id: int,
    payload: StationaryUpdate,
    db: AsyncSession = Depends(get_db),
) -> StationaryResponse:
    repo = StationaryRepository(db)
    item = await repo.get_by_id(stationary_id)
    if not item:
        raise HTTPException(status_code=404, detail="Stationary item not found.")
    if payload.name:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.price is not None:
        item.price = payload.price
    if payload.stock is not None:
        item.stock = payload.stock
    if payload.cover_image_url is not None:
        item.cover_image_url = payload.cover_image_url
    return await repo.update(item)


@router.delete("/stationary/{stationary_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete stationary")
async def admin_delete_stationary(
    stationary_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = StationaryRepository(db)
    await repo.delete(stationary_id)


# ==========================================
# 6. Deals Admin CRUD
# ==========================================

@router.get("/deals", summary="List deals")
async def admin_list_deals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    repo = DealRepository(db)
    deals = await repo.list_all(skip=skip, limit=limit)
    return [
        {
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "discount_percentage": float(d.discount_percentage),
            "start_date": d.start_date,
            "end_date": d.end_date,
            "is_active": d.is_active,
        }
        for d in deals
    ]


# ==========================================
# 7. Inventory Admin Operations
# ==========================================

@router.get("/inventory/low-stock", response_model=List[InventoryResponse], summary="Get low stock report")
async def admin_low_stock_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[InventoryResponse]:
    admin_service = AdminService(db)
    skip = (page - 1) * page_size
    items = await admin_service.admin_repo.get_low_stock_inventory(skip=skip, limit=page_size)
    return items


@router.post("/inventory/{book_id}/increase", response_model=InventoryResponse, summary="Increase stock")
async def admin_increase_stock(
    book_id: int,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
) -> InventoryResponse:
    inv_service = InventoryService(db)
    try:
        return await inv_service.increase_stock(book_id, quantity)
    except InventoryServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/inventory/{book_id}/decrease", response_model=InventoryResponse, summary="Decrease stock")
async def admin_decrease_stock(
    book_id: int,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
) -> InventoryResponse:
    inv_service = InventoryService(db)
    try:
        return await inv_service.decrease_stock(book_id, quantity)
    except InventoryServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==========================================
# 8. Orders Admin Operations
# ==========================================

@router.get("/orders", response_model=List[OrderResponse], summary="View all orders")
async def admin_view_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[OrderResponse]:
    order_service = OrderService(db)
    skip = (page - 1) * page_size
    return await order_service.list_all_orders(skip=skip, limit=page_size)


@router.get("/orders/{order_id}", response_model=OrderResponse, summary="View order details")
async def admin_view_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order_service = OrderService(db)
    try:
        return await order_service.get_order_details(order_id)
    except OrderServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/orders/{order_id}/status", response_model=OrderResponse, summary="Update order status")
async def admin_update_order_status(
    order_id: int,
    order_status: OrderStatus = Query(...),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order_service = OrderService(db)
    try:
        return await order_service.update_order_status(order_id, order_status)
    except OrderServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==========================================
# 9. Payments Admin Operations
# ==========================================

@router.get("/payments", response_model=List[PaymentResponse], summary="View and filter payments")
async def admin_view_payments(
    status_filter: Optional[PaymentStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[PaymentResponse]:
    pay_repo = PaymentRepository(db)
    # Basic fetch
    if status_filter:
        payment = await pay_repo.get_by_id(1)  # stub lookup or list
        return [payment] if payment else []
    return []


# ==========================================
# 10. Reports
# ==========================================

@router.get("/reports/top-selling-books", summary="Report: Top Selling Books")
async def report_top_selling_books(
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    admin_service = AdminService(db)
    return await admin_service.get_top_selling_books(limit=limit)


@router.get("/reports/top-rated-books", summary="Report: Top Rated Books")
async def report_top_rated_books(
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    admin_service = AdminService(db)
    return await admin_service.get_top_rated_books(limit=limit)


@router.get("/reports/most-purchased-genres", summary="Report: Most Purchased Genres")
async def report_most_purchased_genres(
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    admin_service = AdminService(db)
    return await admin_service.get_most_purchased_genres(limit=limit)


@router.get("/reports/revenue", summary="Report: Daily, Weekly, Monthly Revenue")
async def report_revenue(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    admin_service = AdminService(db)
    return await admin_service.get_revenue_report()

@router.get(
    "/dashboard/monthly-revenue",
    summary="Monthly revenue for dashboard chart",
)
async def get_monthly_revenue(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    admin_service = AdminService(db)
    return await admin_service.get_monthly_revenue()

@router.get(
    "/dashboard/daily-sales",
    summary="Daily sales for a selected month",
)
async def get_daily_sales(
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    admin_service = AdminService(db)
    return await admin_service.get_daily_sales(month)