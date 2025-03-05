from datetime import datetime

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.response import ResponseData


class Task(BaseModel):
    task_id: str = Field(...)
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = Field(default='')
    info: Dict[str, Any] = Field(...)
    type: str
    result: Optional[ResponseData] = Field(None)

    @staticmethod
    def end_timestamp() -> str:
        return datetime.now().isoformat()
