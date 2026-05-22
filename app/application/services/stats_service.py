from datetime import datetime, timedelta, timezone
from typing import Literal

from app.infrastructure.repositories.ticket_repository import TicketRepository


Period = Literal["today", "week", "month"]


class StatsService:
    def __init__(self, repo: TicketRepository):
        self.repo = repo

    async def overview(self, period: Period):
        await self.repo.auto_return_expired()
        return await self.repo.stats_overview(self._period_start(period))

    async def moderators(self, period: Period):
        return await self.repo.moderator_stats(self._period_start(period))

    @staticmethod
    def _period_start(period: Period) -> datetime:
        now = datetime.now(timezone.utc)

        if period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "week":
            return now - timedelta(days=7)
        if period == "month":
            return now - timedelta(days=30)

        return now.replace(hour=0, minute=0, second=0, microsecond=0)
