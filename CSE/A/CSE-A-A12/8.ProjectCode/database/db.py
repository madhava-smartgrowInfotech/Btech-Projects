"""
db.py
-----
Lightweight SQLite persistence layer for the Pneumonia Detection system.
Stores every prediction made through the web app so users/doctors can
review history (matches "Technology Awareness" slide: SQLite / MySQL).
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pneumonia_app.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            heatmap_path TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            prob_normal REAL,
            prob_bacterial REAL,
            prob_viral REAL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def insert_prediction(filename, original_path, heatmap_path, prediction,
                       confidence, prob_normal, prob_bacterial, prob_viral):
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO predictions
            (filename, original_path, heatmap_path, prediction, confidence,
             prob_normal, prob_bacterial, prob_viral, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (filename, original_path, heatmap_path, prediction, confidence,
         prob_normal, prob_bacterial, prob_viral, datetime.utcnow().isoformat()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_prediction(pred_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,)).fetchone()
    conn.close()
    return row


def get_all_predictions(limit=200):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows
