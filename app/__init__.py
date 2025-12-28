from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()

    from app.api.chess import chess_router

    app.include_router(chess_router, tags=["chess"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def read_root():
        return {"status": "Chess AI API is running"}

    return app
