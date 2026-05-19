# app/schemas/b2b.py

from uuid import UUID
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field


class EventProductCreated(BaseModel):
    product_id: UUID
    seller_id: UUID
    category_id: Optional[UUID] = None
    queue_priority: int = Field(default=3, ge=1, le=4)
    json_after: dict


class EventProductEdited(BaseModel):
    product_id: UUID
    seller_id: UUID
    category_id: Optional[UUID] = None
    queue_priority: int = Field(default=3, ge=1, le=4)
    json_before: dict
    json_after: dict


class EventProductDeleted(BaseModel):
    product_id: UUID

class IncomingB2BEvent(BaseModel):
    event_type: str
    idempotency_key: UUID
    occurred_at: datetime
    payload: Union[
        EventProductCreated,
        EventProductEdited,
        EventProductDeleted,
    ]