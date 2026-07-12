"""Database engine configuration using SQLAlchemy 2.0 and settings from config.py."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

# Create SQLAlchemy 2.0 Async Engine reading separate DB settings from config.py
engine: AsyncEngine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
