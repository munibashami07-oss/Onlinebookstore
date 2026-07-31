import asyncio
from sqlalchemy import text
from app.core.database import engine


async def main():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, email, full_name, is_active, is_verified, role FROM enrolled_users ORDER BY id")
        )
        rows = result.fetchall()
        print(f"Found {len(rows)} user(s):")
        for row in rows:
            print(row)
    await engine.dispose()


asyncio.run(main())