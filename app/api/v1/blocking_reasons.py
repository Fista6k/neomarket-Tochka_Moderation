from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from fastapi.security import HTTPBearer

from app.database import get_db
from app.schemas.blocking_reason import (
    BlockingReasonCreateRequest,
    BlockingReasonUpdateRequest,
    BlockingReasonResponse,
)
from app.application.services.blocking_reason_service import BlockingReasonService
from app.infrastructure.repositories.blocking_reason_repository import BlockingReasonRepository
from app.api.v1.dependencies.moderator import get_admin_user
from app.models.moderator import Moderator
from app.api.v1.dependencies.key_dependency import verify_service_key

security = HTTPBearer()

router = APIRouter()


async def get_blocking_reason_service(db: AsyncSession = Depends(get_db)):
    repo = BlockingReasonRepository(db)
    return BlockingReasonService(repo)

@router.get("", response_model=list[BlockingReasonResponse], dependencies=[Depends(security)])
async def list_reasons(
    hard_block: bool | None = None,
    is_active: bool | None = Query(default=None),
    service: BlockingReasonService = Depends(get_blocking_reason_service),
):
    return await service.list(
        hard_block=hard_block,
        is_active=is_active,
    )


@router.post("", response_model=BlockingReasonResponse, status_code=201, dependencies=[Depends(security)])
async def create_reason(
    data: BlockingReasonCreateRequest,
    service: BlockingReasonService = Depends(get_blocking_reason_service),
    _: Moderator = Depends(get_admin_user),
):
    return await service.create(data)

@router.get("/list", response_model=list[BlockingReasonResponse])
async def list_reasons(
    hard_block: bool | None = None,
    is_active: bool | None = Query(default=None),
    service: BlockingReasonService = Depends(get_blocking_reason_service),
    service_key: str = Depends(verify_service_key)
):
    return await service.list(
        hard_block=hard_block,
        is_active=is_active,
    )

@router.patch("/{reason_id}", response_model=BlockingReasonResponse, dependencies=[Depends(security)])
async def update_reason(
    reason_id: UUID,
    data: BlockingReasonUpdateRequest,
    service: BlockingReasonService = Depends(get_blocking_reason_service),
    _: Moderator = Depends(get_admin_user),
):
    return await service.update(reason_id, data)


@router.delete("/{reason_id}", status_code=204, dependencies=[Depends(security)])
async def delete_reason(
    reason_id: UUID,
    service: BlockingReasonService = Depends(get_blocking_reason_service),
    _: Moderator = Depends(get_admin_user),
):
    await service.deactivate(reason_id)