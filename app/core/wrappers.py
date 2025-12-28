"""
Response wrappers for ClipboardHealthAI application.
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from starlette.responses import JSONResponse

T = TypeVar("T")


class ErrorCbhResponse(BaseModel):
    """
    Error response model for standardized error formatting.
    """

    message: str


class CbhResponseWrapper(BaseModel, Generic[T]):
    """
    Standard response wrapper for all API endpoints.
    """

    data: Optional[T] = None
    successful: bool = True
    error: Optional[ErrorCbhResponse] = None

    def response(self, status_code: int):
        """
        Create a JSONResponse with proper status code and formatting.
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "data": self.data,
                "successful": self.successful,
                "error": self.error.dict() if self.error else None,
            },
        )
