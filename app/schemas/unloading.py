from typing import List, Dict, Any
from pydantic import Field

from app.schemas.base import BaseTemplateModel


class UnloadingTemplateModel(BaseTemplateModel):
    data: List[Dict[str, Any]] = Field(default_factory=list)
    tables: Dict[str, Dict[str, Any]]
    t: str
    q: str = ''

    def __init__(self, location: str = '/unloading', **data):
        super().__init__(location=location, **data)
