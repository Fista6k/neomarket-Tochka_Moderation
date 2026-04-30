from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.services.moderation_service import ModerationService
from app.schemas import ProductCardResponse, SKUResponse, SKUCharacteristic, ProductSnapshotResponse

router = APIRouter()
moderation_service = ModerationService()


@router.post("/api/v1/product-moderation/get-next")
async def get_next_card(db: Session = Depends(get_db)):
    """Получить следующую карточку из очереди"""
    item = moderation_service.get_next_from_queue()

    if not item:
        return None

    product = item.product
    snapshots = [
        ProductSnapshotResponse(
            snapshot_type=s.snapshot_type,
            data=json.loads(s.data),
            created_at=s.created_at
        )
        for s in product.snapshots
    ]

    skus = [
        SKUResponse(
            id=sku.id,
            name=sku.name,
            price=sku.price,
            status=sku.status,
            characteristics=[
                SKUCharacteristic(name=char.name, value=char.value)
                for char in sku.characteristics
            ]
        )
        for sku in product.skus
    ]

    return ProductCardResponse(
        product_id=product.id,
        external_id=product.external_id,
        seller_id=product.seller_id,
        title=product.title,
        description=product.description,
        category_id=product.category_id,
        status=product.status.value,
        b2b_status=product.b2b_status,
        snapshots=snapshots,
        skus=skus,
        is_new=bool(item.is_new)
    )
