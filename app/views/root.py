from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.views.search import router as search_router
from app.views.unloading import router as unloading_router
from app.views.api import router as api_router


router = APIRouter()

router.include_router(search_router, prefix='/search')
router.include_router(unloading_router, prefix='/unloading')
router.include_router(api_router, prefix='/api')


@router.get("/")
async def read_root():
    return RedirectResponse(url='/search')
