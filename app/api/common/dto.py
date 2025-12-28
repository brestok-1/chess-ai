"""
Common DTOs.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Paging(BaseModel):
    """
    Pagination model for API responses.
    """

    pageSize: int
    pageIndex: int
    totalCount: int


class SearchFilter(BaseModel):
    """
    Search filter model for constructing database queries.

    Attributes:
        name (str): Field name to filter on
        value (str | int): Value to search for
    """

    name: str
    value: str | int


class Scores(BaseModel):
    """
    Scores for the recording.
    """

    communication: int = Field(
        description="Speech professionalism assessment: clarity of presentation, absence of filler words, literacy, 1-100",
    )

    activeListening: int = Field(
        description="Active listening skills: ability to ask clarifying questions, respond to client signals, 1-100",
    )

    conversation: int = Field(
        description="Conversation control: ability to direct conversation, adhere to sales structure, 1-100",
    )

    objection: int = Field(
        description="Objection handling: ability to correctly respond to client doubts and overcome obstacles, 1-100",
    )

    empathy: int = Field(
        description="Emotional intelligence: adaptation to client mood, empathy, building rapport, 1-100",
    )

    final: int = Field(
        description="Overall score: score of completion of conversation, 1-100",
    )

    def __sub__(self, other: "Scores") -> "Scores":
        return Scores(
            communication=self.communication - other.communication,
            activeListening=self.activeListening - other.activeListening,
            conversation=self.conversation - other.conversation,
            objection=self.objection - other.objection,
            empathy=self.empathy - other.empathy,
            final=self.final - other.final,
        )

    def __mod__(self, other: "Scores") -> "Scores":
        def calc_percentage_diff(current: int, previous: int) -> int:
            if previous == 0:
                return 0
            return int(((current - previous) / previous) * 100)

        return Scores(
            communication=calc_percentage_diff(self.communication, other.communication),
            activeListening=calc_percentage_diff(self.activeListening, other.activeListening),
            conversation=calc_percentage_diff(self.conversation, other.conversation),
            objection=calc_percentage_diff(self.objection, other.objection),
            empathy=calc_percentage_diff(self.empathy, other.empathy),
            final=calc_percentage_diff(self.final, other.final),
        )


class DateValue(BaseModel):
    """
    Date value.
    """

    date: datetime
    value: int


class ValueDelta(BaseModel):
    """
    Value delta.
    """

    value: int
    delta: int


class IDName(BaseModel):
    id: str | int
    name: str


class OrderType(Enum):
    """
    Order type.
    """

    ASCENDING = 1
    DESCENDING = -1


class SortBy(BaseModel):
    """
    Sort by.
    """

    name: str
    order: OrderType


class ScenarioPerformanceMistake(BaseModel):
    name: str
    description: str
    occurrences: int


class TokenUsage(BaseModel):
    inputTokens: int
    outputTokens: int
