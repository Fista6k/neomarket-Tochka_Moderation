from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, foreign
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

Base = declarative_base()


class ProductSnapshot(Base):
    """Снимок товара на момент подачи на модерацию"""
    __tablename__ = "product_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    snapshot_type = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    moderation = relationship("ModerationQueueItem", back_populates="snapshots")


class ModerationQueueItem(Base):
    """Очередь товаров на модерацию"""
    __tablename__ = "moderation_queue"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    is_new = Column(Boolean, default=True, nullable=False)
    status = Column(String, nullable=False, default="pending")
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderation_reason = Column(String, nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String, nullable=True)

    snapshots = relationship("ProductSnapshot", back_populates="moderation", lazy="selectin")

