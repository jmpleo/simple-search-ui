from fastapi import Request, APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from typing import Union
from app.services.manticore import ManticoreService
from app.services.tasks import TaskService
from app.services.storage import StorageService

from app.api.v1.unloading.start import (
    unloading_start as api_unloading_start,
    unloading_start_pack as api_unloading_start_pack
)
from app.api.v1.unloading.status import (
    unloading_status as api_unloading_status
)
from app.api.v1.unloading.data import unloading_data as api_unloading_data

from app.templates import templates
from app.schemas.unloading import UnloadingTemplateModel
from app.dependencies.service import (
    get_manticore_service, get_task_service, get_storage_service
)
from app.schemas.response import ResponseData
from app.config import settings

router = APIRouter()


@router.get('/start')
async def unloading_start(
    q: str,
    t: str = settings.manticore_default_table,
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service)
) -> RedirectResponse:
    res = await api_unloading_start(
        t=t, q=q,
        manticore_service=manticore_service,
        task_service=task_service
    )

    if res.error:
        return RedirectResponse(url=f'/unloading?t={t}&error={res.data}')

    return RedirectResponse(url=f'/unloading?t={t}')


@router.post('/start')
async def unloading_start_pack(
    t: str = Query(default=settings.manticore_default_table),
    file: UploadFile = File(...),
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service)
) -> ResponseData:

    return await api_unloading_start_pack(
        t, file, manticore_service, task_service
    )


@router.get("/status/{task_id}")
async def unloading_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> ResponseData:

    return await api_unloading_status(task_id, task_service)


@router.get("/data/{task_id}.{ext}")
async def unloading_data(
    task_id: str, ext: str,
    task_service: TaskService = Depends(get_task_service),
    storage_service: StorageService = Depends(get_storage_service)
):

    res = await api_unloading_data(task_id, ext, task_service, storage_service)

    if isinstance(res, FileResponse):
        return res

    if isinstance(res, ResponseData) and res.error:
        return RedirectResponse(url=f'/unloading?error={res.data}')

    return res


@router.get("", response_class=HTMLResponse)
async def unloading(
    request: Request,
    t: str = Query(default=settings.manticore_default_table),
    error: Union[str, None] = Query(None),
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service)
):

    res = await manticore_service.status()

    if res.error:
        return templates.TemplateResponse(
            "unloading.html",
            UnloadingTemplateModel(
                request=request,
                name='simple ui unloading',
                data=[],
                tables={t: {}},
                t=t,
                error=res.data,
            ).model_dump()
        )

    tables = res.data

    if t not in tables:
        t = list(tables)[0] if len(tables) else ''

    tasks = await task_service.get_tasks()

    return templates.TemplateResponse(
        "unloading.html",
        UnloadingTemplateModel(
            request=request,
            name='simple ui unloading',
            data=tasks,
            tables=tables,
            t=t,
            error=error
        ).model_dump()
    )
