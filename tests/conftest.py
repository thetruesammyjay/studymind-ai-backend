"""
Shared pytest fixtures for StudyMind AI backend tests.
Uses in-memory SQLite + aiosqlite so no external services are required.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.models.base import Base
from app.models.user import User
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Test Settings (no real env vars needed)
# ---------------------------------------------------------------------------
@pytest.fixture
def test_settings() -> Settings:
    """Return a Settings object with test/dummy values."""
    return Settings(
        APP_NAME="StudyMind AI Test",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET="test-secret-key-for-unit-tests",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
        GEMINI_API_KEY="fake-gemini-key",
        GEMINI_MODEL="gemini-1.5-flash",
        CORS_ORIGIN="*",
    )


# ---------------------------------------------------------------------------
# Async Database (in-memory SQLite)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Pre-created test user
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession, test_settings: Settings) -> User:
    auth = AuthService(test_settings)
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=auth.hash_password("TestPassword123"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_service(test_settings: Settings) -> AuthService:
    return AuthService(test_settings)


@pytest.fixture
def auth_headers(auth_service: AuthService, test_user: User) -> dict:
    token = auth_service.create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Mock Gemini service
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.stream = AsyncMock(return_value=AsyncMock(__aiter__=lambda self: self, __anext__=AsyncMock(side_effect=StopAsyncIteration)))
    gemini.transcribe = AsyncMock(return_value="transcribed text")
    gemini.analyze_sentiment = AsyncMock(return_value=("focused", 0.95))
    return gemini


# ---------------------------------------------------------------------------
# FastAPI TestClient with dependency overrides
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(async_engine, test_user, test_settings):
    """Async HTTP client with all dependencies overridden."""
    from app.config import get_settings
    from app.dependencies import get_current_user, get_db
    from app.main import app

    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_get_current_user():
        return test_user

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_settings] = override_get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
