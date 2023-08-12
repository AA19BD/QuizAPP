from fastapi import APIRouter

from app.api.endpoints import auth, game, question, quiz, users
from app.core import config

api_router = APIRouter()
version = config.settings.APP_VERSION


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

api_router.include_router(game.router, prefix=f"/api/{version}/games", tags=["Games"])
api_router.include_router(
    question.router, prefix="/api/v1/quizzes/{quiz_id}/questions", tags=["Questions"]
)
api_router.include_router(
    quiz.router, prefix=f"/api/{version}/quizzes", tags=["Quizzes"]
)
