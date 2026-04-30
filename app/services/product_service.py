import httpx
from typing import Optional
import json

from app.config import settings
from app.models.product import Product, ProductSnapshot, ProductStatus, SKU, Characteristic
from app.database import SessionLocal


class ProductService:
    def __init__(self):
        self.b2b_base_url = settings.B2B_API_BASE_URL
        self.timeout = settings.B2B_TIMEOUT
        self.b2b_token = settings.B2B_API_TOKEN

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.b2b_token:
            headers["Authorization"] = f"Bearer {self.b2b_token}"
        return headers

    async def get_product_from_b2b(self, product_id: int) -> Optional[dict]:
        """Запрашивает данные товара из B2B"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # B2B требует авторизацию, поэтому передаём заголовок
                response = await client.get(
                    f"{self.b2b_base_url}/products/{product_id}"
                    f"{self.b2b_base_url}/products/{product_id}",
                    headers=self._get_headers()
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except httpx.RequestError:
                return None

    def create_product_snapshot(
        self,
        product_id: int,
        snapshot_type: str,
        data: dict
    ) -> ProductSnapshot:
        """Создаёт снимок товара"""
        db = SessionLocal()
        try:
            snapshot = ProductSnapshot(
                product_id=product_id,
                snapshot_type=snapshot_type,
                data=json.dumps(data)
            )
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            return snapshot
        finally:
            db.close()

    def get_product_by_external_id(self, external_id: int) -> Optional[Product]:
        """Получает товар по внешнему ID"""
        db = SessionLocal()
        try:
            return db.query(Product).filter(
                Product.external_id == external_id
            ).first()
        finally:
            db.close()

    def update_product_status(
        self,
        product_id: int,
        status: ProductStatus
    ) -> Optional[Product]:
        """Обновляет статус товара"""
        db = SessionLocal()
        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()
            if product:
                product.status = status
                db.commit()
                db.refresh(product)
            return product
        finally:
            db.close()

    async def notify_b2b_product_approved(self, product_id: int) -> bool:
        """Отправляет в B2B событие об одобрении товара"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # B2B ожидает событие в формате: {"product_id": int, "event": "PRODUCT_APPROVED"}
                response = await client.post(
                    f"{self.b2b_base_url}/events/product-approved",
                    json={"product_id": product_id, "event": "PRODUCT_APPROVED"}
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False

    async def notify_b2b_product_blocked(self, product_id: int, reason: str) -> bool:
        """Отправляет в B2B событие о блокировке товара"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.b2b_base_url}/events/product-blocked",
                    json={"product_id": product_id, "event": "PRODUCT_BLOCKED", "reason": reason}
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False
