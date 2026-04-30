from fastapi import FastAPI

from app.config import settings
from app.api import queue, decisions, reference, webhooks
from app.db_init import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Модуль модерации товаров NeoMarket"
    )

    app.include_router(queue.router)
    app.include_router(decisions.router)
    app.include_router(reference.router)
    app.include_router(webhooks.router)

    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Создаёт таблицы БД при старте"""
    await init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}
