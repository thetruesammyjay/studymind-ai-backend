from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.config import get_settings
from app.services.session_service import SessionService
from app.services.gemini_service import GeminiService
from app.services.sentiment_service import SentimentService
from app.models.session import StudySession

router = APIRouter(tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for conn in self.active_connections[session_id]:
                await conn.send_json(message)

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
        import uuid
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            await websocket.close(code=1008)
            return

        session = await db.get(StudySession, session_uuid)
        if not session:
            await websocket.close(code=1008)
            return

        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                continue
                
            async for token in service.process_message(
                session=session,
                content=content,
                input_mode="text",
            ):
                await manager.send_to_session(session_id, {"type": "token", "content": token})
            
            # End of stream marker
            await manager.send_to_session(session_id, {"type": "end"})

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as e:
        # Log error
        print(f"WebSocket Error: {e}")
        manager.disconnect(session_id, websocket)
