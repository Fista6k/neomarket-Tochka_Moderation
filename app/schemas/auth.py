from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: UUID
    role: Optional[UserRole] = None