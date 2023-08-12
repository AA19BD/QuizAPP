from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.schemas.question_schema import (
    QuestionResponse,
    QuestionsSchema,
    UpdateQuestionSchema,
)
from app.schemas.responses import UserResponse
from app.services.paginate import Paginate
from app.services.question import (
    service_add_questions,
    service_delete_question,
    service_get_questions,
    service_update_question,
)

router = APIRouter()


@router.get("/", response_model=Paginate[QuestionResponse])
async def get_questions(
    quiz_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get questions from quiz
    """
    return await service_get_questions(session, quiz_id, current_user.id)


@router.post("/", status_code=204)
async def add_questions(
    quiz_id: UUID4,
    question_data: QuestionsSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Add questions to quiz
    """
    print("falling here 1")
    return await service_add_questions(session, quiz_id, question_data, current_user.id)


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    quiz_id: UUID4,
    question_id: UUID4,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete question from quiz
    """
    return await service_delete_question(session, quiz_id, question_id, current_user.id)


@router.patch("/{question_id}", status_code=204)
async def update_question(
    quiz_id: UUID4,
    question_id: UUID4,
    question_data: UpdateQuestionSchema,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update question in quiz
    """
    return await service_update_question(
        session, quiz_id, question_id, question_data, current_user.id
    )
