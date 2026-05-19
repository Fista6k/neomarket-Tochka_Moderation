from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.models.moderator import Moderator


class ModeratorRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(
        self,
        email: str,
    ) -> Moderator | None:
        result = await self.db.execute(
            select(Moderator).where(Moderator.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        moderator_id: UUID,
    ) -> Moderator | None:
        return await self.db.get(Moderator, moderator_id)

    async def create(
        self,
        moderator: Moderator,
    ) -> Moderator:
        self.db.add(moderator)
        await self.db.commit()
        await self.db.refresh(moderator)
        return moderator

    async def list(
        self,
        limit: int,
        offset: int,
        is_active: bool | None,
    ):
        query = select(Moderator)

        if is_active is not None:
            query = query.where(Moderator.is_active == is_active)

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Moderator.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        moderators = result.scalars().all()

        return moderators, total_count

    async def save(self):
        await self.db.commit()