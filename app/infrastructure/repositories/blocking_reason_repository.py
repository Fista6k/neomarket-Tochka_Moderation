from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.blocking_reason import BlockingReason


class BlockingReasonRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        reason_id: UUID,
    ) -> BlockingReason | None:
        return await self.db.get(BlockingReason, reason_id)

    async def get_by_code(
        self,
        code: str,
    ) -> BlockingReason | None:
        result = await self.db.execute(
            select(BlockingReason).where(BlockingReason.code == code)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        hard_block: bool | None,
        is_active: bool | None,
    ):
        query = select(BlockingReason)

        if hard_block is not None:
            query = query.where(BlockingReason.hard_block == hard_block)

        query = query.where(BlockingReason.is_active == is_active)

        result = await self.db.execute(query.order_by(BlockingReason.code.asc()))
        return result.scalars().all()

    async def create(
        self,
        reason: BlockingReason,
    ) -> BlockingReason:
        self.db.add(reason)
        await self.db.commit()
        await self.db.refresh(reason)
        return reason

    async def save(self):
        await self.db.commit()