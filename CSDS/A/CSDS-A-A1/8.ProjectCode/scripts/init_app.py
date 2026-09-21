"""Prepare the database, demo account, sample policies and search index (used by setup.bat and reset.bat).

Usage (from the project root):
    venv\\Scripts\\python scripts\\init_app.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    from sqlalchemy import select

    from app.core.config import get_settings
    from app.core.db import SessionLocal, init_db
    from app.core.logging import configure_logging
    from app.models import Document
    from app.services import ingestion
    from app.services.seed import seed_all

    configure_logging()
    settings = get_settings()
    init_db()
    print(f"[OK]   Database ready at {settings.db_path.relative_to(ROOT)}")
    ingestion.start_worker()
    seed_all()
    start = time.time()
    print("       Building the search index for the sample policies (first run takes about a minute)...", flush=True)
    ingestion.wait_until_idle(timeout=1800)
    ingestion.stop_worker()
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(Document.is_sample.is_(True))).all()
        for d in docs:
            card = "Policy Card ready" if d.card else (d.extraction_error or "no Policy Card")
            print(f"[{'OK' if d.status == 'ready' else '!!'}]   {d.product_name or d.file_name}: {d.status}, "
                  f"{len(d.clauses)} clauses, {card}")
    print(f"[OK]   Sample data ready in {time.time() - start:.0f}s")
    print(f"       Demo login: {settings.demo_email} / {settings.demo_password}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
