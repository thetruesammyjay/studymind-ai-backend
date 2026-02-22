from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
from app.config import get_settings, Settings
from app.database import AsyncSessionLocal

security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


from app.models.user import User
from app.services.auth_service import AuthService # We will create this next

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    auth = AuthService(get_settings())
    # AuthService.verify_token handles the decoding and exceptions internally and returns None if invalid
    user_id = auth.verify_token(token, "access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    # We need to import User here or at top. 
    # Since we imported at top now, we can use it.
    # Note: we need to handle UUID conversion if user_id is string from token
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = await db.get(User, user_uuid)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
