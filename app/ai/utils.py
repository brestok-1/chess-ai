import numpy as np
from chess import Board

from app.chess.piece import ChessPiece

def board_to_matrix(chess):
    matrix = np.zeros((13, 8, 8))
    for x in range(8):
        for y in range(8):
            piece: ChessPiece = chess.board[x][y]
            if piece is not None:
                piece_color = 0 if piece.color == 'white' else 6
                piece_type = piece.piece_type
                row = 7 - y
                matrix[piece_type + piece_color, row, x] = 1

    legal_moves = chess.get_legal_moves()
    for (_, _), (to_x, to_y) in legal_moves:
        row_to = 7 - to_y
        matrix[12, row_to, to_x] = 1
    return matrix


if __name__ == "__main__":
    board_ = Board()
    t = board_to_matrix(board_)
    print(t)