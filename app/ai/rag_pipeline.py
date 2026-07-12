"""RAG Pipeline orchestrating document retrieval, prompt generation, and response formatting."""

from typing import Any, Dict, List, Optional
from app.ai.embeddings import EmbeddingService
from app.ai.prompt import PromptBuilder
from app.ai.retriever import Retriever
from app.ai.vector_db import VectorDatabase
from app.ai.scope_guard import is_in_scope, STANDARD_DECLINE_MESSAGE


class OpenAILLM:
    """LLM engine backed by the OpenAI Chat Completions API."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model
        self._client = None
        if self.api_key:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)

    def generate_response(self, prompt: str) -> str:
        """Generate a real LLM response for the given RAG prompt.

        Falls back to a static message if no API key is configured or the
        API call fails for any reason, so the chatbot never hard-crashes.
        """
        if not self._client:
            return (
                "Thank you for contacting Online Book Store customer support! "
                "Our store offers a wide selection of books across multiple genres, 30-day easy returns, "
                "and flat-rate shipping ($5.00, or free on orders over $50). Payments are processed securely via Stripe or PayPal. "
                "How else may I assist you with your reading preferences today?"
            )
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.4,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return (
                "I'm having trouble reaching our AI service right now. "
                "Please try again in a moment, or contact support directly for urgent questions. "
                f"(error: {e})"
            )


class RAGPipeline:
    """Complete RAG Pipeline orchestrator."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDatabase()
        self.retriever = Retriever(self.vector_db, self.embedding_service)
        self.prompt_builder = PromptBuilder()
        self.llm = OpenAILLM(api_key=self.prompt_builder.openai_api_key)

    def run(
        self,
        user_question: str,
        is_admin: bool = False,
        admin_context_docs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Execute full RAG pipeline:
        0. Reject out-of-scope questions before any retrieval/LLM cost.
        1. Retrieve relevant context (vector store for customers, or
           precomputed live business-data docs for admin analytics questions).
        2. Build prompt template (customer or admin variant).
        3. Invoke LLM engine.
        4. Format and return response metadata.

        Args:
            user_question: Question string (customer or admin).
            is_admin: Whether the caller is an authenticated admin. Widens
                the scope guard to admin topics and, when `admin_context_docs`
                is provided, routes to the admin prompt/live data instead of
                the vector store.
            admin_context_docs: Precomputed live business-data documents
                (from `app.ai.admin_analytics.build_admin_context`), fetched
                by the caller BEFORE this synchronous method runs, since
                this class has no async DB access of its own. Only used
                when `is_admin=True`.

        Returns:
            Dict containing question, generated answer, and context metadata.
        """
        # Step 0: Deterministic scope guard — short-circuits obviously
        # off-topic questions (general trivia, unrelated topics, etc.)
        # without touching the vector store or the LLM at all. Admin
        # callers are additionally allowed through on business-analytics
        # keywords (see app/ai/scope_guard.py).
        if not is_in_scope(user_question, is_admin=is_admin):
            return {
                "question": user_question,
                "answer": STANDARD_DECLINE_MESSAGE,
                "context_sources": [],
            }

        # Admin analytics path: real business data was already fetched by
        # the caller (ChatbotService), so skip vector retrieval entirely and
        # build the admin-facing prompt from live figures instead.
        if is_admin and admin_context_docs:
            prompt = self.prompt_builder.build_admin_prompt(user_question, admin_context_docs)
            raw_answer = self.llm.generate_response(prompt)
            return {
                "question": user_question,
                "answer": raw_answer,
                "context_sources": [doc.get("source", "live_data") for doc in admin_context_docs],
            }

        # Step 1: Retrieve context (standard customer-facing path)
        context_docs = self.retriever.get_relevant_documents(user_question, top_k=3)

        # Step 2: Build Prompt
        prompt = self.prompt_builder.build_rag_prompt(user_question, context_docs)

        # Step 3: Generate LLM Response
        raw_answer = self.llm.generate_response(prompt)

        # Step 4: Response Formatting
        return {
            "question": user_question,
            "answer": raw_answer,
            "context_sources": [doc.get("source", "FAQ") for doc in context_docs],
        }