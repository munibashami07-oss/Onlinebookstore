"""Inventory ORM model strictly 1-to-1 with Book."""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book


class Inventory(Base, TimestampMixin):
    """Inventory database model mapping to 'inventories' table."""

    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("books.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="inventory")

    def __repr__(self) -> str:
        return f"<Inventory id={self.id} book_id={self.book_id} stock={self.stock_quantity}>"
