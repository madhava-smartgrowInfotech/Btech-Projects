from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.i18n.messages import GUIDES, HONORIFIC, VOICE, advice, render, scam_type_name, spoken_amount
from app.models import CollectRequest, SmsCheck, Transaction, User
from app.services.voice import find_audio, synthesize

router = APIRouter(prefix="/voice", tags=["voice"])
Lang = Literal["en", "hi", "te"]


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=900)
    lang: Lang = "en"


class LangIn(BaseModel):
    lang: Lang = "en"


def _speak(text: str, lang: str) -> dict:
    key, cached = synthesize(text, lang)
    return {"url": f"/api/voice/audio/{key}.mp3", "text": text, "lang": lang, "cached": cached}


def _name(user: User, lang: str) -> str:
    return render(HONORIFIC[lang], {"name": user.full_name.split()[0]})


@router.post("/speak")
def speak(body: SpeakIn, _: User = Depends(get_current_user)) -> dict:
    return _speak(body.text, body.lang)


@router.post("/payment/{txn_id}")
def speak_payment(txn_id: int, body: LangIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Personalised spoken warning for a payment, in the chosen language."""
    txn = db.get(Transaction, txn_id)
    if txn is None or txn.payer_wallet_id != user.wallet.id or txn.assessment is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "payment_not_found", "Payment not found.")
    lang, a = body.lang, txn.assessment
    params = {"name": _name(user, lang), "amount": spoken_amount(txn.amount_paise / 100, lang), "payee": txn.payee_wallet.display_name}
    reasons = [r["text"][lang] for r in a.reasons if r.get("kind") != "reassurance"]
    scam = txn.intent.matched_scam_type if txn.intent else None
    if a.action == "block":
        text = render(VOICE["payment_blocked"][lang], params)
    elif a.final_level == "high":
        text = render(VOICE["payment_high"][lang], params | {"reasons": " ".join(reasons[:3]), "advice": advice(scam, lang)})
    elif a.final_level == "medium":
        text = render(VOICE["payment_medium"][lang], params | {"reasons": " ".join(reasons[:2])})
    else:
        text = render(VOICE["payment_low"][lang], params)
    if txn.status == "held" and txn.hold:
        text += " " + render(VOICE["hold_started"][lang], {"minutes": txn.hold.hold_minutes})
    return _speak(text, lang)


@router.post("/sms/{check_id}")
def speak_sms(check_id: int, body: LangIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    c = db.get(SmsCheck, check_id)
    if c is None or c.user_id != user.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "sms_not_found", "Message not found.")
    lang = body.lang
    key = {"scam": "sms_scam", "suspicious": "sms_suspicious"}.get(c.verdict, "sms_safe")
    type_name = scam_type_name(c.scam_type, lang) if c.scam_type else ""
    text = render(VOICE[key][lang], {"name": _name(user, lang), "type": type_name, "advice": advice(c.scam_type, lang)})
    return _speak(re.sub(r"\s+", " ", text), lang)


@router.post("/collect/{req_id}")
def speak_collect(req_id: int, body: LangIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    req = db.get(CollectRequest, req_id)
    if req is None or req.payer_wallet_id != user.wallet.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "request_not_found", "Request not found.")
    lang = body.lang
    text = render(VOICE["collect_debit"][lang], {"name": _name(user, lang), "amount": spoken_amount(req.amount_paise / 100, lang)})
    return _speak(text, lang)


@router.post("/qr-trick")
def speak_qr(body: LangIn, user: User = Depends(get_current_user)) -> dict:
    return _speak(render(VOICE["qr_trick"][body.lang], {"name": _name(user, body.lang)}), body.lang)


@router.get("/guide/{screen}")
def guide(screen: str, lang: Lang = "en", _: User = Depends(get_current_user)) -> dict:
    if screen not in GUIDES:
        raise api_error(status.HTTP_404_NOT_FOUND, "guide_not_found", "No guide for this screen.")
    return _speak(GUIDES[screen][lang], lang)


@router.get("/audio/{key}.mp3", include_in_schema=False)
def audio(key: str) -> FileResponse:
    if not re.fullmatch(r"[0-9a-f]{24}", key):
        raise api_error(status.HTTP_404_NOT_FOUND, "audio_not_found", "Audio not found.")
    path = find_audio(key)
    if path is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "audio_not_found", "Audio not found.")
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=2592000"})
