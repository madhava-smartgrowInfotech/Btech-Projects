"""SQLite persistence of review history."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "history.db"


def _conn():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS reviews(
        id TEXT PRIMARY KEY, created TEXT, title TEXT, source TEXT, score INTEGER, verdict TEXT,
        n_findings INTEGER, n_security INTEGER, payload TEXT)""")
    return c


def save(review: dict):
    sec = sum(1 for f in review["findings"] if f["category"] == "security" and f["in_diff"])
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?,?,?,?,?)",
                  (review["id"], review["created"], review["title"], review["source"], review["score"], review["verdict"],
                   len(review["findings"]), sec, json.dumps(review, default=str)))


def list_reviews(limit=100) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT id,created,title,source,score,verdict,n_findings,n_security FROM reviews "
                         "ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    keys = ["id", "created", "title", "source", "score", "verdict", "findings", "security"]
    return [dict(zip(keys, r)) for r in rows]


def load(review_id: str) -> dict | None:
    with _conn() as c:
        r = c.execute("SELECT payload FROM reviews WHERE id=?", (review_id,)).fetchone()
    return json.loads(r[0]) if r else None


def delete(review_id: str):
    with _conn() as c:
        c.execute("DELETE FROM reviews WHERE id=?", (review_id,))
