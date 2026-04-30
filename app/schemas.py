from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class ProductSnapshotResponse(BaseModel):
    snapshot_type: str
    data: dict
    created_at: datetime


class ProductCardResponse(BaseModel):
    product_id: int
    title: str
    description: Optional[str]
    category_id: Optional[int]
    b2b_status: Optional[str]
    snapshots: List[ProductSnapshotResponse]
    skus: List[Any]  # SKU из B2B в сыром виде
    is_new: bool


class BlockingReasonResponse(BaseModel):
    id: int
    code: str
    description: str


class DeclineRequest(BaseModel):
    reason_code: str
    comment: Optional[str] = None


class ApproveResponse(BaseModel):
    message: str
    product_id: int


class DeclineResponse(BaseModel):
    message: str
    product_id: int
