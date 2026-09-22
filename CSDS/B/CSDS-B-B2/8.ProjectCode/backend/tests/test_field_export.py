"""The anonymised field-sample export: rounded positions, pseudonymous devices, no identifiers, deterministic output."""
from __future__ import annotations

import csv
import gzip
import importlib.util
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("export_field_sample", ROOT / "scripts" / "export_field_sample.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_export_is_anonymised_and_repeatable(client, user_headers, tmp_path, monkeypatch):
    key = client.post("/api/devices/phone", headers=user_headers, json={"name": "Export test phone"}).json()["api_key"]
    start = datetime.now(timezone.utc) - timedelta(minutes=10)
    batch = [{"client_uuid": f"export-{i}", "ts": (start + timedelta(seconds=20 * i)).isoformat(), "lat": 26.912345 + i * 1e-4,
              "lon": 75.787654, "accuracy_m": 8, "connection_type": "cellular", "connected": True, "latency_ms": 80 + i, "probes_sent": 3, "probes_ok": 3}
             for i in range(6)]
    r = client.post("/api/ingest/readings", headers={"X-Device-Key": key}, json={"readings": batch})
    assert r.status_code == 200

    mod = _load()
    monkeypatch.setattr(mod, "OUT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["export_field_sample.py", "--min", "1"])
    assert mod.main() == 0
    first = (tmp_path / "field_readings.csv.gz").read_bytes()
    assert mod.main() == 0
    assert (tmp_path / "field_readings.csv.gz").read_bytes() == first, "same database -> identical file"

    rows = list(csv.DictReader(io.StringIO(gzip.decompress(first).decode("utf-8"))))
    assert rows and set(rows[0]) == set(mod.COLUMNS)
    assert not {"client_uuid", "device_id", "asn", "cell_id", "id"} & set(rows[0])
    mine = [x for x in rows if x["lon"] == "75.788"]
    assert len(mine) == 6
    assert all(len(x["lat"].split(".")[1]) <= 3 for x in mine)
    assert all(x["ts"].endswith(":00Z") for x in mine)
    assert all(x["device"].startswith("phone-") for x in rows if x["source"] == "phone")
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["readings"] == len(rows)
