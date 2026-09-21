"""All API routers, mounted under /api."""

from fastapi import APIRouter

from app.api import auth, claims, comparisons, conversations, dashboard, evaluation, health, policies, users

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(policies.router)
api_router.include_router(conversations.router)
api_router.include_router(claims.router)
api_router.include_router(comparisons.router)
api_router.include_router(dashboard.router)
api_router.include_router(evaluation.router)
