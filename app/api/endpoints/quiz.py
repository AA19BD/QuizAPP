from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.schemas.game_schema import GameDetailResponse, QuizGamesResponse
from app.schemas.paginate_schema import PaginateSchema
from app.schemas.quiz_schema import (
    QuizCreateResponse,
    QuizResponse,
    QuizSchema,
    UpdateQuizSchema,
)
from app.schemas.responses import UserResponse
from app.services.paginate import Paginate, pagination_parameters
from app.services.quiz import (
    service_create_quiz,
    service_delete_quiz,
    service_get_quiz_details,
    service_get_quiz_game_details,
    service_get_quiz_games,
    service_get_quizzes,
    service_publish_quiz,
    service_update_quiz,
)

router = APIRouter()


@router.post("/", response_model=QuizCreateResponse)
async def create_quiz(
    quiz_data: QuizSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create empty quiz
    """
    return await service_create_quiz(session, quiz_data, current_user.id)


@router.get("/", response_model=Paginate[QuizResponse])
async def get_user_quizzes(
    pagination: PaginateSchema = Depends(pagination_parameters),
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create empty quiz
    """
    return await service_get_quizzes(
        session, current_user.id, pagination.limit, pagination.offset
    )


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz_details(
    quiz_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Retrieve Quiz Details
    """

    quiz = await service_get_quiz_details(session, quiz_id, current_user.id)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz.__dict__


@router.patch("/{quiz_id}/publish", status_code=204)
async def publish_quiz(
    quiz_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Publish quiz
    """
    return await service_publish_quiz(session, quiz_id, current_user.id)


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(
    quiz_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete quiz
    """
    return await service_delete_quiz(session, quiz_id, current_user.id)


@router.patch("/{quiz_id}", status_code=204)
async def update_quiz(
    quiz_id: UUID4,
    quiz_data: UpdateQuizSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update quiz
    """
    return await service_update_quiz(session, quiz_id, quiz_data, current_user.id)


@router.get("/{quiz_id}/games", response_model=Paginate[QuizGamesResponse])
async def get_quiz_games(
    quiz_id: UUID4,
    pagination: PaginateSchema = Depends(pagination_parameters),
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get lis of quiz games
    """
    return await service_get_quiz_games(
        session, quiz_id, current_user.id, pagination.limit, pagination.offset
    )


@router.get("/{quiz_id}/games/{game_id}", response_model=GameDetailResponse)
async def get_quiz_game_details(
    quiz_id: UUID4,
    game_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get detailed info about quiz game
    """
    return await service_get_quiz_game_details(
        session, quiz_id, game_id, current_user.id
    )
