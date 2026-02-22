"""Tests for app.config — Settings and DATABASE_URL validation."""

import pytest

from app.config import Settings


class TestAssembleDbConnection:
    def test_converts_postgres_scheme(self):
        s = Settings(
            DATABASE_URL="postgres://user:pass@host/db",
            JWT_SECRET="s",
            GEMINI_API_KEY="k",
            _env_file=None,
        )
        assert s.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_converts_postgresql_scheme(self):
        s = Settings(
            DATABASE_URL="postgresql://user:pass@host/db",
            JWT_SECRET="s",
            GEMINI_API_KEY="k",
            _env_file=None,
        )
        assert s.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_preserves_asyncpg_scheme(self):
        url = "postgresql+asyncpg://user:pass@host/db"
        s = Settings(
            DATABASE_URL=url,
            JWT_SECRET="s",
            GEMINI_API_KEY="k",
            _env_file=None,
        )
        assert s.DATABASE_URL == url

    def test_preserves_query_params(self):
        s = Settings(
            DATABASE_URL="postgres://user:pass@host/db?ssl=require",
            JWT_SECRET="s",
            GEMINI_API_KEY="k",
            _env_file=None,
        )
        assert "ssl=require" in s.DATABASE_URL

    def test_sqlite_url_unchanged(self):
        url = "sqlite+aiosqlite:///:memory:"
        s = Settings(
            DATABASE_URL=url,
            JWT_SECRET="s",
            GEMINI_API_KEY="k",
            _env_file=None,
        )
        assert s.DATABASE_URL == url


class TestSettingsDefaults:
    def test_default_values(self, monkeypatch):
        # Prevent reading from .env so we test actual code defaults
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        monkeypatch.delenv("CORS_ORIGIN", raising=False)
        s = Settings(
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            JWT_SECRET="secret",
            GEMINI_API_KEY="key",
            _env_file=None,
        )
        assert s.APP_NAME == "StudyMind AI"
        assert s.DEBUG is False
        assert s.JWT_ALGORITHM == "HS256"
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert s.GEMINI_MODEL == "gemini-1.5-flash"
        assert s.CORS_ORIGIN == "*"
