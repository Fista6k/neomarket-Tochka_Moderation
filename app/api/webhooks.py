from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.services.product_service import ProductService
from app.services.moderation_service import ModerationService
from app.models.product import Product, ProductStatus, SKU, Characteristic

router = APIRouter()
product_service = ProductService()
moderation_service = ModerationService()


class WebhookProductEvent(BaseModel):
    """Формат события от B2B о создании/изменении товара"""
    product_id: int
    event_type: str  # "PRODUCT_CREATED" или "PRODUCT_UPDATED"
    seller_id: int


@router.post("/api/v1/webhooks/product-event")
async def handle_product_webhook(
    event: WebhookProductEvent,
    db: Session = Depends(get_db)
):
    """
    Webhook от B2B: товар создан или изменён.
    
    B2B должен отправлять POST запрос с телом:
    {"product_id": int, "event_type": "PRODUCT_CREATED|PRODUCT_UPDATED", "seller_id": int}
    """
    # Запрашиваем актуальные данные товара из B2B
    b2b_data = await product_service.get_product_from_b2b(event.product_id)
    
    if not b2b_data:
        raise HTTPException(status_code=404, detail="Товар не найден в B2B")

    # Проверяем, есть ли уже товар в базе
    existing_product = product_service.get_product_by_external_id(event.product_id)

    if event.event_type == "PRODUCT_CREATED":
        # Создаём новый товар
        product = Product(
            external_id=b2b_data["id"],
            seller_id=b2b_data["seller_id"],
            title=b2b_data["title"],
            description=b2b_data.get("description"),
            category_id=b2b_data.get("category_id"),
            b2b_status=b2b_data["status"]
        )
        db.add(product)
        db.flush()  # получаем product.id

        # Создаём снимок "after" (после создания)
        product_service.create_product_snapshot(
            product.id,
            "after",
            b2b_data
        )

        # Сохраняем SKU
        for sku_data in b2b_data.get("skus", []):
            sku = SKU(
                product_id=product.id,
                seller_id=sku_data["seller_id"],
                name=sku_data["name"],
                price=sku_data.get("price"),
                status=sku_data.get("status", "CREATED")
            )
            db.add(sku)
            db.flush()

            # Сохраняем характеристики
            for char in sku_data.get("characteristics", []):
                char_obj = Characteristic(
                    sku_id=sku.id,
                    name=char["name"],
                    value=char["value"]
                )
                db.add(char_obj)

        # Добавляем в очередь модерации
        moderation_service.add_to_queue(product.id, is_new=True)

    elif event.event_type == "PRODUCT_UPDATED":
        if not existing_product:
            raise HTTPException(status_code=404, detail="Товар не найден в базе")

        # Сохраняем снимок "before" (старое состояние)
        old_data = {
            "title": existing_product.title,
            "description": existing_product.description,
            "category_id": existing_product.category_id,
            "b2b_status": existing_product.b2b_status
        }
        product_service.create_product_snapshot(
            existing_product.id,
            "before",
            old_data
        )

        # Обновляем товар новыми данными
        existing_product.title = b2b_data["title"]
        existing_product.description = b2b_data.get("description")
        existing_product.category_id = b2b_data.get("category_id")
        existing_product.b2b_status = b2b_data["status"]
        db.commit()
        db.refresh(existing_product)

        # Сохраняем снимок "after" (новое состояние)
        product_service.create_product_snapshot(
            existing_product.id,
            "after",
            b2b_data
        )

        # Добавляем в очередь модерации
        moderation_service.add_to_queue(existing_product.id, is_new=False)

    return {"status": "processed", "product_id": event.product_id}
