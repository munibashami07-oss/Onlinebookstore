"""Chatbot Service module coordinating RAG pipeline execution and persistent conversation logging."""

from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.admin_analytics import build_admin_context, is_admin_analytics_query
from app.ai.rag_pipeline import RAGPipeline
from app.models.chatbot import ChatbotLog
from starlette.concurrency import run_in_threadpool

class ChatbotService:
    """Service layer managing AI chatbot queries and database conversation logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rag_pipeline = RAGPipeline()

    async def ask_chatbot(
        self, question: str, user_id: Optional[int] = None, is_admin: bool = False
    ) -> ChatbotLog:
        """Process a user question through RAG pipeline and record log in database.

        Args:
            question: User query string.
            user_id: Optional primary key of authenticated user.
            is_admin: Whether the caller is an authenticated admin. When True
                and the question looks like an internal business-analytics
                question (stock, trending, orders, revenue), real data is
                fetched from the database and handed to the pipeline instead
                of the usual vector-store FAQ context.

        Returns:
            Saved ChatbotLog ORM instance.
        """
        # Admin live-data fetch happens here (not inside RAGPipeline) because
        # this service already has an async DB session, while RAGPipeline.run
        # is synchronous and executed in a worker thread below -- mixing an
        # AsyncSession into that thread would be unsafe.
        admin_context_docs = None
        if is_admin and is_admin_analytics_query(question):
            admin_context_docs = await build_admin_context(self.db, question)

        pipeline_res = await run_in_threadpool(
            self.rag_pipeline.run,
            question,
            is_admin=is_admin,
            admin_context_docs=admin_context_docs,
        )
        answer = pipeline_res["answer"]

        log = ChatbotLog(
            user_id=user_id,
            question=question,
            answer=answer,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def get_chat_history(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> List[ChatbotLog]:
        """Fetch persistent chat history logs for a user.

        Args:
            user_id: Primary key of the user.
            skip: Records to skip.
            limit: Maximum records to return.

        Returns:
            List of ChatbotLog ORM instances.
        """
        stmt = (
            select(ChatbotLog)
            .where(ChatbotLog.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(ChatbotLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_chat_history(self, user_id: int) -> None:
        """Delete all chat history logs for a user.

        Args:
            user_id: Primary key of the user.
        """
        stmt = delete(ChatbotLog).where(ChatbotLog.user_id == user_id)
        await self.db.execute(stmt)
        await self.db.flush()