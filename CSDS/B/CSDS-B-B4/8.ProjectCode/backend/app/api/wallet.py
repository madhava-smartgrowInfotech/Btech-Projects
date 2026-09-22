from __future__ import annotations

import io
from datetime import timedelta

import qrcode
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import IST, RiskAssessment, SavedPayee, Transaction, User, Wallet, utcnow
from app.services.guard import build_upi_uri
from app.services.payments import find_wallet
from app.services.trust import compute_trust
from app.services.views import party

router = APIRouter(tags=["wallet"])


@router.get("/wallet")
def wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    w = user.wallet
    now = utcnow()
    month_start = now.astimezone(IST).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent = db.scalar(select(func.coalesce(func.sum(Transaction.amount_paise), 0)).where(Transaction.payer_wallet_id == w.id, Transaction.status == "completed", Transaction.created_at >= month_start)) or 0
    received = db.scalar(select(func.coalesce(func.sum(Transaction.amount_paise), 0)).where(Transaction.payee_wallet_id == w.id, Transaction.status == "completed", Transaction.created_at >= month_start)) or 0
    checked = db.scalar(select(func.count(RiskAssessment.id)).join(Transaction).where(Transaction.payer_wallet_id == w.id)) or 0
    stopped = db.scalars(
        select(Transaction).where(
            Transaction.payer_wallet_id == w.id,
            or_(Transaction.status.in_(("cancelled", "rejected", "blocked")), Transaction.status_reason == "cancelled_after_warning"),
        )
    ).all()
    protected = [t for t in stopped if t.assessment and t.assessment.final_level != "low"]
    held = db.scalar(select(func.count(Transaction.id)).where(Transaction.payer_wallet_id == w.id, Transaction.status == "held")) or 0
    levels = dict(
        db.execute(
            select(RiskAssessment.final_level, func.count())
            .join(Transaction)
            .where(Transaction.payer_wallet_id == w.id, Transaction.created_at >= now - timedelta(days=30))
            .group_by(RiskAssessment.final_level)
        ).all()
    )
    # Daily spend for the last 14 days (India time) for the home chart.
    rows = db.execute(
        select(Transaction.created_at, Transaction.amount_paise).where(Transaction.payer_wallet_id == w.id, Transaction.status == "completed", Transaction.created_at >= now - timedelta(days=14))
    ).all()
    daily: dict[str, float] = {}
    for i in range(13, -1, -1):
        daily[(now - timedelta(days=i)).astimezone(IST).strftime("%Y-%m-%d")] = 0.0
    for created, paise in rows:
        key = created.astimezone(IST).strftime("%Y-%m-%d")
        if key in daily:
            daily[key] += paise / 100
    return {
        "upi_id": w.upi_id,
        "display_name": w.display_name,
        "balance": w.balance_paise / 100,
        "is_sample": user.is_sample,
        "qr_uri": build_upi_uri(w.upi_id, w.display_name),
        "stats": {
            "spent_this_month": spent / 100,
            "received_this_month": received / 100,
            "payments_checked": checked,
            "payments_stopped": len(protected),
            "money_protected": sum(t.amount_paise for t in protected) / 100,
            "on_hold": held,
            "levels_30d": {k: levels.get(k, 0) for k in ("low", "medium", "high")},
        },
        "daily_spend": [{"date": k, "amount": round(v, 2)} for k, v in daily.items()],
    }


@router.get("/wallet/qr.png")
def my_qr(amount: float | None = Query(None, gt=0, le=100000), user: User = Depends(get_current_user)) -> StreamingResponse:
    uri = build_upi_uri(user.wallet.upi_id, user.wallet.display_name, amount)
    return _qr_png(uri)


def _qr_png(data: str) -> StreamingResponse:
    img = qrcode.make(data, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/payees/lookup")
def lookup(upi_id: str = Query(..., min_length=3, max_length=80), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    w = find_wallet(db, upi_id)
    times = db.scalar(select(func.count(Transaction.id)).where(Transaction.payer_wallet_id == user.wallet.id, Transaction.payee_wallet_id == w.id, Transaction.status == "completed")) or 0
    saved = db.scalar(select(SavedPayee).where(SavedPayee.user_id == user.id, SavedPayee.payee_wallet_id == w.id))
    return party(w) | {
        "is_self": w.id == user.wallet.id,
        "times_paid": times,
        "saved_as": saved.nickname if saved else None,
        "trust": compute_trust(db, w).as_dict(),
    }


@router.get("/payees/recent")
def recent(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    saved = db.scalars(select(SavedPayee).where(SavedPayee.user_id == user.id).order_by(SavedPayee.created_at)).all()
    counts = dict(
        db.execute(
            select(Transaction.payee_wallet_id, func.count())
            .where(Transaction.payer_wallet_id == user.wallet.id, Transaction.status == "completed")
            .group_by(Transaction.payee_wallet_id)
        ).all()
    )
    recent_ids = [
        pid
        for (pid,) in db.execute(
            select(Transaction.payee_wallet_id)
            .where(Transaction.payer_wallet_id == user.wallet.id, Transaction.status == "completed")
            .group_by(Transaction.payee_wallet_id)
            .order_by(func.max(Transaction.created_at).desc())
            .limit(8)
        ).all()
    ]
    saved_ids = {s.payee_wallet_id for s in saved}
    recent_wallets = [db.get(Wallet, pid) for pid in recent_ids if pid not in saved_ids]
    return {
        "saved": [party(s.payee_wallet) | {"nickname": s.nickname, "relation": s.relation, "times_paid": counts.get(s.payee_wallet_id, 0)} for s in saved],
        "recent": [party(w) | {"times_paid": counts.get(w.id, 0)} for w in recent_wallets if w],
    }


class SavePayeeIn(BaseModel):
    upi_id: str = Field(min_length=3, max_length=80)
    nickname: str = Field(min_length=1, max_length=80)
    relation: str | None = Field(default=None, max_length=30)


@router.post("/payees/save", status_code=status.HTTP_201_CREATED)
def save_payee(body: SavePayeeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    w = find_wallet(db, body.upi_id)
    if w.id == user.wallet.id:
        raise api_error(status.HTTP_400_BAD_REQUEST, "self_payment", "You cannot save your own UPI ID.")
    existing = db.scalar(select(SavedPayee).where(SavedPayee.user_id == user.id, SavedPayee.payee_wallet_id == w.id))
    if existing:
        existing.nickname, existing.relation = body.nickname, body.relation
    else:
        db.add(SavedPayee(user_id=user.id, payee_wallet_id=w.id, nickname=body.nickname, relation=body.relation))
    db.commit()
    return party(w) | {"nickname": body.nickname}
