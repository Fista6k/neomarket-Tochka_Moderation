from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ProductStatus(enum.Enum):
    PENDING = "pending"
    MODERATED = "moderated"
    BLOCKED = "blocked"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    snapshots = relationship("ProductSnapshot", back_populates="product", cascade="all, delete-orphan")


class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    snapshot_type = Column(String, nullable=False)  # "before" или "after"
    data = Column(Text, nullable=False)  # JSON с данными товара
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="snapshots")


class BlockingReason(Base):
    __tablename__ = "blocking_reasons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)


class ModerationQueueItem(Base):
    __tablename__ = "moderation_queue"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    is_new = Column(Integer, default=1)  # 1 - новый товар, 0 - изменённый
    assigned_at = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)

    product = relationship("Product")
