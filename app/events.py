from typing import Callable
from loguru import logger
from fastapi import FastAPI

from app.config import Settings
from app.services.tasks import TaskService
from app.services.storage import StorageService
from app.services.manticore import ManticoreService


def create_start_app_handler(
    app: FastAPI,
    settings: Settings,
) -> Callable:
    async def start_app() -> None:
        app.state.task_service = TaskService()
        app.state.storage_service = StorageService()
        app.state.manticore_service = ManticoreService()

        await app.state.task_service.delete_all_tasks()

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        await app.state.task_service.delete_all_tasks()

    return stop_app
