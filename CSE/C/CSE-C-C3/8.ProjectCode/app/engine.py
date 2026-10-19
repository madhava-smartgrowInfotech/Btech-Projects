"""ParkSure Smart Availability Engine + Trust Score + haversine.

Owns the product's core reliability rules:
- hold-back buffer per location (init/increment/max/24h reset)
- forecasted-availability admission check (bookings + buffer vs capacity)
- haversine nearest-alternate suggestion
- trust score updates (benefit/warning streaks) and suspension rule
- fee multiplier by trust score
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from . import config
from .models import ParkingLocation, Reservation, TrustEvent, User

ACTIVE_BOOKING = ("reserved", "active")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_tz(dt: datetime) -> datetime:
    if dt is None:
        return dt
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in km (implemented directly, no geo API)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def overlapping_count(db: Session, location_id: int, start: datetime, end: datetime,
                      exclude_id: int | None = None) -> int:
    q = db.query(Reservation).filter(
        Reservation.location_id == location_id,
        Reservation.status.in_(ACTIVE_BOOKING),
        Reservation.start_time < end,
        Reservation.end_time > start,
    )
    if exclude_id:
        q = q.filter(Reservation.id != exclude_id)
    return q.count()


def active_parked_count(db: Session, location_id: int) -> int:
    return db.query(Reservation).filter(
        Reservation.location_id == location_id, Reservation.status == "active").count()


def forecast_free(db: Session, loc: ParkingLocation, start: datetime, end: datetime) -> bool:
    """A slot will be free at arrival if overlapping bookings + buffer < capacity."""
    used = overlapping_count(db, loc.id, start, end)
    return (used + loc.buffer_size) < loc.capacity


def fee_multiplier(trust: float) -> float:
    key = max(0, min(5, int(round(trust))))
    return config.FEE_MULTIPLIER[key]


def quote_fee(loc: ParkingLocation, trust: float, start: datetime, end: datetime) -> tuple[float, float]:
    hours = max(0.25, (ensure_tz(end) - ensure_tz(start)).total_seconds() / 3600.0)
    mult = fee_multiplier(trust)
    return round(hours * loc.price_per_hour * mult, 2), mult


def reset_buffers_if_due(db: Session) -> int:
    """Scheduled job: reset each location's buffer to BUFFER_INIT once per rolling 24h."""
    now = utcnow()
    changed = 0
    for loc in db.query(ParkingLocation).all():
        last = ensure_tz(loc.last_buffer_reset) if loc.last_buffer_reset else now
        if (now - last) >= timedelta(hours=config.BUFFER_RESET_HOURS):
            loc.buffer_size = config.BUFFER_INIT
            loc.last_buffer_reset = now
            changed += 1
    if changed:
        db.commit()
    return changed


def record_checkout_trust(db: Session, user: User, on_time: bool, detail: str = "") -> None:
    now = utcnow()
    if on_time:
        user.benefit_streak += 1
        db.add(TrustEvent(user_id=user.id, kind="benefit", detail=detail or "On-time checkout"))
        if user.benefit_streak >= config.BENEFIT_STREAK_FOR_REWARD:
            if user.trust_score < config.TRUST_MAX:
                user.trust_score = min(config.TRUST_MAX, user.trust_score + 1.0)
                db.add(TrustEvent(user_id=user.id, kind="reward", detail="Trust +1 for consistent on-time returns"))
            user.benefit_streak = 0
    else:
        user.benefit_streak = 0
        user.warning_count += 1
        db.add(TrustEvent(user_id=user.id, kind="warning", detail=detail or "Late checkout"))
        if user.warning_count >= config.WARNINGS_FOR_PENALTY:
            user.trust_score = max(config.TRUST_MIN, user.trust_score - 1.0)
            user.warning_count = 0
            db.add(TrustEvent(user_id=user.id, kind="penalty", detail="Trust -1 after repeated late checkouts"))
    db.commit()


def suspension_block(db: Session, user: User) -> str | None:
    """Refuse booking when trust < threshold AND a recent violation exists; apply one cooldown."""
    now = utcnow()
    if user.suspended_until and ensure_tz(user.suspended_until) > now:
        return f"Booking paused until {ensure_tz(user.suspended_until).strftime('%Y-%m-%d %H:%M UTC')} after a recent late checkout. Please try again after the cooldown."
    if user.trust_score < config.TRUST_SUSPEND_THRESHOLD:
        cutoff = now - timedelta(days=config.RECENT_VIOLATION_DAYS)
        recent = db.query(TrustEvent).filter(
            TrustEvent.user_id == user.id, TrustEvent.kind == "warning",
            TrustEvent.created_at >= cutoff).count()
        if recent > 0:
            user.suspended_until = now + timedelta(hours=config.SUSPEND_COOLDOWN_HOURS)
            db.commit()
            return ("Your Trust Score is below the minimum and a recent late checkout was recorded. "
                    f"Booking is paused for {config.SUSPEND_COOLDOWN_HOURS}h. On-time history will restore access.")
    return None


def nearest_alternate(db: Session, origin: ParkingLocation, start: datetime, end: datetime,
                      exclude_ids: set[int] | None = None) -> tuple[ParkingLocation | None, float]:
    """Exactly one nearest location (haversine) that has forecasted availability."""
    best, best_km = None, None
    for loc in db.query(ParkingLocation).filter(ParkingLocation.id != origin.id).all():
        if exclude_ids and loc.id in exclude_ids:
            continue
        if not forecast_free(db, loc, start, end):
            continue
        km = haversine_km(origin.latitude, origin.longitude, loc.latitude, loc.longitude)
        if best is None or km < best_km:
            best, best_km = loc, km
    return best, (best_km or 0.0)
