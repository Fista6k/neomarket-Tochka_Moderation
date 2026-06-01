from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.moderator import get_current_moderator
from app.application.services.ticket_service import TicketService
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.database import get_db
from app.models.enums import TicketStatus
from app.models.moderator import Moderator
from app.schemas.ticket import (
    ApproveRequest,
    BlockDecisionRequest,
    PaginatedTickets,
    TicketDetailResponse,
    TicketResponse,
)
from app.application.services.b2b_moderation_event_client import B2BModerationEventClient


router = APIRouter()


async def get_ticket_service(db: AsyncSession = Depends(get_db)):
    repo = TicketRepository(db)
    b2b_client = B2BModerationEventClient()
    return TicketService(repo, b2b_client)

@router.get("", response_model=PaginatedTickets)
async def list_tickets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    moderator_id: UUID | None = None,
    product_id: UUID | None = None,
    seller_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    service: TicketService = Depends(get_ticket_service),
    _: Moderator = Depends(get_current_moderator),
):
    items, total = await service.list(
        limit=limit,
        offset=offset,
        status=status_filter,
        moderator_id=moderator_id,
        product_id=product_id,
        seller_id=seller_id,
        created_from=created_from,
        created_to=created_to,
    )
    return {
        "items": items,
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse
)
async def get_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service),
    _: Moderator = Depends(get_current_moderator),
):
    return await service.get_detail(ticket_id)


@router.post(
    "/{ticket_id}/release",
    response_model=TicketResponse
)
async def release_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(get_ticket_service),
    moderator: Moderator = Depends(get_current_moderator),
):
    return await service.release(ticket_id, moderator)


@router.post(
    "/{ticket_id}/approve",
    response_model=TicketResponse
)
async def approve_ticket(
    ticket_id: UUID,
    data: ApproveRequest | None = None,
    service: TicketService = Depends(get_ticket_service),
    moderator: Moderator = Depends(get_current_moderator),
):
    return await service.approve(
        ticket_id=ticket_id,
        moderator=moderator,
        comment=data.comment if data else None,
    )


@router.post(
    "/{ticket_id}/block",
    response_model=TicketResponse
)
async def block_ticket(
    ticket_id: UUID,
    data: BlockDecisionRequest,
    service: TicketService = Depends(get_ticket_service),
    moderator: Moderator = Depends(get_current_moderator),
):
    return await service.block(
        ticket_id=ticket_id,
        moderator=moderator,
        blocking_reason_ids=data.blocking_reason_ids,
        field_reports=data.field_reports,
        comment=data.comment,
    )
