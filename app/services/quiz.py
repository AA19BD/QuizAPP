from fastapi import HTTPException
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Game, GameQuestion, Question, Quiz, User
from app.schemas.quiz_schema import QuizSchema, UpdateQuizSchema


async def get_quiz(session: AsyncSession, quiz_id: UUID4) -> Quiz:
    """
    Retrieves quiz by id
    Args:
        session: sqlalchemy session
        quiz_id: quiz id

    Returns:
        sqlalchemy Quiz object

    """
    stmt = select(Quiz).where((Quiz.id == quiz_id) & (~Quiz.deleted))

    result = await session.execute(stmt)
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


async def service_create_quiz(
    session: AsyncSession, quiz_data: QuizSchema, user_id: UUID4
) -> dict:
    """
    Creates empty quiz
    Args:
        session: db session
        quiz_data: quiz data
        user_id: authenticated user id

    Returns:
        dict: containing quiz id

    """
    quiz = Quiz(title=quiz_data.title, published=False, user_id=user_id)
    session.add(quiz)
    await session.commit()
    return {"id": quiz.id}


async def service_get_quizzes(
    session: AsyncSession, user_id: UUID4, limit: int, offset: int
) -> dict:
    """
    Retrieves quizzes created by user
    Args:
        session: db session
        user_id: authenticated user id
        limit: limit
        offset: offset

    Returns:
        list of Quiz objects

    """
    query = select(Quiz.id, Quiz.title, Quiz.published, Quiz.created_at).where(
        (Quiz.user_id == user_id) & (~Quiz.deleted)
    )

    total_count = await session.execute(query)
    quizzes = await session.execute(query.limit(limit).offset(offset))
    quizzes_list = quizzes.all()

    result = [
        {
            "id": str(item[0]),
            "title": item[1],
            "published": item[2],
            "created_at": item[3].isoformat(),
        }
        for item in quizzes_list
    ]

    return {
        "total_count": len(total_count.all()),
        "limit": limit,
        "offset": offset,
        "items": result,
    }


async def service_get_quiz_details(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4
) -> Quiz:
    """
    Retrieves quiz created by user
    Args:
        session: db session
        quiz_id: quiz id
        user_id: authenticated user id

    Returns:
        sqlalchemy Quiz object

    """
    return await service_get_quiz_for_user(session, quiz_id, user_id)


async def service_get_quiz_for_user(
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
    stmt = select(Quiz).where(
        (Quiz.id == quiz_id) & (Quiz.user_id == user_id) & (~Quiz.deleted)
    )

    result = await session.execute(stmt)
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz


async def service_publish_quiz(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4
) -> None:
    """
    Updates quiz row as published in db
    Args:
        quiz_id: quiz id
        user_id: authenticated user id

    Returns:
    :param user_id:
    :param quiz_id:
    :param session:

    """
    quiz = await service_get_quiz_for_user(session, quiz_id, user_id)

    quiz.published = True
    await session.commit()


async def service_delete_quiz(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4
) -> None:
    """
    Updates quiz row as deleted in db
    Args:
        session: db session
        quiz_id: quiz id
        user_id: authenticated user id

    Returns:

    """
    quiz = await service_get_quiz_for_user(session, quiz_id, user_id)
    quiz.deleted = True
    await session.commit()


async def service_update_quiz(
    session: AsyncSession,
    quiz_id: UUID4,
    quiz_data: UpdateQuizSchema,
    user_id: UUID4,
) -> None:
    """
    Updates quiz row as deleted in db
    Args:
        session: db session
        quiz_id: quiz id
        quiz_data: quiz data
        user_id: authenticated user id

    Returns:

    """
    quiz = await service_get_quiz_for_user(session, quiz_id, user_id)
    if quiz.published:
        raise HTTPException(status_code=400, detail="Can't update published quiz")
    quiz.title = quiz_data.title
    await session.commit()


async def service_get_quiz_games(
    session: AsyncSession, quiz_id: UUID4, user_id: UUID4, limit: int, offset: int
) -> dict:
    """
    Retrieves games played in the quiz
    Args:
        session: db session
        quiz_id: quiz id
        user_id: authenticated user id
        limit: limit
        offset: offset

    Returns:
        list of games played in the quiz

    """
    quiz = await service_get_quiz_for_user(session, quiz_id, user_id)

    stmt = (
        select(
            Game.id,
            Game.finished,
            Game.score,
            Game.quiz_id,
            Game.user_id,
            Quiz.title,
        )
        .join(Quiz, Game.quiz_id == Quiz.id)
        .join(User, Game.user_id == User.id)
        .where(Game.quiz_id == quiz.id)
    )

    total_count = await session.execute(stmt)
    games = await session.execute(stmt.limit(limit).offset(offset))
    games_list = games.all()

    result = [
        {
            "id": str(item[0]),
            "finished": item[1],
            "score": item[2],
            "quiz_id": item[3],
            "user_id": item[4],
            "title": item[5],
        }
        for item in games_list
    ]

    return {
        "total_count": len(total_count.all()),
        "limit": limit,
        "offset": offset,
        "items": result,
    }


async def service_get_quiz_game_details(
    session: AsyncSession, quiz_id: UUID4, game_id: UUID4, user_id: UUID4
):
    """
    Retrieves detailed info about quiz game
    Args:
        session: db session
        quiz_id: quiz id
        game_id: game id
        user_id: authenticated user id

    Returns:
        stats about single question

    """
    quiz = await service_get_quiz_for_user(session, quiz_id, user_id)
    stmt = (
        select(GameQuestion.answer_score, Question.title)
        .join(Question, Question.id == GameQuestion.question_id)
        .where(GameQuestion.game_id == game_id)
        .where(Question.quiz_id == quiz.id)
    )

    question_stats = await session.execute(stmt)
    formated_question_stats = [
        {"answer_score": answer_score, "title": title}
        for answer_score, title in question_stats.all()
    ]

    return {
        "question_stats": formated_question_stats,
    }
