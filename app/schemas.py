from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class SKUCharacteristic(BaseModel):
    name: str
    value: str


class SKUResponse(BaseModel):
    id: int
    name: str
    price: Optional[int]
    status: str
    characteristics: List[SKUCharacteristic] = []


class ProductSnapshotResponse(BaseModel):
    snapshot_type: str
    data: dict
    created_at: datetime


class ProductCardResponse(BaseModel):
    product_id: int
    external_id: int
    seller_id: int
    title: str
    description: Optional[str]
    category_id: Optional[int]
    status: str
    b2b_status: Optional[str]
    snapshots: List[ProductSnapshotResponse]
    skus: List[SKUResponse]
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
    status: str


class DeclineResponse(BaseModel):
    message: str
    product_id: int
    status: str
