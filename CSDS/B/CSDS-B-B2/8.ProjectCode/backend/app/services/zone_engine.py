"""Zone engine: keeps each (H3 cell, operator) zone's state and drives automatic complaints and verification.

Everything is judged on reading time (not arrival time), so readings uploaded late after an outage and
replayed traces are treated exactly like live ones.

    bad zone      at least DETECT_MIN_READINGS readings in the last DETECT_WINDOW_MIN minutes of that zone,
                  of which at least DETECT_BAD_SHARE are Weak or Dead
    Detected      a bad zone without an open complaint
    Registered    still bad DETECT_PERSIST_MIN minutes after the first bad reading (evidence frozen, notified)
    Dismissed     the zone recovered before registration, or no further readings arrived within 24 hours
    Verified      after Resolved: at least VERIFY_MIN_READINGS new readings, VERIFY_STRONG_SHARE of them Strong
    Reopened      after Resolved: VERIFY_REOPEN_SHARE of the new readings Weak or Dead (back to Registered)
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import timedelta

import h3
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.db import utcnow
from ..core.logging import log_event
from ..models import OPEN_STATUSES, Complaint, Device, Reading, ZoneState
from . import complaint_service as cs
from . import settings_service
from .evidence import build_evidence, summary_text

log = logging.getLogger("signalscout.zones")
DETECTED_TIMEOUT = timedelta(hours=24)


def _coverage_filter(q):
    return q.filter(Reading.zone_label.is_not(None), ~((Reading.source == "phone") & (Reading.link == "wifi")))


def _readings(db: Session, cell: str, operator: str, start=None, end=None) -> list[Reading]:
    q = _coverage_filter(db.query(Reading).filter(Reading.h3_cell == cell, Reading.operator == operator))
    if start is not None:
        q = q.filter(Reading.ts >= start)
    if end is not None:
        q = q.filter(Reading.ts <= end)
    return q.order_by(Reading.ts).all()


def _median(values):
    vals = sorted(v for v in values if v is not None)
    return vals[len(vals) // 2] if vals else None


def _reporter(db: Session, readings: list[Reading]) -> int | None:
    phones = Counter(r.device_id for r in readings if r.source == "phone" and r.zone_label in ("Weak", "Dead"))
    if not phones:
        return None
    device = db.get(Device, phones.most_common(1)[0][0])
    return device.owner_id if device else None


def evaluate(db: Session, cell: str, operator: str, cfg: dict | None = None) -> Complaint | None:
    cfg = cfg or settings_service.get_all(db)
    latest = _coverage_filter(db.query(func.max(Reading.ts)).filter(Reading.h3_cell == cell, Reading.operator == operator)).scalar()
    if latest is None:
        return None
    window = _readings(db, cell, operator, latest - timedelta(minutes=cfg["detect_window_min"]), latest)
    n = len(window)
    counts = Counter(r.zone_label for r in window)
    bad = counts["Weak"] + counts["Dead"]
    bad_share = bad / n if n else 0.0
    is_bad = n >= cfg["detect_min_readings"] and bad_share >= cfg["detect_bad_share"]
    enough = n >= cfg["detect_min_readings"]

    zs = db.get(ZoneState, (cell, operator)) or ZoneState(h3_cell=cell, operator=operator)
    zs.label = max(("Strong", "Weak", "Dead"), key=lambda k: (counts[k], ["Strong", "Weak", "Dead"].index(k))) if n else None
    zs.confidence = round(sum(r.zone_confidence or 0 for r in window) / n, 3) if n else None
    zs.readings_window, zs.bad_share, zs.last_reading_at = n, round(bad_share, 3), latest
    zs.median_rsrp = _median([r.rsrp for r in window])
    zs.median_latency = _median([r.latency_ms for r in window])
    zs.median_dl = _median([r.dl_mbps for r in window])
    first_bad = min((r.ts for r in window if r.zone_label in ("Weak", "Dead")), default=None)
    db.add(zs)

    open_c = (db.query(Complaint).filter(Complaint.h3_cell == cell, Complaint.operator == operator, Complaint.status.in_(OPEN_STATUSES))
              .order_by(Complaint.id.desc()).first())

    if open_c is None:
        zs.first_bad_at = first_bad if is_bad else None
        zs.open_complaint_id = None
        if not is_bad:
            db.commit()
            return None
        lat, lon = h3.cell_to_latlng(cell)
        source = Counter(r.source for r in window).most_common(1)[0][0]
        ev = build_evidence(db, window, cell, operator, with_suggestion=False)
        c = Complaint(h3_cell=cell, operator=operator, lat=lat, lon=lon, status="detected",
                      severity="dead" if counts["Dead"] >= counts["Weak"] else "weak", origin="auto", source=source,
                      reporter_user_id=_reporter(db, window), evidence=ev, detected_at=first_bad or latest, ref_code=f"tmp-{cell}-{latest.timestamp()}")
        db.add(c)
        db.flush()
        c.ref_code = cs.next_ref(db, c)
        zs.open_complaint_id = c.id
        cs.add_event(db, c, "status", f"{bad} of {n} readings Weak or Dead within {cfg['detect_window_min']} minutes", None, None, "detected")
        db.commit()
        cs.publish(c, "detected")
        log_event(log, "complaint detected", ref=c.ref_code, operator=operator, cell=cell, source=source)
        open_c = c

    zs.open_complaint_id = open_c.id
    if open_c.status == "detected":
        start = min(open_c.detected_at, first_bad or open_c.detected_at)
        if is_bad and latest - start >= timedelta(minutes=cfg["detect_persist_min"]):
            since = _readings(db, cell, operator, start, latest)
            ev = build_evidence(db, since, cell, operator, with_suggestion=True)
            open_c.evidence = ev
            open_c.severity = "dead" if ev["classes"]["Dead"] >= ev["classes"]["Weak"] else "weak"
            open_c.summary = summary_text(ev, operator, open_c.ref_code)
            open_c.reporter_user_id = open_c.reporter_user_id or _reporter(db, since)
            cs.register(db, open_c, f"Still Weak/Dead after {cfg['detect_persist_min']} minutes - evidence frozen with {ev['readings']} readings",
                        at=min(latest, utcnow()))
        elif enough and not is_bad and latest > open_c.detected_at:
            cs.transition(db, open_c, "dismissed", None, "Zone recovered before the persistence threshold")
        else:
            open_c.evidence = build_evidence(db, window, cell, operator, with_suggestion=False)
            db.commit()
    elif open_c.status in ("registered", "acknowledged", "in_progress"):
        open_c.evidence = {**(open_c.evidence or {}), "latest": {"readings": n, "bad_share": round(bad_share, 3),
                                                                 "last": latest.isoformat() + "Z", "classes": dict(counts)}}
        db.commit()
    elif open_c.status == "resolved":
        verify(db, open_c, cfg)
    return open_c


def verify(db: Session, c: Complaint, cfg: dict) -> None:
    """Auto-verification from readings taken after the complaint was marked resolved."""
    if c.resolved_at is None:
        return
    after = _readings(db, c.h3_cell, c.operator, start=c.resolved_at + timedelta(seconds=1))
    n = len(after)
    counts = Counter(r.zone_label for r in after)
    strong_share = counts["Strong"] / n if n else 0.0
    bad_share = (counts["Weak"] + counts["Dead"]) / n if n else 0.0
    state = {"state": "waiting", "readings": n, "strong_share": round(strong_share, 3), "bad_share": round(bad_share, 3),
             "needed": cfg["verify_min_readings"], "checked_at": utcnow().isoformat() + "Z"}
    if n >= cfg["verify_min_readings"] and strong_share >= cfg["verify_strong_share"]:
        c.verification = {**state, "state": "verified"}
        cs.transition(db, c, "verified", None, f"{counts['Strong']} of {n} new readings are Strong - fix confirmed")
    elif n >= cfg["verify_min_readings"] and bad_share >= cfg["verify_reopen_share"]:
        c.verification = {**state, "state": "failed"}
        cs.register(db, c, f"{counts['Weak'] + counts['Dead']} of {n} new readings are still Weak or Dead - reopened", reopen=True)
    else:
        if c.resolved_at and utcnow() - c.resolved_at > timedelta(days=cfg["verify_timeout_days"]) and n < cfg["verify_min_readings"]:
            state["state"] = "awaiting_data"
        c.verification = state
        db.commit()


def on_ingest(db: Session, affected: set[tuple[str, str]]) -> None:
    if not affected:
        return
    cfg = settings_service.get_all(db)
    for cell, operator in affected:
        try:
            evaluate(db, cell, operator, cfg)
        except Exception:
            db.rollback()
            log.exception("zone evaluation failed", extra={"fields": {"cell": cell, "operator": operator}})


def sweep(db: Session) -> None:
    """Periodic housekeeping: time out unconfirmed detections and re-check resolved complaints."""
    cfg = settings_service.get_all(db)
    now = utcnow()
    sample_now = db.query(func.max(Reading.ts)).filter(Reading.source == "sample_dataset").scalar()
    for c in db.query(Complaint).filter(Complaint.status == "detected").all():
        zs = db.get(ZoneState, (c.h3_cell, c.operator))
        last = zs.last_reading_at if zs and zs.last_reading_at else c.detected_at
        # replayed sample data is judged on its own timeline; live zones on the wall clock
        reference = sample_now if c.source == "sample_dataset" and sample_now else now
        if reference - last > DETECTED_TIMEOUT:
            cs.transition(db, c, "dismissed", None, "Not confirmed - no further readings in this zone within 24 hours")
    for c in db.query(Complaint).filter(Complaint.status == "resolved").all():
        verify(db, c, cfg)
