"""ParkSure FastAPI application: API + static frontend + scheduler + seed."""
from __future__ import annotations
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import config
from .auth import admin_user, create_token, current_user, hash_password, verify_password
from .database import Base, SessionLocal, engine, get_db
from .engine import (ACTIVE_BOOKING, active_parked_count, ensure_tz, fee_multiplier, forecast_free,
                     nearest_alternate, overlapping_count, quote_fee, record_checkout_trust,
                     reset_buffers_if_due, suspension_block, utcnow)
from .models import ParkingLocation, Payment, Reservation, TrustEvent, User
from .schemas import LocationIn, LoginIn, RegisterIn, ReservationIn
from .stripe_pay import create_checkout, stripe_configured

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

scheduler = BackgroundScheduler()


def _job_reset_buffers():
    db = SessionLocal()
    try:
        reset_buffers_if_due(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Seed on first run so a fresh install has realistic demo data.
    from .seed import seed_if_empty
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    if not scheduler.running:
        scheduler.add_job(_job_reset_buffers, "interval", minutes=30, id="buffer-reset")
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="ParkSure", version=config.APP_VERSION,
              description="Smart parking reservation platform", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


def _pub(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "trust_score": round(u.trust_score, 1), "benefit_streak": u.benefit_streak,
            "warning_count": u.warning_count, "account_credit": round(u.account_credit, 2),
            "suspended_until": u.suspended_until.isoformat() if u.suspended_until else None}


def _loc(l: ParkingLocation) -> dict:
    return {"id": l.id, "name": l.name, "address": l.address, "latitude": l.latitude,
            "longitude": l.longitude, "capacity": l.capacity, "buffer_size": l.buffer_size,
            "price_per_hour": l.price_per_hour}


def _res(r: Reservation, db: Session) -> dict:
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == r.location_id).first()
    pay = db.query(Payment).filter(Payment.reservation_id == r.id).first()
    return {"id": r.id, "location_id": r.location_id, "location_name": loc.name if loc else "",
            "start_time": ensure_tz(r.start_time).isoformat(), "end_time": ensure_tz(r.end_time).isoformat(),
            "status": r.status, "fee": r.fee, "fee_multiplier": r.fee_multiplier,
            "checked_in_at": ensure_tz(r.checked_in_at).isoformat() if r.checked_in_at else None,
            "checked_out_at": ensure_tz(r.checked_out_at).isoformat() if r.checked_out_at else None,
            "decline_reason": r.decline_reason or "", "parent_id": r.parent_id,
            "payment_status": pay.status if pay else None, "payment_provider": pay.provider if pay else None}


def _require_future_window(start: datetime, end: datetime):
    s, e = ensure_tz(start), ensure_tz(end)
    if (e - s).total_seconds() > 30 * 24 * 3600:
        raise HTTPException(status_code=400, detail="Reservations are limited to 30 days in length")


# ---------- Auth ----------
@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    role = "admin" if db.query(User).count() == 0 else "driver"  # first account becomes admin
    u = User(name=body.name.strip(), email=body.email.strip().lower(),
             password_hash=hash_password(body.password), role=role, trust_score=config.TRUST_START)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"token": create_token(u), "user": _pub(u)}


@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(func.lower(User.email) == body.email.lower()).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"token": create_token(u), "user": _pub(u)}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return _pub(user)


# ---------- Locations ----------
@app.get("/api/locations")
def list_locations(db: Session = Depends(get_db)):
    return [_loc(l) for l in db.query(ParkingLocation).order_by(ParkingLocation.name).all()]


