"""Tests for ProgressService — XP, streaks, levels."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.progress import UserProgress
from app.schemas.progress import ProgressUpdate
from app.services.progress_service import ProgressService


@pytest.fixture
def user_id():
    return uuid.uuid4()


class TestGetProgress:
    @pytest.mark.asyncio
    async def test_creates_new_if_none_exists(self, async_session, user_id):
        service = ProgressService(async_session)
        progress = await service.get_progress(user_id)
        assert progress is not None
        assert progress.user_id == user_id
        assert progress.xp_points == 0
        assert progress.level == 1

    @pytest.mark.asyncio
    async def test_returns_existing(self, async_session, user_id):
        # Pre-create
        existing = UserProgress(
            user_id=user_id,
            total_study_time_seconds=100,
            sessions_completed=2,
            current_streak_days=1,
            xp_points=50,
            level=1,
            last_updated=datetime.utcnow(),
        )
        async_session.add(existing)
        await async_session.commit()

        service = ProgressService(async_session)
        progress = await service.get_progress(user_id)
        assert progress.xp_points == 50
        assert progress.sessions_completed == 2


class TestUpdateProgress:
    @pytest.mark.asyncio
    async def test_increments_stats(self, async_session, user_id):
        service = ProgressService(async_session)
        update = ProgressUpdate(study_time_seconds=600, sessions_increment=1, xp_increment=25)
        progress = await service.update_progress(user_id, update)
        assert progress.total_study_time_seconds == 600
        assert progress.sessions_completed == 1
        assert progress.xp_points == 25

    @pytest.mark.asyncio
    async def test_level_up_at_100_xp(self, async_session, user_id):
        service = ProgressService(async_session)
        update = ProgressUpdate(xp_increment=250)
        progress = await service.update_progress(user_id, update)
        # 250 xp -> level 1 + (250 // 100) = 3
        assert progress.level == 3

    @pytest.mark.asyncio
    async def test_streak_continues_on_consecutive_day(self, async_session, user_id):
        # Pre-create with yesterday's date
        yesterday = datetime.utcnow() - timedelta(days=1)
        existing = UserProgress(
            user_id=user_id,
            total_study_time_seconds=0,
            sessions_completed=0,
            current_streak_days=5,
            xp_points=0,
            level=1,
            last_study_date=yesterday,
            last_updated=datetime.utcnow(),
        )
        async_session.add(existing)
        await async_session.commit()

        service = ProgressService(async_session)
        update = ProgressUpdate(xp_increment=10)
        progress = await service.update_progress(user_id, update)
        assert progress.current_streak_days == 6

    @pytest.mark.asyncio
    async def test_streak_resets_on_gap(self, async_session, user_id):
        # Pre-create with 3 days ago
        old_date = datetime.utcnow() - timedelta(days=3)
        existing = UserProgress(
            user_id=user_id,
            total_study_time_seconds=0,
            sessions_completed=0,
            current_streak_days=10,
            xp_points=0,
            level=1,
            last_study_date=old_date,
            last_updated=datetime.utcnow(),
        )
        async_session.add(existing)
        await async_session.commit()

        service = ProgressService(async_session)
        update = ProgressUpdate(xp_increment=10)
        progress = await service.update_progress(user_id, update)
        assert progress.current_streak_days == 1

    @pytest.mark.asyncio
    async def test_streak_starts_at_1_when_no_previous_study(self, async_session, user_id):
        service = ProgressService(async_session)
        update = ProgressUpdate(xp_increment=10)
        progress = await service.update_progress(user_id, update)
        assert progress.current_streak_days == 1
