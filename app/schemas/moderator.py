from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import UserRole


class ModeratorCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    first_name: str = Field(max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: UserRole
    category_specializations: Optional[List[UUID]] = None


class ModeratorUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    category_specializations: Optional[List[UUID]] = None


class ModeratorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: Optional[str]
    role: UserRole
    is_active: bool
    category_specializations: Optional[List[UUID]]
    created_at: datetime
    last_login_at: Optional[datetime]


class PaginatedModerators(BaseModel):
    items: list[ModeratorResponse]
    total_count: int
    limit: int
    offset: int