"""Service Layer Initialization & Registry."""

from app.services.auth_service import AuthService, AuthServiceError
from app.services.user_service import UserService, UserServiceError
from app.services.book_service import BookService, BookServiceError
from app.services.cart_service import CartService, CartServiceError
from app.services.checkout_service import CheckoutService, CheckoutServiceError
from app.services.payment_service import PaymentService, PaymentServiceError
from app.services.inventory_service import InventoryService, InventoryServiceError
from app.services.deal_service import DealService, DealServiceError
from app.services.review_service import ReviewService, ReviewServiceError
from app.services.recommendation_service import RecommendationService, RecommendationServiceError
from app.services.admin_service import AdminService, AdminServiceError

__all__ = [
    "AuthService",
    "AuthServiceError",
    "UserService",
    "UserServiceError",
    "BookService",
    "BookServiceError",
    "CartService",
    "CartServiceError",
    "CheckoutService",
    "CheckoutServiceError",
    "PaymentService",
    "PaymentServiceError",
    "InventoryService",
    "InventoryServiceError",
    "DealService",
    "DealServiceError",
    "ReviewService",
    "ReviewServiceError",
    "RecommendationService",
    "RecommendationServiceError",
    "AdminService",
    "AdminServiceError",
]
