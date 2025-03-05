from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.services.manticore import ManticoreService
from app.dependencies.service import get_manticore_service
from app.schemas.response import ResponseData

router = APIRouter()


@router.get("")
async def search(
    t: str = Query(''),
    q: str = Query(''),
    p: int = Query(0),
    l: int = settings.limit_records_on_page,
    mm: int = settings.manticore_matches_default,
    manticore_service: ManticoreService = Depends(get_manticore_service),
) -> ResponseData:
    return await manticore_service.search(t, q, p, limit=l, max_matches=mm)
