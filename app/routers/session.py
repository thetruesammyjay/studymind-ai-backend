from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.session import StudySession
from app.schemas.session import SessionCreate, SessionResponse
from app.services.session_service import SessionService
from app.services.gemini_service import GeminiService
from app.services.sentiment_service import SentimentService
from app.config import get_settings

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Determine correct service initialization
    # SessionService requires GeminiService and SentimentService
    settings = get_settings()
    gemini = GeminiService(settings)
    sentiment = SentimentService(db, gemini)
    service = SessionService(db, gemini, sentiment)
    
    session = await service.create_session(
        user_id=current_user.id,
        subject_id=session_data.subject_id
    )
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudySession).where(StudySession.user_id == current_user.id)
    )
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(StudySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this session")
    return session
