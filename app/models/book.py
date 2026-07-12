"""Book ORM model."""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.deal import book_deals

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.deal import Deal
    from app.models.genre import Genre
    from app.models.inventory import Inventory
    from app.models.order_item import OrderItem
    from app.models.review import Review


class Book(Base, TimestampMixin):
    """Book database model mapping to 'books' table."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    isbn: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    genre_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("genres.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    # Relationships
    genre: Mapped["Genre"] = relationship("Genre", back_populates="books")
    inventory: Mapped[Optional["Inventory"]] = relationship(
        "Inventory", back_populates="book", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="book", cascade="all, delete-orphan"
    )
    deals: Mapped[List["Deal"]] = relationship(
        "Deal", secondary=book_deals, back_populates="books"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="book"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="book"
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title='{self.title}' isbn='{self.isbn}'>"
