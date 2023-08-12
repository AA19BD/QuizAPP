from fastapi import HTTPException
from pydantic import UUID4
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Answer, Game, GameAnswer, GameQuestion, Question, Quiz
from app.schemas.game_answer_schema import GameAnswerSchema
from app.schemas.game_schema import GameStartSchema
from app.schemas.question_schema import QuestionTypeEnum
from app.services.question import get_question, paginate_questions
from app.services.quiz import get_quiz


async def service_get_games(
    session: AsyncSession, user_id: UUID4, limit: int, offset: int
) -> dict:
    """
        Lists of all games for user
    :param session: db session
    :param user_id: user_id for filtering
    :param limit:
    :param offset:
    :return: games played by user
    """

    stmt1 = (
        select(Quiz.title, Game.id, Game.finished, Game.created_at)
        .join(Quiz.games)
        .where(Game.user_id == user_id)
    )

    stmt2 = (
        select(Quiz.title, Game.id, Game.finished, Game.created_at)
        .join(Quiz.games)
        .where(Game.user_id == user_id)
    )

    total_count = await session.execute(stmt1)
    games = await session.execute(stmt2.limit(limit).offset(offset))

    game_items = [
        {
            "id": str(game_id),
            "title": title,
            "finished": finished,
            "created_at": created_at.isoformat(),
        }
        for title, game_id, finished, created_at in games.all()
    ]

    return {
        "total_count": len(total_count.all()),
        "limit": limit,
        "offset": offset,
        "items": game_items,
    }


async def service_start(
    session: AsyncSession, game_body: GameStartSchema, user_id: UUID4
) -> dict:
    """
    Creates empty game with default values
    Args:
        session: db session
        game_body: payload containing quiz_id
        user_id: authenticated user id

    Returns:
        id of started game

    """
    quiz = await get_quiz(session, game_body.quiz_id)
    if quiz.deleted or not quiz.published:
        raise HTTPException(status_code=404, detail="Quiz not found")

    stmt = (
        select(Game)
        .where(Game.quiz_id == game_body.quiz_id)
        .where(Game.user_id == user_id)
    )

    existing_game = await session.execute(stmt)

    if not existing_game.all():
        new_game = Game(
            finished=False,
            score=0,
            offset=0,
            quiz_id=game_body.quiz_id,
            user_id=user_id,
        )
        session.add(new_game)
        await session.commit()
        return {"id": new_game.id}

    if existing_game.scalar().finished:
        raise HTTPException(status_code=400, detail="You already played this game")

    return {"id": existing_game.scalar().id}


async def service_next_question(
    session: AsyncSession, game_id: UUID4, user_id: UUID4
) -> dict:
    """
    Retrieves next question to answer from quiz, if not answered or skipped always returns same
    Args:
        session: db session
        game_id: game id
        user_id: authenticated user id

    Returns:
        questions details if there is next questions, otherwise raises error

    """
    game = await get_game(session, game_id, user_id)
    if game.finished:
        raise HTTPException(status_code=400, detail="Game is already finished")

    question = await paginate_questions(session, game.quiz_id, game.offset)

    if not question:
        await session.execute(
            update(Game).where(Game.id == game.id).values(finished=True)
        )
        await session.commit()
        raise HTTPException(status_code=400, detail="Game is already finished")

    game_question_stmt = (
        select(GameQuestion)
        .where(GameQuestion.question_id == question.id)
        .where(GameQuestion.game_id == game_id)
    )

    game_question = await session.execute(game_question_stmt)
    game_question_result = game_question.unique().scalars().first()

    if not game_question_result:
        new_game_question = GameQuestion(
            answered=False,
            skipped=False,
            game_id=game_id,
            question_id=question.id,
        )
        session.add(new_game_question)
        await session.commit()

    return {
        "id": game_question_result.id,
        "type": question.type,
        "title": question.title,
        "answers": [answer.__dict__ for answer in question.answers],
    }


async def get_game(session: AsyncSession, game_id: UUID4, user_id: UUID4) -> Game:
    """
    Retrieves game by game id
    Args:
        session: sqlalchemy session
        game_id: game id
        user_id: authenticated user id

    Returns:
        sqlalchemy Game object

    """
    stmt = (
        select(Game)
        .where(Game.id == game_id)
        .where(Game.user_id == user_id)
        .join(Quiz.games)
    )

    game = await session.execute(stmt)
    game_list = game.scalars().all()

    if not game_list:
        raise HTTPException(status_code=404, detail="Game not found")

    return game_list[0]


