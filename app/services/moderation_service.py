from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.models.product import ModerationQueueItem, BlockingReason
from app.services.product_service import ProductService

def get_moderation_service(
        product_service: ProductService = Depends()
) -> ModerationService:
    return ModerationService(product_service)

class ModerationService:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    async def get_next_from_queue(self, session: AsyncSession) -> Optional[ModerationQueueItem]:
        """Получает следующую карточку из очереди (асинхронно)"""
        result = await session.execute(
            select(ModerationQueueItem)
            .where(ModerationQueueItem.status == "pending",
                   ModerationQueueItem.assigned_at.is_(None))
            .order_by(ModerationQueueItem.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )

        item = result.scalar_one_or_none()

        if item:
            item.assigned_at = datetime.now(timezone.utc)
            await session.flush()

        return item

    async def approve_product(
        self,
        session: AsyncSession,
        product_id: int
    ) -> Optional[ModerationQueueItem]:
        """Одобрить товар и удалить из очереди"""
        result = await session.execute(
            select(ModerationQueueItem)
            .where(ModerationQueueItem.product_id == product_id,
                   ModerationQueueItem.status == "pending",
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        item.status = "approved"
        item.moderated_at = datetime.now(timezone.utc)

        await session.flush()

        await self.product_service.notify_b2b_product_approved(item.product_id)

        return item

    async def decline_product(
        self,
        session: AsyncSession,
        product_id: int,
        reason_code: str,
        comment: Optional[str] = None
    ) -> Optional[ModerationQueueItem]:
        """Заблокировать товар и удалить из очереди"""
        result = await session.execute(
            select(ModerationQueueItem)
            .where(ModerationQueueItem.product_id == product_id,
                   ModerationQueueItem.status == "pending",
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        item.status = "declined"
        item.moderation_reason = (
            f"{reason_code}: {comment}" if comment else reason_code
        )
        item.moderated_at = datetime.now(timezone.utc)

        await session.flush()

        await self.product_service.notify_b2b_product_blocked(
            item.product_id,
            item.moderation_reason
        )

        return item

    async def get_blocking_reasons(
            self,
            session: AsyncSession
    ) -> list[BlockingReason]:
        """Возвращает статический список причин блокировки"""
        
        result = await session.execute(
            select(BlockingReason)
            .where(BlockingReason.is_active == True)
            .order_by(BlockingReason.id)
        )

        return result.scalars().all()

    async def add_to_queue(
        self,
        session: AsyncSession,
        product_id: int,
        is_new: bool = True
    ) -> ModerationQueueItem:
        """Добавляет товар в очередь модерации"""
        existing = await session.execute(
            select(ModerationQueueItem)
            .where(ModerationQueueItem.product_id == product_id)
        )
        item = existing.scalar_one_or_none()

        if item:
            return item

        item = ModerationQueueItem(
            product_id=product_id,
            is_new=is_new,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

        session.add(item)
        await session.flush()

        return item
