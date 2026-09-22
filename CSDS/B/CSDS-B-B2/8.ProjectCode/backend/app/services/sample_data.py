"""Sample data: replay a few public drive-test traces through the real ingestion pipeline on first start.

The readings, zones and complaints this creates are genuine outputs of the classifier and zone engine, and
are tagged source="sample_dataset" (shown with a "Sample" badge, removable from Settings). Dates are moved
forward by whole weeks so weekday and time-of-day patterns stay true to the original measurements.
"""
from __future__ import annotations

import logging
import math
import threading
from datetime import timedelta

import numpy as np
import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import SessionLocal, utcnow
from ..core.logging import log_event
from ..core.security import new_device_key
from ..models import Complaint, Device, Reading, User, ZoneState
from ..schemas.readings import ReadingIn
from .ingest import ingest

log = logging.getLogger("signalscout.sample")

CITY_BBOX = (51.84, 51.95, -8.62, -8.34)       # Cork city and suburbs - where the drive tests are densest
TRACES_PER_OPERATOR = 8
STEP = 2                                        # keep every 2nd reading of the 1 Hz traces
status = {"state": "idle", "readings": 0}


def _pick_traces(df: pd.DataFrame) -> list[str]:
    lat0, lat1, lon0, lon1 = CITY_BBOX
    inside = df[df.lat.between(lat0, lat1) & df.lon.between(lon0, lon1) & (df.family == "lte_nr")]
    counts = inside.groupby(["operator", "device_key", "mobility"]).size().reset_index(name="n")
    counts = counts[(counts.n >= 300) & counts.mobility.isin(["pedestrian", "car", "bus"])]
    counts = counts.sort_values(["n", "device_key"], ascending=[False, True])      # the longest walks and drives cover most ground
    return sorted(counts.groupby("operator").head(TRACES_PER_OPERATOR).device_key.tolist())


def seed_sample_data(db: Session) -> int:
    if db.query(Reading.id).filter(Reading.source == "sample_dataset").first():
        return 0
    path = settings.data_dir / "processed" / "lte_speed_clean.csv.gz"
    if not path.exists():
        log.warning("processed dataset missing - run python ml/prepare_data.py; no sample data loaded")
        return 0
    admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
    if not admin:
        return 0
    status.update(state="loading", readings=0)
    df = pd.read_csv(path, parse_dates=["ts"])
    traces = _pick_traces(df)
    lat0, lat1, lon0, lon1 = CITY_BBOX
    data = df[df.device_key.isin(traces) & (df.family == "lte_nr") & df.lat.between(lat0, lat1) & df.lon.between(lon0, lon1)]
    data = data[data.groupby("device_key").cumcount() % STEP == 0].sort_values("ts")
    weeks = math.floor((utcnow() - data.ts.max().to_pydatetime()).days / 7)
    shift = timedelta(weeks=weeks)

    device = db.query(Device).filter(Device.kind == "replay").first()
    if not device:
        _, key_hash, prefix = new_device_key()
        device = Device(owner_id=admin.id, kind="replay", name="Public drive-test replay", api_key_hash=key_hash, api_key_prefix=prefix,
                        hardware="4G LTE Speed Dataset (Cork), replayed", config={"traces": traces, "shift_weeks": weeks})
        db.add(device)
        db.commit()
        db.refresh(device)

    def num(v):
        return None if pd.isna(v) else float(v)

    items = [ReadingIn(
        client_uuid=f"sample-{r.device_key.replace('/', '-')}-{i}", ts=r.ts.to_pydatetime() + shift, lat=r.lat, lon=r.lon, accuracy_m=5.0,
        operator=r.operator, network_type=r.network_mode, rsrp=num(r.level), rsrq=num(r.quality), sinr=num(r.sinr), rssi=num(r.rssi),
        cqi=num(r.cqi), cell_id=None if pd.isna(r.cell_id) else int(r.cell_id),
        dl_mbps=None if pd.isna(r.dl_kbps) else r.dl_kbps / 1000.0, ul_mbps=None if pd.isna(r.ul_kbps) else r.ul_kbps / 1000.0,
    ) for i, r in zip(np.arange(len(data)), data.itertuples())]
    total = 0
    for start in range(0, len(items), 500):
        total += ingest(db, device, items[start:start + 500], publish=False).result.accepted
        status["readings"] = total
    status.update(state="done", readings=total)
    log_event(log, "sample data loaded", readings=total, traces=len(traces), shifted_weeks=weeks)
    return total


def seed_in_background() -> None:
    def run():
        try:
            with SessionLocal() as db:
                seed_sample_data(db)
        except Exception:
            status["state"] = "error"
            log.exception("sample data could not be loaded")
    threading.Thread(target=run, name="sample-data", daemon=True).start()


def remove_sample_data(db: Session) -> dict:
    readings = db.execute(delete(Reading).where(Reading.source == "sample_dataset")).rowcount
    complaints = db.execute(delete(Complaint).where(Complaint.source == "sample_dataset")).rowcount
    db.execute(delete(Device).where(Device.kind == "replay"))
    db.commit()
    # zone states are rebuilt from what remains
    db.execute(delete(ZoneState))
    db.commit()
    status.update(state="removed", readings=0)
    return {"readings": readings, "complaints": complaints}
