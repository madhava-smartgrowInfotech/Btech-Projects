"""All API routers, mounted under /api."""
from fastapi import APIRouter

from app.api import audit, auth, data, health, imports, plans, settings, users

api_router = APIRouter(prefix="/api")
for module in (health, auth, users, settings, imports, data, plans, audit):
    api_router.include_router(module.router)
