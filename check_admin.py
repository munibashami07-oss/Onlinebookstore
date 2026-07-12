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
        result = await conn.execute(
            text("SELECT * FROM admins WHERE email = :email"),
            {"email": "admin@bookstore.com"},
        )
        rows = result.mappings().all()
        for row in rows:
            print(dict(row))
        if not rows:
            print("No matching admin row found.")
    await engine.dispose()

asyncio.run(main())