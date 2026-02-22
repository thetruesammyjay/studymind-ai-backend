from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ProgressBase(BaseModel):
    total_study_time_seconds: int
    sessions_completed: int
    current_streak_days: int
    last_study_date: datetime | None = None
    xp_points: int
    level: int

class ProgressUpdate(BaseModel):
    study_time_seconds: int = 0
    sessions_increment: int = 0
    xp_increment: int = 0

class ProgressResponse(ProgressBase):
    id: UUID
    user_id: UUID
    last_updated: datetime

    class Config:
        from_attributes = True
