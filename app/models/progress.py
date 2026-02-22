from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, Float, DateTime
from datetime import datetime
import uuid
from .base import Base

class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    
    total_study_time_seconds: Mapped[int] = mapped_column(default=0)
    sessions_completed: Mapped[int] = mapped_column(default=0)
    current_streak_days: Mapped[int] = mapped_column(default=0)
    last_study_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    xp_points: Mapped[int] = mapped_column(default=0)
    level: Mapped[int] = mapped_column(default=1)
    
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="progress")
    
# We need to update User model to include the back_populates
# "progress": Mapped["UserProgress"] = relationship(back_populates="user", uselist=False)
