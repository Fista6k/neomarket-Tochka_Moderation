from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.moderator import (
    ModeratorCreateRequest,
    ModeratorUpdateRequest,
    ModeratorResponse,
    PaginatedModerators,
)
from app.application.services.moderator_service import ModeratorService
from app.api.v1.dependencies.moderator import (
    get_current_moderator,
    get_admin_user,
)
from app.infrastructure.repositories.moderator_repository import ModeratorRepository
from app.models.moderator import Moderator


router = APIRouter()

async def get_moderator_service(db: AsyncSession = Depends(get_db)):
    repo = ModeratorRepository(db)
    return ModeratorService(repo)

@router.get("", response_model=PaginatedModerators)
async def list_moderators(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_active: bool | None = None,
    service: ModeratorService = Depends(get_moderator_service),
    _: Moderator = Depends(get_admin_user),
):
    moderators, total_count = await service.list(
        limit=limit,
        offset=offset,
        is_active=is_active,
    )

    return {
        "items": moderators,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=ModeratorResponse, status_code=201)
async def create_moderator(
    data: ModeratorCreateRequest,
    service: ModeratorService = Depends(get_moderator_service),
    _: Moderator = Depends(get_admin_user),
):
    return await service.create(data)


@router.get("/me", response_model=ModeratorResponse)
async def get_me(
    current_user: Moderator = Depends(get_current_moderator),
):
    return current_user


@router.get("/{moderator_id}", response_model=ModeratorResponse)
async def get_moderator(
    moderator_id: UUID,
    service: ModeratorService = Depends(get_moderator_service),
    _: Moderator = Depends(get_admin_user),
):
    return await service.get_by_id(moderator_id)


@router.patch("/{moderator_id}", response_model=ModeratorResponse)
async def update_moderator(
    moderator_id: UUID,
    data: ModeratorUpdateRequest,
    service: ModeratorService = Depends(get_moderator_service),
    _: Moderator = Depends(get_admin_user),
):
    return await service.update(moderator_id, data)


@router.delete("/{moderator_id}", status_code=204)
async def delete_moderator(
    moderator_id: UUID,
    service: ModeratorService = Depends(get_moderator_service),
    _: Moderator = Depends(get_admin_user),
):
    await service.deactivate(moderator_id)