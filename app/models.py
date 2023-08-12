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

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    quizzes = relationship("Quiz")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(String)
    is_correct = Column(Boolean)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    type = Column(String)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))
    answers = relationship("Answer", lazy=False)


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    published = Column(Boolean)
    deleted = Column(Boolean, index=True, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    questions = relationship("Question")
    games = relationship("Game")


class Game(Base):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finished = Column(Boolean)
    score = Column(Float)
    offset = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"))
    game_questions = relationship("GameQuestion")


class GameQuestion(Base):
    __tablename__ = "game_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answered = Column(Boolean)
    skipped = Column(Boolean)
    answer_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), index=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"))
    game_answers = relationship("GameAnswer", lazy=False)


class GameAnswer(Base):
    __tablename__ = "game_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    choice = Column(String)
    game_question_id = Column(UUID(as_uuid=True), ForeignKey("game_questions.id"))
