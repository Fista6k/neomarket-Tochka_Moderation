from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert

from app.models.idempotency_key import IdempotencyKey


class IdempotencyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_if_not_exists(self, key: str, expires_at: datetime) -> bool:
        expires_at = self._as_naive_utc(expires_at)
        stmt = insert(IdempotencyKey).values(key=key, expires_at=expires_at)
        stmt = stmt.on_conflict_do_nothing(index_elements=['key'])
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def cleanup_expired(self):
        await self.db.execute(
            delete(IdempotencyKey).where(
                IdempotencyKey.expires_at < self._now_naive_utc()
            )
        )
        await self.db.commit()

    @staticmethod
    def _now_naive_utc() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _as_naive_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
