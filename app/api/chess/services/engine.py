from app.ai.prediction import predict_move
from app.api.chess.services.piece import Bishop, ChessPiece, King, Knight, Pawn, Queen, Rook


class ChessEngine:
    PIECE_MAP = {
        'p': Pawn, 'n': Knight, 'b': Bishop, 'r': Rook, 'q': Queen, 'k': King,
        'P': Pawn, 'N': Knight, 'B': Bishop, 'R': Rook, 'Q': Queen, 'K': King,
    }
    
    def __init__(self):
        self.board: list[list[ChessPiece | None]] = [[None for _ in range(8)] for _ in range(8)]
        self.turn: str = "white"
        self.winner: str | None = None
        self.pawn_promotion: ChessPiece | None = None
        self.initialize_board()

    @classmethod
    def from_fen(cls, fen: str) -> "ChessEngine":
        engine = cls.__new__(cls)
        engine.board = [[None for _ in range(8)] for _ in range(8)]
        engine.winner = None
        engine.pawn_promotion = None
        
        parts = fen.split(' ')
        board_fen = parts[0]
        turn_fen = parts[1] if len(parts) > 1 else 'w'
        
        engine.turn = "white" if turn_fen == 'w' else "black"
        
        rows = board_fen.split('/')
        for y, row in enumerate(rows):
            x = 0
            for char in row:
                if char.isdigit():
                    x += int(char)
                else:
                    color = "white" if char.isupper() else "black"
                    piece_class = cls.PIECE_MAP.get(char)
                    if piece_class:
                        piece = piece_class(color, [x, y])
                        piece.has_moved = True
                        engine.board[x][y] = piece
                    x += 1
        
        return engine

    def reset(self):
        self.turn = "white"
        self.winner = None
        self.pawn_promotion = None
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_board()

    def initialize_board(self):
        for x in range(8):
            self.board[x][6] = Pawn("white", [x, 6])
            self.board[x][1] = Pawn("black", [x, 1])
        back_row = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for x, piece_class in enumerate(back_row):
            self.board[x][7] = piece_class("white", [x, 7])
            self.board[x][0] = piece_class("black", [x, 0])

    def make_ai_move(self) -> str | None:
        if self.winner:
            return None
        if self.pawn_promotion:
            raise ValueError("Awaiting promotion")
        ai_move = predict_move(self)
        return ai_move

    def get_piece_at(self, x: int, y: int) -> ChessPiece | None:
        if 0 <= x < 8 and 0 <= y < 8:
            return self.board[x][y]
        return None

    def is_empty(self, x: int, y: int):
        return self.get_piece_at(x, y) is None

    def is_enemy_piece(self, color: str, x: int, y: int):
        piece = self.get_piece_at(x, y)
        return piece and piece.color != color

    def filter_valid_moves(self, piece: ChessPiece, moves: list[list[int, int]]):
        valid_moves = []
        for x, y in moves:
            if 0 <= x < 8 and 0 <= y < 8:
                target_piece = self.get_piece_at(x, y)
                if not target_piece or target_piece.color != piece.color:
                    valid_moves.append([x, y])
        return valid_moves

    def get_straight_moves(self, piece: ChessPiece):
        directions = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        return self.get_moves_in_directions(piece, directions)

    def get_diagonal_moves(self, piece: ChessPiece):
        directions = [[-1, -1], [1, 1], [-1, 1], [1, -1]]
        return self.get_moves_in_directions(piece, directions)

    def get_moves_in_directions(self, piece: ChessPiece, directions: list[list[int]]) -> list[list[int]]:
        moves = []
        x, y = piece.position
        for dx, dy in directions:
            nx, ny = x, y
            while True:
                nx += dx
                ny += dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    target_piece = self.get_piece_at(nx, ny)
                    if not target_piece:
                        moves.append([nx, ny])
                    elif target_piece.color != piece.color:
                        moves.append([nx, ny])
                        break
                    else:
                        break
                else:
                    break
        return moves

    def is_position_attacked(self, position: list[int, int], color: str):
        opponent_color = "black" if color == "white" else "white"
        for x in range(8):
            for y in range(8):
                piece = self.get_piece_at(x, y)
                if piece and piece.color == opponent_color:
                    if position in piece.possible_moves(self, is_attacking=True):
                        return True
        return False

    def find_king(self, color: str) -> King | None:
        for x in range(8):
            for y in range(8):
                piece = self.get_piece_at(x, y)
                if isinstance(piece, King) and piece.color == color:
                    return piece
        return None

    def can_castle(self, color: str, side: str) -> bool:
        king = self.find_king(color)
        if king is None or king.has_moved:
            return False
        rook = self.get_piece_at(7, king.position[1]) if side == "king" else self.get_piece_at(0, king.position[1])
        if not isinstance(rook, Rook) or rook.color != color or rook.has_moved:
            return False
        start = min(king.position[0], rook.position[0]) + 1
        end = max(king.position[0], rook.position[0])
        for x in range(start, end):
            if not self.is_empty(x, king.position[1]):
                return False
        return True

    def get_legal_moves(self) -> list[list[list[int, int]]]:
        legal_moves: list[list[list[int, int]]] = []
        for x in range(8):
            for y in range(8):
                piece = self.get_piece_at(x, y)
                if piece is not None and piece.color == self.turn:
                    possible_moves = piece.possible_moves(self)
                    for move in possible_moves:
                        nx, ny = move
                        legal_moves.append([[x, y], [nx, ny]])
        return legal_moves
