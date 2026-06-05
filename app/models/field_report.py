import uuid
from uuid6 import uuid7
from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FieldSeverity


class FieldReport(Base):
    __tablename__ = "field_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
    )

    sku_id: Mapped[uuid.UUID | None] = mapped_column(
            UUID(as_uuid=True),
            nullable=True
        )

    field_name: Mapped[str] = mapped_column(String(255))
    comment: Mapped[str] = mapped_column(String(1000))
    severity: Mapped[FieldSeverity] = mapped_column(
        Enum(FieldSeverity),
        default=FieldSeverity.ERROR,
    )

    ticket = relationship("Ticket", back_populates="field_reports")