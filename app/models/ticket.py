import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base
from app.models.enums import TicketKind, TicketStatus
from app.models.field_report import FieldReport
from app.models.ticket_history import TicketHistory


ticket_blocking_reasons = Table(
    "ticket_blocking_reasons",
    Base.metadata,
    Column(
        "ticket_id",
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "reason_id",
        UUID(as_uuid=True),
        ForeignKey("blocking_reasons.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    kind: Mapped[TicketKind] = mapped_column(Enum(TicketKind))
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus),
        default=TicketStatus.PENDING,
        index=True,
    )

    queue_priority: Mapped[int] = mapped_column(Integer)

    assigned_moderator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("moderators.id"),
        nullable=True,
    )

    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    claim_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_deleted: bool = False

    product_updated_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    json_before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    json_after: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=datetime.now(timezone.utc),
        nullable=True,
    )

    moderator = relationship("Moderator")
    field_reports = relationship("FieldReport", back_populates="ticket")
    history = relationship("TicketHistory", back_populates="ticket")
    blocking_reasons = relationship("BlockingReason", secondary=ticket_blocking_reasons)
