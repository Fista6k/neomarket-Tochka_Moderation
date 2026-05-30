from uuid import UUID
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator


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
    idempotency_key: str
    occurred_at: datetime
    payload: Union[
        EventProductCreated,
        EventProductEdited,
        EventProductDeleted,
    ]

    @field_validator('payload', mode='before')
    @classmethod
    def decode_payload(cls, v, info):
        event_type = info.data.get('event_type')
        if event_type == 'PRODUCT_CREATED':
            return EventProductCreated(**v)
        if event_type == 'PRODUCT_EDITED':
            return EventProductEdited(**v)
        if event_type == 'PRODUCT_DELETED':
            return EventProductDeleted(**v)
        raise ValueError(f'Unknown event_type: {event_type}')