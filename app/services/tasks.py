import json
import aioredis
import asyncio
from loguru import logger
from hashlib import sha256
from typing import Optional, Dict, Any, List, Callable, Union
from pydantic import ValidationError

from app.schemas.response import ResponseData
from app.schemas.task import Task
from app.config import settings


class TaskService:
    def __init__(self):
        self.redis_client = aioredis.from_url(
            f"redis://{settings.redis_host}"
            f":{settings.redis_port}"
            f"/{settings.redis_db}",
            decode_responses=True
        )

    async def delete_all_tasks(self):

        keys = await self._execute_redis_command(
            self.redis_client.keys,
            "unloading_task:*"
        )

        if keys:
            for k in keys:
                await self._execute_redis_command(self.redis_client.delete, k)

    async def delete_task(self, task_id: str) -> None:

        await self._execute_redis_command(
            self.redis_client.delete,
            f"unloading:{task_id}"
        )

    async def register_task(self, info: Dict[str, Any],
                            type: str = 'single') -> ResponseData:
        task_id = self._generate_task_id(info)

        if await self._task_exists(task_id):
            task = await self.get_task(task_id)
            if task and task.result:
                return ResponseData(
                    error=True,
                    data="уже было загружено ранее"
                )

        task = Task(
            task_id=task_id,
            info=info,
            type=type
        )

        await self._store_task(task)

        return ResponseData(data={"task_id": task_id})

    async def get_task(self, task_id: str) -> Optional[Task]:
        task_data = await self._execute_redis_command(
            self.redis_client.hgetall, f"unloading_task:{task_id}"
        )

        if task_data:
            try:
                if 'info' in task_data:
                    task_data['info'] = json.loads(task_data['info'])

                if 'result' in task_data:
                    task_data['result'] = json.loads(task_data['result'])

                    if task_data['result']:
                        task_data['result'] = ResponseData.model_validate(
                            task_data['result']
                        )

                return Task.model_validate(task_data)

            except ValidationError as e:
                logger.error(f"Validation error for task {task_id}: {str(e)}")
                return None
        else:
            # logger.warning(f"No task found with ID: {task_id}")
            return None

    async def get_tasks(self) -> List[Task]:
        unloading_tasks = []
        keys = await self._execute_redis_command(
            self.redis_client.keys,
            "unloading_task:*"
        )

        for key in keys:
            _, task_id = key.split(':', 1)
            task = await self.get_task(task_id)
            if task:
                unloading_tasks.append(task)

        return unloading_tasks

    async def start_task(
        self, task_id: str, f: Optional[Callable[[], ResponseData]]
    ) -> None:
        task = await self.get_task(task_id)
        if task and f:
            asyncio.create_task(self._run_task(task_id, f))

    async def complete_task(
        self, task_id: str, f: Union[Callable, None] = None
    ) -> Any:
        task = await self.get_task(task_id)
        res = None
        if task and task.result and not task.result.error:
            if f and task.result.data['total'] > 0:
                res = await f()

            await self.redis_client.expire(
                f"unloading_task:{task_id}",
                settings.ttl_unloading_task
            )

        return res

    async def _run_task(
        self, task_id: str, f: Callable[[], ResponseData]
    ) -> None:

        result = await f()

        await self._update_task_result(task_id, result)

        ttl = settings.ttl_long_unloading_task

        if result.error or (
            result.data.get('total', 0) == 0
        ):
            ttl = settings.ttl_unloading_task

        await self.redis_client.expire(f"unloading_task:{task_id}", ttl)

    def _generate_task_id(self, info: Dict[str, Any]) -> str:
        info_str = json.dumps(info, sort_keys=True)
        return sha256(info_str.encode('utf-8')).hexdigest()[:8]

    async def _task_exists(self, task_id: str) -> bool:
        return await self.redis_client.exists(f"unloading_task:{task_id}")

    async def _store_task(self, task: Task) -> None:
        try:
            task_data = task.model_dump()

            task_data['info'] = json.dumps(
                task_data['info'], ensure_ascii=False
            )

            if task_data.get('result', None) is None:
                task_data['result'] = json.dumps(None)

            else:
                task_data['result'] = task_data['result'].model_dump_json()

            await self.redis_client.hset(
                f"unloading_task:{task.task_id}",
                mapping=task_data
            )
            # logger.info(f"Task {task.task_id} stored successfully.")

        except Exception as e:
            logger.error(f"Failed to store task {task.task_id}: {e}")

    async def _update_task_result(
        self, task_id: str, result: ResponseData
    ) -> None:
        if await self._task_exists(task_id):
            await self._execute_redis_command(
                self.redis_client.hset,
                f"unloading_task:{task_id}", mapping={
                    "result": result.model_dump_json(),
                    "end_time": Task.end_timestamp()
                }
            )

    async def _execute_redis_command(
            self, command, *args, **kwargs
    ) -> Optional[Any]:
        try:
            return await command(*args, **kwargs)
        except aioredis.RedisError as e:
            logger.error(f"Redis error occurred: {e}")
            return None
