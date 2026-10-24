"""Local numeric event history and atomic JSON settings. No imagery is stored."""
import csv
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from core import Settings

class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory/'events.sqlite3')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp TEXT, source TEXT, state TEXT, quality TEXT, reason TEXT, ear REAL, closure REAL, blink_rate REAL, closed_fraction REAL, roll REAL, alert INTEGER)')
        self.db.commit()

    def add(self, source, decision):
        d = asdict(decision)
        values = [datetime.now(timezone.utc).isoformat(), source] + [d[k] for k in ('state','quality','reason','ear','closure','blink_rate','closed_fraction','roll','alert')]
        self.db.execute('INSERT INTO events VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)', values)
        self.db.commit()

    def recent(self, limit=500):
        return self.db.execute('SELECT * FROM events ORDER BY id DESC LIMIT ?', (limit,)).fetchall()

    def export(self, path):
        cursor = self.db.execute('SELECT * FROM events ORDER BY id')
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([d[0] for d in cursor.description])
            writer.writerows(cursor)

    def load_settings(self):
        path = self.directory/'settings.json'
        if not path.exists():
            return Settings(), 'Default threshold: calibrate before a live demonstration.'
        try:
            return Settings(**json.loads(path.read_text(encoding='utf-8'))).validate(), 'Saved settings loaded.'
        except (OSError, ValueError, TypeError):
            return Settings(), 'Invalid saved settings; safe defaults loaded. Recalibrate.'

    def save_settings(self, settings):
        settings.validate()
        temporary = self.directory/'settings.tmp'
        temporary.write_text(json.dumps(asdict(settings), indent=2), encoding='utf-8')
        temporary.replace(self.directory/'settings.json')

    def close(self):
        self.db.close()
