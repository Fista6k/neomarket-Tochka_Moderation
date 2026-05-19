from sqlalchemy import select
from app.database import engine, Base, async_session_maker
from app.models.moderator import Moderator
from app.models.enums import UserRole
from app.api.v1.dependencies.security import hash_password
from app.core.config import settings


async def init_db():
    """Создаёт все таблицы в БД (асинхронно)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:

        result = await session.execute(
            select(Moderator).where(Moderator.role == UserRole.ADMIN)
        )
        admin_exists = result.scalar_one_or_none()

        if admin_exists:
            return

        admin = Moderator(
            email=settings.INITIAL_ADMIN_EMAIL,
            hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            first_name="Super",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )

        session.add(admin)
        await session.commit()

        print("✅ Initial ADMIN created")
