from fastapi import HTTPException

from app.api.chess.dto import PlayerColor
from app.api.chess.models import ChessGameModel
from app.api.chess.schemas import ChessGameState, CreateGameRequest, MoveRequest, PromoteRequest
from app.api.chess.services.engine import ChessEngine
from app.api.chess.utils import BackendUtils
from app.api.common.db_requests import get_obj_by_id
from app.core.config import settings

utils = BackendUtils()


async def create_game_obj(request: CreateGameRequest) -> ChessGameState:
    engine = ChessEngine()
    last_ai_move = None
    if request.playerColor == PlayerColor.BLACK and request.aiEnabled:
        last_ai_move = engine.make_ai_move()
    game = ChessGameModel(
        board=engine.board_as_schema(),
        turn=PlayerColor(engine.turn),
        winner=PlayerColor(engine.winner) if engine.winner else None,
        pendingPromotion=engine.pending_promotion_schema(),
        aiEnabled=request.aiEnabled,
        playerColor=request.playerColor,
        lastAIMove=last_ai_move,
    )
    await settings.DB_CLIENT.chessgames.insert_one(game.to_mongo())
    return utils.build_state(
        game.id,
        game.board,
        game.turn,
        game.winner,
        game.pendingPromotion,
        game.aiEnabled,
        game.playerColor,
        last_ai_move,
        utils.convert_moves_to_uci(engine.get_legal_moves()),
    )


def engine_from_game(game: ChessGameModel) -> ChessEngine:
    return ChessEngine(
        board_state=game.board,
        turn=game.turn,
        winner=game.winner,
        pending_promotion=game.pendingPromotion,
    )


async def persist_game(game: ChessGameModel, engine: ChessEngine, last_ai_move: str | None) -> ChessGameState:
    game.board = engine.board_as_schema()
    game.turn = PlayerColor(engine.turn)
    game.winner = PlayerColor(engine.winner) if engine.winner else None
    game.pendingPromotion = engine.pending_promotion_schema()
    game.lastAIMove = last_ai_move
    await settings.DB_CLIENT.chessgames.update_one({"id": game.id}, {"$set": game.to_mongo()})
    return utils.build_state(
        game.id,
        game.board,
        game.turn,
        game.winner,
        game.pendingPromotion,
        game.aiEnabled,
        game.playerColor,
        last_ai_move,
        utils.convert_moves_to_uci(engine.get_legal_moves()),
    )


async def get_game_state_obj(game_id: str) -> ChessGameState:
    game = await get_obj_by_id(ChessGameModel, game_id)
    engine = engine_from_game(game)
    return utils.build_state(
        game.id,
        game.board,
        game.turn,
        game.winner,
        game.pendingPromotion,
        game.aiEnabled,
        game.playerColor,
        game.lastAIMove,
        utils.convert_moves_to_uci(engine.get_legal_moves()),
    )


async def player_move_obj(game_id: str, request: MoveRequest) -> ChessGameState:
    game = await get_obj_by_id(ChessGameModel, game_id)
    engine = engine_from_game(game)
    if game.aiEnabled and game.playerColor.value != engine.turn:
        raise HTTPException(status_code=400, detail="It is not the player's turn")
    try:
        engine.apply_move(request.move, request.promotion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return await persist_game(game, engine, game.lastAIMove)


async def promote_pawn_obj(game_id: str, request: PromoteRequest) -> ChessGameState:
    game = await get_obj_by_id(ChessGameModel, game_id)
    engine = engine_from_game(game)
    if engine.pawn_promotion is None:
        raise HTTPException(status_code=400, detail="No pawn promotion pending")
    engine.promote_pawn(request.piece)
    return await persist_game(game, engine, game.lastAIMove)


async def ai_move_obj(game_id: str) -> ChessGameState:
    game = await get_obj_by_id(ChessGameModel, game_id)
    if not game.aiEnabled:
        raise HTTPException(status_code=400, detail="AI is disabled for this game")
    engine = engine_from_game(game)
    if engine.turn == game.playerColor.value:
        raise HTTPException(status_code=400, detail="It is the player's turn")
    try:
        ai_move = engine.make_ai_move()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return await persist_game(game, engine, ai_move or game.lastAIMove)


async def reset_game_obj(game_id: str) -> ChessGameState:
    game = await get_obj_by_id(ChessGameModel, game_id)
    engine = ChessEngine()
    last_ai_move = None
    if game.playerColor == PlayerColor.BLACK and game.aiEnabled:
        last_ai_move = engine.make_ai_move()
    game.board = engine.board_as_schema()
    game.turn = PlayerColor(engine.turn)
    game.winner = None
    game.pendingPromotion = None
    game.lastAIMove = last_ai_move
    await settings.DB_CLIENT.chessgames.update_one({"id": game.id}, {"$set": game.to_mongo()})
    return utils.build_state(
        game.id,
        game.board,
        game.turn,
        game.winner,
        game.pendingPromotion,
        game.aiEnabled,
        game.playerColor,
        last_ai_move,
        utils.convert_moves_to_uci(engine.get_legal_moves()),
    )

