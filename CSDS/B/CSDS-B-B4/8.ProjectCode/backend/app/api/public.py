"""Public (no sign-in) endpoints used by the landing page: headline model results and guide audio."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from app.api.models_info import FAMILIES, _latest
from app.core.deps import api_error
from app.i18n.messages import GUIDES
from app.services.voice import PREBUILT, clean_for_speech, voice_key

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/highlights")
def highlights() -> dict:
    """Headline numbers straight from the latest training runs (experiments/*/metrics.json)."""
    risk, sms, behaviour = (_latest(FAMILIES[k]) for k in ("risk", "sms", "behaviour"))
    out: dict = {"languages": 3}
    if risk:
        out["risk"] = {
            "pr_auc": risk["models"]["XGBoost"]["test"]["pr_auc"],
            "roc_auc": risk["models"]["XGBoost"]["test"]["roc_auc"],
            "scams_checked": risk["policy"]["test"]["scams_reaching_medium_or_high"],
            "scams_held": risk["policy"]["test"]["scams_reaching_high_hold"],
            "genuine_straight_through": risk["policy"]["test"]["genuine_payments_low"],
            "test_payments": risk["dataset"]["rows"]["test"],
        }
    if sms:
        out["sms"] = {"f1": sms["verdict"]["test"]["f1"], "pr_auc": sms["verdict"]["test"]["pr_auc"], "test_messages": sms["dataset"]["rows"]["test"]}
    if behaviour:
        out["behaviour"] = {"roc_auc": behaviour["models"]["XGBoost"]["test"]["roc_auc"], "test_transactions": behaviour["dataset"]["rows"]["test"]}
    return out


@router.get("/guide/{screen}.mp3", include_in_schema=False)
def guide_audio(screen: str, lang: Literal["en", "hi", "te"] = "en") -> FileResponse:
    """Serves only the pre-built guide recordings (never synthesises new speech)."""
    if screen not in GUIDES:
        raise api_error(status.HTTP_404_NOT_FOUND, "guide_not_found", "No guide for this screen.")
    path = PREBUILT / f"{voice_key(lang, clean_for_speech(GUIDES[screen][lang]))}.mp3"
    if not path.exists():
        raise api_error(status.HTTP_404_NOT_FOUND, "audio_not_found", "Audio not found.")
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=86400"})
