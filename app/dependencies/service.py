from fastapi import Request

from app.services.tasks import TaskService
from app.services.storage import StorageService
from app.services.manticore import ManticoreService


def get_manticore_service(request: Request) -> ManticoreService:
    return request.app.state.manticore_service


def get_storage_service(request: Request) -> StorageService:
    return request.app.state.storage_service


def get_task_service(request: Request) -> TaskService:
    return request.app.state.task_service
