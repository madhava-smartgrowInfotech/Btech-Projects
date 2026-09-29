from ..config import CAMERA_SOURCE
from ..db import SessionLocal, Setting

DEFAULTS = {
    "room_name": "Living room",
    "camera_source": CAMERA_SOURCE,
    "privacy_mode": True,
    "low_light": "auto",          # auto | on | off
    "confirm_seconds": 3.0,       # fall confirmation window
    "countdown_seconds": 20,      # 'I'm OK' countdown before alerts go out
    "inactivity_minutes": 30.0,   # long-inactivity warning threshold
    "monitor_running": False,     # resume monitoring after a restart
}


def _cast(key, raw):
    d = DEFAULTS[key]
    if isinstance(d, bool):
        return str(raw).lower() in ("1", "true", "yes", "on")
    if isinstance(d, int):
        return int(float(raw))
    if isinstance(d, float):
        return float(raw)
    return str(raw)


def get_settings():
    with SessionLocal() as db:
        rows = {s.key: s.value for s in db.query(Setting).all()}
    return {k: _cast(k, rows[k]) if k in rows else v for k, v in DEFAULTS.items()}


def update_settings(values: dict):
    with SessionLocal() as db:
        for k, v in values.items():
            if k not in DEFAULTS or v is None:
                continue
            v = _cast(k, v)
            row = db.get(Setting, k)
            if row:
                row.value = str(v)
            else:
                db.add(Setting(key=k, value=str(v)))
        db.commit()
    return get_settings()
