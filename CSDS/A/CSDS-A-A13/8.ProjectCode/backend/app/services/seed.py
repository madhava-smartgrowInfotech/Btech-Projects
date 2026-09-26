"""Demo accounts, created on first start when the user table is empty."""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models import User
from app.models.user import ROLE_ADMIN, ROLE_INVIGILATOR, STATUS_ACTIVE

log = logging.getLogger("app.seed")

# Sample staff for the demo workspace (fictional people).
SAMPLE_INVIGILATORS = [
    "Maya Fernandes", "Daniel Okafor", "Priya Raman", "Lucas Bennett", "Aisha Karim",
    "Tomas Novak", "Grace Mensah", "Kenji Watanabe", "Elena Petrova",
]


def seed_demo_users(db: Session, settings: Settings) -> int:
    if db.scalar(select(func.count()).select_from(User)):
        return 0
    password = hash_password(settings.demo_password)
    users = [
        User(email=settings.demo_admin_email, full_name="Alex Morgan", role=ROLE_ADMIN,
             status=STATUS_ACTIVE, password_hash=password),
        User(email=settings.demo_invigilator_email, full_name="Sam Taylor", role=ROLE_INVIGILATOR,
             status=STATUS_ACTIVE, password_hash=password),
    ]
    users += [
        User(email=f"inv{i:02d}@seatwise.local", full_name=name, role=ROLE_INVIGILATOR,
             status=STATUS_ACTIVE, password_hash=password)
        for i, name in enumerate(SAMPLE_INVIGILATORS, start=1)
    ]
    db.add_all(users)
    db.commit()
    log.info("Created demo accounts", extra={"count": len(users)})
    return len(users)
