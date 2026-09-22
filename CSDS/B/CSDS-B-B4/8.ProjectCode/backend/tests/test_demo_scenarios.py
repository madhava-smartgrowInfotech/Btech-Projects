"""The four product demo scenarios, end to end through the API with the real models."""
from __future__ import annotations

from tests.conftest import PIN


def _balance(client, headers) -> float:
    return client.get("/api/wallet", headers=headers).json()["balance"]


def test_1_known_contact_normal_amount_is_low_and_paid_instantly(client, demo, clock):
    clock("11:15")
    before = _balance(client, demo)
    r = client.post("/api/payments/assess", json={"upi_id": "ravi.kumar@upg", "amount": 600}, headers=demo)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["status"] == "draft"
    assert p["assessment"]["level"] == "low", p["assessment"]
    assert any(x["code"] == "KNOWN_PAYEE" for x in p["assessment"]["reassurance"])
    r = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": PIN}, headers=demo)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    assert _balance(client, demo) == before - 600


def test_2_kyc_sms_is_a_scam_with_highlights_and_hindi_voice(client, demo, monkeypatch):
    r = client.post("/api/sms/check", json={"text": "Your KYC expires today, click link http://kyc-verify-now.top/a77 to update or your account will be blocked."}, headers=demo)
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["verdict"] == "scam"
    assert c["scam_type"] == "kyc_fraud"
    assert c["highlights"], "scam phrases should be highlighted"
    assert any("KYC" in h["text"] or "block" in h["text"] for h in c["highlights"])
    assert "बैंक" in c["advice"]["hi"]

    spoken = {}

    def fake_synthesize(text, lang, target_dir=None):
        spoken["text"], spoken["lang"] = text, lang
        return "0" * 24, False

    monkeypatch.setattr("app.api.voice.synthesize", fake_synthesize)
    r = client.post(f"/api/voice/sms/{c['id']}", json={"lang": "hi"}, headers=demo)
    assert r.status_code == 200, r.text
    assert spoken["lang"] == "hi" and "सावधान" in spoken["text"]


def test_3_large_new_payee_at_night_is_high_needs_intent_is_held_and_cancelled(client, demo, clock):
    clock("01:30")
    before = _balance(client, demo)
    p = client.post("/api/payments/assess", json={"upi_id": "vikram.4411@upg", "amount": 25000}, headers=demo).json()
    a = p["assessment"]
    assert a["level"] == "high", a
    codes = {r["code"] for r in a["reasons"]}
    assert {"NEW_ACCOUNT", "NIGHT"} & codes, codes
    assert a["contributions"], "SHAP contributions are returned"
    assert p["questions"], "intent questions are offered"

    r = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": PIN}, headers=demo)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "intent_required"

    r = client.post(f"/api/payments/{p['id']}/intent", json={"purpose": "family_friend", "asked_by_someone": True, "verified_by_call": False}, headers=demo)
    assert r.status_code == 200, r.text
    result = r.json()["result"]
    assert result["scam_type"] == "impersonation" and result["final_level"] == "high"

    r = client.post(f"/api/payments/{p['id']}/confirm", json={"pin": PIN}, headers=demo)
    held = r.json()
    assert held["status"] == "held" and held["hold"]["status"] == "active"
    assert _balance(client, demo) == before - 25000  # reserved while on hold

    r = client.post(f"/api/payments/{p['id']}/cancel", headers=demo)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert _balance(client, demo) == before


def test_4_collect_request_disguised_as_refund_warns_it_is_a_debit(client, demo, clock):
    clock("12:00")
    items = client.get("/api/collect/incoming", headers=demo).json()["items"]
    req = next(i for i in items if i["counterparty"]["upi_id"] == "refund.desk@upg" and i["status"] == "pending")
    assert req["guard"]["is_debit"] is True
    assert "deceptive_note" in req["guard"]["flags"]
    p = client.post(f"/api/collect/{req['id']}/assess", headers=demo).json()
    codes = [r["code"] for r in p["assessment"]["reasons"]]
    assert codes[0] == "COLLECT_DEBIT"
    assert "DECEPTIVE_NOTE" in codes or p["assessment"]["guard"]["note"]["promises_money"]
    assert p["assessment"]["level"] == "high"
    r = client.post(f"/api/payments/{p['id']}/intent", json={"purpose": "refund", "asked_by_someone": False}, headers=demo)
    assert r.json()["result"]["scam_type"] == "collect_request"
    r = client.post(f"/api/payments/{p['id']}/cancel", headers=demo)
    assert r.json()["status"] == "cancelled"
