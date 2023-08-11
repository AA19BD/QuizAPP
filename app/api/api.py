from fastapi import APIRouter

from app.api.endpoints import auth, users
from app.core import config

api_router = APIRouter()
version = config.settings.APP_VERSION

api_router.include_router(auth.router, prefix=f"/api/{version}/auth", tags=["auth"])
api_router.include_router(users.router, prefix=f"/api/{version}/users", tags=["users"])
