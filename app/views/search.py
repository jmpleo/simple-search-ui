from fastapi import Request, APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.templates import templates
from app.config import settings
from app.schemas.search import SearchTemplateModel
from app.resources.strings import (
    ERROR_TABLES_UNAVAILABE
)
from app.services.manticore import ManticoreService
from app.dependencies.service import get_manticore_service


router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def search(
    request: Request,
    t: str = Query(settings.manticore_default_table),
    q: str = Query(''),
    p: int = Query(0),
    l: int = Query(settings.limit_records_on_page),
    mm: int = Query(settings.manticore_matches_default),
    manticore_service: ManticoreService = Depends(get_manticore_service)
):

    max_matches = min(max(mm, 1), settings.manticore_max_matches)
    limit = min(max(l, 1), settings.limit_records_on_page, max_matches)

    res = await manticore_service.status()

    if res.error:
        return templates.TemplateResponse("index.html", SearchTemplateModel(
            request=request,
            tables={t: {}},
            t=t, q=q, page=p,
            limit=settings.limit_records_on_page,
            mm=settings.manticore_matches_default,
            error=res.data,
        ).model_dump())

    tables = res.data

    if t:
        if t in tables:
            pass

        else:
            return templates.TemplateResponse(
                "index.html",
                SearchTemplateModel(
                    request=request,
                    tables=tables,
                    t=t, q=q,
                    page=p, limit=l, mm=mm,
                    error=f"Таблица {t} недоступна"
                ).model_dump()
            )

    else:
        if len(tables):
            t = list(tables)[0]

        else:
            return templates.TemplateResponse(
                "index.html",
                SearchTemplateModel(
                    request=request,
                    tables=tables,
                    t=t, q=q,
                    page=p, limit=l, mm=mm,
                    error=ERROR_TABLES_UNAVAILABE
                ).model_dump()
            )

    fields = tables[t].get('fields', [])

    if len(q) == 0:
        return templates.TemplateResponse("index.html", SearchTemplateModel(
            request=request,
            tables=tables,
            t=t, q=q,
            page=p, limit=l, mm=mm,
        ).model_dump())

    res = await manticore_service.search(
        t, q, p,
        highlight_fields=fields,
        limit=limit,
        max_matches=max_matches
    )

    if res.error:
        return templates.TemplateResponse("index.html", SearchTemplateModel(
            request=request,
            tables=tables,
            t=t, q=q,
            page=p, limit=l, mm=mm,
            error=res.data,
        ).model_dump())

    res = await ManticoreService.simple_format(res.data, tables[t])

    if res.error:
        return templates.TemplateResponse("index.html", SearchTemplateModel(
            request=request,
            tables=tables,
            t=t, q=q,
            page=p, limit=l, mm=mm,
            error=res.data,
        ).model_dump())

    data = res.data

    total = data['total']
    took = data['took']

    return templates.TemplateResponse("index.html", SearchTemplateModel(
        request=request,
        data=data['data'],
        tables=tables,
        t=t, q=q,
        page=p, limit=l, mm=mm,
        total=total,
        took=took
    ).model_dump())
