from __future__ import annotations

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
        self.url = f"{settings.B2B_API_BASE_URL.rstrip('/')}/moderation/events"
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
        await self._post(
            {
                "idempotency_key": str(idempotency_key),
                "product_id": str(product_id),
                "event_type": "BLOCKED",
                "moderator_id": str(moderator_id),
                "moderator_comment": moderator_comment,
                "blocking_reason_id": str(blocking_reason_id),
                "hard_block": hard_block,
                "field_reports": self._field_reports_payload(field_reports),
                "occurred_at": occurred_at.isoformat(),
            }
        )

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
            self.url,
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

    @staticmethod
    def _field_reports_payload(field_reports: list[Any] | None):
        if not field_reports:
            return None

        payload = []
        for report in field_reports:
            severity = report.severity
            if isinstance(severity, FieldSeverity):
                severity = severity.value

            payload.append(
                {
                    "field_path": report.field_path,
                    "message": report.message,
                    "severity": severity,
                }
            )
        return payload
