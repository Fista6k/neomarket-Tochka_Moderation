from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.api import queue, decisions, reference, webhooks
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DEBUG:
        from app.db_init import init_db
        await init_db()

    yield

    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Модуль модерации товаров NeoMarket",
        lifespan=lifespan,
    )

    app.include_router(queue.router)
    app.include_router(decisions.router)
    app.include_router(reference.router)
    app.include_router(webhooks.router)

    return app


app = create_app()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
