from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from functools import partial
from typing import Union

from app.filters import reduce_large_number_filter
from app.config import settings
from app.services.manticore import ManticoreService
from app.services.storage import StorageService
from app.services.tasks import TaskService
from app.dependencies.service import (
    get_manticore_service, get_task_service, get_storage_service
)
from app.schemas.response import ResponseData

router = APIRouter(prefix='/api/v1')


@router.get("/search")
async def search(
    t: str = '',
    q: str = '',
    p: int = 0,
    l: int = settings.limit_records_on_page,
    mm: int = settings.manticore_matches_default,
    manticore_service: ManticoreService = Depends(get_manticore_service),
) -> ResponseData:
    return await manticore_service.search(t, q, p, limit=l, max_matches=mm)


@router.get('/unloading/start')
async def unloading_start(
    t: str, q: str,
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service)
) -> ResponseData:

    if t not in settings.manticore_tables:
        return ResponseData(
            error=True,
            data=f"таблица {t} недоступна"
        )

    if not q:
        return ResponseData(
            error=True,
            data="невозоможно выполнить пустой запрос"
        )

    res = await task_service.register_task({'t': t, 'q': q})

    if (res.error or 'task_id' not in res.data):
        return ResponseData(
            error=True,
            data=res.data
        )

    task_id = res.data['task_id']

    async def unload(
            _manticore_service: ManticoreService, _t: str, _q: str
    ) -> ResponseData:
        _res = await _manticore_service.unload(_t, _q)
        if _res.error:
            return ResponseData(
                error=True,
                data=_res.data
            )

        return await ManticoreService.simple_format(_res.data)

    await task_service.start_task(
        task_id,
        partial(unload, manticore_service, t, q)
    )

    return ResponseData(
        data={
            "task_id": task_id,
            "status": 'started'
        }
    )


@router.get("/unloading/status/{task_id}")
async def unloading_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> ResponseData:

    task = await task_service.get_task(task_id)

    if not task:
        error = f'Задача {task_id} протухла, или даже не была запущена'
        return ResponseData(error=True, data=error)

    if not task or 'start_time' not in task:
        error = f'Задача {task_id} сломана, требуется перезагрузка'
        return ResponseData(error=True, data=error)

    result = task['result']

    if result and not result.error:
        result.data = {
            'total_pure': result.data['total'],
            'total': reduce_large_number_filter(result.data['total'])
        }

    return ResponseData(
        data={
            'result': result,
            'start_time': task['start_time'],
            'timestamp': datetime.now().isoformat()
        }
    )


@router.get("/unloading/data/{task_id}.{ext}", response_model=None)
async def unloading_data(
    task_id: str, ext: str,
    task_service: TaskService = Depends(get_task_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> Union[ResponseData, FileResponse]:

    task = await task_service.get_task(task_id)

    if not task:
        return ResponseData(
            error=True,
            data=f'Задача {task_id} протухла / не была запущена'
        )

    if 'info' not in task or 't' not in task['info'] or 'result' not in task:
        return ResponseData(
            error=True,
            data=f'Задача {task_id} пропала и имеет некорректный формат'
        )

    result: ResponseData = task['result']

    if result is None:
        return ResponseData(
            error=True,
            data=f'Задача {task_id} еще выполняется'
        )

    if result.error:
        return ResponseData(
            error=True,
            data=f"Задача {task_id} завершилась с ошибкой: " + result.data
        )

    data = result.data

    res = await task_service.complete_task(
        task_id,
        partial(
            storage_service.unload_data_to_file,
            f"{task_id}.{ext}",
            data['data']
        )
    )

    if not res:
        return ResponseData(
            error=True,
            data=f'Не удалось извлечь результат задачаи {task_id}'
        )

    return FileResponse(**res)
