from fastapi import APIRouter
from app.database import engine
from sqlalchemy import text

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 OK if the service is running.
    Checks database connection.
    """
    health_status = {"status": "ok", "database": "unknown"}
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
        
    return health_status
