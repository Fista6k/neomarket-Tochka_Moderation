import httpx
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import settings
from app.models.product import ProductSnapshot

async def get_http_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(
        timeout=settings.B2B_TIMEOUT
    ) as client:
        yield client

class ProductService:
    def __init__(self, client: httpx.AsyncClient):
        self.b2b_base_url = settings.B2B_API_BASE_URL
        self.timeout = settings.B2B_TIMEOUT
        self.b2b_token = settings.B2B_API_TOKEN
        self.client = client

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.b2b_token:
            headers["Authorization"] = f"Bearer {self.b2b_token}"
        return headers

    async def get_product_from_b2b(self, product_id: int) -> dict:
        """Запрашивает данные товара из B2B"""

        response = await self.client.get(
            f"{self.b2b_base_url}/product/{product_id}",
            headers = self._get_headers()
        )

        response = raise_for_status()
        return response.json()

    async def create_product_snapshot(
        self,
        session: AsyncSession,
        product_id: int,
        snapshot_type: str,
        data: dict
    ) -> ProductSnapshot:
        """Создаёт снимок товара (асинхронно)"""

        snapshot = ProductSnapshot(
            product_id=product_id,
            snapshot_type=snapshot_type,
            data=data
        )

        session.add(snapshot)
        await session.flush()

        return snapshot
    
    async def get_latest_snapshot(
            self,
            session: AsyncSession,
            product_id: int,
    ) -> Optional[ProductSnapshot]:
        """Получить последний snapshot товара"""

        result = await session.execute(
            select(ProductSnapshot)
            .where(ProductSnapshot.product_id == product_id)
            .order_by(ProductSnapshot.created_at.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def notify_b2b_product_approved(self, product_id: int) -> None:
        """Отправляет в B2B событие об одобрении товара"""

        response = await self.client.post(
            f"{self.b2b_base_url}/event/product-approved",
            headers=self._get_headers(),
            json = {
                "product_id": product_id,
                "event": "PRODUCT_APPROVED"
            },
        )

        response.raise_for_status()

    async def notify_b2b_product_blocked(
            self,
            product_id: int,
            reason: str) -> None:
        """Отправляет в B2B событие о блокировке товара"""
        
        response = await self.client.post(
            f"{self.b2b_base_url}/event/product-blocked",
            headers=self._get_headers(),
            json={
                "product_id":product_id,
                "event":"PRODUCT_BLOCKED",
                reason: reason
            },
        )

        response.raise_for_status()

def get_product_service() -> ProductService:
    client = httpx.AsyncClient(timeout=settings.B2B_TIMEOUT)
    return ProductService(client)
