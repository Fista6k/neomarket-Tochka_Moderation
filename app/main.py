from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.database import engine
from app.api.router import api_router


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

    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
