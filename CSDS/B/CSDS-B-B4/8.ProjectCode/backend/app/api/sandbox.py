"""Sandbox tools: sample messages, sample QR codes, a sample incoming collect request, reset."""
from __future__ import annotations

from datetime import timedelta
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base, engine, get_db, session_scope
from app.core.deps import api_error, get_current_user, require_admin
from app.core.logging import get_logger
from app.models import CollectRequest, User, Wallet, utcnow
from app.services.guard import build_upi_uri, collect_guard
from app.services.notifier import notify
from app.services.views import collect_view

router = APIRouter(prefix="/sandbox", tags=["sandbox"])
log = get_logger("upi_guardian.sandbox")

SAMPLE_SMS = [
    {"id": "kyc_en", "language": "en", "kind": "scam", "text": "Your KYC expires today, click link http://kyc-verify-now.top/a77 to update or your account will be blocked."},
    {"id": "kyc_hi", "language": "hi", "kind": "scam", "text": "प्रिय ग्राहक, आपका KYC आज समाप्त हो रहा है। खाता बंद कर दिया जाएगा। तुरंत KYC अपडेट करें: http://acct-help-india.site/4412"},
    {"id": "refund_te", "language": "te", "kind": "scam", "text": "మీ ₹4,999 రీఫండ్ సిద్ధంగా ఉంది. డబ్బు పొందడానికి refund.desk@upg నుండి వచ్చిన అభ్యర్థనను ఆమోదించి PIN ఎంటర్ చేయండి."},
    {"id": "prize_en", "language": "en", "kind": "scam", "text": "Congratulations! Your number won Rs 5,00,000 in the Mega Lucky Draw. Pay processing fee of Rs 4,999 to luckydraw.winner@upg to claim now."},
    {"id": "job_hi", "language": "hi", "kind": "scam", "text": "Ghar baithe kamaayein Rs 5000 roz. Task unlock karne ke liye Rs 999 deposit bhejein tasks.pay@upg"},
    {"id": "power_te", "language": "te", "kind": "scam", "text": "Mee current ee raatri 9:30 ki cut avutundi. Bill update kosam ventane 9123456780 ki call cheyandi."},
    {"id": "bank_en", "language": "en", "kind": "genuine", "text": "Rs 450 debited from A/c XX4821 to Lakshmi General Stores via UPI. Ref 5521908812. Never share your OTP with anyone. -BUNB"},
    {"id": "otp_hi", "language": "hi", "kind": "genuine", "text": "Bharat Union Bank मोबाइल बैंकिंग लॉगिन के लिए आपका OTP 482913 है। यह 5 मिनट के लिए मान्य है। किसी के साथ OTP साझा न करें।"},
    {"id": "chat_te", "language": "te", "kind": "genuine", "text": "Nenu intiki cherukunnanu. Repu call chesta."},
]


def _qr_samples() -> list[dict]:
    items = [
        {"id": "grocery", "kind": "genuine", "title": "Lakshmi General Stores", "payload": build_upi_uri("lakshmistores@upg", "Lakshmi General Stores")},
        {"id": "tea", "kind": "genuine", "title": "Anand Tea Stall - Rs 40", "payload": build_upi_uri("anandtea@upg", "Anand Tea Stall", 40)},
        {"id": "cashback", "kind": "trick", "title": "'Scan to receive Rs 5,000 cashback'", "payload": build_upi_uri("cashback.offer@upg", "Cashback Offers", 5000, "Scan to receive cashback Rs 5000")},
        {"id": "mismatch", "kind": "trick", "title": "'Electricity bill' QR that pays someone else", "payload": build_upi_uri("vikram.4411@upg", "Sunrise Power Bills", 1850, "Electricity bill")},
        {"id": "link", "kind": "trick", "title": "QR code that opens a website", "payload": "http://kyc-verify-now.top/scan-and-verify"},
    ]
    for i in items:
        i["image_url"] = f"/api/qr/image?payload={quote(i['payload'], safe='')}"
    return items


@router.get("/samples")
def samples(_: User = Depends(get_current_user)) -> dict:
    return {"sms": SAMPLE_SMS, "qr": _qr_samples()}


class IncomingIn(BaseModel):
    kind: Literal["refund_trick", "genuine"] = "refund_trick"


@router.post("/incoming-collect", status_code=status.HTTP_201_CREATED)
def incoming_collect(body: IncomingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """A sample account sends the signed-in user a collect request (to try the F9 guard)."""
    if body.kind == "refund_trick":
        upi, amount, note = "refund.desk@upg", 4999.0, "Refund for order #48213 - approve to receive Rs 4,999"
    else:
        upi, amount, note = "priya@upg", 650.0, "Dinner split"
    requester = db.scalar(select(Wallet).where(Wallet.upi_id == upi))
    if requester is None or requester.id == user.wallet.id:
        raise api_error(status.HTTP_409_CONFLICT, "sample_unavailable", "The sample account is not available in this sandbox.")
    req = CollectRequest(requester_wallet_id=requester.id, payer_wallet_id=user.wallet.id, amount_paise=int(amount * 100), note=note, expires_at=utcnow() + timedelta(days=2))
    db.add(req)
    db.flush()
    req.guard = collect_guard(note, amount)
    notify(db, user.id, "collect_received", {"request_id": req.id, "amount": amount, "requested_by": requester.display_name})
    db.commit()
    return collect_view(req, user)


@router.post("/reset")
def reset(_: User = Depends(require_admin)) -> dict:
    """Deletes all sandbox data and loads the sample data again (fraud-risk team only)."""
    from app.seed import seed_if_empty

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        seed_if_empty(db)
    log.info("sandbox reset")
    return {"status": "reset"}
