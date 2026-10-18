"""Persistence. SQLite via the standard library behind a small interface so PostgreSQL can replace it later."""
from __future__ import annotations

import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store(ABC):
    @abstractmethod
    def create_run(self, run_id: str, config: dict, resolved: dict) -> None: ...
    @abstractmethod
    def finish_run(self, run_id: str, status: str, summary: dict, fingerprint: str) -> None: ...
    @abstractmethod
    def add_event(self, run_id: str, event: dict) -> None: ...
    @abstractmethod
    def add_safety_event(self, run_id: str, event: dict) -> None: ...
    @abstractmethod
    def add_step(self, run_id: str, step: int, row: dict) -> None: ...
    @abstractmethod
    def list_runs(self, limit: int = 50) -> list[dict]: ...
    @abstractmethod
    def get_run(self, run_id: str) -> dict | None: ...
    @abstractmethod
    def list_events(self, run_id: str, event_type: str | None = None, limit: int = 500) -> list[dict]: ...
    @abstractmethod
    def list_safety_events(self, run_id: str, status: str | None = None, limit: int = 500) -> list[dict]: ...
    @abstractmethod
    def get_steps(self, run_id: str) -> list[dict]: ...
    @abstractmethod
    def save_experiment(self, exp_id: str, spec: dict, results: dict) -> None: ...
    @abstractmethod
    def list_experiments(self) -> list[dict]: ...
    @abstractmethod
    def get_experiment(self, exp_id: str) -> dict | None: ...


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, created_at TEXT, finished_at TEXT, status TEXT, config TEXT, resolved TEXT, summary TEXT, fingerprint TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step INTEGER, event_type TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS safety_events(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step INTEGER, status TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS steps(run_id TEXT, step INTEGER, payload TEXT, PRIMARY KEY(run_id, step));
CREATE TABLE IF NOT EXISTS experiments(exp_id TEXT PRIMARY KEY, created_at TEXT, spec TEXT, results TEXT);
CREATE INDEX IF NOT EXISTS ix_events_run ON events(run_id, event_type);
CREATE INDEX IF NOT EXISTS ix_safety_run ON safety_events(run_id, status);
"""


class SQLiteStore(Store):
    def __init__(self, database_url: str):
        path = database_url.replace("sqlite:///", "", 1) if database_url.startswith("sqlite") else database_url
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(SCHEMA)

    def _exec(self, sql: str, args: tuple = ()) -> None:
        with self._lock:
            self._db.execute(sql, args)
            self._db.commit()

    def _q(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(sql, args).fetchall()

    def create_run(self, run_id, config, resolved):
        self._exec("INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?,?,?,?)",
                   (run_id, _now(), None, "running", json.dumps(config), json.dumps(resolved, default=str), "{}", ""))

    def finish_run(self, run_id, status, summary, fingerprint):
        self._exec("UPDATE runs SET finished_at=?, status=?, summary=?, fingerprint=? WHERE run_id=?",
                   (_now(), status, json.dumps(summary, default=str), fingerprint, run_id))

    def add_event(self, run_id, event):
        self._exec("INSERT INTO events(run_id, step, event_type, payload) VALUES(?,?,?,?)",
                   (run_id, event.get("step", -1), event["event_type"], json.dumps(event, default=str)))

    def add_safety_event(self, run_id, event):
        self._exec("INSERT INTO safety_events(run_id, step, status, payload) VALUES(?,?,?,?)",
                   (run_id, event.get("step", -1), event.get("status", event.get("shield_status")), json.dumps(event, default=str)))

    def add_step(self, run_id, step, row):
        self._exec("INSERT OR REPLACE INTO steps VALUES(?,?,?)", (run_id, step, json.dumps(row, default=str)))

    @staticmethod
    def _run(r: sqlite3.Row) -> dict:
        return {"run_id": r["run_id"], "created_at": r["created_at"], "finished_at": r["finished_at"], "status": r["status"],
                "config": json.loads(r["config"]), "summary": json.loads(r["summary"] or "{}"), "fingerprint": r["fingerprint"]}

    def list_runs(self, limit=50):
        return [self._run(r) for r in self._q("SELECT * FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,))]

    def get_run(self, run_id):
        rows = self._q("SELECT * FROM runs WHERE run_id=?", (run_id,))
        if not rows:
            return None
        d = self._run(rows[0])
        d["resolved"] = json.loads(rows[0]["resolved"])
        return d

    def list_events(self, run_id, event_type=None, limit=500):
        if event_type:
            rows = self._q("SELECT payload FROM events WHERE run_id=? AND event_type=? ORDER BY id DESC LIMIT ?", (run_id, event_type, limit))
        else:
            rows = self._q("SELECT payload FROM events WHERE run_id=? ORDER BY id DESC LIMIT ?", (run_id, limit))
        return [json.loads(r["payload"]) for r in rows]

    def list_safety_events(self, run_id, status=None, limit=500):
        if status:
            rows = self._q("SELECT payload FROM safety_events WHERE run_id=? AND status=? ORDER BY id DESC LIMIT ?", (run_id, status, limit))
        else:
            rows = self._q("SELECT payload FROM safety_events WHERE run_id=? ORDER BY id DESC LIMIT ?", (run_id, limit))
        return [json.loads(r["payload"]) for r in rows]

    def get_steps(self, run_id):
        return [json.loads(r["payload"]) for r in self._q("SELECT payload FROM steps WHERE run_id=? ORDER BY step", (run_id,))]

    def save_experiment(self, exp_id, spec, results):
        self._exec("INSERT OR REPLACE INTO experiments VALUES(?,?,?,?)", (exp_id, _now(), json.dumps(spec), json.dumps(results, default=str)))

    def list_experiments(self):
        return [{"exp_id": r["exp_id"], "created_at": r["created_at"], "spec": json.loads(r["spec"])}
                for r in self._q("SELECT exp_id, created_at, spec FROM experiments ORDER BY created_at DESC")]

    def get_experiment(self, exp_id):
        rows = self._q("SELECT * FROM experiments WHERE exp_id=?", (exp_id,))
        if not rows:
            return None
        r = rows[0]
        return {"exp_id": r["exp_id"], "created_at": r["created_at"], "spec": json.loads(r["spec"]), "results": json.loads(r["results"])}
