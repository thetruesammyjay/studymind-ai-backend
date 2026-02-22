from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Float, DateTime
from datetime import datetime
import uuid
from .base import Base

class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_sessions.id"))
    label: Mapped[str] = mapped_column(String(50)) # focus, confused, frustrated, confident
    confidence: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    session: Mapped["StudySession"] = relationship(back_populates="sentiment_records")
