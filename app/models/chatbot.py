"""Chatbot ORM model for storing query and response history."""

from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChatbotLog(Base, TimestampMixin):
    """Chatbot history log database model mapping to 'chatbot_logs' table."""

    __tablename__ = "chatbot_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("enrolled_users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="chatbot_logs")

    def __repr__(self) -> str:
        return f"<ChatbotLog id={self.id} user_id={self.user_id}>"
