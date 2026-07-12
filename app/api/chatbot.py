"""API Router for AI Chatbot and RAG Q&A endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chatbot import ChatbotService
from app.dependencies import get_current_active_user, get_current_user_optional, get_db
from app.models.user import User, UserRole
from app.schemas.chatbot import ChatHistoryResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI Chatbot a question",
)
async def ask_chatbot(
    payload: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Submit a question to the bookstore AI chatbot RAG pipeline.

    Works for both guests and authenticated users. Answers book questions,
    genre recommendations, shipping rules, and return policy FAQs for
    everyone. Authenticated ADMIN users additionally get real-time answers
    to internal business questions (stock levels, trending books, order
    counts, revenue) -- customers never see this data or this code path,
    regardless of how they phrase a question.

    Note: uses `get_current_user_optional` (never raises for guests) rather
    than `get_current_active_user` (raises 401 unconditionally when no
    bearer token is present, even though its return type here was annotated
    Optional) -- that mismatch previously broke this endpoint for anonymous
    visitors.
    """
    chatbot_service = ChatbotService(db)
    user_id = current_user.id if current_user else None
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN)
    log = await chatbot_service.ask_chatbot(payload.question, user_id=user_id, is_admin=is_admin)
    return ChatResponse(question=log.question, answer=log.answer)


@router.get(
    "/history",
    response_model=List[ChatHistoryResponse],
    summary="Get user chat history",
)
async def get_chat_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatHistoryResponse]:
    """Retrieve paginated chat history for the authenticated user."""
    chatbot_service = ChatbotService(db)
    skip = (page - 1) * page_size
    logs = await chatbot_service.get_chat_history(current_user.id, skip=skip, limit=page_size)
    return logs


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear user chat history",
)
async def clear_chat_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all persistent chatbot logs for the authenticated user."""
    chatbot_service = ChatbotService(db)
    await chatbot_service.delete_chat_history(current_user.id)