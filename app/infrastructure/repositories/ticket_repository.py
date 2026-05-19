from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from app.models.ticket import Ticket
from app.models.enums import TicketKind, TicketStatus


class TicketRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def close_by_product(
        self,
        product_id: UUID,
    ):
        await self.db.execute(
            update(Ticket)
            .where(
                Ticket.product_id == product_id,
                Ticket.status.in_(
                    [TicketStatus.PENDING, TicketStatus.IN_REVIEW]
                ),
            )
            .values(status=TicketStatus.BLOCKED)
        )
        await self.db.commit()