from typing import List, Dict, Any
from pydantic import Field

from app.schemas.base import BaseTemplateModel


class SearchTemplateModel(BaseTemplateModel):
    data: List[List[Any]] = Field(default_factory=list)
    tables: Dict[str, Dict[str, Any]]
    t: str
    q: str
    page: int
    limit: int
    mm: int
    total: int = 0
    took: int = 0

    def __init__(self, location: str = '/search', **data):
        super().__init__(location=location, **data)
