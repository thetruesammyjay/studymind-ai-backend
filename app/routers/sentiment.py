from fastapi import APIRouter, Depends, HTTPException, status

# Redis removed, SSE stream disabled for now.
# Real-time sentiment updates would require a different mechanism (e.g. periodic polling or PG LISTEN/NOTIFY).

router = APIRouter(tags=["sentiment"])

@router.get("/events/sentiment/{session_id}")
async def sentiment_stream(session_id: str):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Real-time sentiment stream is currently disabled due to removal of Redis."
    )
