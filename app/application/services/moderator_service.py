from fastapi import HTTPException
from uuid import UUID

from app.models.moderator import Moderator
from app.schemas.moderator import (
    ModeratorCreateRequest,
    ModeratorUpdateRequest,
)
from app.api.v1.dependencies.security import hash_password
from app.infrastructure.repositories.moderator_repository import ModeratorRepository


class ModeratorService:

    def __init__(self, repo: ModeratorRepository):
        self.repo = repo

    async def create(
        self,
        data: ModeratorCreateRequest,
    ) -> Moderator:

        existing = await self.repo.get_by_email(data.email)

        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")

        moderator = Moderator(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            category_specializations=data.category_specializations,
        )

        return await self.repo.create(moderator)

    async def get_by_id(
        self,
        moderator_id: UUID,
    ) -> Moderator:

        moderator = await self.repo.get_by_id(moderator_id)

        if not moderator:
            raise HTTPException(status_code=404, detail="Moderator not found")

        return moderator

    async def list(
        self,
        limit: int,
        offset: int,
        is_active: bool | None,
    ):
        return await self.repo.list(limit, offset, is_active)

    async def update(
        self,
        moderator_id: UUID,
        data: ModeratorUpdateRequest,
    ) -> Moderator:

        moderator = await self.repo.get_by_id(moderator_id)

        if not moderator:
            raise HTTPException(status_code=404, detail="Moderator not found")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(moderator, field, value)

        await self.repo.save()
        await self.repo.db.refresh(moderator)

        return moderator

    async def deactivate(
        self,
        moderator_id: UUID,
    ):

        moderator = await self.repo.get_by_id(moderator_id)

        if not moderator:
            raise HTTPException(status_code=404, detail="Moderator not found")

        moderator.is_active = False
        await self.repo.save()