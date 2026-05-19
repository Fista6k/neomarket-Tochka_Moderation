from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from uuid import UUID

from app.models.moderator import Moderator
from app.api.v1.dependencies.security import (
    verify_password,
    create_auth_tokens,
    decode_token,
)
from app.models.enums import UserRole


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(
        self,
        email: str,
        password: str,
    ) -> dict:

        result = await self.db.execute(
            select(Moderator).where(Moderator.email == email)
        )
        moderator = result.scalar_one_or_none()

        if not moderator:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not moderator.is_active:
            raise HTTPException(status_code=403, detail="User inactive")

        if not verify_password(password, moderator.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        tokens = create_auth_tokens(
            user_id=moderator.id,
            role=moderator.role.value,
        )

        return tokens

    async def refresh(
        self,
        refresh_token: str,
    ) -> dict:

        payload = decode_token(refresh_token, expected_type="refresh")

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")

        try:
            user_uuid = UUID(user_id)
        except:
            raise HTTPException(401, "Invalid token payload")

        moderator = await self.db.get(Moderator, user_uuid)

        role = moderator.role.value

        if not moderator or not moderator.is_active:
            raise HTTPException(status_code=401, detail="User not found")

        return create_auth_tokens(
            user_id=moderator.id,
            role=role,
        )