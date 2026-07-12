"""CartItem ORM model."""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.cart import Cart


class CartItem(Base, TimestampMixin):
    """CartItem database model mapping to 'cart_items' table."""

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_at_add_time: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    book: Mapped["Book"] = relationship("Book", back_populates="cart_items")

    def __repr__(self) -> str:
        return f"<CartItem id={self.id} cart_id={self.cart_id} book_id={self.book_id} qty={self.quantity}>"
