from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.moderator import get_current_moderator
from app.application.services.ticket_service import TicketService
from app.database import get_db
from app.api.v1.tickets import get_ticket_service
from app.models.moderator import Moderator
from app.schemas.queue import ClaimRequest
from app.schemas.ticket import PaginatedTickets, TicketResponse


router = APIRouter()


@router.get("", response_model=PaginatedTickets)
async def list_queue(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    queue_priority: int | None = Query(default=None, ge=1, le=4),
    category_id: UUID | None = None,
    seller_id: UUID | None = None,
    service: TicketService = Depends(get_ticket_service),
    _: Moderator = Depends(get_current_moderator),
):
    items, total = await service.list_queue(
        limit=limit,
        offset=offset,
        queue_priority=queue_priority,
        category_id=category_id,
        seller_id=seller_id,
    )
    return {
        "items": items,
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/claim",
    response_model=TicketResponse,
    responses={204: {"description": "Queue is empty"}},
)
async def claim_ticket(
    data: ClaimRequest | None = None,
    service: TicketService = Depends(get_ticket_service),
    moderator: Moderator = Depends(get_current_moderator),
):
    ticket = await service.claim_next(
        moderator=moderator,
        queue_priority=data.queue_priority if data else None,
        category_ids=data.category_ids if data else None,
    )

    if ticket is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return ticket
