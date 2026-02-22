from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
import uuid
from .base import Base

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String)
    
    # Relationships
    # sessions: Mapped[list["StudySession"]] = relationship(back_populates="subject")
