"""
SQL Alchemy models declaration.
https://docs.sqlalchemy.org/en/14/orm/declarative_styles.html#example-two-dataclasses-with-declarative-table
Dataclass style for powerful autocompletion support.

https://alembic.sqlalchemy.org/en/latest/tutorial.html
Note, it is used by alembic migrations logic, see `alembic/env.py`

Alembic shortcuts:
# create migration
alembic revision --autogenerate -m "migration_name"

# apply all migrations
alembic upgrade head
"""
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_model"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda _: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(254), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=lambda _: str(uuid.uuid4())
    )
    value: Mapped[str] = mapped_column(String(254))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id")
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(254))
    type: Mapped[str] = mapped_column(String(254))
    quiz_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id"))
    answers = relationship("Answer", lazy=False)


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String)
    published: Mapped[bool] = mapped_column(Boolean)
    deleted: Mapped[bool] = mapped_column(Boolean, index=True, default=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_model.id")
    )
    questions = relationship("Question")
    games = relationship("Game")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finished: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float)
    offset: Mapped[int] = mapped_column(Integer)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_model.id")
    )
    quiz_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id"))
    game_questions = relationship("GameQuestion")


class GameQuestion(Base):
    __tablename__ = "game_questions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    answered: Mapped[bool] = mapped_column(Boolean)
    skipped: Mapped[bool] = mapped_column(Boolean)
    answer_score: Mapped[float] = mapped_column(Float)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), index=True
    )
    game_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"))
    game_answers = relationship("GameAnswer", lazy=False)


class GameAnswer(Base):
    __tablename__ = "game_answers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    choice: Mapped[str] = mapped_column(String)
    game_question_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("game_questions.id")
    )
