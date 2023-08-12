from fastapi import HTTPException
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Answer, Question, Quiz
from app.schemas.question_schema import (
    QuestionsSchema,
    QuestionTypeEnum,
    UpdateQuestionSchema,
)


async def paginate_questions(
    session: AsyncSession, quiz_id: UUID4, offset: int
) -> Question:
    """
    Retrieves questions one by one
    Args:
        offset:
        session: db session
        quiz_id: quiz id

    Returns:
        sqlalchemy Questions object

    """
    stmt = select(Question).where(Question.quiz_id == quiz_id).limit(1).offset(offset)
    result = await session.execute(stmt)
    question = result.scalar()

    return question
    # return await session.execute(stmt.scalar())


async def get_question(session: AsyncSession, question_id: UUID4) -> Question:
    """
    Retrieves detailed info about question
    Args:
        session: sqlalchemy session
        question_id: question id

    Returns:
        sqlalchemy Question object

    """
    stmt = select(Question).where(Question.id == question_id)

    question = await session.execute(stmt)
    unique_questions = question.unique().scalars().all()

    # print("get_question func", unique_questions[0])
    # question_row = unique_questions.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=400, detail="Question not found")

    return unique_questions[0]


async def service_get_questions(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4
) -> dict:
    """
    Retrieves questions from quiz
    Args:
        session: db session
        quiz_id: quiz id
        user_id: authenticated user id

    Returns:

    """
    quiz = await get_quiz_for_user(session, quiz_id, user_id)

    stmt = select(Question).where(Question.quiz_id == quiz.id)

    questions = await session.execute(stmt)

    items = [
        {
            "id": question.id,
            "title": question.title,
            "type": question.type,
            "answers": [answer.__dict__ for answer in question.answers],
        }
        for question in questions.unique().scalars().all()
    ]

    return {
        "total_count": len(items),
        "limit": len(items),
        "offset": 0,
        "items": items,
    }


async def get_quiz_for_user(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4
) -> Quiz:
    """
    Retrieves quiz created by user
    Args:
        session: sqlalchemy session
        quiz_id: quiz id
        user_id: authenticated user id

    Returns:
        sqlalchemy Quiz object

    """
    stmt = (
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .where(Quiz.user_id == user_id)
        .where(~Quiz.deleted)
    )

    quiz = await session.execute(stmt)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz.all()[0][0]


async def service_add_questions(
    session: AsyncSession,
    quiz_id: UUID4,
    questions_data: QuestionsSchema,
    user_id: UUID4,
) -> None:
    """
    Adds questions to already created unpublished quiz
    Args:
        session: db session
        quiz_id: quiz id
        questions_data: questions data
        user_id: authenticated user id

    Returns:

    """

    quiz = await get_quiz_for_user(session, quiz_id, user_id)

    if quiz.published:
        raise HTTPException(
            status_code=400,
            detail="Can't add questions to already published quiz",
        )

    if len(questions_data.questions) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of questions per quiz is 10",
        )

    for question_data in questions_data.questions:
        await validate_answers(question_data.answers, question_data.type)
        question = Question(
            title=question_data.title,
            type=question_data.type.value,
            quiz_id=quiz.id,
            answers=[
                Answer(value=answer.value, is_correct=answer.is_correct)
                for answer in question_data.answers
            ],
        )
        session.add(question)
    await session.commit()


async def validate_answers(answers: list, question_type: QuestionTypeEnum):
    correct_answers = 0
    for answer in answers:
        if answer.is_correct:
            correct_answers += 1
    if question_type == QuestionTypeEnum.SINGLE_ANSWER and correct_answers > 1:
        raise HTTPException(
            status_code=400,
            detail=f"{question_type.value} can't have multiple correct answers",
        )
    if correct_answers == 0:
        raise HTTPException(
            status_code=400,
            detail="There must be at least one correct answer",
        )


async def service_delete_question(
    session: AsyncSession, quiz_id: UUID4, question_id: UUID4, user_id: UUID4
) -> None:
    """
    Deletes question from quiz if quiz is not published
    Args:
        session: db session
        quiz_id: quiz id
        question_id: question id
        user_id: authenticated user id

    Returns:

    """
    quiz = await get_quiz_for_user(session, quiz_id, user_id)

    if quiz.published:
        raise HTTPException(
            status_code=400, detail="Can't delete question from published quiz"
        )
    question = await get_question(session, question_id)

    await session.delete(question)
    await session.commit()


async def service_update_question(
    session: AsyncSession,
    quiz_id: UUID4,
    question_id: UUID4,
    question_data: UpdateQuestionSchema,
    user_id: UUID4,
) -> None:
    """
    Deletes question from quiz if quiz is not published
    Args:
        session: db session
        quiz_id: quiz id
        question_id: question id
        question_data: Question Data
        user_id: authenticated user id

    Returns:

    """
    quiz = await get_quiz_for_user(session, quiz_id, user_id)
    if quiz.published:
        raise HTTPException(
            status_code=400, detail="Can't update question from published quiz"
        )
    question = await get_question(session, question_id)
    if question_data.type and question_data.answers:
        await validate_answers(question_data.answers, question_data.type)
        question.answers = [
            Answer(value=answer.value, is_correct=answer.is_correct)
            for answer in question_data.answers
        ]
        question.type = question_data.type.value
    elif question_data.type and question_data.type != question.type:
        await validate_answers(question.answers, question_data.type)
        question.type = question_data.type.value
    elif question_data.answers:
        await validate_answers(question_data.answers, QuestionTypeEnum[question.type])
        question.answers = [
            Answer(value=answer.value, is_correct=answer.is_correct)
            for answer in question_data.answers
        ]
    if question_data.title:
        question.title = question_data.title
    await session.commit()
