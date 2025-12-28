from enum import Enum


class PlayerColor(str, Enum):
    WHITE = "white"
    BLACK = "black"


class PieceType(str, Enum):
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"

