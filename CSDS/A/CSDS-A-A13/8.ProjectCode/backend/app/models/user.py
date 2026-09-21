from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._common import utcnow

ROLE_ADMIN = "admin"
ROLE_INVIGILATOR = "invigilator"
STATUS_ACTIVE = "active"
STATUS_PENDING = "pending"
STATUS_DISABLED = "disabled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=ROLE_INVIGILATOR)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_PENDING)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(default=None)

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
