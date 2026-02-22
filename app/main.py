from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

from app.utils import setup_logging

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to StudyMind AI API"}

from app.routers import auth_router, session_router, chat_router, sentiment_router, subject_router, health_router

app.include_router(auth_router)
app.include_router(session_router)
app.include_router(chat_router)
app.include_router(sentiment_router)
app.include_router(subject_router)
app.include_router(health_router)
