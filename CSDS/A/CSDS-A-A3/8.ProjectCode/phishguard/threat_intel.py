"""Stage 3 - crowdsourced threat intelligence.

Objective 4: community members (and optional public feeds) report URLs as
phishing or safe. Reports are stored in SQLite. A URL becomes *confirmed*
phishing when its net vote count reaches `CONSENSUS_THRESHOLD`, or when it
arrives from a trusted feed. Confirmed entries:

    1. override the ML model immediately at check time (zero-day coverage), and
    2. feed the continuous retraining loop (see retrain.py).
"""
from __future__ import annotations

import sqlite3
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config
from .features import normalize_url

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url_norm    TEXT NOT NULL,
    url         TEXT NOT NULL,
    verdict     TEXT NOT NULL CHECK (verdict IN ('phishing','safe')),
    reporter    TEXT NOT NULL DEFAULT 'anonymous',
    source      TEXT NOT NULL DEFAULT 'community',
    note        TEXT,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_url ON reports(url_norm);
CREATE TABLE IF NOT EXISTS intel (
    url_norm        TEXT PRIMARY KEY,
    url             TEXT NOT NULL,
    phishing_votes  INTEGER NOT NULL DEFAULT 0,
    safe_votes      INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending',   -- pending | confirmed_phishing | confirmed_safe
    source          TEXT NOT NULL DEFAULT 'community',
    first_seen      TEXT NOT NULL,
    last_updated    TEXT NOT NULL,
    used_in_training INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS checks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT NOT NULL,
    verdict     TEXT NOT NULL,
    probability REAL,
    decided_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ThreatIntel:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or config.TI_DATABASE)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Reporting
    # ------------------------------------------------------------------ #
    def report(self, url: str, verdict: str, reporter: str = "anonymous",
               note: str = "", source: str = "community", trusted: bool = False) -> dict:
        """Record a report and recompute consensus for the URL."""
        verdict = verdict.lower().strip()
        if verdict not in ("phishing", "safe"):
            raise ValueError("verdict must be 'phishing' or 'safe'")
        url_norm = normalize_url(url)
        if not url_norm:
            raise ValueError("empty URL")
        now = _now()
        with self._conn() as c:
            c.execute(
                "INSERT INTO reports(url_norm,url,verdict,reporter,source,note,created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (url_norm, url.strip(), verdict, reporter or "anonymous", source, note, now),
            )
            row = c.execute("SELECT * FROM intel WHERE url_norm=?", (url_norm,)).fetchone()
            if row is None:
                p, s = (1, 0) if verdict == "phishing" else (0, 1)
                c.execute(
                    "INSERT INTO intel(url_norm,url,phishing_votes,safe_votes,status,source,"
                    "first_seen,last_updated) VALUES (?,?,?,?,?,?,?,?)",
                    (url_norm, url.strip(), p, s, "pending", source, now, now),
                )
                p_votes, s_votes = p, s
            else:
                p_votes = row["phishing_votes"] + (verdict == "phishing")
                s_votes = row["safe_votes"] + (verdict == "safe")
            status = self._consensus(p_votes, s_votes, trusted and verdict == "phishing")
            c.execute(
                "UPDATE intel SET phishing_votes=?, safe_votes=?, status=?, last_updated=?,"
                " used_in_training = CASE WHEN status=? THEN used_in_training ELSE 0 END"
                " WHERE url_norm=?",
                (p_votes, s_votes, status, now, status, url_norm),
            )
        return self.lookup(url)

    @staticmethod
    def _consensus(p_votes: int, s_votes: int, trusted: bool = False) -> str:
        net = p_votes - s_votes
        if trusted or net >= config.CONSENSUS_THRESHOLD:
            return "confirmed_phishing"
        if -net >= config.CONSENSUS_THRESHOLD:
            return "confirmed_safe"
        return "pending"

    # ------------------------------------------------------------------ #
    # Lookup
    # ------------------------------------------------------------------ #
    def lookup(self, url: str) -> dict | None:
        url_norm = normalize_url(url)
        with self._conn() as c:
            row = c.execute("SELECT * FROM intel WHERE url_norm=?", (url_norm,)).fetchone()
            if row is None:
                # also match on the bare host so a confirmed domain covers its pages
                return None
            reports = c.execute(
                "SELECT verdict, reporter, source, note, created_at FROM reports "
                "WHERE url_norm=? ORDER BY id DESC LIMIT 10", (url_norm,)).fetchall()
        d = dict(row)
        d["reports"] = [dict(r) for r in reports]
        return d

    def lookup_host(self, url: str) -> dict | None:
        """Return a confirmed-phishing entry whose host matches this URL's host."""
        from urllib.parse import urlsplit
        host = (urlsplit(normalize_url(url)).hostname or "").lower()
        if not host:
            return None
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM intel WHERE status='confirmed_phishing' AND "
                "(url_norm LIKE ? OR url_norm LIKE ?)",
                (f"http://{host}%", f"https://{host}%")).fetchall()
        for r in rows:
            h = (urlsplit(r["url_norm"]).hostname or "").lower()
            if h == host:
                return dict(r)
        return None

    def recent(self, limit: int = 50, status: str | None = None) -> list[dict]:
        q = "SELECT * FROM intel"
        args: tuple = ()
        if status:
            q += " WHERE status=?"
            args = (status,)
        q += " ORDER BY last_updated DESC LIMIT ?"
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args + (limit,)).fetchall()]

    def training_examples(self, only_new: bool = False) -> list[tuple[str, int]]:
        """Confirmed URLs as (url, label) pairs for retraining."""
        q = ("SELECT url_norm, status FROM intel WHERE status IN "
             "('confirmed_phishing','confirmed_safe')")
        if only_new:
            q += " AND used_in_training=0"
        with self._conn() as c:
            rows = c.execute(q).fetchall()
        return [(r["url_norm"], 1 if r["status"] == "confirmed_phishing" else 0) for r in rows]

    def mark_trained(self) -> int:
        with self._conn() as c:
            cur = c.execute("UPDATE intel SET used_in_training=1 WHERE status LIKE 'confirmed_%'")
            return cur.rowcount

    def pending_training_count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM intel WHERE status LIKE 'confirmed_%' "
                             "AND used_in_training=0").fetchone()[0]

    # ------------------------------------------------------------------ #
    # Check logging (for the dashboard)
    # ------------------------------------------------------------------ #
    def log_check(self, url: str, verdict: str, probability: float | None, decided_by: str):
        with self._conn() as c:
            c.execute("INSERT INTO checks(url,verdict,probability,decided_by,created_at) "
                      "VALUES (?,?,?,?,?)", (url, verdict, probability, decided_by, _now()))

    def recent_checks(self, limit: int = 20) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM checks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def stats(self) -> dict:
        with self._conn() as c:
            s = {
                "reports": c.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
                "urls_tracked": c.execute("SELECT COUNT(*) FROM intel").fetchone()[0],
                "confirmed_phishing": c.execute(
                    "SELECT COUNT(*) FROM intel WHERE status='confirmed_phishing'").fetchone()[0],
                "confirmed_safe": c.execute(
                    "SELECT COUNT(*) FROM intel WHERE status='confirmed_safe'").fetchone()[0],
                "pending": c.execute(
                    "SELECT COUNT(*) FROM intel WHERE status='pending'").fetchone()[0],
                "checks": c.execute("SELECT COUNT(*) FROM checks").fetchone()[0],
                "awaiting_training": c.execute(
                    "SELECT COUNT(*) FROM intel WHERE status LIKE 'confirmed_%' "
                    "AND used_in_training=0").fetchone()[0],
            }
        return s

    # ------------------------------------------------------------------ #
    # Public feed synchronisation (optional)
    # ------------------------------------------------------------------ #
    def sync_feeds(self, feeds: dict | None = None, limit_per_feed: int = 500,
                   timeout: int = 20) -> dict:
        """Pull newly reported phishing URLs from trusted public feeds.

        Each feed line is treated as one trusted phishing report. Network
        failures are reported, not raised, so the app keeps working offline.
        """
        feeds = feeds or config.THREAT_FEEDS
        outcome = {}
        for name, feed_url in feeds.items():
            try:
                req = urllib.request.Request(feed_url, headers={"User-Agent": "PhishGuard/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    text = resp.read().decode("utf-8", errors="ignore")
                added = 0
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    self.report(line, "phishing", reporter=f"feed:{name}", source=name,
                                trusted=True)
                    added += 1
                    if added >= limit_per_feed:
                        break
                outcome[name] = {"ok": True, "added": added}
            except Exception as exc:  # noqa: BLE001
                outcome[name] = {"ok": False, "error": str(exc)[:200]}
        return outcome
