from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
    settings = get_settings()
    gemini = GeminiService(settings)
    sentiment = SentimentService(db, gemini)
    service = SessionService(db, gemini, sentiment)
    
    session = await service.create_session(
        user_id=current_user.id,
        subject_id=session_data.subject_id
    )
    # Eagerly load messages to avoid MissingGreenlet in async context
    await db.refresh(session, attribute_names=["messages"])
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudySession)
        .where(StudySession.user_id == current_user.id)
        .options(selectinload(StudySession.messages))
    )
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudySession)
        .where(StudySession.id == session_id)
        .options(selectinload(StudySession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this session")
    return session
