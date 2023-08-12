from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.schemas.game_answer_schema import GameAnswerSchema
from app.schemas.game_question_schema import NextQuestionResponse
from app.schemas.game_schema import (
    FinalResultsResponse,
    GameResponse,
    GameStartSchema,
    StartGameResponse,
)
from app.schemas.paginate_schema import PaginateSchema
from app.schemas.responses import UserResponse
from app.services.game import (
    service_answer_question,
    service_get_games,
    service_get_results,
    service_next_question,
    service_skip_question,
    service_start,
)
from app.services.paginate import Paginate, pagination_parameters

router = APIRouter()


@router.get("/", response_model=Paginate[GameResponse])
async def get_user_games(
    pagination: PaginateSchema = Depends(pagination_parameters),
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
         Lists of all games for user
    :param pagination: offset
    :param current_user: user_id for filtering
    :param session: db session
    :return: games played by user
    :rtype: dict
    """

    return await service_get_games(
        session, current_user.id, pagination.limit, pagination.offset
    )


@router.post("/start", response_model=StartGameResponse)
async def start_game(
    game_body: GameStartSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Start a new game from quiz
    """
    return await service_start(session, game_body, current_user.id)


@router.get("/{game_id}/questions/next", response_model=NextQuestionResponse)
async def next_question(
    game_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Retrieves next question, returns same if question is not answered or skipped.
    """
    return await service_next_question(session, game_id, current_user.id)


@router.post("/{game_id}/questions/{question_id}/submit", status_code=204)
async def answer_question(
    game_id: UUID4,
    question_id: UUID4,
    answer_data: GameAnswerSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Answer a question
    """
    return await service_answer_question(
        session, answer_data, game_id, question_id, current_user.id
    )


@router.post("/{game_id}/questions/{question_id}/skip", status_code=204)
async def skip_question(
    game_id: UUID4,
    question_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Skip question
    """
    return await service_skip_question(session, game_id, question_id, current_user.id)


@router.get("/{game_id}/results", response_model=FinalResultsResponse)
async def get_results(
    game_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get final results
    """
    return await service_get_results(session, game_id, current_user.id)
