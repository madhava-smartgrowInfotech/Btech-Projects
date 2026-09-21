"""Create the SeatWise database and demo accounts.

    venv\\Scripts\\python scripts\\init_db.py           # create tables if missing (safe to repeat)
    venv\\Scripts\\python scripts\\init_db.py --reset   # delete the database and start fresh

The API also creates the database on its first start, so this is optional.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset the SeatWise database.")
    parser.add_argument("--reset", action="store_true", help="delete the database file first (all data is lost)")
    args = parser.parse_args()

    from app.core.config import get_settings

    settings = get_settings()
    db_path = Path(settings.database_url.removeprefix("sqlite:///"))
    if args.reset:
        for suffix in ("", "-wal", "-shm", "-journal"):
            target = db_path.with_name(db_path.name + suffix)
            if target.exists():
                try:
                    target.unlink()
                except PermissionError:
                    sys.exit("The database is in use. Stop SeatWise (stop.bat) and try again.")
        print(f"Deleted {db_path}")

    from app.core.db import SessionLocal, create_all
    from app.services.seed import seed_demo_users

    create_all()
    created = 0
    if settings.seed_demo_users:
        with SessionLocal() as db:
            created = seed_demo_users(db, settings)
    print(f"Database ready at {db_path}" + (f" ({created} demo accounts created)" if created else ""))


if __name__ == "__main__":
    main()
