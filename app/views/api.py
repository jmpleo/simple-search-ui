from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.templates import templates

router = APIRouter()


@router.get("/api", response_class=HTMLResponse)
async def search(request: Request):
    return templates.TemplateResponse("api.html", {
            "request": request,
            "location": "/api"
        }
    )
