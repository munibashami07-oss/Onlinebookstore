"""SQLAlchemy 2.0 ORM Models Initialization & Registry."""

from app.models.base import Base, TimestampMixin
from app.models.user import User, UserRole
from app.models.admin import Admin
from app.models.genre import Genre
from app.models.deal import Deal, book_deals, stationary_deals
from app.models.book import Book
from app.models.inventory import Inventory
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.payment import Payment, PaymentStatus
from app.models.stationary import Stationary
from app.models.review import Review
from app.models.chatbot import ChatbotLog

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "Admin",
    "Genre",
    "Deal",
    "book_deals",
    "stationary_deals",
    "Book",
    "Inventory",
    "Cart",
    "CartItem",
    "Order",
    "OrderStatus",
    "OrderItem",
    "Payment",
    "PaymentStatus",
    "Stationary",
    "Review",
    "ChatbotLog",
]
