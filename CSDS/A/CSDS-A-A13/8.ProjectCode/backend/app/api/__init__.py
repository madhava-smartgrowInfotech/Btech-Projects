"""All API routers, mounted under /api."""
from fastapi import APIRouter

from app.api import attendance, audit, auth, data, exports, health, imports, plans, public, settings, users

api_router = APIRouter(prefix="/api")
for module in (health, auth, users, settings, imports, data, plans, exports, attendance, audit, public):
    api_router.include_router(module.router)
