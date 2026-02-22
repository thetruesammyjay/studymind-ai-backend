"""Integration tests for API routers using httpx AsyncClient."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.session import StudySession


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealthRouter:
    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        resp = await client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuthRouter:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        resp = await client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "StrongP@ss1",
            "full_name": "New User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client):
        payload = {"email": "dup@example.com", "password": "Pass123", "full_name": "Dup"}
        await client.post("/auth/register", json=payload)
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        # Register first
        await client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "LoginPass1",
        })
        # Login via form data
        resp = await client.post("/auth/login", data={
            "username": "login@example.com",
            "password": "LoginPass1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        await client.post("/auth/register", json={
            "email": "wrong@example.com",
            "password": "Correct1",
        })
        resp = await client.post("/auth/login", data={
            "username": "wrong@example.com",
            "password": "WrongPassword",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "testuser@example.com"


# ── Subjects ──────────────────────────────────────────────────────────────────

class TestSubjectRouter:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/subjects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_create_subject(self, client):
        resp = await client.post(
            "/subjects",
            json={"name": "Biology", "description": "AP Bio"},
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Biology"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_subject(self, client):
        payload = {"name": "Chemistry", "description": "Chem"}
        await client.post("/subjects", json=payload, headers={"Authorization": "Bearer fake"})
        resp = await client.post("/subjects", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_returns_created(self, client):
        await client.post(
            "/subjects",
            json={"name": "Physics"},
            headers={"Authorization": "Bearer fake"},
        )
        resp = await client.get("/subjects")
        names = [s["name"] for s in resp.json()]
        assert "Physics" in names


# ── Sentiment ─────────────────────────────────────────────────────────────────

class TestSentimentRouter:
    @pytest.mark.asyncio
    async def test_sentiment_stream_disabled(self, client):
        resp = await client.get("/events/sentiment/some-session-id")
        assert resp.status_code == 501


# ── Sessions ──────────────────────────────────────────────────────────────────

class TestSessionRouter:
    @pytest_asyncio.fixture
    async def subject_in_db(self, async_engine):
        """Insert a subject directly so the session router can reference it."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            s = Subject(id=uuid.uuid4(), name="Math-Sessions-Test")
            session.add(s)
            await session.commit()
            await session.refresh(s)
            return s

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client):
        resp = await client.get("/sessions", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/sessions/{fake_id}",
            headers={"Authorization": "Bearer fake"},
        )
        assert resp.status_code == 404


# ── Root ──────────────────────────────────────────────────────────────────────

class TestRoot:
    @pytest.mark.asyncio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "StudyMind" in resp.json()["message"]
