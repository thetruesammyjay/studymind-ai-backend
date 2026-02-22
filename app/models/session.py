from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, DateTime
from datetime import datetime
import uuid
from .base import Base

class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    tab_label: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    subject: Mapped["Subject"] = relationship()
    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    sentiment_records: Mapped[list["SentimentRecord"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_sessions.id"))
    role: Mapped[str] = mapped_column(String(20)) # user, assistant
    content: Mapped[str] = mapped_column(Text)
    input_mode: Mapped[str] = mapped_column(String(20), default="text") # text, audio
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    session: Mapped["StudySession"] = relationship(back_populates="messages")
