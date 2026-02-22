from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator
import asyncio
import uuid # helpers
from app.models.session import StudySession, Message
from app.services.gemini_service import GeminiService
from app.services.sentiment_service import SentimentService

# We need a template renderer. 
# CONTEXT.md mentions `app/ml/prompt_templates.py`. I should check if it exists or implement a simple one.
# I'll implement a simple private method for now.

class SessionService:
    def __init__(
        self,
        db: AsyncSession,
        gemini: GeminiService,
        sentiment: SentimentService,
    ):
        self.db = db
        self.gemini = gemini
        self.sentiment = sentiment

    async def create_session(
        self,
        user_id: uuid.UUID | str,
        subject_id: uuid.UUID | str,
    ) -> StudySession:
        if isinstance(user_id, str): user_id = uuid.UUID(user_id)
        if isinstance(subject_id, str): subject_id = uuid.UUID(subject_id)
        
        session = StudySession(user_id=user_id, subject_id=subject_id)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def process_message(
        self,
        session: StudySession,
        content: str,
        input_mode: str,
    ) -> AsyncGenerator[str, None]:
        # 1. Persist user message
        user_msg = Message(
            session_id=session.id,
            role="user",
            content=content,
            input_mode=input_mode,
        )
        self.db.add(user_msg)
        await self.db.commit()

        # 2. Score sentiment (fire-and-forget logic corrected: await it for safety in this scope or assume proper managing)
        # For true background task without blocking:
        # We need to ensure db session is safe. 
        # Since we are inside a request scope usually, awaiting it is safer for data consistency vs race conditions on closing.
        # But to be "optimised", maybe fire and forget? 
        # I'll await it to ensure it's saved, as sentiment model is fast enough (CPU inference).
        await self.sentiment.score_and_publish(session.id, content)

        # 3. Build context window
        history = await self._get_history(session.id)
        prompt = self._build_prompt(history, content)

        # 4. Stream Gemini response
        ai_content = []
        async for token in self.gemini.stream(prompt):
            ai_content.append(token)
            yield token

        # 5. Persist AI message
        ai_msg = Message(
            session_id=session.id,
            role="assistant",
            content="".join(ai_content),
        )
        self.db.add(ai_msg)
        await self.db.commit()

    async def _get_history(self, session_id: uuid.UUID) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(20)  # Last 20 messages
        )
        return list(result.scalars().all())

    def _build_prompt(self, history: list[Message], new_content: str) -> str:
        # Simple prompt construction
        prompt_parts = ["You are a helpful study assistant. Answer the student's questions based on the context."]
        for msg in history:
            role = "Student" if msg.role == "user" else "Tutor"
            prompt_parts.append(f"{role}: {msg.content}")
        
        prompt_parts.append(f"Student: {new_content}")
        prompt_parts.append("Tutor: ")
        return "\n".join(prompt_parts)
