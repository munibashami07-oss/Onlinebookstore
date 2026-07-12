"""Deal ORM model and discount association tables for books and stationary."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.stationary import Stationary

# Association table for Book <-> Deal
book_deals = Table(
    "book_deals",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("deal_id", Integer, ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for Stationary <-> Deal
stationary_deals = Table(
    "stationary_deals",
    Base.metadata,
    Column("stationary_id", Integer, ForeignKey("stationary.id", ondelete="CASCADE"), primary_key=True),
    Column("deal_id", Integer, ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True),
)


class Deal(Base, TimestampMixin):
    """Deal database model mapping to 'deals' table."""

    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", secondary=book_deals, back_populates="deals"
    )
    stationary_items: Mapped[List["Stationary"]] = relationship(
        "Stationary", secondary=stationary_deals, back_populates="deals"
    )

    def __repr__(self) -> str:
        return f"<Deal id={self.id} title='{self.title}' discount={self.discount_percentage}%>"
