from pydantic import BaseModel
from uuid import UUID

class SubjectBase(BaseModel):
    name: str
    description: str | None = None

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: UUID

    class Config:
        from_attributes = True
