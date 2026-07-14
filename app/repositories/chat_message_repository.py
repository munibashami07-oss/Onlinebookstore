"""Repository for ChatMessage database operations."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat_message import ChatMessage


class ChatMessageRepository:
    """Data access layer for the ChatMessage model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_message(self, message: ChatMessage) -> ChatMessage:
        """Insert a new chat message record."""
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_conversation(
        self, user_a_id: int, user_b_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        """Fetch the full message history between two specific users.

        Matches messages in either direction (A->B or B->A), since a
        conversation is symmetric regardless of who sent which message.
        Returned oldest-first so callers can render it directly as a
        scrollback without re-sorting.
        """
        stmt = (
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender),
                selectinload(ChatMessage.receiver),
            )
            .where(
                or_(
                    and_(
                        ChatMessage.sender_id == user_a_id,
                        ChatMessage.receiver_id == user_b_id,
                    ),
                    and_(
                        ChatMessage.sender_id == user_b_id,
                        ChatMessage.receiver_id == user_a_id,
                    ),
                )
            )
            .order_by(ChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: int, from_user_id: int) -> int:
        """Count unread messages sent TO `user_id` FROM `from_user_id` specifically.

        Scoped to a single sender (not a global unread count) so the UI can
        show a per-conversation unread badge.
        """
        stmt = select(func.count()).where(
            ChatMessage.receiver_id == user_id,
            ChatMessage.sender_id == from_user_id,
            ChatMessage.is_read.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_conversation_read(self, user_id: int, from_user_id: int) -> None:
        """Mark all messages sent TO `user_id` FROM `from_user_id` as read.

        Called when `user_id` opens/focuses that specific conversation.
        """
        stmt = (
            update(ChatMessage)
            .where(
                ChatMessage.receiver_id == user_id,
                ChatMessage.sender_id == from_user_id,
                ChatMessage.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_message(self, message_id: int) -> Optional[ChatMessage]:
        """Fetch a single message by primary key."""
        stmt = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
