"""All API routers, mounted under /api."""
from fastapi import APIRouter

from app.api import auth, data, health, imports, settings, users

api_router = APIRouter(prefix="/api")
for module in (health, auth, users, settings, imports, data):
    api_router.include_router(module.router)
