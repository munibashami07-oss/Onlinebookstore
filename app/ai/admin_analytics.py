"""Admin-only analytics data access for the AI chatbot.

Runs real SQL/ORM aggregate queries against the store's own database so
that admin questions about stock, trending books, orders, and revenue are
answered with ACTUAL numbers -- never guessed or hallucinated by the LLM.

This module is only ever invoked for authenticated users with the ADMIN
role. It is never wired into the customer-facing retrieval path (see
`app/api/chatbot.py`, which decides `is_admin` from the JWT-authenticated
user's role, and `app/ai/scope_guard.py`, which gates admin-only topics).

Design: each `get_*` function returns real data. `build_admin_context`
inspects the admin's question, decides which queries are relevant, and
formats the results into the same `{"source": ..., "content": ...}` shape
the vector retriever normally produces, so `PromptBuilder` / `RAGPipeline`
can treat "live business data" and "vector store FAQ context" identically.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

# Keywords that identify a question as an internal business-analytics
# question, independent of `scope_guard`'s customer-facing keyword list.
# Deliberately kept separate: a customer asking "is this in stock" should
# never trigger a live DB query or see internal figures like exact stock
# counts, revenue, or order volume -- only an authenticated admin should.
ADMIN_ANALYTICS_KEYWORDS: List[str] = [
    "stock", "inventory", "low stock", "restock", "out of stock", "stock level",
    "trending", "best seller", "bestseller", "best-selling", "top selling",
    "popular book", "most sold", "top book",
    "revenue", "sales total", "earnings", "income", "profit", "how much did we make",
    "orders today", "how many orders", "order count", "orders placed", "orders on",
    "sales this", "business", "dashboard", "analytics",
]


def is_admin_analytics_query(question: str) -> bool:
    """Return True if the question looks like an internal business query."""
    text = (question or "").strip().lower()
    return any(keyword in text for keyword in ADMIN_ANALYTICS_KEYWORDS)


async def get_stock_summary(
    db: AsyncSession, low_stock_only: bool = False, limit: int = 15
) -> List[Dict[str, Any]]:
    """Return current stock levels per book, lowest stock first."""
    stmt = (
        select(Book.title, Book.author, Inventory.stock_quantity, Inventory.low_stock_threshold)
        .join(Inventory, Inventory.book_id == Book.id)
        .order_by(Inventory.stock_quantity.asc())
        .limit(limit)
    )
    if low_stock_only:
        stmt = stmt.where(Inventory.stock_quantity <= Inventory.low_stock_threshold)

    result = await db.execute(stmt)
    return [
        {
            "title": row.title,
            "author": row.author,
            "stock": row.stock_quantity,
            "low_stock_threshold": row.low_stock_threshold,
        }
        for row in result.all()
    ]


async def get_trending_books(
    db: AsyncSession, days: int = 30, limit: int = 10
) -> List[Dict[str, Any]]:
    """Return best-selling books (by units sold) over the trailing `days` window."""
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(
            Book.title,
            Book.author,
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(OrderItem, OrderItem.book_id == Book.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= since)
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(Book.id, Book.title, Book.author)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {"title": row.title, "author": row.author, "units_sold": int(row.units_sold)}
        for row in result.all()
    ]


async def get_orders_summary(db: AsyncSession, target_date: Optional[date] = None) -> Dict[str, Any]:
    """Return order count + revenue for a single calendar day (defaults to today, UTC)."""
    target_date = target_date or datetime.utcnow().date()
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)

    stmt = (
        select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.created_at >= start)
        .where(Order.created_at < end)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    result = await db.execute(stmt)
    count, total = result.one()
    return {"date": target_date.isoformat(), "order_count": int(count), "revenue": float(total)}


async def get_revenue_summary(db: AsyncSession, days: int = 30) -> Dict[str, Any]:
    """Return total revenue and order count over the trailing `days` window."""
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.created_at >= since)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    result = await db.execute(stmt)
    count, total = result.one()
    return {"period_days": days, "order_count": int(count), "total_revenue": float(total)}


async def build_admin_context(db: AsyncSession, question: str) -> List[Dict[str, Any]]:
    """Route an admin question to the relevant analytics quer(y/ies) and
    format results as context documents for the prompt.

    Multiple sections can be included if the question touches more than one
    topic (e.g. "how's stock and revenue looking?").
    """
    q = (question or "").lower()
    docs: List[Dict[str, Any]] = []

    if any(w in q for w in ["stock", "inventory", "low stock", "restock", "out of stock", "stock level"]):
        low_only = any(w in q for w in ["low stock", "restock", "running low", "out of stock"])
        stock = await get_stock_summary(db, low_stock_only=low_only)
        lines = "\n".join(
            f"- {s['title']} by {s['author']}: {s['stock']} in stock (reorder threshold {s['low_stock_threshold']})"
            for s in stock
        ) or "No inventory records matched."
        docs.append({"source": "live_inventory_data", "content": lines})

    if any(w in q for w in ["trending", "best seller", "bestseller", "best-selling", "top selling", "popular book", "most sold", "top book"]):
        trending = await get_trending_books(db)
        lines = "\n".join(
            f"- {t['title']} by {t['author']}: {t['units_sold']} units sold (last 30 days)"
            for t in trending
        ) or "No sales recorded in the last 30 days."
        docs.append({"source": "live_sales_data", "content": lines})

    if any(w in q for w in ["orders today", "how many orders", "order count", "orders placed", "orders on", "today"]):
        orders = await get_orders_summary(db)
        docs.append(
            {
                "source": "live_orders_data",
                "content": f"On {orders['date']}: {orders['order_count']} orders placed, totaling ${orders['revenue']:.2f} in revenue.",
            }
        )

    if any(w in q for w in ["revenue", "sales total", "earnings", "income", "profit", "how much did we make"]):
        revenue = await get_revenue_summary(db)
        docs.append(
            {
                "source": "live_revenue_data",
                "content": f"Over the last {revenue['period_days']} days: {revenue['order_count']} orders, ${revenue['total_revenue']:.2f} total revenue.",
            }
        )

    if not docs:
        # Question matched the broad admin-analytics gate but no specific
        # sub-topic -- give a general snapshot rather than nothing.
        stock = await get_stock_summary(db, limit=5)
        revenue = await get_revenue_summary(db, days=7)
        stock_bit = ", ".join(f"{s['title']} ({s['stock']})" for s in stock) or "no inventory data"
        docs.append(
            {
                "source": "live_store_snapshot",
                "content": (
                    f"Last 7 days: {revenue['order_count']} orders, ${revenue['total_revenue']:.2f} revenue. "
                    f"Lowest stock items: {stock_bit}."
                ),
            }
        )

    return docs