from fastapi import APIRouter, Depends, Response, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.application.services.auth_service import AuthService


router = APIRouter()
security = HTTPBearer()

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login(email=data.email, password=data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.refresh(refresh_token=data.refresh_token)


@router.post("/logout", status_code=204, dependencies=[Depends(security)])
async def logout():
    """
    Logout на JWT stateless ничего не делает.
    """
    return Response(status_code=204)