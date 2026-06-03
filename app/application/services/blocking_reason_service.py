from fastapi import HTTPException
from uuid import UUID

from app.models.blocking_reason import BlockingReason
from app.schemas.blocking_reason import (
    BlockingReasonCreateRequest,
    BlockingReasonUpdateRequest,
)
from app.infrastructure.repositories.blocking_reason_repository import BlockingReasonRepository


class BlockingReasonService:

    def __init__(self, repo: BlockingReasonRepository):
        self.repo = repo

    async def create(
        self,
        data: BlockingReasonCreateRequest,
    ) -> BlockingReason:

        existing = await self.repo.get_by_code(data.code)

        if existing:
            raise HTTPException(status_code=409, detail="Code already exists")

        reason = BlockingReason(
            code=data.code,
            title=data.title,
            description=data.description,
            hard_block=data.hard_block,
            is_active=True,
        )

        return await self.repo.create(reason)

    async def list(
        self,
        hard_block: bool | None,
        is_active: bool | None,
    ):
        if is_active is None:
            is_active = True

        return await self.repo.list(
            hard_block,
            is_active,
        )
    
    async def update(
        self,
        reason_id: UUID,
        data: BlockingReasonUpdateRequest,
    ) -> BlockingReason:

        reason = await self.repo.get_by_id(reason_id)

        if not reason:
            raise HTTPException(status_code=404, detail="Blocking reason not found")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(reason, field, value)

        await self.repo.save()
        await self.repo.db.refresh(reason)

        return reason

    async def deactivate(
        self,
        reason_id: UUID,
    ):

        reason = await self.repo.get_by_id(reason_id)

        if not reason:
            raise HTTPException(status_code=404, detail="Blocking reason not found")
        
        if await self.repo.is_used(reason_id):
            raise HTTPException(
                status_code=409,
                detail="Cannot deactivate blocking reason that is already used in moderation tickets"
            )

        reason.is_active = False
        await self.repo.save()