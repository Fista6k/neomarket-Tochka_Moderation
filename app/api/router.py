from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from app.api.v1 import auth, moderators, blocking_reasons, b2b, queue, stats, tickets

security = HTTPBearer()

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(moderators.router, prefix="/moderators", tags=["Moderators"], dependencies=[Depends(security)])
api_router.include_router(blocking_reasons.router, prefix="/blocking-reasons", tags=["BlockingReasons"], dependencies=[Depends(security)])
api_router.include_router(b2b.router, prefix="/b2b", tags=["B2B Events"])
api_router.include_router(queue.router, prefix="/queue", tags=["Queue"], dependencies=[Depends(security)])
api_router.include_router(stats.router, prefix="/stats", tags=["Stats"], dependencies=[Depends(security)])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"], dependencies=[Depends(security)])
