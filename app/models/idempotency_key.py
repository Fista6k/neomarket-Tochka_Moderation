import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    expires_at: Mapped[datetime] = mapped_column()