async def service_answer_question(
    session: AsyncSession,
    answer_data: GameAnswerSchema,
    game_id: UUID4,
    question_id: UUID4,
    user_id: UUID4,
) -> None:
    """
    Saves info about answered question
    Args:
        session: db session
        answer_data: user sent data
        game_id: game id
        question_id: question id
        user_id: authenticated user id

    Returns:

    """
    game = await get_game(session, game_id, user_id)
    game_question = await get_game_question(session, game_id, question_id)
    await check_question_answered_or_skipped(game_question)
    question = await get_question(session, game_question.question_id)

    if question.type == QuestionTypeEnum.SINGLE_ANSWER.value:
        if len(answer_data.choices) > 1:
            raise HTTPException(
                status_code=400,
                detail=f"{question.type} does not support multiple answers",
            )

    score = await calculate_answer_score(
        answer_data.choices, question.answers, question.type
    )

    await session.execute(
        update(Game)
        .where(Game.id == game.id)
        .values(score=game.score + score, offset=game.offset + 1)
    )

    game_question.answer_score = score
    game_question.answered = True

    for choice in answer_data.choices:
        game_answer = GameAnswer(choice=str(choice), game_question_id=game_question.id)
        session.add(game_answer)

    await session.commit()


async def get_game_question(
    session: AsyncSession, game_id: UUID4, question_id: UUID4
) -> GameQuestion:
    """
    Retrieves info about answered question
    Args:
        session: sqlalchemy session
        game_id: game id
        question_id: question id

    Returns:
        sqlalchemy GameQuestion object

    """

    stmt = (
        select(GameQuestion)
        .where(GameQuestion.id == question_id)
        .where(GameQuestion.game_id == game_id)
    )

    game_question = await session.execute(stmt)
    game_question_list = game_question.scalar()

    if not game_question_list:
        raise HTTPException(status_code=400, detail="Question not found for game")

    return game_question_list


async def check_question_answered_or_skipped(game_question: GameQuestion) -> None:
    """
    Raises exceptions if question is already skipped or answered
    Args:
        game_question: game question object

    Returns:

    """
    if game_question.skipped:
        raise HTTPException(status_code=400, detail="Question already skipped")
    if game_question.answered:
        raise HTTPException(status_code=400, detail="Question already answered")


async def calculate_answer_score(
    user_choices: list[UUID4], actual_answers: list[Answer], question_type: str
) -> float:
    """
    Calculates score for current answered question
    Args:
        user_choices: choices user made
        actual_answers: actual answers stored in db
        question_type: type of question

    Returns:
        float: score

    """
    correct_answers_set = set()
    false_answers_set = set()

    for actual_answer in actual_answers:
        if actual_answer.is_correct:
            correct_answers_set.add(actual_answer.id)
        else:
            false_answers_set.add(actual_answer.id)

    if question_type == QuestionTypeEnum.SINGLE_ANSWER.value:
        if user_choices[0] in correct_answers_set:
            return 1
        if user_choices[0] in false_answers_set:
            return -1
        raise HTTPException(status_code=400, detail="Choice not in choices list")

    if question_type == QuestionTypeEnum.MULTIPLE_ANSWERS.value:
        plus_score = 0
        minus_score = 0
        for user_choice in user_choices:
            if user_choice in correct_answers_set:
                plus_score += 1
            elif user_choice in false_answers_set:
                minus_score += 1
            else:
                raise HTTPException(
                    status_code=400, detail="Choice not in choices list"
                )

        plus_score = plus_score / len(correct_answers_set)
        minus_score = minus_score / len(false_answers_set)

        return plus_score - minus_score

    raise ValueError("Unknown question_type")


async def service_skip_question(
    session: AsyncSession, game_id: UUID4, question_id: UUID4, user_id: UUID4
) -> None:
    """
    Skips question without modifying anything
    Args:
        session: db session
        game_id: game id
        question_id: question id
        user_id: authenticated user id

    Returns:

    """
    game = await get_game(session, game_id, user_id)
    game_question = await get_game_question(session, game_id, question_id)
    await check_question_answered_or_skipped(game_question)

    game_question.answer_score = 0
    game_question.skipped = True

    await session.execute(
        update(Game).where(Game.id == game.id).values(offset=game.offset + 1)
    )

    await session.commit()


async def service_get_results(
    session: AsyncSession, game_id: UUID4, user_id: UUID4
) -> dict:
    """
    Retrieves final results of the finished game
    Args:
        session: db session
        game_id: game id
        user_id: authenticated user id

    Returns:

    """
    game = await get_game(session, game_id, user_id)

    if not game.finished:
        raise HTTPException(status_code=400, detail="Game is not finished yet")

    stmt = (
        select(GameQuestion.answer_score, Question.title)
        .join(Question, Question.id == GameQuestion.question_id)
        .where(GameQuestion.game_id == game_id)
    )

    question_stats = await session.execute(stmt)
    question_stats_result = question_stats.all()

    formatted_question_stats = [
        {"answer_score": answer_score, "title": title}
        for answer_score, title in question_stats_result
    ]

    max_score = len(question_stats_result)
    score_percentage = game.score / max_score * 100

    return {
        "score": game.score,
        "score_percentage": score_percentage,
        "question_stats": formatted_question_stats,
    }
