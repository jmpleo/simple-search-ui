from pydantic import BaseModel
from typing import Any, Union, Dict


class ResponseData(BaseModel):
    error: bool = False
    data: Union[Dict[str, Any], str]
