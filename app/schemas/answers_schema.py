from pydantic import UUID4, BaseModel


class AnswerSchema(BaseModel):
    value: str
    is_correct: bool

    class Config:
        """Extra configuration options"""

        anystr_strip_whitespace = True
        min_anystr_length = 1


class AnswerResponse(BaseModel):
    id: UUID4
    value: str
    is_correct: bool
