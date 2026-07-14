"""User ORM model mapping to 'enrolled_users' table."""

import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.chatbot import ChatbotLog
    from app.models.chat_message import ChatMessage
    from app.models.notification import Notification
    from app.models.order import Order
    from app.models.review import Review


class UserRole(str, enum.Enum):
    """Enumeration of user access roles."""

    ADMIN = "admin"
    CUSTOMER = "customer"


class User(Base, TimestampMixin):
    """User database model strictly mapped to 'enrolled_users'."""

    __tablename__ = "enrolled_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.CUSTOMER, nullable=False
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    cart: Mapped[Optional["Cart"]] = relationship(
        "Cart", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    chatbot_logs: Mapped[List["ChatbotLog"]] = relationship(
        "ChatbotLog", back_populates="user"
    )
    sent_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
    )
    received_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"