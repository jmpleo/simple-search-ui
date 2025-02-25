from pydantic import BaseModel, Field
from fastapi import Request
from typing import Optional


class BaseTemplateModel(BaseModel):
    request: Optional[Request] = None
    name: str = Field(default='simple search ui')
    error: Optional[str] = None
    location: str = Field(default="/search")

    def __init__(self, **data):
        super().__init__(**data)

    class Config:
        arbitrary_types_allowed = True
