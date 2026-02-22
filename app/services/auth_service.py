import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, settings: Settings):
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "type": "access",
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "type": "refresh",
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str, expected_type: str) -> str | None:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != expected_type:
                return None
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def hash_password(self, password: str) -> str:
        # Check password length and handle accordingly if needed, though bcrypt in python handles bytes.
        # However, the error 'password cannot be longer than 72 bytes' is from passlib using bcrypt backend.
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
