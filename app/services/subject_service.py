from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate

class SubjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_subjects(self) -> List[Subject]:
        stmt = select(Subject)
        result = await self.db.execute(stmt)
        subjects = result.scalars().all()
        return list(subjects)

    async def create_subject(self, subject_data: SubjectCreate) -> Subject:
        subject = Subject(name=subject_data.name, description=subject_data.description)
        self.db.add(subject)
        await self.db.commit()
        await self.db.refresh(subject)
        return subject

