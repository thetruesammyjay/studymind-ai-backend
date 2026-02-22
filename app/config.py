from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "StudyMind AI"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External Services
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    CORS_ORIGIN: str = "*"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str):
             if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
             if v.startswith("postgresql://") and "asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
             # asyncpg uses 'ssl' not 'sslmode', and doesn't support 'channel_binding'
             if "asyncpg" in v:
                v = v.replace("sslmode=", "ssl=")
                # Remove channel_binding param (not supported by asyncpg)
                import re
                v = re.sub(r"[&?]channel_binding=[^&]*", "", v)
        return v

@lru_cache
def get_settings():
    return Settings()
