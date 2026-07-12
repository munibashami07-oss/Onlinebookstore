"""Deterministic scope guard for the AI chatbot.

This is a lightweight, zero-cost pre-filter that runs BEFORE the RAG
pipeline touches the vector store or the LLM. It exists as a second,
independent layer of defense on top of the system prompt instructions in
`app/ai/prompt.py` — even if a crafted message manages to talk the LLM
into ignoring its instructions, an obviously off-topic question never
reaches the LLM in the first place.

Approach: a broad allow-list of bookstore-domain keywords/phrases. If the
user's message contains none of them (and isn't a short greeting/thanks),
it's treated as out-of-scope and short-circuited with a canned decline
message — no vector search, no LLM call.

This is intentionally permissive (allow-list, not a block-list of "bad"
topics) to minimize false positives against real store questions phrased
in unexpected ways. Tune `IN_SCOPE_KEYWORDS` below as real usage reveals
phrasings that should or shouldn't pass through.

Admin scope: `ADMIN_KEYWORDS` covers internal business-analytics topics
(stock, trending, revenue, orders). These are ONLY checked when the caller
passes `is_admin=True` -- i.e. the request is already authenticated as an
admin (see `app/api/chatbot.py`). A regular customer message is NEVER
checked against `ADMIN_KEYWORDS`, so business terms don't accidentally
widen what an unauthenticated/customer session can ask about.
"""

import re
from typing import List

STANDARD_DECLINE_MESSAGE = (
    "I'm the BookHaven store assistant, so I can only help with book recommendations, "
    "orders, and store policies. Is there something about our catalog or your order I can help with?"
)

# Bookstore-domain vocabulary. Kept as word/phrase stems (matched via substring
# on the lower-cased message) rather than an exhaustive exact-match list, so
# minor pluralization/conjugation ("shipping" vs "ship", "returns" vs "return")
# is naturally covered.
IN_SCOPE_KEYWORDS: List[str] = [
    # Catalog / books
    "book", "novel", "author", "genre", "isbn", "title", "series", "publisher",
    "read", "reading", "recommend", "recommendation", "review", "rating",
    "bestseller", "fiction", "non-fiction", "nonfiction", "paperback", "hardcover",
    "ebook", "audiobook", "stationary", "stationery","pen", "pencil", "notebook", "stock",
    "available", "availability", "inventory",
    # Commerce / checkout
    "price", "cost", "discount", "deal", "sale", "promo", "coupon", "voucher",
    "gift card", "cart", "checkout", "buy", "purchase", "order", "orders",
    "payment", "pay", "card", "cash on delivery", "cod", "invoice", "receipt",
    "refund", "return", "exchange", "cancel", "cancellation",
    # Shipping / fulfilment
    "ship", "shipping", "deliver", "delivery", "track", "tracking", "arrive",
    "arriving", "address",
    # Account / site
    "account", "login", "log in", "sign up", "signup", "register", "password",
    "profile", "wishlist", "subscribe", "newsletter",
    # Store identity
    "store", "shop", "bookhaven", "website", "site", "policy", "policies",
    "support", "help", "customer service", "admin",
]

# Internal business-analytics vocabulary. Only checked for admin callers
# (see `is_in_scope(..., is_admin=True)`). Kept separate from
# IN_SCOPE_KEYWORDS so these topics stay off-limits for ordinary customers.
ADMIN_KEYWORDS: List[str] = [
    "stock", "inventory", "low stock", "restock", "out of stock", "stock level",
    "trending", "best seller", "bestseller", "best-selling", "top selling",
    "popular book", "most sold", "top book",
    "revenue", "sales", "sales total", "earnings", "income", "profit",
    "orders today", "how many orders", "order count", "orders placed", "orders on",
    "business", "dashboard", "analytics", "report", "performance",
]

# Short greetings / pleasantries are always allowed through so the assistant
# doesn't feel broken during ordinary small talk.
GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|hiya|yo|good\s(morning|afternoon|evening)|thanks|thank\s?you|"
    r"thx|ok|okay|cool|great|bye|goodbye|see\s?you)[\s!.,]*$",
    re.IGNORECASE,
)


def is_in_scope(message: str, is_admin: bool = False) -> bool:
    """Return True if the message should be allowed through to the RAG/LLM
    pipeline, False if it should be short-circuited with a decline message.

    Args:
        message: The raw user (or admin) message text.
        is_admin: Whether the caller is an authenticated admin. When True,
            `ADMIN_KEYWORDS` are checked in addition to the normal
            customer-facing `IN_SCOPE_KEYWORDS`.
    """
    if not message or not message.strip():
        return True  # let empty/whitespace input hit normal validation upstream

    text = message.strip().lower()

    # Always allow short greetings/pleasantries through.
    if GREETING_PATTERN.match(text):
        return True

    # Very short messages (<=2 words) are ambiguous rather than clearly
    # off-topic; give the benefit of the doubt and let the LLM (with its
    # own scope instructions) handle them.
    if len(text.split()) <= 2:
        return True

    keywords = IN_SCOPE_KEYWORDS + ADMIN_KEYWORDS if is_admin else IN_SCOPE_KEYWORDS
    return any(keyword in text for keyword in keywords)