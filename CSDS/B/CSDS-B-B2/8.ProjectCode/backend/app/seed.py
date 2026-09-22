"""First-run data: the three demo accounts (documented in README and docs/03_HOW_TO_RUN.md)."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .core.logging import log_event
from .core.security import hash_password
from .models import User

log = logging.getLogger("signalscout.seed")

DEMO_PASSWORD = "Scout@2026"
DEMO_USERS = [
    {"email": "user@signalscout.demo", "name": "Demo Field User", "role": "user"},
    {"email": "engineer@signalscout.demo", "name": "Demo Engineer", "role": "engineer"},
    {"email": "admin@signalscout.demo", "name": "Demo Admin", "role": "admin"},
]


def seed_demo_users(db: Session) -> int:
    created = 0
    for spec in DEMO_USERS:
        if db.query(User).filter(User.email == spec["email"]).first():
            continue
        db.add(User(**spec, password_hash=hash_password(DEMO_PASSWORD), is_demo=True))
        created += 1
    if created:
        db.commit()
        log_event(log, "demo accounts created", count=created)
    return created
