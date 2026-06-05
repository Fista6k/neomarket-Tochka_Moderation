from fastapi import Header, HTTPException
from app.core.config import settings


async def verify_service_key(
    x_service_key: str | None = Header(None),
) -> None:
    if x_service_key is None or x_service_key != settings.B2B_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")