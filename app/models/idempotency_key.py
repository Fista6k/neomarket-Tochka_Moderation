import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    expires_at: Mapped[datetime] = mapped_column()
