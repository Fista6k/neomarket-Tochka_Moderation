from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from app.api.v1 import auth, moderators, blocking_reasons

security = HTTPBearer()

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(moderators.router, prefix="/moderators", tags=["Moderators"], dependencies=[Depends(security)])
api_router.include_router(blocking_reasons.router, prefix="/blocking-reasons", tags=["BlockingReasons"], dependencies=[Depends(security)])