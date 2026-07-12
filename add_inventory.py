import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

BOOK_ID = 2        # <-- change this to your book's actual ID
STOCK_QUANTITY = 20  # <-- change this to whatever quantity you want

async def main():
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASS}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO inventories (book_id, stock_quantity, low_stock_threshold, created_at, updated_at) "
                "VALUES (:book_id, :stock_quantity, :low_stock_threshold, :created_at, :updated_at)"
            ),
            {
                "book_id": BOOK_ID,
                "stock_quantity": STOCK_QUANTITY,
                "low_stock_threshold": 5,
                "created_at": now,
                "updated_at": now,
            },
        )
    print(f"Inventory created for book_id={BOOK_ID} with stock={STOCK_QUANTITY}")
    await engine.dispose()

asyncio.run(main())