# app/schemas/ticket.py

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import (
    TicketKind,
    TicketStatus,
    FieldSeverity,
    TicketAction,
)
from .blocking_reason import BlockingReasonResponse


class FieldReport(BaseModel):
    field_path: str = Field(example="images[0].url")
    message: str = Field(max_length=1000)
    severity: FieldSeverity = Field(default=FieldSeverity.ERROR)


class FieldReportResponse(FieldReport):
    model_config = ConfigDict(from_attributes=True)
    id: UUID



class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    seller_id: UUID
    category_id: Optional[UUID]

    kind: TicketKind
    status: TicketStatus
    queue_priority: int

    assigned_moderator_id: Optional[UUID]
    claimed_at: Optional[datetime]
    claim_expires_at: Optional[datetime]
    decision_at: Optional[datetime]

    created_at: datetime
    updated_at: Optional[datetime]



class TicketHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    at: datetime
    action: TicketAction
    moderator_id: Optional[UUID]
    comment: Optional[str]



class DiffEntry(BaseModel):
    field: str
    old_value: Optional[Any]
    new_value: Optional[Any]


class TicketDetailResponse(TicketResponse):
    json_before: Optional[dict]
    json_after: dict

    diff: Optional[List[DiffEntry]] = None
    field_reports: List[FieldReportResponse] = []
    blocking_reasons: List[BlockingReasonResponse] = []
    decision_comment: Optional[str] = None
    history: List[TicketHistoryEntry] = []



class ApproveRequest(BaseModel):
    comment: Optional[str] = Field(default=None, max_length=2000)


class BlockDecisionRequest(BaseModel):
    blocking_reason_ids: List[UUID] = Field(min_length=1)
    comment: Optional[str] = Field(default=None, max_length=2000)
    field_reports: Optional[List[FieldReport]] = None



class PaginatedTickets(BaseModel):
    items: List[TicketResponse]
    total_count: int
    limit: int
    offset: int