from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):
    queue_priority: Optional[int] = Field(default=None, ge=1, le=4)
    category_ids: Optional[List[UUID]] = None