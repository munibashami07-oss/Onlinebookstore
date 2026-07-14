"""ChatMessage ORM model for the Customer <-> Admin live chat feature."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChatMessage(Base, TimestampMixin):
    """A single chat message between two users (one customer, one admin).

    Direction is captured generically via `sender_id`/`receiver_id` rather
    than fixed "customer_id"/"admin_id" columns, since either party can be
    the sender on a given message. Business rules about *who is allowed to
    message whom* (customer -> any admin, admin -> any customer) live in
    the service layer, not here -- this model only stores what happened.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("enrolled_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("enrolled_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_messages"
    )
    receiver: Mapped["User"] = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_messages"
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage id={self.id} sender_id={self.sender_id} "
            f"receiver_id={self.receiver_id} is_read={self.is_read}>"
        )
