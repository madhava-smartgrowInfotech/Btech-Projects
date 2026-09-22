from fastapi import APIRouter

from app.api import auth, health, notifications, settings

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(settings.router)
router.include_router(notifications.router)