@app.post("/api/locations")
def create_location(body: LocationIn, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    loc = ParkingLocation(**body.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return _loc(loc)


@app.put("/api/locations/{lid}")
def update_location(lid: int, body: LocationIn, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == lid).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    for k, v in body.model_dump().items():
        setattr(loc, k, v)
    db.commit()
    return _loc(loc)


@app.delete("/api/locations/{lid}")
def delete_location(lid: int, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == lid).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(loc)
    db.commit()
    return {"ok": True}


@app.get("/api/search")
def search(start_time: datetime, end_time: datetime, db: Session = Depends(get_db)):
    """Availability search: each location annotated with forecasted free slots."""
    _require_future_window(start_time, end_time)
    s, e = ensure_tz(start_time), ensure_tz(end_time)
    if e <= s:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    out = []
    for loc in db.query(ParkingLocation).order_by(ParkingLocation.name).all():
        used = overlapping_count(db, loc.id, s, e)
        bookable = max(0, loc.capacity - loc.buffer_size - used)
        d = _loc(loc)
        d.update({"overlapping": used, "bookable": bookable, "available": bookable > 0})
        out.append(d)
    return out


# ---------- Reservations ----------
@app.post("/api/reservations")
def create_reservation(body: ReservationIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == body.location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Parking location not found")
    s, e = ensure_tz(body.start_time), ensure_tz(body.end_time)
    _require_future_window(s, e)
    blocked = suspension_block(db, user)
    if blocked:
        r = Reservation(user_id=user.id, location_id=loc.id, start_time=s, end_time=e,
                        status="declined", decline_reason=blocked)
        db.add(r)
        db.commit()
        raise HTTPException(status_code=403, detail=blocked)
    if not forecast_free(db, loc, s, e):
        reason = (f"{loc.name} is fully reserved for the requested window "
                  f"(capacity {loc.capacity}, hold-back buffer {loc.buffer_size}). Please try another time or location.")
        r = Reservation(user_id=user.id, location_id=loc.id, start_time=s, end_time=e,
                        status="declined", decline_reason=reason)
        db.add(r)
        db.commit()
        raise HTTPException(status_code=409, detail=reason)
    fee, mult = quote_fee(loc, user.trust_score, s, e)
    # Account credit offsets the fee automatically.
    credit_used = min(user.account_credit, fee)
    user.account_credit = round(user.account_credit - credit_used, 2)
    r = Reservation(user_id=user.id, location_id=loc.id, start_time=s, end_time=e,
                    status="reserved", fee=fee, fee_multiplier=mult)
    db.add(r)
    db.flush()
    payable = round(fee - credit_used, 2)
    pay = Payment(reservation_id=r.id, user_id=user.id, amount=payable,
                  provider="demo", status="paid" if payable == 0 else "pending")
    db.add(pay)
    db.commit()
    db.refresh(r)
    checkout = None
    if payable > 0:
        checkout = create_checkout(payable, r.id, user.email)
        pay.provider = checkout["provider"]
        if checkout["provider"] == "demo":
            pay.status = "pending"
        else:
            pay.stripe_session_id = checkout["session_id"]
        pay.status = pay.status
        db.commit()
    d = _res(r, db)
    d["credit_applied"] = round(credit_used, 2)
    d["amount_due"] = payable
    d["checkout"] = checkout
    d["stripe_configured"] = stripe_configured()
    return d


@app.get("/api/reservations")
def my_reservations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Reservation).filter(Reservation.user_id == user.id).order_by(Reservation.start_time.desc()).all()
    return [_res(r, db) for r in rows]


@app.post("/api/reservations/{rid}/cancel")
def cancel_reservation(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.query(Reservation).filter(Reservation.id == rid).first()
    if not r or (r.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Reservation not found")
    if r.status not in ("reserved",):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {r.status} reservation")
    r.status = "cancelled"
    pay = db.query(Payment).filter(Payment.reservation_id == r.id).first()
    if pay and pay.status == "paid":
        owner = db.query(User).filter(User.id == r.user_id).first()
        owner.account_credit = round(owner.account_credit + r.fee, 2)
        pay.status = "refunded"
    elif pay:
        pay.status = "refunded"
    db.commit()
    return _res(r, db)


@app.post("/api/reservations/{rid}/checkin")
def checkin(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.query(Reservation).filter(Reservation.id == rid).first()
    if not r or (r.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Reservation not found")
    if r.status != "reserved":
        raise HTTPException(status_code=400, detail=f"Cannot check in a {r.status} reservation")
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == r.location_id).first()
    parked = active_parked_count(db, loc.id)
    if parked >= loc.capacity:
        # Rare overstay edge case: suggest exactly one nearest alternate (haversine).
        alt, km = nearest_alternate(db, loc, ensure_tz(r.start_time), ensure_tz(r.end_time))
        if alt is None:
            r.status = "failed"
            r.decline_reason = "No free slot at arrival and no alternate with space. Fee credited automatically."
            owner = db.query(User).filter(User.id == r.user_id).first()
            owner.account_credit = round(owner.account_credit + r.fee, 2)
            pay = db.query(Payment).filter(Payment.reservation_id == r.id).first()
            if pay:
                pay.status = "refunded"
            db.commit()
            return {"moved": False, "failed": True, "reservation": _res(r, db),
                    "message": r.decline_reason}
        fee, mult = quote_fee(alt, user.trust_score, ensure_tz(r.start_time), ensure_tz(r.end_time))
        new = Reservation(user_id=r.user_id, location_id=alt.id, start_time=ensure_tz(r.start_time),
                          end_time=ensure_tz(r.end_time), status="active",
                          checked_in_at=utcnow(), fee=fee, fee_multiplier=mult, parent_id=r.id)
        db.add(new)
        r.status = "failed"
        r.decline_reason = f"No free slot at {loc.name} on arrival; moved to {alt.name} ({km:.1f} km away)."
        db.commit()
        db.refresh(new)
        return {"moved": True, "distance_km": round(km, 2), "alternate": _loc(alt),
                "reservation": _res(new, db),
                "message": f"{loc.name} was full on arrival. We moved you to {alt.name}, {km:.1f} km away."}
    r.status = "active"
    r.checked_in_at = utcnow()
    db.commit()
    return {"moved": False, "reservation": _res(r, db), "message": f"Checked in at {loc.name}. Enjoy your parking."}


@app.post("/api/reservations/{rid}/checkout")
def checkout(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.query(Reservation).filter(Reservation.id == rid).first()
    if not r or (r.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Reservation not found")
    if r.status != "active":
        raise HTTPException(status_code=400, detail="Only a checked-in reservation can be checked out")
    now = utcnow()
    r.checked_out_at = now
    r.status = "completed"
    on_time = now <= ensure_tz(r.end_time) + timedelta(minutes=10)
    loc = db.query(ParkingLocation).filter(ParkingLocation.id == r.location_id).first()
    if on_time and loc.buffer_size < config.BUFFER_MAX:
        loc.buffer_size += 1  # buffer grows as on-time behaviour is observed
    owner = db.query(User).filter(User.id == r.user_id).first()
    db.commit()
    record_checkout_trust(db, owner, on_time,
                          detail=("On-time checkout" if on_time else "Late checkout (overstay)"))
    return {"reservation": _res(r, db), "on_time": on_time,
            "message": "Checked out on time. Thank you!" if on_time else "Checked out late — recorded as an overstay."}


# ---------- Trust ----------
@app.get("/api/trust")
def trust(db: Session = Depends(get_db), user: User = Depends(current_user)):
    events = db.query(TrustEvent).filter(TrustEvent.user_id == user.id).order_by(TrustEvent.id.desc()).limit(20).all()
    return {"trust_score": round(user.trust_score, 1), "benefit_streak": user.benefit_streak,
            "warning_count": user.warning_count,
            "next_reward_in": max(0, config.BENEFIT_STREAK_FOR_REWARD - user.benefit_streak),
            "fee_multiplier": fee_multiplier(user.trust_score),
            "events": [{"kind": e.kind, "detail": e.detail,
                        "at": ensure_tz(e.created_at).isoformat()} for e in events]}


# ---------- Payments ----------
@app.get("/api/payments/demo-confirm")
def demo_confirm(reservation_id: int, session_id: str, db: Session = Depends(get_db)):
    pay = db.query(Payment).filter(Payment.reservation_id == reservation_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    pay.status = "paid"
    if not pay.stripe_session_id:
        pay.stripe_session_id = session_id
    db.commit()
    return {"ok": True, "status": "paid"}


@app.post("/api/payments/{rid}/confirm")
def confirm_payment(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pay = db.query(Payment).filter(Payment.reservation_id == rid).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
    r = db.query(Reservation).filter(Reservation.id == rid).first()
    if r and r.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your reservation")
    pay.status = "paid"
    db.commit()
    return {"ok": True, "status": "paid"}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not stripe_configured():
        return {"received": False, "reason": "Stripe not configured"}
    import stripe as _stripe
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = _stripe.Webhook.construct_event(payload, sig, config.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")
    if event["type"] == "checkout.session.completed":
        sid = event["data"]["object"]["id"]
        pay = db.query(Payment).filter(Payment.stripe_session_id == sid).first()
        if pay:
            pay.status = "paid"
            db.commit()
    return {"received": True}


# ---------- Admin ----------
@app.get("/api/admin/overview")
def admin_overview(db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    return {"users": db.query(User).count(), "locations": db.query(ParkingLocation).count(),
            "reservations": db.query(Reservation).count(),
            "revenue": round(db.query(func.coalesce(func.sum(Payment.amount), 0))
                             .filter(Payment.status == "paid").scalar() or 0, 2),
            "unable_to_park": db.query(Reservation).filter(Reservation.status == "failed").count(),
            "declined": db.query(Reservation).filter(Reservation.status == "declined").count()}


@app.get("/api/admin/users")
def admin_users(db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    return [_pub(u) for u in db.query(User).order_by(User.id).all()]


@app.get("/api/admin/bookings")
def admin_bookings(db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    rows = db.query(Reservation).order_by(Reservation.start_time.desc()).limit(300).all()
    return [_res(r, db) for r in rows]


@app.post("/api/admin/reset-buffers")
def admin_reset_buffers(db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    n = reset_buffers_if_due(db)
    # Admin button forces a reset even inside the window.
    forced = 0
    if n == 0:
        for loc in db.query(ParkingLocation).all():
            loc.buffer_size = config.BUFFER_INIT
            loc.last_buffer_reset = utcnow()
            forced += 1
        db.commit()
    return {"reset_by_policy": n, "forced": forced}


@app.get("/api/admin/insights")
def admin_insights(window_days: int = 60, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    """Real metrics from stored data + deterministic simulation across buffer configs."""
    from scripts.compute_buffer_strategy_metrics import compute_all
    return compute_all(db, window_days=window_days)


# ---------- Static frontend ----------
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")


@app.get("/", include_in_schema=False)
def root():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx), headers={"Cache-Control": "no-store"})
    return {"app": "ParkSure", "docs": "/docs"}


@app.get("/{page}", include_in_schema=False)
def pages(page: str):
    Sana = {"dashboard", "admin", "login"}
    if page in Sana and (STATIC_DIR / f"{page}.html").exists():
        return FileResponse(str(STATIC_DIR / f"{page}.html"), headers={"Cache-Control": "no-store"})
    idx = STATIC_DIR / "index.html"
    if idx.exists() and "." not in page:
        return FileResponse(str(idx))
    return JSONResponse({"detail": "Not found"}, status_code=404)
