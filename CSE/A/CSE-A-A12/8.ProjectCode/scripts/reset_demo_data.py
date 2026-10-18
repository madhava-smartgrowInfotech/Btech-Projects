"""
Clears the prediction history and the saved uploads/heatmaps (demo data only).
Use it before capturing screenshots or handing the project over.

    python scripts/reset_demo_data.py
"""

import glob
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db = os.path.join(ROOT, "pneumonia_app.db")
if os.path.exists(db):
    c = sqlite3.connect(db)
    try:
        c.execute("DELETE FROM predictions")
        c.execute("DELETE FROM sqlite_sequence WHERE name='predictions'")
        c.commit()
    except sqlite3.OperationalError:
        pass  # table not created yet
    c.close()

removed = 0
for folder in ("uploads", "heatmaps"):
    for f in glob.glob(os.path.join(ROOT, "static", folder, "*")):
        if not f.endswith(".gitkeep"):
            os.remove(f)
            removed += 1
print(f"History cleared, {removed} image files removed.")
