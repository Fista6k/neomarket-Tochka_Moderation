from app.database import engine, Base
from app.models.product import Product, ProductSnapshot, BlockingReason, ModerationQueueItem, SKU, Characteristic

def init_db():
    """Создаёт все таблицы в БД"""
    Base.metadata.create_all(bind=engine)
