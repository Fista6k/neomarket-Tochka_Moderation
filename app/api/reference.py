from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.moderation_service import ModerationService
from app.schemas import BlockingReasonResponse

router = APIRouter()
moderation_service = ModerationService()


@router.get("/api/v1/product-blocking-reasons")
async def get_blocking_reasons(db: Session = Depends(get_db)):
    """Получить список причин блокировки"""
    reasons = moderation_service.get_blocking_reasons()

    return [
        BlockingReasonResponse(
            id=r.id,
            code=r.code,
            description=r.description
        )
        for r in reasons
    ]
