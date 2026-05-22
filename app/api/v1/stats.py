from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.moderator import get_current_moderator
from app.application.services.stats_service import StatsService
from app.database import get_db
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.models.moderator import Moderator
from app.schemas.stats import ModeratorStats, StatsOverview


Period = Literal["today", "week", "month"]

router = APIRouter()


async def get_stats_service(db: AsyncSession = Depends(get_db)):
    return StatsService(TicketRepository(db))


@router.get("/overview", response_model=StatsOverview)
async def stats_overview(
    period: Period = Query(default="today"),
    service: StatsService = Depends(get_stats_service),
    _: Moderator = Depends(get_current_moderator),
):
    return await service.overview(period)


@router.get("/moderators", response_model=list[ModeratorStats])
async def moderator_stats(
    period: Period = Query(default="week"),
    service: StatsService = Depends(get_stats_service),
    _: Moderator = Depends(get_current_moderator),
):
    return await service.moderators(period)
