"""Audit-log tests: event creation, hash chaining, verification, tamper detection."""

from tests.conftest import auth, upload_ciphertext


def test_audit_events_and_chain_verification(client, owner):
    _, token = owner
    upload_ciphertext(client, token, filename="audited.txt")
    events = client.get("/api/audit?limit=50", headers=auth(token)).json()
    assert len(events) >= 2
    assert all(e["current_hash"] and e["previous_hash"] for e in events)

    v = client.get("/api/audit/verify", headers=auth(token)).json()
    assert v["valid"] is True
    assert v["checked"] >= 2


def test_audit_tamper_detection(client, owner):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.app.db.database import get_session_factory
    from backend.app.db.models import AuditLog
    from backend.app.services import audit_service

    _, token = owner
    upload_ciphertext(client, token, filename="tamper.txt")
    db = get_session_factory()()
    try:
        first = db.query(AuditLog).order_by(AuditLog.id.asc()).first()
        first.details = "TAMPERED DETAILS"
        db.commit()
        valid, checked, failure = audit_service.verify_chain(db)
        assert valid is False
        assert failure == first.id
    finally:
        db.close()
