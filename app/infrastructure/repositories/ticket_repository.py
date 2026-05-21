from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.blocking_reason import BlockingReason
from app.models.enums import TicketStatus
from app.models.field_report import FieldReport
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory


CLAIM_TTL_MINUTES = 30


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def close_by_product(self, product_id: UUID):
        await self.db.execute(
            update(Ticket)
            .where(
                Ticket.product_id == product_id,
                Ticket.status.in_([TicketStatus.PENDING, TicketStatus.IN_REVIEW]),
            )
            .values(
                status=TicketStatus.BLOCKED,
                assigned_moderator_id=None,
                claimed_at=None,
                claim_expires_at=None,
                decision_at=datetime.now(timezone.utc),
            )
        )

    async def get_by_id(self, ticket_id: UUID) -> Ticket | None:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                selectinload(Ticket.field_reports),
                selectinload(Ticket.history),
                selectinload(Ticket.moderator),
                selectinload(Ticket.blocking_reasons),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int,
        offset: int,
        status: TicketStatus | None = None,
        moderator_id: UUID | None = None,
        product_id: UUID | None = None,
        seller_id: UUID | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ):
        query = select(Ticket)

        if status is not None:
            query = query.where(Ticket.status == status)
        if moderator_id is not None:
            query = query.where(Ticket.assigned_moderator_id == moderator_id)
        if product_id is not None:
            query = query.where(Ticket.product_id == product_id)
        if seller_id is not None:
            query = query.where(Ticket.seller_id == seller_id)
        if created_from is not None:
            query = query.where(Ticket.created_at >= created_from)
        if created_to is not None:
            query = query.where(Ticket.created_at <= created_to)

        total_count = await self._count(query)
        result = await self.db.execute(
            query.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total_count

    async def list_queue(
        self,
        limit: int,
        offset: int,
        queue_priority: int | None = None,
        category_id: UUID | None = None,
        seller_id: UUID | None = None,
    ):
        query = select(Ticket).where(Ticket.status == TicketStatus.PENDING)

        if queue_priority is not None:
            query = query.where(Ticket.queue_priority == queue_priority)
        if category_id is not None:
            query = query.where(Ticket.category_id == category_id)
        if seller_id is not None:
            query = query.where(Ticket.seller_id == seller_id)

        total_count = await self._count(query)
        result = await self.db.execute(
            query.order_by(Ticket.queue_priority.asc(), Ticket.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total_count

    async def claim_next(
        self,
        moderator_id: UUID,
        queue_priority: int | None = None,
        category_ids: list[UUID] | None = None,
    ) -> Ticket | None:
        await self.auto_return_expired()

        now = datetime.now(timezone.utc)
        query = select(Ticket).where(Ticket.status == TicketStatus.PENDING)

        if queue_priority is not None:
            query = query.where(Ticket.queue_priority == queue_priority)
        if category_ids:
            query = query.where(Ticket.category_id.in_(category_ids))

        result = await self.db.execute(
            query.order_by(Ticket.queue_priority.asc(), Ticket.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        ticket = result.scalar_one_or_none()

        if ticket is None:
            return None

        ticket.status = TicketStatus.IN_REVIEW
        ticket.assigned_moderator_id = moderator_id
        ticket.claimed_at = now
        ticket.claim_expires_at = now + timedelta(minutes=CLAIM_TTL_MINUTES)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def release(self, ticket: Ticket) -> Ticket:
        ticket.status = TicketStatus.PENDING
        ticket.assigned_moderator_id = None
        ticket.claimed_at = None
        ticket.claim_expires_at = None
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def set_approved(self, ticket: Ticket) -> Ticket:
        ticket.status = TicketStatus.APPROVED
        ticket.assigned_moderator_id = None
        ticket.claim_expires_at = None
        ticket.decision_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def set_blocked(self, ticket: Ticket, hard: bool) -> Ticket:
        ticket.status = TicketStatus.HARD_BLOCKED if hard else TicketStatus.BLOCKED
        ticket.assigned_moderator_id = None
        ticket.claim_expires_at = None
        ticket.decision_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def set_blocking_reasons(
        self,
        ticket: Ticket,
        reasons: list[BlockingReason],
    ) -> Ticket:
        ticket.blocking_reasons = reasons
        await self.db.flush()
        return ticket

    async def add_history(self, history: TicketHistory) -> TicketHistory:
        self.db.add(history)
        await self.db.flush()
        return history

    async def add_field_reports(
        self,
        reports: list[FieldReport],
    ) -> list[FieldReport]:
        self.db.add_all(reports)
        await self.db.flush()
        return reports

    async def get_blocking_reasons(
        self,
        reason_ids: list[UUID],
    ) -> list[BlockingReason]:
        result = await self.db.execute(
            select(BlockingReason).where(BlockingReason.id.in_(reason_ids))
        )
        return result.scalars().all()

    async def auto_return_expired(self):
        await self.db.execute(
            update(Ticket)
            .where(
                Ticket.status == TicketStatus.IN_REVIEW,
                Ticket.claim_expires_at < datetime.now(timezone.utc),
            )
            .values(
                status=TicketStatus.PENDING,
                assigned_moderator_id=None,
                claimed_at=None,
                claim_expires_at=None,
            )
        )

    async def _count(self, query) -> int:
        result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        return result.scalar_one()
