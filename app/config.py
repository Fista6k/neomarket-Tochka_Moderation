from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeoMarket Moderation"
    VERSION: str = "1.0"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moderation"

    B2B_API_BASE_URL: str = "http://b2b-service/api/v1"
    B2B_TIMEOUT: float = 5.0
    B2B_API_TOKEN: Optional[str] = None  # Токен авторизации для B2B

    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
