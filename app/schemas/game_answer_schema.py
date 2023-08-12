from pydantic import UUID4, BaseModel


class GameAnswerSchema(BaseModel):
    choices: list[UUID4]
