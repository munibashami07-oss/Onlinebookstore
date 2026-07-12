"""Order ORM model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
    from app.models.payment import Payment
    from app.models.user import User


class OrderStatus(str, enum.Enum):
    """Enumeration of order processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"



class Order(Base, TimestampMixin):
    """Order database model mapping to 'orders' table."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("enrolled_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Set exactly once, the moment the order transitions into DELIVERED.
    # Kept separate from updated_at, which changes on every subsequent edit.
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} user_id={self.user_id} status='{self.status}' total={self.total_amount}>"