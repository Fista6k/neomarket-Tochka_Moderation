from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class Error(ErrorResponse):
    pass
