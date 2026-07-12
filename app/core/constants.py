"""Application constants and global definitions."""

# User Roles
ROLE_ADMIN = "admin"
ROLE_CUSTOMER = "customer"

# Order Statuses
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PROCESSING = "processing"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_DELIVERED = "delivered"
ORDER_STATUS_CANCELLED = "cancelled"

# Payment Statuses
PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_COMPLETED = "completed"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_REFUNDED = "refunded"

# Pagination Defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# RAG & AI Vector Store Constants (Phase 13 Preparation)
CHROMA_COLLECTION_NAME = "book_embeddings"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
