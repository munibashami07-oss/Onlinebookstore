"""Repository Layer Initialization & Registry."""

from app.repositories.user_repository import UserRepository
from app.repositories.book_repository import BookRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.genre_repository import GenreRepository
from app.repositories.stationary_repository import StationaryRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.admin_repository import AdminRepository

__all__ = [
    "UserRepository",
    "BookRepository",
    "InventoryRepository",
    "CartRepository",
    "OrderRepository",
    "PaymentRepository",
    "ReviewRepository",
    "GenreRepository",
    "StationaryRepository",
    "DealRepository",
    "AdminRepository",
]
