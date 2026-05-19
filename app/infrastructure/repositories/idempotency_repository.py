from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert

from app.models.idempotency_key import IdempotencyKey


class IdempotencyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_if_not_exists(self, key: UUID, expires_at: datetime) -> bool:
        stmt = insert(IdempotencyKey).values(key=key, expires_at=expires_at)
        stmt = stmt.on_conflict_do_nothing(index_elements=['key'])
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def cleanup_expired(self):
        await self.db.execute(
            delete(IdempotencyKey).where(
                IdempotencyKey.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.db.commit()