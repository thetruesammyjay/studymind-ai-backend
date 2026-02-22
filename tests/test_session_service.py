"""Tests for SessionService."""

import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Message, StudySession
from app.models.subject import Subject
from app.services.session_service import SessionService


@pytest_asyncio.fixture
async def subject(async_session: AsyncSession) -> Subject:
    s = Subject(id=uuid.uuid4(), name="Mathematics", description="Math course")
    async_session.add(s)
    await async_session.commit()
    await async_session.refresh(s)
    return s


@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.analyze_sentiment = AsyncMock(return_value=("focused", 0.9))
    return gemini


@pytest.fixture
def mock_sentiment():
    sentiment = MagicMock()
    sentiment.score_and_publish = AsyncMock()
    return sentiment


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_creates_session(self, async_session, test_user, subject, mock_gemini, mock_sentiment):
        service = SessionService(async_session, mock_gemini, mock_sentiment)
        session = await service.create_session(test_user.id, subject.id)
        assert session.user_id == test_user.id
        assert session.subject_id == subject.id
        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_accepts_string_uuids(self, async_session, test_user, subject, mock_gemini, mock_sentiment):
        service = SessionService(async_session, mock_gemini, mock_sentiment)
        session = await service.create_session(str(test_user.id), str(subject.id))
        assert session.user_id == test_user.id


class TestBuildPrompt:
    def test_formats_prompt_correctly(self, async_session, mock_gemini, mock_sentiment):
        service = SessionService(async_session, mock_gemini, mock_sentiment)
        messages = [
            SimpleNamespace(role="user", content="What is 2+2?"),
            SimpleNamespace(role="assistant", content="2+2 equals 4."),
        ]
        prompt = service._build_prompt(messages, "What about 3+3?")
        assert "Student: What is 2+2?" in prompt
        assert "Tutor: 2+2 equals 4." in prompt
        assert "Student: What about 3+3?" in prompt
        assert prompt.endswith("Tutor: ")

    def test_empty_history(self, async_session, mock_gemini, mock_sentiment):
        service = SessionService(async_session, mock_gemini, mock_sentiment)
        prompt = service._build_prompt([], "Hello")
        assert "Student: Hello" in prompt
        assert "study assistant" in prompt.lower()


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_messages_ordered(self, async_session, test_user, subject, mock_gemini, mock_sentiment):
        service = SessionService(async_session, mock_gemini, mock_sentiment)
        study_session = await service.create_session(test_user.id, subject.id)

        # Add messages
        for i in range(3):
            msg = Message(
                session_id=study_session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"message {i}",
            )
            async_session.add(msg)
        await async_session.commit()

        history = await service._get_history(study_session.id)
        assert len(history) == 3
        assert history[0].content == "message 0"
