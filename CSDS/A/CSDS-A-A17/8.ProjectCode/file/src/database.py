"""
database.py
-----------
Lightweight SQLite-backed detection history store. Records one
row per image analysed: filename, object count, average
confidence and timestamp. Used by the History and Dashboard
pages.
"""

import sqlite3
from pathlib import Path

from src.utils import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "detection_history.db"


def init_db(db_path: str | Path = DB_PATH) -> None:
    """Create the history table if it doesn't already exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                object_count INTEGER NOT NULL,
                avg_confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def add_record(filename: str, object_count: int, avg_confidence: float,
                timestamp: str, db_path: str | Path = DB_PATH) -> None:
    """Insert one detection-run record into the history table."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO detection_history (filename, object_count, avg_confidence, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (filename, object_count, avg_confidence, timestamp),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(db_path: str | Path = DB_PATH) -> list[dict]:
    """Return all history rows, most recent first."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT filename, object_count, avg_confidence, timestamp "
            "FROM detection_history ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_history(db_path: str | Path = DB_PATH) -> None:
    """Delete all rows from the history table."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM detection_history")
        conn.commit()
    finally:
        conn.close()
