from datetime import datetime

from pydantic import UUID4, BaseModel


class QuizSchema(BaseModel):
    title: str

    class Config:
        """Extra configuration options"""

        anystr_strip_whitespace = True
        min_anystr_length = 1


class QuizCreateResponse(BaseModel):
    id: UUID4


class QuizResponse(BaseModel):
    id: UUID4
    title: str
    published: bool
    created_at: datetime


class UpdateQuizSchema(BaseModel):
    title: str

    class Config:
        """Extra configuration options"""

        anystr_strip_whitespace = True
        min_anystr_length = 1
