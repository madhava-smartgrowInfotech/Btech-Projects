"""Database models for CipherVault."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # base64 SPKI
    encrypted_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON bundle
    private_key_salt: Mapped[str | None] = mapped_column(String(64), nullable=True)  # base64
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    files = relationship("FileRecord", back_populates="owner", cascade="all, delete-orphan")
    audit_events = relationship("AuditLog", back_populates="user")


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False, default="application/octet-stream")
    encrypted_size: Mapped[int] = mapped_column(nullable=False, default=0)
    original_size: Mapped[int] = mapped_column(nullable=False, default=0)
    iv: Mapped[str] = mapped_column(String(64), nullable=False)  # base64, 12 bytes
    owner_wrapped_fek: Mapped[str] = mapped_column(Text, nullable=False)  # base64 RSA-OAEP output
    plaintext_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    owner = relationship("User", back_populates="files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_files_owner_created", "owner_id", "created_at"),)


class FilePermission(Base):
    __tablename__ = "file_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # viewer | editor
    wrapped_fek: Mapped[str] = mapped_column(Text, nullable=False)  # recipient-specific RSA-wrapped FEK
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    file = relationship("FileRecord", back_populates="permissions")

    __table_args__ = (UniqueConstraint("file_id", "user_id", name="uq_file_user"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="GENESIS")
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    user = relationship("User", back_populates="audit_events")

    __table_args__ = (Index("ix_audit_file_time", "file_id", "timestamp_utc"),)
