from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeoMarket Moderation"
    VERSION: str = "1.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moderation"

    B2B_API_BASE_URL: str = "http://b2b-service/api/v1"
    B2B_TIMEOUT: float = 5.0
    B2B_API_TOKEN: Optional[str] = None  # Токен авторизации для B2B
    B2B_SERVICE_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECURE: bool = False

    INITIAL_ADMIN_EMAIL: str
    INITIAL_ADMIN_PASSWORD: str

    IDEMPOTENCY_TTL_HOURS: int = 24

    DEBUG: bool = True

    MODERATION_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
