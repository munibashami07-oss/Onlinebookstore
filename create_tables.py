import asyncio
from app.core.database import engine  # adjust import if your engine lives elsewhere
from app.models import Base       # Base should already have all models registered via __init__.py

async def create_missing_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done — any missing tables have been created.")

if __name__ == "__main__":
    asyncio.run(create_missing_tables())