from datetime import datetime

from pydantic import UUID4, BaseModel, root_validator, validator


class GameStartSchema(BaseModel):
    quiz_id: UUID4


class StartGameResponse(BaseModel):
    id: UUID4


class GameResponse(BaseModel):
    id: UUID4
    title: str
    finished: bool
    created_at: datetime


class QuestionStat(BaseModel):
    answer_score: float
    title: str
    answer_score_percentage: float

    @root_validator
    def answer_score_percentage(cls, values):
        values["answer_score_percentage"] = float(
            "{:.3f}".format(values["answer_score"] * 100)
        )
        values["answer_score"] = float("{:.3f}".format(values["answer_score"]))
        return values


class FinalResultsResponse(BaseModel):
    score: float
    score_percentage: float
    question_stats: list[QuestionStat]

    @validator("score", "score_percentage")
    def round_float(cls, field_value):
        return float(f"{field_value:.3f}")


class GameDetailResponse(BaseModel):
    question_stats: list[QuestionStat]


class QuizGamesResponse(BaseModel):
    id: UUID4
    finished: bool
    score: float
    quiz_id: UUID4
    user_id: UUID4
    title: str

    @validator("score")
    def round_float(cls, score):
        return float(f"{score:.3f}")
