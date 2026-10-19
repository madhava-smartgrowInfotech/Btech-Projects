"""Reset ParkSure demo database to a clean freshly-seeded state."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import Base, engine, SessionLocal
from app.seed import seed_if_empty

if __name__ == "__main__":
    import os
    db_path = Path(__file__).resolve().parent.parent / "parksure.db"
    # Close-aggressive: just remove the file; caller must stop the server first.
    if db_path.exists():
        db_path.unlink()
        print("removed parksure.db")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("seeded:", seed_if_empty(db))
    finally:
        db.close()
