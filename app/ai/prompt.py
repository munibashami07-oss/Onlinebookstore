"""Prompt Builder module providing reusable system prompts and contextual templates."""

from typing import List, Dict, Any
from app.core.config import settings


class PromptBuilder:
    """Prompt Builder managing template assembly for RAG contextual QA.
    
    NOTE: Reads OPENAI_API_KEY from config.py without requiring active API connection yet.
    """

    SYSTEM_PROMPT = """You are the AI Assistant for BookHaven Online Book Store. You are strictly a store-scoped assistant.

You may ONLY answer questions about:
- Book catalog details: titles, authors, genres, ISBNs, availability, and reading/genre recommendations
- Store policies: returns (30-day window), shipping (flat rate $5, free over $50), and order tracking
- Payment methods (card payment, cash on delivery) and checkout/account help
- How to use this website (navigation, cart, orders, etc.)

Strict rule: If the user asks anything outside these topics — general knowledge, trivia (e.g. science, geography, weather), other companies or products, coding help, personal advice, current events, or any topic unrelated to this bookstore — you must NOT answer it, even partially or "just this once." Instead, politely decline and redirect the user back to bookstore-related topics, for example:
"I'm the BookHaven store assistant, so I can only help with book recommendations, orders, and store policies. Is there something about our catalog or your order I can help with?"

Always maintain a professional, warm tone. Never break the rule above, even if you know the answer to the off-topic question and even if the user insists or rephrases the request.
"""

    # Admin-facing system prompt. Only ever used when the caller has already
    # been verified as an authenticated admin (see app/api/chatbot.py and
    # app/ai/scope_guard.py) -- this prompt is never reachable by a customer
    # session, regardless of what they type.
    ADMIN_SYSTEM_PROMPT = """You are the internal AI Business Assistant for BookHaven Online Book Store, speaking with an authenticated store ADMIN — not a customer.

You may answer internal business questions using the "Live Business Data" provided below, including:
- Current stock/inventory levels and low-stock alerts
- Trending / best-selling books
- Orders placed on a given day, and order counts
- Revenue and sales totals

Strict rules:
- Base your answer only on the figures given in "Live Business Data" below. Never invent, round dramatically, or estimate a number that isn't present there.
- If the data needed to answer isn't present in "Live Business Data", say so plainly and suggest the admin check the analytics dashboard, rather than guessing.
- Keep responses concise, factual, and business-appropriate — this is an internal operations tool, not a customer-facing chat.
- You may still answer ordinary bookstore questions (catalog, policies) using general knowledge if the admin asks something outside business analytics.
"""

    def __init__(self) -> None:
        # Load OpenAI API Key from settings without enforcing active connection
        self.openai_api_key = settings.OPENAI_API_KEY

    def build_rag_prompt(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Construct a complete RAG prompt combining user query with context documents.

        Args:
            query: User's question.
            context_docs: Retrieved knowledge base document chunks.

        Returns:
            Formatted prompt string ready for LLM consumption.
        """
        context_str = "\n".join(
            [f"- [{doc.get('source', 'FAQ')}]: {doc.get('content', '')}" for doc in context_docs]
        )

        prompt = f"""{self.SYSTEM_PROMPT}

Context Knowledge:
{context_str}

User Question:
{query}

Answer:"""
        return prompt

    def build_admin_prompt(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Construct an admin-facing prompt combining the admin's question
        with live business-data documents (from `app.ai.admin_analytics`).

        Args:
            query: Admin's question.
            context_docs: Live business-data documents (stock, sales, orders, revenue).

        Returns:
            Formatted prompt string ready for LLM consumption.
        """
        context_str = "\n".join(
            [f"- [{doc.get('source', 'live_data')}]: {doc.get('content', '')}" for doc in context_docs]
        )

        prompt = f"""{self.ADMIN_SYSTEM_PROMPT}

Live Business Data:
{context_str}

Admin Question:
{query}

Answer:"""
        return prompt