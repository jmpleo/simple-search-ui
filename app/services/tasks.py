import json
import logging
import aioredis
import datetime
import asyncio
from loguru import logger
from hashlib import sha256
from typing import Optional, Dict, Any, List, Callable
from pydantic import ValidationError

from app.schemas.response import ResponseData
from app.config import settings

# Create directory for unloading data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TaskService:
    def __init__(self):
        self.redis_client = aioredis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}"
            f"/{settings.redis_db}",
            decode_responses=True
        )

    async def delete_all_tasks(self):

        keys = await self._execute_redis_command(
            self.redis_client.keys,
            "unloading_task:*"
        )

        for k in keys:
            await self._execute_redis_command(self.redis_client.delete, k)

    async def register_task(self, info: Dict[str, Any]) -> ResponseData:
        task_id = self._generate_task_id(info)

        if await self._task_exists(task_id):
            task = await self.get_task(task_id)
            if task and task['result']:
                return ResponseData(
                    error=True,
                    data="Task already unloaded before"
                )

        start_time = datetime.datetime.now().isoformat()
        await self._store_task(task_id, start_time, info)

        return ResponseData(data={"task_id": task_id})

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:

        task = await self._execute_redis_command(
            self.redis_client.hgetall, f"unloading_task:{task_id}"
        )
        if task:
            task['task_id'] = task_id
            task['info'] = json.loads(task.get('info', 'null'))
            task['result'] = json.loads(task.get('result', 'null'))
            if (task['result']):
                try:
                    task['result'] = ResponseData.model_validate(
                        task['result']
                    )
                except ValidationError as e:
                    logger.error(e)

        return task

    async def get_tasks(self) -> List[Dict[str, Any]]:
        unloading_tasks = []
        keys = await self._execute_redis_command(
            self.redis_client.keys,
            "unloading_task:*"
        )

        for key in keys:
            _, task_id = key.split(':', 1)
            task = await self.get_task(task_id)
            unloading_tasks.append(task)

        return unloading_tasks

    async def start_task(
        self, task_id: str, f: Optional[Callable[[], ResponseData]]
    ) -> None:
        task = await self.get_task(task_id)
        if task and f:
            asyncio.create_task(self._run_task(task_id, f))

    async def complete_task(self, task_id: str, f: Callable) -> None:
        task = await self.get_task(task_id)
        if task:
            res = await f()
            await self.redis_client.expire(
                f"unloading_task:{task_id}",
                settings.ttl_unloading_task
            )
            return res
        return None

    async def _run_task(self, task_id: str, f: Callable) -> None:
        result = await f()
        await self._update_task_result(task_id, result)

    def _generate_task_id(self, info: Dict[str, Any]) -> str:
        info_str = json.dumps(info, sort_keys=True)
        return sha256(info_str.encode('utf-8')).hexdigest()[:8]

    async def _task_exists(self, task_id: str) -> bool:
        return await self.redis_client.exists(f"unloading_task:{task_id}")

    async def _store_task(
            self, task_id: str, start_time: str, info: Dict[str, Any]
    ) -> None:
        await self.redis_client.hset(
            f"unloading_task:{task_id}", mapping={
                "start_time": start_time,
                "info": json.dumps(info),
                "result": json.dumps(None)
            }
        )

    async def _update_task_result(
            self, task_id: str, result: ResponseData
    ) -> None:
        await self._execute_redis_command(
            self.redis_client.hset,
            f"unloading_task:{task_id}", mapping={
                "result": result.model_dump_json()
            }
        )

    async def _execute_redis_command(
            self, command, *args, **kwargs
    ) -> Optional[Any]:
        try:
            return await command(*args, **kwargs)
        except aioredis.RedisError as e:
            logging.error(f"Redis error occurred: {e}")
            return None

    def _format_task_data(
        self, key: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "task_id": key.split(':')[1],
            "start_time": task_data.get('start_time'),
            "info": json.loads(task_data.get('info')),
            "result": json.loads(task_data.get('result'))
        }
