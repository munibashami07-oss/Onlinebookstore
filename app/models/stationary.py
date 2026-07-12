"""Stationary ORM model for non-book merchandise."""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.deal import stationary_deals

if TYPE_CHECKING:
    from app.models.deal import Deal


class Stationary(Base, TimestampMixin):
    """Stationary database model mapping to 'stationary' table."""

    __tablename__ = "stationary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    deals: Mapped[List["Deal"]] = relationship(
        "Deal", secondary=stationary_deals, back_populates="stationary_items"
    )

    def __repr__(self) -> str:
        return f"<Stationary id={self.id} name='{self.name}' price={self.price} stock={self.stock}>"
