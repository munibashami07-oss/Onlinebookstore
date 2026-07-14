"""Notification ORM model for the real-time notifications feature.

Covers both customer-facing notifications (order placed, payment success,
order shipped/delivered/cancelled, promotions, back-in-stock) and
admin-facing notifications (new order, new customer, payment received,
low stock, customer message, new review) in a single table, distinguished
by `NotificationType`. They share identical structure (recipient, type,
title, message, read state, optional structured payload), so one table
keeps the schema simple; the type enum is what the service layer branches
on when deciding what to send and to whom.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    """Enumeration of all customer- and admin-facing notification kinds."""

    # Customer notifications
    ORDER_PLACED = "order_placed"
    PAYMENT_SUCCESS = "payment_success"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    PROMOTIONAL = "promotional"
    BOOK_BACK_IN_STOCK = "book_back_in_stock"

    # Admin notifications
    NEW_ORDER = "new_order"
    NEW_CUSTOMER = "new_customer"
    PAYMENT_RECEIVED = "payment_received"
    LOW_STOCK = "low_stock"
    CUSTOMER_MESSAGE = "customer_message"
    NEW_REVIEW = "new_review"


class Notification(Base, TimestampMixin):
    """A single notification delivered (or queued for delivery) to one user."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("enrolled_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional structured payload for frontend use, e.g. {"order_id": 42}
    # so the UI can deep-link without parsing the message text.
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user_id={self.user_id} "
            f"type='{self.type.value}' is_read={self.is_read}>"
        )
