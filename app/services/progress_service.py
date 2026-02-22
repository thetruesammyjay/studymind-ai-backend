from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.models.progress import UserProgress
from app.schemas.progress import ProgressUpdate

class ProgressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_progress(self, user_id: uuid.UUID) -> UserProgress:
        stmt = select(UserProgress).where(UserProgress.user_id == user_id)
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            # Create if not exists
            progress = UserProgress(
                user_id=user_id,
                total_study_time_seconds=0,
                sessions_completed=0,
                current_streak_days=0,
                xp_points=0,
                level=1,
                last_updated=datetime.utcnow()
            )
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)
            
        return progress

    async def update_progress(self, user_id: uuid.UUID, update_data: ProgressUpdate) -> UserProgress:
        progress = await self.get_progress(user_id)
        
        # Update stats
        progress.total_study_time_seconds += update_data.study_time_seconds
        progress.sessions_completed += update_data.sessions_increment
        progress.xp_points += update_data.xp_increment
        
        # Simple level up logic: 100 XP per level
        progress.level = 1 + (progress.xp_points // 100)
        
        # Streak logic
        now = datetime.utcnow()
        if progress.last_study_date:
            delta = now.date() - progress.last_study_date.date()
            if delta.days == 1:
                progress.current_streak_days += 1
            elif delta.days > 1:
                progress.current_streak_days = 1
        else:
            progress.current_streak_days = 1
            
        progress.last_study_date = now
        
        await self.db.commit()
        await self.db.refresh(progress)
        return progress
