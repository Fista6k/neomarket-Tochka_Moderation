from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json
from enum import Enum

from app.database import get_db
from app.services.product_service import ProductService, get_product_service
from app.services.moderation_service import ModerationService, get_moderation_service

router = APIRouter()

class ProductEventType(str, Enum):
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"

class WebhookProductEvent(BaseModel):
    """Формат события от B2B о создании/изменении товара"""
    product_id: int
    event_type: ProductEventType
    seller_id: int


@router.post(
        "/api/v1/webhooks/product-event",
        response_model=dict,
        status_code=200)
async def handle_product_webhook(
    event: WebhookProductEvent,
    db: AsyncSession = Depends(get_db),
    moderation_service: ModerationService = Depends(get_moderation_service),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Webhook от B2B: товар создан или изменён.
    
    B2B должен отправлять POST запрос с телом:
    {"product_id": int, "event_type": "PRODUCT_CREATED|PRODUCT_UPDATED", "seller_id": int}
    """

    b2b_data = await product_service.get_product_from_b2b(event.product_id)

    if event.event_type == ProductEventType.PRODUCT_CREATED:

        await product_service.create_product_snapshot(
            db,
            event.product_id,
            "after",
            b2b_data
        )

        await moderation_service.add_to_queue(
            db,
            event.product_id,
            is_new=True
        )

    elif event.event_type == "PRODUCT_UPDATED":
        last_snapshot = await product_service.get_latest_snapshot(
            db,
            event.product_id
        )

        if last_snapshot:
            await product_service.create_product_snapshot(
                db,
                event.product_id,
                "before",
                json.loads(last_snapshot.data)
            )

        await product_service.create_product_snapshot(
            db,
            event.product_id,
            "after",
            b2b_data
        )

        await moderation_service.add_to_queue(
            db,
            event.product_id,
            is_new=False
        )

    return {"status": "processed", "product_id": event.product_id}
