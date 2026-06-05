from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.blocking_reason import BlockingReason
from app.models.enums import TicketAction, TicketStatus
from app.models.field_report import FieldReport
from app.models.moderator import Moderator
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory

from typing import Optional


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
                Ticket.status.in_([TicketStatus.PENDING, TicketStatus.IN_REVIEW, TicketStatus.HARD_BLOCKED, TicketStatus.BLOCKED]),
            )
            .values(
                status=TicketStatus.DELETED,
                assigned_moderator_id=None,
                claimed_at=None,
                is_deleted=True,
                claim_expires_at=None,
                decision_at=datetime.now(timezone.utc),
            )
        )

    async def update(self, ticket: Ticket) -> Ticket:
        """Сохраняет изменения в существующем тикете."""
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def get_last_by_product(self, product_id: UUID):
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.product_id == product_id)
            .order_by(Ticket.created_at)
            .limit(1)
            .options(
                selectinload(Ticket.field_reports),
                selectinload(Ticket.history),
                selectinload(Ticket.moderator),
                selectinload(Ticket.blocking_reasons),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_ticket_by_product(self, product_id: UUID) -> Ticket | None:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.product_id == product_id)
            .where(Ticket.status.in_([TicketStatus.PENDING, TicketStatus.IN_REVIEW]))
            .limit(1)
        )
        return result.scalar_one_or_none()

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
    
    async def get_active_in_review_by_moderator(self, moderator_id: UUID) -> Ticket | None:
        """Возвращает активный (неистекший) IN_REVIEW тикет модератора, если есть."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Ticket)
            .where(
                Ticket.status == TicketStatus.IN_REVIEW,
                Ticket.assigned_moderator_id == moderator_id,
                Ticket.claim_expires_at > now,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def claim_next(
        self,
        moderator_id: UUID,
        queue_priority: int | None = None,
        category_ids: list[UUID] | None = None,
        b2b_client: Optional["B2BModerationEventClient"] = None
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
        
        product_updated_at = None
        if b2b_client:
            try:
                product_data = await b2b_client.get_product_public(ticket.product_id)
                product_updated_at = product_data.get("updated_at")
                if product_updated_at:
                    product_updated_at = datetime.fromisoformat(product_updated_at.replace("Z", "+00:00"))
            except Exception as e:
                logger.error(f"Failed to fetch product {ticket.product_id} from B2B: {e}")
                return None

        ticket.status = TicketStatus.IN_REVIEW
        ticket.assigned_moderator_id = moderator_id
        ticket.claimed_at = now
        ticket.claim_expires_at = now + timedelta(minutes=CLAIM_TTL_MINUTES)
        ticket.product_updated_at = product_updated_at
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

    async def stats_overview(self, period_start: datetime) -> dict:
        status_result = await self.db.execute(
            select(Ticket.status, func.count()).group_by(Ticket.status)
        )
        status_counts = {
            status.value if hasattr(status, "value") else status: count
            for status, count in status_result.all()
        }

        decision_result = await self.db.execute(
            select(Ticket.status, func.count())
            .where(
                Ticket.status.in_(
                    [
                        TicketStatus.APPROVED,
                        TicketStatus.BLOCKED,
                        TicketStatus.HARD_BLOCKED,
                    ]
                ),
                Ticket.decision_at >= period_start,
            )
            .group_by(Ticket.status)
        )
        decision_counts = {
            status.value if hasattr(status, "value") else status: count
            for status, count in decision_result.all()
        }

        priority_result = await self.db.execute(
            select(Ticket.queue_priority, func.count())
            .where(Ticket.status == TicketStatus.PENDING)
            .group_by(Ticket.queue_priority)
        )
        pending_by_priority = {str(priority): count for priority, count in priority_result.all()}

        avg_result = await self.db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.decision_at - Ticket.claimed_at)
                )
            ).where(
                Ticket.decision_at >= period_start,
                Ticket.claimed_at.is_not(None),
                Ticket.decision_at.is_not(None),
            )
        )
        avg_review_time = avg_result.scalar_one_or_none()

        return {
            "pending_count": status_counts.get(TicketStatus.PENDING.value, 0),
            "in_review_count": status_counts.get(TicketStatus.IN_REVIEW.value, 0),
            "approved_count": decision_counts.get(TicketStatus.APPROVED.value, 0),
            "blocked_count": decision_counts.get(TicketStatus.BLOCKED.value, 0),
            "hard_blocked_count": decision_counts.get(TicketStatus.HARD_BLOCKED.value, 0),
            "avg_review_time_seconds": int(avg_review_time) if avg_review_time else None,
            "pending_by_priority": {
                str(priority): pending_by_priority.get(str(priority), 0)
                for priority in range(1, 5)
            },
        }

    async def moderator_stats(self, period_start: datetime) -> list[dict]:
        decisions = [TicketAction.APPROVED, TicketAction.BLOCKED, TicketAction.HARD_BLOCKED]
        result = await self.db.execute(
            select(
                Moderator.id.label("moderator_id"),
                func.concat(
                    Moderator.first_name,
                    case((Moderator.last_name.is_not(None), " "), else_=""),
                    func.coalesce(Moderator.last_name, ""),
                ).label("moderator_name"),
                func.count(TicketHistory.id).filter(TicketHistory.action.in_(decisions)).label("decisions_count"),
                func.count(TicketHistory.id).filter(TicketHistory.action == TicketAction.APPROVED).label("approved_count"),
                func.count(TicketHistory.id).filter(TicketHistory.action == TicketAction.BLOCKED).label("blocked_count"),
                func.count(TicketHistory.id).filter(TicketHistory.action == TicketAction.HARD_BLOCKED).label("hard_blocked_count"),
                func.count(TicketHistory.id).filter(TicketHistory.action == TicketAction.RELEASED).label("released_count"),
                func.avg(
                    func.extract("epoch", Ticket.decision_at - Ticket.claimed_at)
                )
                .filter(
                    TicketHistory.action.in_(decisions),
                    Ticket.claimed_at.is_not(None),
                    Ticket.decision_at.is_not(None),
                )
                .label("avg_review_time_seconds"),
            )
            .select_from(Moderator)
            .join(TicketHistory, TicketHistory.moderator_id == Moderator.id)
            .outerjoin(Ticket, Ticket.id == TicketHistory.ticket_id)
            .where(TicketHistory.at >= period_start)
            .group_by(Moderator.id, Moderator.first_name, Moderator.last_name)
            .order_by(func.count(TicketHistory.id).filter(TicketHistory.action.in_(decisions)).desc())
        )

        stats = []
        for row in result.mappings().all():
            item = dict(row)
            avg_review_time = item["avg_review_time_seconds"]
            item["avg_review_time_seconds"] = int(avg_review_time) if avg_review_time else None
            stats.append(item)
        return stats
