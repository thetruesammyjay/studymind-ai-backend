import logging
import traceback
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.config import get_settings
from app.services.session_service import SessionService
from app.services.gemini_service import GeminiService
from app.services.sentiment_service import SentimentService
from app.models.session import StudySession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"[WS] Connected. Session={session_id}, total connections={len(self.active_connections[session_id])}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"[WS] Disconnected. Session={session_id}")

    async def send_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for conn in self.active_connections[session_id]:
                try:
                    await conn.send_json(message)
                except Exception as e:
                    logger.error(f"[WS] Failed to send to connection: {e}")

manager = ConnectionManager()

@router.websocket("/ws/study/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    await manager.connect(session_id, websocket)
    
    settings = get_settings()
    
    try:
        gemini = GeminiService(settings)
        sentiment = SentimentService(db, gemini)
        service = SessionService(db, gemini, sentiment)
        
        # Verify session exists
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            logger.error(f"[WS] Invalid session UUID: {session_id}")
            await websocket.send_json({"type": "error", "content": "Invalid session ID"})
            await websocket.close(code=1008)
            return

        session = await db.get(StudySession, session_uuid)
        if not session:
            logger.error(f"[WS] Session not found: {session_id}")
            await websocket.send_json({"type": "error", "content": "Session not found"})
            await websocket.close(code=1008)
            return

        logger.info(f"[WS] Session verified, waiting for messages...")

        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            logger.info(f"[WS] Received message: '{content[:50] if content else 'EMPTY'}'")
            
            if not content:
                continue
            
            try:
                logger.info(f"[WS] Processing message with Gemini...")
                token_count = 0
                async for token in service.process_message(
                    session=session,
                    content=content,
                    input_mode="text",
                ):
                    token_count += 1
                    await manager.send_to_session(session_id, {"type": "token", "content": token})
                
                logger.info(f"[WS] Stream complete. Sent {token_count} tokens.")
                # End of stream marker
                await manager.send_to_session(session_id, {"type": "end"})
            except Exception as e:
                logger.error(f"[WS] Error processing message: {e}\n{traceback.format_exc()}")
                await manager.send_to_session(session_id, {
                    "type": "error",
                    "content": f"Failed to process: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {session_id}")
        manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"[WS] Unexpected error: {e}\n{traceback.format_exc()}")
        manager.disconnect(session_id, websocket)
