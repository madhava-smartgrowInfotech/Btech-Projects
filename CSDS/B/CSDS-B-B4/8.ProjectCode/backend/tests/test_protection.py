"""Delayed Protection holds, trusted-contact approval, blocking, QR guard and auth."""
from __future__ import annotations

from datetime import timedelta

from app.core.db import SessionLocal
from app.models import Hold, Transaction, utcnow
from app.services.holds import process_due_holds
from tests.conftest import PIN


def _held_payment(client, headers, amount=15000):
    p = client.post("/api/payments/assess", json={"upi_id": "vikram.4411@upg", "amount": amount}, headers=headers).json()
    assert p["assessment"]["level"] == "high", p["assessment"]
    client.post(f"/api/payments/{p['id']}/intent", json={"purpose": "shopping", "asked_by_someone": False, "advance_to_online_seller": False}, headers=headers)
    held = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": PIN}, headers=headers).json()
    assert held["status"] == "held"
    return held


def test_hold_releases_after_cooling_off(client, demo, clock):
    clock("00:45")
    held = _held_payment(client, demo)
    with SessionLocal() as db:
        n = process_due_holds(db, now=utcnow() + timedelta(minutes=31))
        db.commit()
        assert n >= 1
        txn = db.get(Transaction, held["id"])
        assert txn.status == "completed" and txn.hold.status == "released"


def test_trusted_contact_can_reject_a_held_payment(client, demo, family, clock):
    clock("00:50")
    client.put("/api/settings", json={"trusted_approval_required": True}, headers=demo)
    try:
        before = client.get("/api/wallet", headers=demo).json()["balance"]
        held = _held_payment(client, demo, amount=12000)
        assert held["hold"]["needs_approval"] is True
        approvals = client.get("/api/approvals", headers=family).json()["items"]
        item = next(a for a in approvals if a["hold_id"] == held["hold"]["id"])
        assert item["approval_status"] == "pending"
        r = client.post(f"/api/approvals/{item['hold_id']}/reject", headers=family)
        assert r.status_code == 200 and r.json()["status"] == "rejected"
        assert client.get("/api/wallet", headers=demo).json()["balance"] == before
    finally:
        client.put("/api/settings", json={"trusted_approval_required": False}, headers=demo)


def test_hold_without_approval_expires_and_refunds(client, demo, clock):
    clock("01:05")
    client.put("/api/settings", json={"trusted_approval_required": True}, headers=demo)
    try:
        held = _held_payment(client, demo, amount=11000)
        with SessionLocal() as db:
            process_due_holds(db, now=utcnow() + timedelta(minutes=31))
            db.commit()
            h = db.get(Hold, held["hold"]["id"])
            assert h.status == "expired" and h.transaction.status == "cancelled"
    finally:
        client.put("/api/settings", json={"trusted_approval_required": False}, headers=demo)


def test_wrong_pin_is_rejected_and_counted(client, demo, clock):
    clock("10:00")
    p = client.post("/api/payments/assess", json={"upi_id": "anandtea@upg", "amount": 30}, headers=demo).json()
    r = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": "9999"}, headers=demo)
    assert r.status_code == 400 and r.json()["detail"]["code"] == "wrong_pin"
    client.post(f"/api/payments/{p['id']}/cancel", headers=demo)


def test_reported_scam_account_is_blocked(client, demo, clock):
    clock("13:00")
    p = client.post("/api/payments/assess", json={"upi_id": "kyc.helpdesk@upg", "amount": 4999}, headers=demo).json()
    assert p["assessment"]["action"] == "block"
    assert any(r["code"] == "REPORTED" for r in p["assessment"]["reasons"])
    client.post(f"/api/payments/{p['id']}/intent", json={"purpose": "kyc"}, headers=demo)
    r = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": PIN}, headers=demo)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "payment_blocked"


def test_qr_guard_flags_scan_to_receive_and_name_mismatch(client, demo):
    samples = {s["id"]: s for s in client.get("/api/sandbox/samples", headers=demo).json()["qr"]}
    trick = client.post("/api/qr/parse", json={"payload": samples["cashback"]["payload"]}, headers=demo).json()
    assert "scan_to_receive" in trick["flags"] and trick["qr_flag"] == 1.0
    mismatch = client.post("/api/qr/parse", json={"payload": samples["mismatch"]["payload"]}, headers=demo).json()
    assert "name_mismatch" in mismatch["flags"]
    genuine = client.post("/api/qr/parse", json={"payload": samples["grocery"]["payload"]}, headers=demo).json()
    assert genuine["valid"] and not genuine["flags"]
    link = client.post("/api/qr/parse", json={"payload": samples["link"]["payload"]}, headers=demo).json()
    assert "qr_is_link" in link["flags"]


def test_auth_register_login_and_errors(client):
    r = client.post("/api/auth/register", json={"full_name": "Test Person", "phone": "9876500001", "password": "longenough1", "pin": "4321", "language": "te"})
    assert r.status_code == 201, r.text
    assert r.json()["user"]["upi_id"].endswith("@upg") and r.json()["user"]["language"] == "te"
    assert client.post("/api/auth/register", json={"full_name": "Test Person", "phone": "9876500001", "password": "longenough1", "pin": "4321"}).status_code == 409
    bad = client.post("/api/auth/login", json={"identifier": "9876500001", "password": "wrong-password"})
    assert bad.status_code == 401 and bad.json()["detail"]["code"] == "bad_credentials"
    assert client.get("/api/wallet").status_code == 401
    v = client.post("/api/auth/register", json={"full_name": "X", "phone": "12", "password": "secret-value", "pin": "1"})
    assert v.status_code == 422 and "secret-value" not in v.text  # passwords are never echoed back


def test_admin_analytics_require_admin(client, demo, admin):
    assert client.get("/api/admin/overview", headers=demo).status_code == 403
    o = client.get("/api/admin/overview", headers=admin).json()
    assert o["payments_scored"] > 0 and o["payments_stopped"] > 0 and o["sms_scams"] > 0
    assert client.get("/api/admin/trends", headers=admin).status_code == 200
    assert client.get("/api/admin/scam-types", headers=admin).json()["items"]
    assert client.get("/api/admin/reports", headers=admin).json()["items"][0]["reports"] >= 2
    r = client.put("/api/admin/policy", json={"medium": 30, "high": 20, "block_report_score": 2.5}, headers=admin)
    assert r.status_code == 422


def test_models_endpoint_exposes_metrics_and_plots(client, demo):
    m = client.get("/api/models", headers=demo).json()
    assert all(m["loaded"][k]["loaded"] for k in ("behaviour", "sms", "risk"))
    risk = m["models"]["risk"]
    assert risk["models"]["XGBoost"]["test"]["pr_auc"] > 0.5
    assert client.get(risk["plot_urls"][0]).status_code == 200
