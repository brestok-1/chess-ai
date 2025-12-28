from fastapi import APIRouter

chess_router = APIRouter(
    prefix="/api/chess",
)

from . import views

