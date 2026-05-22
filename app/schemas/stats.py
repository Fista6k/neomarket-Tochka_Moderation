from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class StatsOverview(BaseModel):
    pending_count: int
    in_review_count: int
    approved_count: int
    blocked_count: int
    hard_blocked_count: int
    avg_review_time_seconds: Optional[int]
    pending_by_priority: dict[str, int]


class ModeratorStats(BaseModel):
    moderator_id: UUID
    moderator_name: str
    decisions_count: int
    approved_count: int
    blocked_count: int
    hard_blocked_count: int
    avg_review_time_seconds: Optional[int]
    released_count: int