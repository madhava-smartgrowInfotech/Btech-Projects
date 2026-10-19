from sqlalchemy.orm import Session
from app.models.models import AuditLog
from datetime import datetime

def log_event(db: Session, actor_user_id, actor_username, action, entity_type=None, entity_id=None, details=None, ip=None):
    entry = AuditLog(
        actor_user_id=actor_user_id,
        actor_username=actor_username,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
        ip_address=ip
    )
    db.add(entry)
    db.commit()
    return entry
