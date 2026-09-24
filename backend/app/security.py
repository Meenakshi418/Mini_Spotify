from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from pydantic_settings import BaseSettings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Settings(BaseSettings):
    JWT_SECRET: str = "change-me-before-deployment"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    youtube_api_key: str | None = None
    class Config:
        env_file = ".env"

settings = Settings()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.JWT_SECRET, algorithm="HS256")
