from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.templates import templates
from app.schemas.api import (
    ApiTemplateModel
)
from app.resources.api import METHOD_DESCRIPTION


router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def search(request: Request):
    return templates.TemplateResponse(
        "api.html",
        ApiTemplateModel(
            request=request,
            location="/api",
            data=METHOD_DESCRIPTION
        ).model_dump()
    )
