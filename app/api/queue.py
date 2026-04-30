from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_204_NO_CONTENT
import json

from app.database import get_db
from app.services.moderation_service import ModerationService, get_moderation_service
from app.schemas import ProductCardResponse, ProductSnapshotResponse

router = APIRouter()


@router.get(
        "/api/v1/product-moderation/get-next",
        response_model=ProductCardResponse,
        responses={
            204: {"description": "Очередь пуста"}
        }
    )
async def get_next_card(
    db: AsyncSession = Depends(get_db),
    moderation_service: ModerationService = Depends(get_moderation_service)):
    """Получить следующую карточку из очереди"""

    item = await moderation_service.get_next_from_queue(db)

    if not item:
        return Response(status_code=HTTP_204_NO_CONTENT)

    snapshots = [
        ProductSnapshotResponse(
            snapshot_type=s.snapshot_type,
            data=s.data,
            created_at=s.created_at
        )
        for s in item.snapshots
    ]

    latest_snapshot = snapshots[0].data if snapshots else {}

    return ProductCardResponse(
        product_id=item.product_id,
        title=latest_snapshot.get("title", ""),
        description=latest_snapshot.get("description"),
        category_id=latest_snapshot.get("category_id"),
        b2b_status=latest_snapshot.get("status"),
        snapshots=snapshots,
        skus=latest_snapshot.get("skus", []),
        is_new=item.is_new
    )
