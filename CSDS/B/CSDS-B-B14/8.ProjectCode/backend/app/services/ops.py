"""Glue between the database (active leaks, alerts) and the twin / model services."""
from datetime import datetime, timezone

from sqlalchemy import select

from ..db import Alert, LeakEvent, add_alert
from . import anomaly, imbalance, twin


def active_leaks(db):
    rows = db.scalars(select(LeakEvent).where(LeakEvent.active.is_(True))).all()
    return tuple((r.pipe, round(r.leak_lps, 2)) for r in rows)


def twin_state(db):
    return imbalance.state(active_leaks(db))


def sync_alerts(db):
    """Raise alerts for flagged meters and zone imbalance (idempotent via alert refs)."""
    for m in anomaly.flagged_meters():
        sev = "high" if m["type"] in ("burst", "suspected_theft") else "medium"
        add_alert(db, "anomaly", sev, f"{m['type'].replace('_', ' ').capitalize()} on meter {m['meter_id']}",
                  f"{m['description']} {m['anomalous_days']} abnormal day(s) since {m['since']}.",
                  zone=m["zone"], ref=f"meter:{m['meter_id']}:{m['since']}")
    _, _, s = twin_state(db)
    worst = min(s["zones"].values(), key=lambda z: z["pressure_adequacy"])
    ref = f"imbalance:{worst['zone']}:{datetime.now(timezone.utc):%Y-%m-%d}"
    if s["equity_score"] < 90:
        add_alert(db, "imbalance", "medium", f"Supply imbalance - {worst['name']} under-served",
                  f"Equity score {s['equity_score']}; {worst['low_pressure_hours']} h below {twin.REQUIRED_PRESSURE:g} m "
                  f"(min {worst['min_pressure']} m). Open the imbalance view for a rebalancing plan.",
                  zone=worst["zone"], ref=ref)


def open_alerts(db, limit=50):
    return db.scalars(select(Alert).order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit)).all()


def alert_dict(a):
    return {"id": a.id, "created_at": a.created_at.isoformat(), "kind": a.kind, "severity": a.severity,
            "zone": a.zone, "title": a.title, "detail": a.detail, "open": a.open}
