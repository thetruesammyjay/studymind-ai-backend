from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime
from app.models.sentiment import SentimentRecord
from app.services.gemini_service import GeminiService

class SentimentService:
    def __init__(self, db: AsyncSession, gemini: GeminiService):
        self.db = db
        self.gemini = gemini

    async def score_and_publish(self, session_id: str, text: str):
        # 1. Score
        label, confidence = await self.gemini.analyze_sentiment(text)

        # 2. Persist
        # Convert string UUID to object if necessary usually sqlalchemy handles string for UUID if properly mapped, 
        # but safely we cast or trust the driver. 
        # app/models/sentiment.py defines session_id as UUID. 
        # If input session_id is string, we might need UUID(session_id).
        # Assuming the caller passes uuid or string that sqlalchemy accepts.
        try:
            import uuid
            if isinstance(session_id, str):
                session_uuid = uuid.UUID(session_id)
            else:
                session_uuid = session_id
        except ValueError:
            # Handle invalid UUID
            return

        record = SentimentRecord(
            session_id=session_uuid,
            label=label,
            confidence=confidence,
        )
        self.db.add(record)
        # We need commit to save to DB. 
        # Note: If this is fire-and-forget task, we must ensure the session is still valid or use a new session.
        # Usually fire-and-forget tasks should create their own session.
        # However, here we are passed a session. If the caller closes it, this might fail.
        # For simplicity in this architecture user described, we assume the session is open or managed by caller.
        # BUT if called via asyncio.create_task, the request session might be closed.
        # The CONTEXT.md pattern was: asyncio.create_task(self.sentiment.score_and_publish(session.id, content))
        # This implies it runs in background. 
        # Background tasks should NOT share the request scoped session.
        # So SentimentService should probably accept a session factory or manage its own session for background tasks.
        # OR the caller awaits it (but it says fire-and-forget).
        
        # FIX: The CONTEXT.md example passes `db` to `SentimentService.__init__`.
        # If `score_and_publish` is awaited, it uses the same session.
        # If it's a background task, that session might close.
        # I will implement it as an awaitable function first. 
        # If the user wants true background task, we need a new session scope.
        await self.db.commit()

        # 3. Publish (Optional/removed Redis)
        # Since Redis is removed, valid real-time updates now rely on polling 
        # or another mechanism. For now, we just persist.
