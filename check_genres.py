import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASS}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, name FROM genres ORDER BY id"))
        print(result.fetchall())
    await engine.dispose()

asyncio.run(main())