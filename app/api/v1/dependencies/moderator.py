from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models.moderator import Moderator
from app.api.v1.dependencies.security import decode_token


async def get_current_moderator(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> Moderator:

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]

    payload = decode_token(token, expected_type="access")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    try:
        user_uuid = UUID(user_id)
    except:
        raise HTTPException(401, "Invalid token payload")

    moderator = await db.get(Moderator, user_uuid)

    if not moderator or not moderator.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return moderator

async def get_admin_user(
    moderator: Moderator = Depends(get_current_moderator),
) -> Moderator:

    if moderator.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return moderator