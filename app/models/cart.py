"""Cart ORM model."""

from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.user import User


class Cart(Base, TimestampMixin):
    """Cart database model mapping to 'carts' table."""

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("enrolled_users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cart id={self.id} user_id={self.user_id}>"
