from fastapi import APIRouter

from ..config import settings
from ..services.owasp import OWASP_TOP10, SEVERITY_WEIGHT

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/owasp")
def owasp_catalog():
    return {"top10": [{"id": k, "name": v} for k, v in OWASP_TOP10.items()],
            "severity_weights": SEVERITY_WEIGHT}


@router.get("/config")
def public_config():
    return {
        "scope_allowlist": settings.scope_allowlist,
        "gemini_enabled": bool(settings.gemini_api_key),
    }
