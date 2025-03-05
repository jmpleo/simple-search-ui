from fastapi import APIRouter

from app.api.v1.search import router as search_router
from app.api.v1.unloading.api import router as unloading_router
from app.api.v1.health import router as health_router

router = APIRouter()

router.include_router(search_router, prefix='/search')
router.include_router(unloading_router, prefix='/unloading')
router.include_router(health_router, prefix='/health')
