from typing import Optional
from datetime import datetime

from app.models.product import (
    Product, ProductSnapshot, ProductStatus,
    ModerationQueueItem, BlockingReason
)
from app.database import SessionLocal
from app.services.product_service import ProductService


class ModerationService:
    def __init__(self):
        self.product_service = ProductService()

    def get_next_from_queue(self) -> Optional[ModerationQueueItem]:
        """Получает следующую карточку из очереди"""
        db = SessionLocal()
        try:
            item = db.query(ModerationQueueItem).filter(
                ModerationQueueItem.assigned_at.is_(None)
            ).order_by(ModerationQueueItem.id).first()

            if item:
                item.assigned_at = datetime.utcnow()
                db.commit()
                db.refresh(item)
            return item
        finally:
            db.close()

    async def approve_product(self, product_id: int) -> Optional[Product]:
        """Одобрить товар и отправить уведомление в B2B"""
        db = SessionLocal()
        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            if not product:
                return None

            product.status = ProductStatus.MODERATED
            db.commit()
            db.refresh(product)

            queue_item = db.query(ModerationQueueItem).filter(
                ModerationQueueItem.product_id == product_id
            ).first()
            if queue_item:
                db.delete(queue_item)
                db.commit()

            # Отправляем уведомление в B2B (фоновая задача)
            await self.product_service.notify_b2b_product_approved(product.external_id)

            return product
        finally:
            db.close()

    async def decline_product(
        self,
        product_id: int,
        reason_code: str,
        comment: Optional[str] = None
    ) -> Optional[Product]:
        """Заблокировать товар с причиной и отправить уведомление в B2B"""
        db = SessionLocal()
        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            if not product:
                return None

            product.status = ProductStatus.BLOCKED
            db.commit()
            db.refresh(product)

            queue_item = db.query(ModerationQueueItem).filter(
                ModerationQueueItem.product_id == product_id
            ).first()
            if queue_item:
                db.delete(queue_item)
                db.commit()

            # Отправляем уведомление в B2B (фоновая задача)
            reason = f"{reason_code}: {comment}" if comment else reason_code
            await self.product_service.notify_b2b_product_blocked(
                product.external_id,
                reason
            )

            return product
        finally:
            db.close()

    def get_blocking_reasons(self) -> list[BlockingReason]:
        """Получает список причин блокировки"""
        db = SessionLocal()
        try:
            return db.query(BlockingReason).all()
        finally:
            db.close()

    def add_to_queue(
        self,
        product_id: int,
        is_new: bool = True
    ) -> ModerationQueueItem:
        """Добавляет товар в очередь модерации"""
        db = SessionLocal()
        try:
            existing = db.query(ModerationQueueItem).filter(
                ModerationQueueItem.product_id == product_id
            ).first()

            if existing:
                return existing

            item = ModerationQueueItem(
                product_id=product_id,
                is_new=1 if is_new else 0
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()
