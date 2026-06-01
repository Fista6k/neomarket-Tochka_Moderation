from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.application.services.b2b_moderation_event_client import B2BModerationEventClient
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.models.enums import TicketAction, TicketStatus, UserRole
from app.models.field_report import FieldReport
from app.models.moderator import Moderator
from app.models.ticket_history import TicketHistory


class TicketService:

    def __init__(
        self,
        repo: TicketRepository,
        b2b_events: B2BModerationEventClient | None = None,
    ):
        self.repo = repo
        self.b2b_events = b2b_events or B2BModerationEventClient()

    async def list(self, **filters):
        await self.repo.auto_return_expired()
        return await self.repo.list(**filters)

    async def list_queue(self, **filters):
        await self.repo.auto_return_expired()
        return await self.repo.list_queue(**filters)

    async def claim_next(
        self,
        moderator: Moderator,
        queue_priority: int | None = None,
        category_ids: list[UUID] | None = None,
    ):
        ticket = await self.repo.claim_next(
            moderator_id=moderator.id,
            queue_priority=queue_priority,
            category_ids=category_ids,
        )

        if ticket is None:
            return None

        await self.repo.add_history(
            TicketHistory(
                ticket_id=ticket.id,
                action=TicketAction.CLAIMED,
                moderator_id=moderator.id,
                at=datetime.now(timezone.utc),
            ),
        )
        await self.repo.db.commit()
        return await self.repo.get_by_id(ticket.id)

    async def get_detail(self, ticket_id: UUID):
        ticket = await self.repo.get_by_id(ticket_id)

        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")

        return ticket

    async def release(self, ticket_id: UUID, moderator: Moderator):
        ticket = await self._get_owned_ticket(
            ticket_id=ticket_id,
            moderator=moderator,
            allow_admin=True,
        )

        ticket = await self.repo.release(ticket)
        await self.repo.add_history(
            TicketHistory(
                ticket_id=ticket.id,
                action=TicketAction.RELEASED,
                moderator_id=moderator.id,
                at=datetime.now(timezone.utc),
            ),
        )
        await self.repo.db.commit()
        return await self.repo.get_by_id(ticket.id)

    async def approve(
        self,
        ticket_id: UUID,
        moderator: Moderator,
        comment: str | None,
    ):
        ticket = await self._get_owned_ticket(
            ticket_id=ticket_id,
            moderator=moderator,
            allow_admin=False,
        )

        skus = await self.b2b_events.get_product_skus(ticket.product_id)

        if not skus:
            raise HTTPException(status_code=409, detail="Product can not be approved without SKU")
        
        current_product = await self.b2b_events.get_product_public(ticket.product_id)
        current_updated_at = datetime.fromisoformat(current_product["updated_at"].replace("Z", "+00:00"))

        if ticket.product_updated_at and current_updated_at > ticket.product_updated_at:
            raise HTTPException(status_code=409, detail="Product was edited during review")

        ticket = await self.repo.set_approved(ticket)
        await self.repo.add_history(
            TicketHistory(
                ticket_id=ticket.id,
                action=TicketAction.APPROVED,
                moderator_id=moderator.id,
                comment=comment,
                at=datetime.now(timezone.utc),
            ),
        )
        await self.b2b_events.send_moderated(
            idempotency_key=ticket.id,
            product_id=ticket.product_id,
            moderator_id=moderator.id,
            moderator_comment=comment,
            occurred_at=ticket.decision_at,
        )
        await self.repo.db.commit()
        return await self.repo.get_by_id(ticket.id)

    async def block(
        self,
        ticket_id: UUID,
        moderator: Moderator,
        blocking_reason_ids: list[UUID],
        field_reports: list | None,
        comment: str | None,
    ):
        ticket = await self._get_owned_ticket(
            ticket_id=ticket_id,
            moderator=moderator,
            allow_admin=False,
        )

        reasons = await self.repo.get_blocking_reasons(blocking_reason_ids)
        found_reason_ids = {reason.id for reason in reasons}
        if len(found_reason_ids) != len(set(blocking_reason_ids)):
            raise HTTPException(status_code=400, detail="Invalid blocking reason")
        if any(not reason.is_active for reason in reasons):
            raise HTTPException(status_code=400, detail="Inactive blocking reason")

        hard = any(reason.hard_block for reason in reasons)
        await self.repo.set_blocking_reasons(ticket, reasons)
        ticket = await self.repo.set_blocked(ticket, hard=hard)

        if field_reports:
            reports = [
                FieldReport(
                    ticket_id=ticket.id,
                    field_path=report.field_path,
                    message=report.message,
                    severity=report.severity,
                )
                for report in field_reports
            ]
            await self.repo.add_field_reports(reports)

        await self.repo.add_history(
            TicketHistory(
                ticket_id=ticket.id,
                action=TicketAction.HARD_BLOCKED if hard else TicketAction.BLOCKED,
                moderator_id=moderator.id,
                comment=comment,
                at=datetime.now(timezone.utc),
            ),
        )
        await self.b2b_events.send_blocked(
            idempotency_key=ticket.id,
            product_id=ticket.product_id,
            moderator_id=moderator.id,
            moderator_comment=comment,
            blocking_reason_id=reasons[0].id,
            blocking_reason_title=reasons[0].title,
            hard_block=hard,
            field_reports=field_reports,
            occurred_at=ticket.decision_at,
        )
        await self.repo.db.commit()
        return await self.repo.get_by_id(ticket.id)

    async def _get_owned_ticket(
        self,
        ticket_id: UUID,
        moderator: Moderator,
        allow_admin: bool,
    ):
        await self.repo.auto_return_expired()
        ticket = await self.repo.get_by_id(ticket_id)

        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket.status == TicketStatus.HARD_BLOCKED:
            raise HTTPException(status_code=403, detail="Hard blocked ticket cannot be modified")

        if ticket.status != TicketStatus.IN_REVIEW:
            raise HTTPException(status_code=409, detail="Ticket is not in review")

        is_admin = moderator.role == UserRole.ADMIN
        if (not allow_admin or not is_admin) and ticket.assigned_moderator_id != moderator.id:
            raise HTTPException(status_code=403, detail="Ticket belongs to another moderator")

        return ticket
