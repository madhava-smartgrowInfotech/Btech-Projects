"""SQLite storage for one hospital's FHIR resources (one file per hospital)."""
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS resources (
    type TEXT NOT NULL,
    id TEXT NOT NULL,
    patient_id TEXT,
    date TEXT,
    json TEXT NOT NULL,
    PRIMARY KEY (type, id)
);
CREATE INDEX IF NOT EXISTS ix_res_patient ON resources (patient_id, type);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def resource_date(res: dict) -> str | None:
    """Best clinical date of a resource, used for sorting timelines."""
    for key in ("effectiveDateTime", "authoredOn", "recordedDate", "onsetDateTime", "issued", "occurrenceDateTime"):
        if res.get(key):
            return res[key]
    period = res.get("period") or {}
    return period.get("start")


def upsert(conn: sqlite3.Connection, res: dict, patient_id: str | None) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO resources (type, id, patient_id, date, json) VALUES (?, ?, ?, ?, ?)",
        (res["resourceType"], res["id"], patient_id, resource_date(res), json.dumps(res)),
    )
