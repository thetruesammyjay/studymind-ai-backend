"""Tests for SentimentService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sentiment import SentimentRecord
from app.models.session import StudySession
from app.models.subject import Subject
from app.services.sentiment_service import SentimentService


@pytest_asyncio.fixture
async def subject(async_session: AsyncSession) -> Subject:
    s = Subject(id=uuid.uuid4(), name="Physics")
    async_session.add(s)
    await async_session.commit()
    return s


@pytest_asyncio.fixture
async def study_session(async_session: AsyncSession, test_user, subject) -> StudySession:
    ss = StudySession(id=uuid.uuid4(), user_id=test_user.id, subject_id=subject.id)
    async_session.add(ss)
    await async_session.commit()
    await async_session.refresh(ss)
    return ss


@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.analyze_sentiment = AsyncMock(return_value=("focused", 0.95))
    return gemini


class TestScoreAndPublish:
    @pytest.mark.asyncio
    async def test_persists_record(self, async_session, study_session, mock_gemini):
        service = SentimentService(async_session, mock_gemini)
        await service.score_and_publish(study_session.id, "I understand this concept well!")

        result = await async_session.execute(select(SentimentRecord))
        records = result.scalars().all()
        assert len(records) == 1
        assert records[0].label == "focused"
        assert records[0].confidence == 0.95
        assert records[0].session_id == study_session.id

    @pytest.mark.asyncio
    async def test_calls_gemini(self, async_session, study_session, mock_gemini):
        service = SentimentService(async_session, mock_gemini)
        await service.score_and_publish(study_session.id, "test text")
        mock_gemini.analyze_sentiment.assert_awaited_once_with("test text")

    @pytest.mark.asyncio
    async def test_accepts_string_uuid(self, async_session, study_session, mock_gemini):
        service = SentimentService(async_session, mock_gemini)
        # Pass string instead of UUID object
        await service.score_and_publish(str(study_session.id), "text")
        result = await async_session.execute(select(SentimentRecord))
        assert len(result.scalars().all()) == 1

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_silently(self, async_session, mock_gemini):
        service = SentimentService(async_session, mock_gemini)
        # Should not raise — just return
        await service.score_and_publish("not-a-uuid", "text")
        result = await async_session.execute(select(SentimentRecord))
        assert len(result.scalars().all()) == 0
