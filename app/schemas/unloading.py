from typing import List, Dict, Any
from pydantic import Field

from app.schemas.base import BaseTemplateModel
from app.schemas.task import Task


class UnloadingTemplateModel(BaseTemplateModel):
    data: List[Task] = Field([])
    tables: Dict[str, Dict[str, Any]]
    t: str
    q: str = ''

    def __init__(self, location: str = '/unloading', **data):
        super().__init__(location=location, **data)
