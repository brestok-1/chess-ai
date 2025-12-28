from app.api.chess import chess_router
from app.api.chess.schemas import AIMoveRequest, AIMoveResponse
from app.api.chess.services.engine import ChessEngine


@chess_router.post("/ai-move")
async def get_ai_move(request: AIMoveRequest) -> AIMoveResponse:
    try:
        engine = ChessEngine.from_fen(request.fen)
        ai_move = engine.make_ai_move()
        
        if ai_move is None:
            return AIMoveResponse(error="No valid move found")
        
        from_square = ai_move[:2]
        to_square = ai_move[2:4]
        promotion = ai_move[4] if len(ai_move) > 4 else None
        
        return AIMoveResponse(
            move=ai_move,
            from_square=from_square,
            to_square=to_square,
            promotion=promotion
        )
    except Exception as e:
        return AIMoveResponse(error=str(e))
