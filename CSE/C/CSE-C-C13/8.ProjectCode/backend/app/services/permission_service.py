"""RBAC helpers: owner / editor / viewer enforcement."""

from sqlalchemy.orm import Session

from backend.app.db.models import FilePermission, FileRecord

VALID_SHARE_ROLES = ("viewer", "editor")


def get_effective_role(db: Session, file: FileRecord, user_id: int) -> str | None:
    """Return 'owner', 'editor', 'viewer', or None (no access)."""
    if file.owner_id == user_id:
        return "owner"
    perm = (
        db.query(FilePermission)
        .filter(FilePermission.file_id == file.id, FilePermission.user_id == user_id)
        .first()
    )
    return perm.role if perm else None


def can_read(role: str | None) -> bool:
    return role in ("owner", "editor", "viewer")


def can_write(role: str | None) -> bool:
    return role in ("owner", "editor")


def can_delete(role: str | None) -> bool:
    return role == "owner"


def can_share(role: str | None) -> bool:
    return role == "owner"
