from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.schemas.b2b import (
    IncomingB2BEvent,
    EventProductCreated,
    EventProductEdited,
    EventProductDeleted,
)
from app.models.ticket import Ticket
from app.models.enums import TicketKind, TicketStatus
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.infrastructure.repositories.idempotency_repository import IdempotencyRepository
from app.core.config import settings



IDEMPOTENCY_TTL_HOURS = settings.IDEMPOTENCY_TTL_HOURS


class B2BService:

    def __init__(self, ticketRepo: TicketRepository, idempotencyRepo: IdempotencyRepository):
        self.ticketRepo = ticketRepo
        self.idempotencyRepo = idempotencyRepo

    async def handle_event(
        self,
        event: IncomingB2BEvent,
    ):
        await self.idempotencyRepo.cleanup_expired()

        created = await self.idempotencyRepo.create_if_not_exists(
            event.idempotency_key,
            datetime.now(timezone.utc) + timedelta(hours=IDEMPOTENCY_TTL_HOURS)
        )

        if not created:
            raise HTTPException(status_code=409, detail="Duplicate event")

        if event.event_type == "PRODUCT_CREATED":
            await self._handle_created(event.payload)

        elif event.event_type == "PRODUCT_EDITED":
            await self._handle_edited(event.payload)

        elif event.event_type == "PRODUCT_DELETED":
            await self._handle_deleted(event.payload)

        else:
            raise HTTPException(status_code=400, detail="Unknown event type")


    async def _handle_created(
        self,
        payload: EventProductCreated,
    ):
        ticket = Ticket(
            product_id=payload.product_id,
            seller_id=payload.seller_id,
            category_id=payload.category_id,
            kind=TicketKind.CREATE,
            status=TicketStatus.PENDING,
            queue_priority=payload.queue_priority,
            json_before=None,
            json_after=payload.json_after,
        )

        await self.ticketRepo.create(ticket)

    async def _handle_edited(
        self,
        payload: EventProductEdited,
    ):
        ticket = Ticket(
            product_id=payload.product_id,
            seller_id=payload.seller_id,
            category_id=payload.category_id,
            kind=TicketKind.EDIT,
            status=TicketStatus.PENDING,
            queue_priority=payload.queue_priority,
            json_before=payload.json_before,
            json_after=payload.json_after,
        )

        await self.ticketRepo.create(ticket)

    async def _handle_deleted(
        self,
        payload: EventProductDeleted,
    ):
        await self.ticketRepo.close_by_product(
            payload.product_id,
        )
