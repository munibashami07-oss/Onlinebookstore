"""Pydantic v2 schemas for the Chat REST endpoints.

The live message stream itself is JSON over the `/ws/chat` WebSocket
(see app/api/chat.py); these schemas back the REST side: loading past
messages for a thread, listing all of a user's conversation threads
(inbox view), and resolving the fixed support contact for customers.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserPublic


class ChatMessageResponse(BaseModel):
    """A single persisted chat message."""

    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    """One row in a user's conversation inbox: a counterparty, the most
    recent message exchanged with them, and how many of their messages
    are still unread."""

    other_user: UserPublic
    last_message: ChatMessageResponse
    unread_count: int

    model_config = ConfigDict(from_attributes=True)
