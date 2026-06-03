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
            return
        
        payload = event.payload

        if isinstance(payload, EventProductCreated):
            await self._handle_created(payload)

        elif isinstance(payload, EventProductEdited):
            await self._handle_edited(payload)

        elif isinstance(payload, EventProductDeleted):
            await self._handle_deleted(payload)

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
        existing_ticket = await self.ticketRepo.get_last_by_product(payload.product_id)
        if existing_ticket and existing_ticket.status == TicketStatus.HARD_BLOCKED:
            return
        
        if existing_ticket and existing_ticket.status == TicketStatus.IN_REVIEW:
            existing_ticket.seller_id = payload.seller_id
            existing_ticket.category_id = payload.category_id
            existing_ticket.queue_priority = payload.queue_priority
            existing_ticket.json_before = payload.json_before
            existing_ticket.json_after = payload.json_after
            await self.ticketRepo.update(existing_ticket)
            return

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
