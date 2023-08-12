import pydantic
from fastapi import Query

from app.schemas.paginate_schema import BasePaginate, PaginateSchema


class Paginate:
    def __class_getitem__(cls, item):
        return pydantic.create_model(
            f"Paginate{item.__name__}", items=(list[item], ...), __base__=BasePaginate
        )


def pagination_parameters(
    limit: int = Query(15, ge=1, le=20),
    offset: int = 0,
):
    return PaginateSchema(limit=limit, offset=offset)
