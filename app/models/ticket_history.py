import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.database import Base
from app.models.enums import TicketAction

if TYPE_CHECKING:
    from app.models.ticket import Ticket

class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
    )

    action: Mapped[TicketAction] = mapped_column(Enum(TicketAction))

    moderator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )

    ticket = relationship("Ticket", back_populates="history")