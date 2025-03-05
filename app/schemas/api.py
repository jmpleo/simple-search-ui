import json

from typing import List, Dict, Optional

from pydantic import Field, BaseModel

from app.schemas.base import BaseTemplateModel


class ApiMethodDescription(BaseModel):
    name: str
    description: str
    http_method: str
    path: str
    parameters: Optional[List[Dict]] = None
    json_responses: List[str] = Field(default_factory=list)
    responses: List[Dict]
    prefix: str = Field('/api')

    def __init__(self, responses: List[Dict], **p):
        super().__init__(responses=responses, **p)
        self.json_responses = [
            json.dumps(r, indent=2, ensure_ascii=False)
            for r in responses
        ]


class ApiV1MethodDescription(ApiMethodDescription):
    def __init__(self, **p):
        super().__init__(prefix='/api/v1', **p)


class ApiTemplateModel(BaseTemplateModel):
    data: List[ApiMethodDescription] = Field(...)

    def __init__(self, location: str = '/api', **p):
        super().__init__(location=location, **p)

