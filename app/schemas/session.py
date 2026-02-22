from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SessionCreate(BaseModel):
    subject_id: UUID

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    subject_id: UUID
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    summary: str | None = None
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    session_id: UUID
    content: str
