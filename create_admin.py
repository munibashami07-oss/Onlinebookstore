import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.security import get_password_hash

async def main():
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASS}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
    hashed = get_password_hash(settings.ADMIN_PASSWORD)
    now = datetime.now(timezone.utc)

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO enrolled_users "
                "(email, full_name, hashed_password, is_active, is_superuser, role, created_at, updated_at) "
                "VALUES (:email, :full_name, :hashed_password, :is_active, :is_superuser, :role, :created_at, :updated_at)"
            ),
            {
                "email": settings.ADMIN_EMAIL,
                "full_name": "Store Administrator",
                "hashed_password": hashed,
                "is_active": True,
                "is_superuser": True,
                "role": "ADMIN",
                "created_at": now,
                "updated_at": now,
            },
        )
    print(f"Admin user created in enrolled_users: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
    await engine.dispose()

asyncio.run(main())