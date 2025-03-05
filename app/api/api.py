from fastapi import APIRouter

from app.api.v1.api import router as api_v1_router

router = APIRouter(prefix="/api")

router.include_router(api_v1_router, prefix='/v1')
