"""Export this installation's own field readings as an anonymised sample in data/field/.

    venv\\Scripts\\python scripts\\export_field_sample.py              # phone probe (mobile data) + ESP32 nodes
    venv\\Scripts\\python scripts\\export_field_sample.py --min 200    # refuse to write a sample smaller than 200 readings
    venv\\Scripts\\python scripts\\export_field_sample.py --all        # also readings over Wi-Fi or from this PC's own network

Only readings measured by real devices are exported (source "phone" or "esp32"); the public-dataset sample and the
simulator are left out. Anonymisation:
  - positions rounded to 3 decimals (about 110 m) and the zone recomputed from the rounded position;
  - times rounded down to the minute;
  - device and account identifiers replaced by pseudonyms in order of first appearance (phone-1, node-1, ...);
  - reading IDs, receipt times, network numbers (ASN) and serving-cell identifiers are dropped.
The output is deterministic for the same database (sorted rows, gzip without a timestamp).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import h3  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.models import Device, Reading  # noqa: E402

OUT = ROOT / "data" / "field"
COLUMNS = ["ts", "device", "source", "lat", "lon", "h3_cell", "accuracy_m", "operator", "link", "network_type", "connected",
           "latency_ms", "jitter_ms", "packet_loss", "probes_sent", "probes_ok", "dl_mbps", "ul_mbps", "effective_type",
           "downlink_est", "rtt_est", "wifi_rssi", "ble_rssi", "rsrp", "rsrq", "sinr", "rssi", "zone_label", "zone_confidence",
           "label_method", "radio_estimate", "radio_estimate_conf"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--min", type=int, default=50, help="minimum number of readings needed to write a sample")
    ap.add_argument("--all", action="store_true", help="include readings over Wi-Fi and from this PC's own network")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        q = db.query(Reading).filter(Reading.source.in_(("phone", "esp32")))
        if not args.all:
            q = q.filter(~((Reading.source == "phone") & (Reading.link == "wifi")), Reading.operator != "Local network")
        rows = q.order_by(Reading.ts, Reading.id).all()
        kinds = {d.id: d.kind for d in db.query(Device).all()}
    finally:
        db.close()

    if len(rows) < args.min:
        print(f"Only {len(rows)} field readings found (need at least {args.min}). Collect more with the field probe "
              "(mobile data on, Wi-Fi off) or an ESP32 node, then run this again.")
        return 1

    names: dict[int, str] = {}
    per_kind: Counter = Counter()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        if r.device_id not in names:
            kind = "node" if kinds.get(r.device_id) == "esp32" else "phone"
            per_kind[kind] += 1
            names[r.device_id] = f"{kind}-{per_kind[kind]}"
        lat, lon = round(r.lat, 3), round(r.lon, 3)
        rec = {k: getattr(r, k, None) for k in COLUMNS if hasattr(Reading, k)}
        rec.update(ts=r.ts.replace(second=0, microsecond=0).isoformat() + "Z", device=names[r.device_id], lat=lat, lon=lon,
                   h3_cell=h3.latlng_to_cell(lat, lon, settings.h3_resolution))
        w.writerow({k: ("" if v is None else v) for k, v in rec.items()})

    OUT.mkdir(parents=True, exist_ok=True)
    data = buf.getvalue().encode("utf-8")
    with open(OUT / "field_readings.csv.gz", "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz:
        gz.write(data)
    summary = {
        "readings": len(rows), "devices": dict(per_kind), "from": rows[0].ts.isoformat() + "Z", "to": rows[-1].ts.isoformat() + "Z",
        "by_source": dict(Counter(r.source for r in rows)), "by_operator": dict(Counter(r.operator for r in rows)),
        "by_class": dict(Counter(r.zone_label for r in rows if r.zone_label)), "zones": len({(r.h3_cell, r.operator) for r in rows}),
        "anonymisation": "positions rounded to 3 decimals (~110 m), times to the minute, device pseudonyms; IDs, ASN and cell identifiers dropped",
        "columns": COLUMNS,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} readings from {len(names)} devices to {OUT / 'field_readings.csv.gz'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
