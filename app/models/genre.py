"""Genre ORM model for book classification."""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book


class Genre(Base, TimestampMixin):
    """Genre database model mapping to 'genres' table."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    books: Mapped[List["Book"]] = relationship(
        "Book", back_populates="genre", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name='{self.name}'>"
