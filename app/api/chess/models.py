from app.api.chess.dto import PlayerColor
from app.api.chess.schemas import PendingPromotion, PieceSchema
from app.core.database import MongoBaseModel


class ChessGameModel(MongoBaseModel):
    board: list[list[PieceSchema | None]]
    turn: PlayerColor = PlayerColor.WHITE
    winner: PlayerColor | None = None
    pendingPromotion: PendingPromotion | None = None
    aiEnabled: bool = True
    playerColor: PlayerColor = PlayerColor.WHITE
    lastAIMove: str | None = None

