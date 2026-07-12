"""OrderItem ORM model."""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.order import Order


class OrderItem(Base, TimestampMixin):
    """OrderItem database model mapping to 'order_items' table."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    book: Mapped["Book"] = relationship("Book", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} order_id={self.order_id} book_id={self.book_id} qty={self.quantity}>"
