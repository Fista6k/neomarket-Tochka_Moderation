from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.b2b import IncomingB2BEvent
from app.application.services.b2b_service import B2BService
from app.api.v1.dependencies.key_dependency import verify_service_key
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.infrastructure.repositories.idempotency_repository import IdempotencyRepository


router = APIRouter()

async def get_b2b_service(db:AsyncSession = Depends(get_db)):
    tRepo = TicketRepository(db)
    iRepo = IdempotencyRepository(db)
    return B2BService(ticketRepo=tRepo, idempotencyRepo=iRepo)

@router.post("/events", status_code=202)
async def receive_event(
    event: IncomingB2BEvent,
    service: B2BService = Depends(get_b2b_service),
    _: None = Depends(verify_service_key),
):
    await service.handle_event(event)