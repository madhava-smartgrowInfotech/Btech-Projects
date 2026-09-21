"""All API routers, mounted under /api."""
from fastapi import APIRouter

from app.api import auth, health, settings, users

api_router = APIRouter(prefix="/api")
for module in (health, auth, users, settings):
    api_router.include_router(module.router)
