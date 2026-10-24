"""SentinelFlow SQLite storage (detections, mitigations, health, settings)."""

import json
import sqlite3
import threading
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    interface TEXT NOT NULL,
    source TEXT NOT NULL,
    prediction TEXT NOT NULL,
    confidence REAL NOT NULL,
    severity TEXT NOT NULL,
    packet_rate REAL NOT NULL,
    byte_rate REAL NOT NULL,
    source_count INTEGER NOT NULL,
    destination_count INTEGER NOT NULL,
    distributed_risk REAL NOT NULL,
    mitigation_status TEXT NOT NULL,
    detail_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mitigations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    ip TEXT NOT NULL,
    reason TEXT NOT NULL,
    duration INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS health_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    cpu_percent REAL NOT NULL,
    memory_percent REAL NOT NULL,
    bytes_sent INTEGER NOT NULL,
    bytes_recv INTEGER NOT NULL,
    packets_sent INTEGER NOT NULL,
    packets_recv INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        try:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
        except Exception as exc:
            raise RuntimeError("SentinelFlow database initialization failed at %s: %s" % (path, exc))

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # -- detections ---------------------------------------------------
    def add_detection(self, record: dict) -> int:
        with self._lock:
            try:
                with self._connect() as conn:
                    cur = conn.execute(
                        """INSERT INTO detections (timestamp, interface, source, prediction,
                           confidence, severity, packet_rate, byte_rate, source_count,
                           destination_count, distributed_risk, mitigation_status, detail_json)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (record.get("timestamp", time.time()),
                         record.get("interface", ""),
                         record.get("source", ""),
                         record.get("prediction", ""),
                         float(record.get("confidence", 0)),
                         record.get("severity", ""),
                         float(record.get("packet_rate", 0)),
                         float(record.get("byte_rate", 0)),
                         int(record.get("source_count", 0)),
                         int(record.get("destination_count", 0)),
                         float(record.get("distributed_risk", 0)),
                         record.get("mitigation_status", ""),
                         json.dumps(record.get("detail", {}), default=str)),
                    )
                    conn.commit()
                    return int(cur.lastrowid)
            except Exception as exc:
                raise RuntimeError("Failed to store detection event: %s" % exc)

    def get_detections(self, limit: int = 100) -> list:
        with self._lock:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                raise RuntimeError("Failed to read detections: %s" % exc)

    def count_by_prediction(self) -> dict:
        with self._lock:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT prediction, COUNT(*) c FROM detections GROUP BY prediction").fetchall()
                    return {r["prediction"]: r["c"] for r in rows}
            except Exception:
                return {}

    def count_by_severity(self) -> dict:
        with self._lock:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT severity, COUNT(*) c FROM detections GROUP BY severity").fetchall()
                    return {r["severity"]: r["c"] for r in rows}
            except Exception:
                return {}

    # -- mitigations --------------------------------------------------
    def add_mitigation(self, ip: str, reason: str, duration: int, status: str):
        with self._lock:
            try:
                with self._connect() as conn:
                    conn.execute(
                        "INSERT INTO mitigations (timestamp, ip, reason, duration, status) VALUES (?,?,?,?,?)",
                        (time.time(), ip, reason, int(duration), status))
                    conn.commit()
            except Exception as exc:
                raise RuntimeError("Failed to store mitigation event: %s" % exc)

    def mark_mitigation_recovered(self, ip: str, reason: str):
        with self._lock:
            try:
                with self._connect() as conn:
                    conn.execute(
                        """UPDATE mitigations SET status='recovered'
                           WHERE ip=? AND reason=? AND status='active'""", (ip, reason))
                    conn.commit()
            except Exception as exc:
                print("SentinelFlow recovery-history write failed: %s" % exc)

    def get_mitigations(self, limit: int = 100) -> list:
        with self._lock:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT * FROM mitigations ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                raise RuntimeError("Failed to read mitigations: %s" % exc)

    # -- health -------------------------------------------------------
    def add_health(self, sample: dict):
        with self._lock:
            try:
                with self._connect() as conn:
                    conn.execute(
                        """INSERT INTO health_samples (timestamp, cpu_percent, memory_percent,
                           bytes_sent, bytes_recv, packets_sent, packets_recv)
                           VALUES (?,?,?,?,?,?,?)""",
                        (sample.get("timestamp", time.time()),
                         float(sample.get("cpu_percent", 0)),
                         float(sample.get("memory_percent", 0)),
                         int(sample.get("bytes_sent", 0)),
                         int(sample.get("bytes_recv", 0)),
                         int(sample.get("packets_sent", 0)),
                         int(sample.get("packets_recv", 0))))
                    conn.commit()
            except Exception as exc:
                print("SentinelFlow health-history write failed: %s" % exc)

    def get_health_history(self, limit: int = 60) -> list:
        with self._lock:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT * FROM health_samples ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
                    return [dict(r) for r in reversed(rows)]
            except Exception:
                return []

    # -- settings -----------------------------------------------------
    def get_setting(self, key: str, default: str = "") -> str:
        with self._lock:
            try:
                with self._connect() as conn:
                    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
                    return row["value"] if row else default
            except Exception:
                return default

    def set_setting(self, key: str, value: str):
        with self._lock:
            try:
                with self._connect() as conn:
                    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
                    conn.commit()
            except Exception as exc:
                raise RuntimeError("Failed to store setting: %s" % exc)
