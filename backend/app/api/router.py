from fastapi import APIRouter

from app.api.routes.manual_mode import router as manual_mode_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(manual_mode_router)
