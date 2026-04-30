from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.moderation_service import ModerationService
from app.schemas import ApproveResponse, DeclineResponse, DeclineRequest

router = APIRouter()
moderation_service = ModerationService()


@router.post("/api/v1/products/{id}/approve")
async def approve_product(
    id: int,
    db: Session = Depends(get_db)
):
    """Одобрить товар"""
    product = await moderation_service.approve_product(id)

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден в очереди")

    return ApproveResponse(
        message="Товар одобрен",
        product_id=product.id,
        status=product.status.value
    )


@router.post("/api/v1/products/{id}/decline")
async def decline_product(
    id: int,
    request: DeclineRequest,
    db: Session = Depends(get_db)
):
    """Заблокировать товар с причиной"""
    product = await moderation_service.decline_product(
        id,
        request.reason_code,
        request.comment
    )

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден в очереди")

    return DeclineResponse(
        message="Товар заблокирован",
        product_id=product.id,
        status=product.status.value
    )
