from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BlockingReasonCreateRequest(BaseModel):
    code: str = Field(pattern="^[A-Z_]+$", max_length=64)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    hard_block: bool


class BlockingReasonUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None


class BlockingReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    description: Optional[str]
    hard_block: bool
    is_active: bool