"""Seed script to insert admin user into PostgreSQL database reading credentials from .env."""

import asyncio
import logging
from passlib.context import CryptContext
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin_user() -> None:
    """Inserts initial admin credentials loaded from .env into enrolled_users table."""
    logger.info("Initializing database seed for admin user...")

    admin_username = settings.ADMIN_USERNAME
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    hashed_password = pwd_context.hash(admin_password)

    async with engine.begin() as conn:
        # Create enrolled_users table if not exists (minimal schema before models phase)
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS enrolled_users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_superuser BOOLEAN NOT NULL DEFAULT TRUE,
                    role VARCHAR(50) NOT NULL DEFAULT 'admin',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        )

        # Check if admin already exists
        result = await conn.execute(
            text("SELECT id FROM enrolled_users WHERE email = :email"),
            {"email": admin_email},
        )
        existing = result.first()

        if existing:
            logger.info(f"Admin user ({admin_email}) already exists. Skipping insertion.")
        else:
            await conn.execute(
                text(
                    """
                    INSERT INTO enrolled_users (email, full_name, hashed_password, is_active, is_superuser, role)
                    VALUES (:email, :full_name, :hashed_password, TRUE, TRUE, 'admin')
                    """
                ),
                {
                    "email": admin_email,
                    "full_name": admin_username,
                    "hashed_password": hashed_password,
                },
            )
            logger.info(f"Successfully seeded admin user ({admin_email}) into enrolled_users table.")


if __name__ == "__main__":
    asyncio.run(seed_admin_user())
