from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.moderation_service import ModerationService, get_moderation_service
from app.schemas import ApproveResponse, DeclineResponse, DeclineRequest

router = APIRouter()

@router.post("/api/v1/products/{product_id}/approve",
             response_model=ApproveResponse)
async def approve_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Одобрить товар"""
    item = await moderation_service.approve_product(db, product_id)

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден в очереди")

    return ApproveResponse(
        message="Товар одобрен",
        product_id=item.product_id
    )


@router.post("/api/v1/products/{product_id}/decline",
             response_model=DeclineResponse)
async def decline_product(
    product_id: int,
    request: DeclineRequest,
    db: AsyncSession = Depends(get_db),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Заблокировать товар с причиной"""
    item = await moderation_service.decline_product(
        db,
        product_id,
        request.reason_code,
        request.comment
    )

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден в очереди")

    return DeclineResponse(
        message="Товар заблокирован",
        product_id=item.product_id
    )
