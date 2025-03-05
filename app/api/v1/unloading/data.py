import asyncio

from loguru import logger
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from functools import partial

from typing import Union

from app.services.storage import StorageService
from app.services.tasks import TaskService
from app.dependencies.service import (
    get_task_service, get_storage_service
)
from app.schemas.response import ResponseData


router = APIRouter()


@router.get("/{task_id}.{ext}", response_model=None)
async def unloading_data(
    task_id: str,
    ext: str,
    task_service: TaskService = Depends(get_task_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> Union[ResponseData, FileResponse]:

    task = await task_service.get_task(task_id)

    if task is None:
        return ResponseData(
            error=True,
            data=f'Задача {task_id} протухла / не была запущена'
        )

    result = task.result

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

    match task.type:
        case 'single':
            res = await task_service.complete_task(
                task_id,
                partial(
                    storage_service.unload_data_to_file,
                    f"{task_id}_{task.info['q']}",
                    ext,
                    data['data']
                )
            )
        case 'pack':
            task_master = task
            task_master_id = task_id
            try:
                slave_tasks_list = [
                    ResponseData.model_validate(slave_task_info)
                    for slave_task_info in task_master.info.get('tasks', [])
                ]
            except Exception as e:
                logger.error(str(e))
                return ResponseData(
                    error=True,
                    data="Ошибка разработчика, требуется bug report"
                )

            slave_tasks_id = [
                slave_task_info.data['task_id']
                for slave_task_info in slave_tasks_list
                if not slave_task_info.error
            ]

            cotasks = [
                task_service.get_task(id) for id in slave_tasks_id
            ]

            slave_tasks = await asyncio.gather(*cotasks)

            files = []
            for slave_task_id, slave_task in zip(slave_tasks_id, slave_tasks):
                if slave_task and slave_task.result and (
                    not slave_task.result.error
                ):
                    # FIXME: возможно нужно использовать
                    # task_service.complete_task
                    ext = 'csv'
                    name = f"{slave_task_id}_{slave_task.info['q']}"
                    res = await storage_service.unload_data_to_file(
                        name,
                        ext,
                        slave_task.result.data['data']
                    )
                    if res:
                        files.append(res["filename"])

            res = await task_service.complete_task(
                task_master_id,
                partial(
                    storage_service.unload_files_to_packs,
                    task_master_id,
                    'zip',
                    files
                )
            )

            await asyncio.gather(*[
                task_service.complete_task(slave_task_id)
                for slave_task_id in slave_tasks_id
            ])

    if not res:
        return ResponseData(
            error=True,
            data=f'Не удалось извлечь результат задачаи {task_id}'
        )

    return FileResponse(**res)
