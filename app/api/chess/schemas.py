from typing import Optional

from pydantic import BaseModel


class AIMoveRequest(BaseModel):
    fen: str


class AIMoveResponse(BaseModel):
    move: Optional[str] = None
    from_square: Optional[str] = None
    to_square: Optional[str] = None
    promotion: Optional[str] = None
    error: Optional[str] = None
