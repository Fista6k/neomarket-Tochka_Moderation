from __future__ import annotations

import httpx
import asyncio
import json
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import HTTPException

from app.core.config import settings
from app.models.enums import FieldSeverity


class B2BModerationEventClient:
    def __init__(self):
        self.url = settings.B2B_API_BASE_URL.rstrip('/')
        self.timeout = settings.B2B_TIMEOUT
        self.service_key = settings.B2B_SERVICE_KEY

    async def send_moderated(
        self,
        *,
        idempotency_key: UUID,
        product_id: UUID,
        moderator_id: UUID,
        moderator_comment: str | None,
        occurred_at: datetime,
    ):
        await self._post(
            {
                "idempotency_key": str(idempotency_key),
                "product_id": str(product_id),
                "event_type": "MODERATED",
                "moderator_id": str(moderator_id),
                "moderator_comment": moderator_comment,
                "blocking_reason_id": None,
                "hard_block": False,
                "field_reports": None,
                "occurred_at": occurred_at.isoformat(),
            }
        )

    async def send_blocked(
        self,
        *,
        idempotency_key: UUID,
        product_id: UUID,
        moderator_id: UUID,
        moderator_comment: str | None,
        blocking_reason_id: UUID,
        hard_block: bool,
        field_reports: list[Any] | None,
        occurred_at: datetime,
    ):
        if field_reports:
            skus = await self.get_product_skus(product_id)
            print(skus)
            if skus is None:
                raise HTTPException(status_code=400, detail="no skus")
            sku_ids = {str(sku["id"]) for sku in skus}
            for report in field_reports:
                if report.sku_id and str(report.sku_id) not in sku_ids:
                    raise HTTPException(400, f"SKU {report.sku_id} not found in product")

        await self._post(
            {
                "idempotency_key": str(idempotency_key),
                "product_id": str(product_id),
                "event_type": "BLOCKED",
                "moderator_id": str(moderator_id),
                "moderator_comment": moderator_comment,
                "blocking_reason_id": str(blocking_reason_id),
                "hard_block": hard_block,
                "field_reports": self._field_reports_payload(field_reports, product_id),
                "occurred_at": occurred_at.isoformat(),
            }
        )

    async def get_product_skus(self, product_id: UUID) -> list[dict]:
        """Возвращает список SKU товара. Если нет SKU → пустой список."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/products/{product_id}/skus",
                headers={"X-Service-Key": self.service_key}
            )
            if response.status_code == 404:
                raise HTTPException(404, f"Product {product_id} not found in B2B")
            response.raise_for_status()
            return response.json()  # список SKU

    async def get_product_public(self, product_id: UUID) -> dict:
        """Возвращает публичные данные товара (включая updated_at)."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.url}/products/{product_id}",
                headers={"X-Service-Key": self.service_key}
            )
            if response.status_code == 404:
                raise HTTPException(404, f"Product {product_id} not found in B2B")
            response.raise_for_status()
            return response.json()

    async def _post(self, payload: dict[str, Any]):
        try:
            await asyncio.to_thread(self._post_sync, payload)
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise HTTPException(
                    status_code=502,
                    detail=f"B2B rejected moderation event with {exc.code}",
                ) from exc
            raise HTTPException(
                status_code=503,
                detail=f"B2B moderation events endpoint failed with {exc.code}",
            ) from exc
        except URLError as exc:
            raise HTTPException(
                status_code=503,
                detail="B2B moderation events endpoint is unavailable",
            ) from exc

    def _post_sync(self, payload: dict[str, Any]):
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.url}/moderation/events",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Service-Key": self.service_key,
            },
        )

        with urlopen(request, timeout=self.timeout) as response:
            if response.status != 204:
                raise HTTPException(
                    status_code=503,
                    detail=f"B2B moderation events endpoint returned {response.status}",
                )

    def _field_reports_payload(self, field_reports: list[Any] | None, product_id: UUID):
        if not field_reports:
            return None

        payload = []
        for report in field_reports:
            payload.append(
                {
                    "field_name": report.field_name,
                    "sku_id": str(report.sku_id),
                    "comment": report.comment,
                }
            )
        return payload
