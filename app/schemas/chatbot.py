"""Pydantic v2 schemas for Chatbot interactions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Chatbot question request payload."""

    question: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """Chatbot answer response payload."""

    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Chatbot conversation history record."""

    id: int
    user_id: Optional[int] = None
    question: str
    answer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
