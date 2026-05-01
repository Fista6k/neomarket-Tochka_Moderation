from app.database import engine, Base


async def init_db():
    """Создаёт все таблицы в БД (асинхронно)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
