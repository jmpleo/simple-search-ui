from fastapi import APIRouter

from app.api.v1.unloading.start import router as start_router
from app.api.v1.unloading.data import router as data_router
from app.api.v1.unloading.status import router as status_router

router = APIRouter()

router.include_router(start_router, prefix='/start')
router.include_router(data_router, prefix='/data')
router.include_router(status_router, prefix='/status')
