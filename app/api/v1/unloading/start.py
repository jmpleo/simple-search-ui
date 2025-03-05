import tempfile
import os
import aiofiles
import asyncio

from fastapi import (
    APIRouter, Depends, File, UploadFile, Query
)
from functools import partial

from typing import List

from app.config import settings
from app.services.manticore import ManticoreService
from app.services.tasks import TaskService
from app.dependencies.service import (
    get_manticore_service, get_task_service
)
from app.schemas.response import ResponseData

router = APIRouter()


@router.get("")
async def unloading_start(
    *,
    t: str = settings.manticore_default_table,
    q: str = '',
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service),
    tag: str = '',
    type: str = 'single'
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

    res = await task_service.register_task(
        info={'t': t, 'q': q, 'tag': tag},
        type=type
    )

    if (res.error or 'task_id' not in res.data):
        return ResponseData(
            error=True,
            data=res.data
        )

    task_id = res.data['task_id']

    async def unload(
        _manticore_service: ManticoreService, _t: str, _q: str,
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


@router.post("")
async def unloading_start_pack(
    t: str = Query(default=settings.manticore_default_table),
    file: UploadFile = File(...),
    manticore_service: ManticoreService = Depends(get_manticore_service),
    task_service: TaskService = Depends(get_task_service),
) -> ResponseData:

    if file.size > settings.file_upload_max_size:
        return ResponseData(
            error=True,
            data=(
                "файл должен не больше"
                f" {settings.file_upload_max_size // (1024 * 1024)} МБ"
            )
        )

    if file.content_type != 'text/plain':
        return ResponseData(
            error=True,
            data="файл должен иметь формат .txt"
        )

    if t not in settings.manticore_tables:
        return ResponseData(
            error=True,
            data=f"таблица {t} недоступна"
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_location = os.path.join(tmpdirname, file.filename)

            async with aiofiles.open(file_location, "wb") as buffer:
                await buffer.write(await file.read())

            async with aiofiles.open(file_location, "r") as f:
                qs = await f.readlines()

                if len(qs) > settings.file_upload_limit_lines:
                    return ResponseData(
                        error=True,
                        data=(
                            "файл содержит слишком много строк"
                            f" (всего: {len(qs)},"
                            f" max: {settings.file_upload_limit_lines})"
                        )
                    )

                cotasks = [
                    unloading_start(
                        t=t,
                        q=q.strip(),
                        manticore_service=manticore_service,
                        task_service=task_service,
                        tag=file.filename
                    )
                    for q in qs
                ]

                tasks = await asyncio.gather(*cotasks)

                res = await task_service.register_task(
                    type='pack',
                    info={
                        "t": t,
                        "tag": file.filename,
                        "tasks": list(map(lambda r: r.model_dump(), tasks)),
                        "filename": file.filename
                    }
                )

                if res.error:
                    return ResponseData(
                        error=True,
                        data=str(res.data)
                    )

                task_id = res.data['task_id']

                async def _check(
                    _task_service: TaskService,
                    _tasks_list: List[ResponseData],
                    _ttl: int = 720
                ) -> ResponseData:
                    while _ttl > 0:
                        _ttl -= 1
                        _cotasks = [
                            _task_service.get_task(_task.data['task_id'])
                            for _task in _tasks_list
                            if not _task.error
                        ]
                        _tasks = await asyncio.gather(*_cotasks)

                        if all(t.result is not None for t in _tasks if t):
                            total = sum(
                                t.result.data['total']
                                for t in _tasks
                                if t and not t.result.error
                            )
                            return ResponseData(data={'total': total})

                        else:
                            await asyncio.sleep(5)

                await task_service.start_task(
                    task_id,
                    partial(_check, task_service, tasks)
                )

    except Exception as e:
        return ResponseData(
            error=True,
            data=str(e)
        )

    return ResponseData(data={
        "task_id": task_id,
        "type": "pack"
    })
