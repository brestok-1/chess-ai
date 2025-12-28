"""
Common schemas.
"""

from typing import TypeVar, Generic

from pydantic import BaseModel

from app.api.common.dto import Paging, SearchFilter, SortBy

T = TypeVar("T", bound=BaseModel)


class AllObjectsResponse(BaseModel, Generic[T]):
    """
    Response model for all objects.
    """

    paging: Paging
    data: list[T]


class SearchRequest(BaseModel):
    """
    Request schema for searching calls or statistics.

    Attributes:
        filter (list[SearchFilter]): List of filters to apply
        pageSize (int): Number of items to return per page
        pageIndex (int): Page index to retrieve
    """

    filter: list[SearchFilter]
    pageSize: int
    pageIndex: int


class FilterRequest(BaseModel, Generic[T]):
    """
    Filter request.
    """

    filter: T
    sortBy: SortBy | None = None
    pageSize: int = 10
    pageIndex: int = 0


class PlainTextResponse(BaseModel):
    """
    Response model for plain text.
    """

    text: str


class BatchIdsRequest(BaseModel):
    """
    Batch ids request.
    """

    ids: list[str]


class EmailRequest(BaseModel):
    """
    Email request.
    """

    email: str