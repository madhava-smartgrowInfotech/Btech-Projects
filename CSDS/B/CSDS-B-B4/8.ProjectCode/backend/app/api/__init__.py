from fastapi import APIRouter

from app.api import (
    admin,
    auth,
    collect,
    health,
    holds,
    models_info,
    notifications,
    payments,
    public,
    qr,
    sandbox,
    settings,
    sms,
    trust,
    trusted,
    voice,
    wallet,
)

router = APIRouter()
for module in (health, auth, wallet, payments, qr, collect, holds, trusted, trust, sms, voice, settings, notifications, admin, models_info, sandbox, public):
    router.include_router(module.router)
