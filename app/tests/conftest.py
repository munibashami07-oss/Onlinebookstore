"""Pytest configuration, shared fixtures, and test database setup.

Uses a separate SQLite async test database to avoid touching the production PostgreSQL instance.
All fixtures use function scope to ensure test isolation.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.session import get_db
from app.models import Base
from app.models.user import User, UserRole
from app.security.hashing import hash_password
from app.security.jwt import create_access_token

from sqlalchemy.pool import StaticPool

# ── Test Database ────────────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)




# ── DB schema create / drop per test function ────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop afterwards for isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── DB session override ─────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async session for direct repository/service tests."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override for FastAPI dependency injection."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── FastAPI Test Client ──────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app with test DB override."""
    from app.main import app  # noqa: import here to avoid circular imports

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver/api/v1") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helper: create a test user ───────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a regular customer user for testing."""
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=hash_password("TestPass123"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create and return an admin user for testing."""
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("AdminPass123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create and return a deactivated user for testing."""
    user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=hash_password("InactivePass1"),
        role=UserRole.CUSTOMER,
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Auth header helpers ──────────────────────────────────────────────────────
@pytest.fixture
def user_auth_headers(test_user: User) -> dict:
    """Return auth headers for test_user."""
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin: User) -> dict:
    """Return auth headers for test_admin."""
    token = create_access_token(subject=test_admin.id)
    return {"Authorization": f"Bearer {token}"}
