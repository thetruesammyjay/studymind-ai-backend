"""Tests for Pydantic schemas."""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.schemas.progress import ProgressBase, ProgressResponse, ProgressUpdate
from app.schemas.sentiment import SentimentEvent
from app.schemas.session import ChatRequest, MessageResponse, SessionCreate, SessionResponse
from app.schemas.subject import SubjectBase, SubjectCreate, SubjectResponse
from app.schemas.voice import VoiceTranscriptionRequest, VoiceTranscriptionResponse


# ── Auth schemas ──────────────────────────────────────────────────────────────

class TestToken:
    def test_valid(self):
        t = Token(access_token="abc", refresh_token="xyz", token_type="bearer")
        assert t.access_token == "abc"
        assert t.token_type == "bearer"


class TestUserCreate:
    def test_valid(self):
        u = UserCreate(email="a@b.com", password="secret")
        assert u.full_name is None

    def test_with_name(self):
        u = UserCreate(email="a@b.com", password="secret", full_name="Alice")
        assert u.full_name == "Alice"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="secret")


class TestUserLogin:
    def test_valid(self):
        u = UserLogin(email="a@b.com", password="pwd")
        assert u.email == "a@b.com"


class TestUserResponse:
    def test_valid(self):
        uid = uuid.uuid4()
        r = UserResponse(id=uid, email="a@b.com", is_active=True)
        assert r.id == uid
        assert r.full_name is None


# ── Session schemas ───────────────────────────────────────────────────────────

class TestSessionCreate:
    def test_valid(self):
        sid = uuid.uuid4()
        s = SessionCreate(subject_id=sid)
        assert s.subject_id == sid


class TestMessageResponse:
    def test_valid(self):
        m = MessageResponse(
            id=uuid.uuid4(), role="user", content="hello", created_at=datetime.utcnow()
        )
        assert m.role == "user"


class TestSessionResponse:
    def test_defaults(self):
        s = SessionResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            subject_id=uuid.uuid4(),
            status="active",
            started_at=datetime.utcnow(),
        )
        assert s.ended_at is None
        assert s.messages == []


class TestChatRequest:
    def test_valid(self):
        c = ChatRequest(session_id=uuid.uuid4(), content="explain this")
        assert c.content == "explain this"


# ── Subject schemas ───────────────────────────────────────────────────────────

class TestSubjectCreate:
    def test_valid(self):
        s = SubjectCreate(name="Math")
        assert s.description is None


class TestSubjectResponse:
    def test_valid(self):
        s = SubjectResponse(id=uuid.uuid4(), name="Physics", description="AP Physics")
        assert s.name == "Physics"


# ── Progress schemas ──────────────────────────────────────────────────────────

class TestProgressUpdate:
    def test_defaults(self):
        p = ProgressUpdate()
        assert p.study_time_seconds == 0
        assert p.xp_increment == 0


class TestProgressResponse:
    def test_valid(self):
        p = ProgressResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            total_study_time_seconds=3600,
            sessions_completed=5,
            current_streak_days=3,
            xp_points=250,
            level=3,
            last_updated=datetime.utcnow(),
        )
        assert p.level == 3


# ── Sentiment schemas ─────────────────────────────────────────────────────────

class TestSentimentEvent:
    def test_valid(self):
        s = SentimentEvent(label="focused", confidence=0.92, timestamp=datetime.utcnow())
        assert s.label == "focused"


# ── Voice schemas ─────────────────────────────────────────────────────────────

class TestVoiceTranscriptionRequest:
    def test_defaults(self):
        v = VoiceTranscriptionRequest(audio_data="base64data")
        assert v.format == "webm"

    def test_custom_format(self):
        v = VoiceTranscriptionRequest(audio_data="data", format="wav")
        assert v.format == "wav"


class TestVoiceTranscriptionResponse:
    def test_valid(self):
        v = VoiceTranscriptionResponse(text="hello world")
        assert v.text == "hello world"
