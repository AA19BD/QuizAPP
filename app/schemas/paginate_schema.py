from dataclasses import dataclass

from pydantic import BaseModel


class BasePaginate(BaseModel):
    total_count: int
    limit: int
    offset: int


@dataclass
class PaginateSchema:
    limit: int
    offset: int
