"""One-off script: update the existing admin account's email address.

Editing ADMIN_EMAIL in .env alone does NOT change an admin account that
was already created by seed.py -- that only sets the default used the
*next* time an admin is seeded from scratch. Run this script once to
update the email on the admin row that already exists in your database.

Usage:
    1. Edit OLD_ADMIN_EMAIL / NEW_ADMIN_EMAIL below.
    2. python update_admin_email.py
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.models.user import User, UserRole

# EDIT THESE TWO LINES:
OLD_ADMIN_EMAIL = "admin@bookstore.com"          # the admin's current email in the DB (config.py default, since .env never set ADMIN_EMAIL)
NEW_ADMIN_EMAIL = "aibuildersstudio@gmail.com"    # the new email you want the admin to use


async def update_admin_email() -> None:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == OLD_ADMIN_EMAIL))
        admin = result.scalar_one_or_none()

        if not admin:
            # Fall back to "whoever is currently an admin" if the old
            # email doesn't match (e.g. you already changed it once).
            result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
            admin = result.scalars().first()

        if not admin:
            print("No admin user found in the database -- nothing to update.")
            return

        print(f"Updating admin email: '{admin.email}' -> '{NEW_ADMIN_EMAIL}'")
        admin.email = NEW_ADMIN_EMAIL
        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(update_admin_email())