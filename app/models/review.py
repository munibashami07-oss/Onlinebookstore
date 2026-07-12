"""Review ORM model."""

from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class Review(Base, TimestampMixin):
    """Review database model mapping to 'reviews' table."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("enrolled_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    book: Mapped["Book"] = relationship("Book", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review id={self.id} user_id={self.user_id} book_id={self.book_id} rating={self.rating}>"
