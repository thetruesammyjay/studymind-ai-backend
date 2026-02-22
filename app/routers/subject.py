from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.subject import Subject
from app.schemas.subject import SubjectResponse, SubjectCreate
from app.models.user import User

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.get("", response_model=List[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    # Optional: require auth
    # current_user: User = Depends(get_current_user) 
):
    result = await db.execute(select(Subject))
    return result.scalars().all()

@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Only auth users can create
):
    # Check existing
    result = await db.execute(select(Subject).where(Subject.name == subject.name))
    if result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Subject already exists")

    new_subject = Subject(name=subject.name, description=subject.description)
    db.add(new_subject)
    await db.commit()
    await db.refresh(new_subject)
    return new_subject
