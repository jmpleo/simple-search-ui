from datetime import datetime
from fastapi import APIRouter, Depends

from app.filters import reduce_large_number_filter
from app.services.tasks import TaskService
from app.dependencies.service import get_task_service
from app.schemas.response import ResponseData


router = APIRouter()


@router.get("/{task_id}")
async def unloading_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> ResponseData:

    task = await task_service.get_task(task_id)

    if task is None:
        error = f'Задача {task_id} протухла, или даже не была запущена'
        return ResponseData(error=True, data=error)

    result = task.result

    if result and not result.error:
        result = ResponseData(data={
            'total': result.data['total'],
            'total_pretty': reduce_large_number_filter(
                result.data['total']
            )
        })

    return ResponseData(data={
        'result': result,
        'start_time': task.start_time,
        'timestamp': datetime.now().isoformat()
    })
