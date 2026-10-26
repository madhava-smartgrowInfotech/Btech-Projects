import hashlib

import pytest

from conftest import SENT


# ------------------------------------------------------------------ health + auth
def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_register_returns_token_and_profile(client):
    r = client.post("/api/auth/register", json={"name": "Asha", "email": "asha1@test.app", "password": "secret1"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["email"] == "asha1@test.app"


def test_register_duplicate_email_rejected(client):
    p = {"name": "Dup", "email": "dup@test.app", "password": "secret1"}
    assert client.post("/api/auth/register", json=p).status_code == 200
    assert client.post("/api/auth/register", json=p).status_code == 400


@pytest.mark.parametrize("payload", [
    {"name": "x", "email": "x@test.app", "password": "12345"},      # too short
    {"name": "x", "email": "not-an-email", "password": "123456"},   # bad email
    {"name": "x", "password": "123456"},                            # missing email
])
def test_register_validation(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_login_ok_and_wrong_password(client, user_a):
    email, _ = user_a
    assert client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "ghost@test.app", "password": "x"}).status_code == 401


def test_password_is_stored_hashed(client, user_a):
    from backend.app import models
    from backend.app.db import SessionLocal
    email, _ = user_a
    with SessionLocal() as db:
        u = db.query(models.User).filter_by(email=email).one()
        assert u.password_hash != "Passw0rd!" and u.password_hash.startswith("$2")


def test_me_requires_valid_token(client, user_a):
    _, h = user_a
    assert client.get("/api/auth/me", headers=h).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_expired_token_rejected(client):
    from datetime import datetime, timedelta, timezone

    import jwt

    from backend.app import config
    tok = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}, config.JWT_SECRET, algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


# ------------------------------------------------------------------ guardians
G = {"name": "Mother", "phone": "+910000000001", "email": "mom@test.app", "telegram_chat_id": "123"}


def test_guardian_crud(client, user_a):
    _, h = user_a
    g = client.post("/api/guardians", json=G, headers=h).json()
    assert g["name"] == "Mother" and "id" in g
    assert len(client.get("/api/guardians", headers=h).json()) == 1
    upd = client.put(f"/api/guardians/{g['id']}", json={**G, "name": "Mum"}, headers=h).json()
    assert upd["name"] == "Mum"
    assert client.delete(f"/api/guardians/{g['id']}", headers=h).json() == {"ok": True}
    assert client.get("/api/guardians", headers=h).json() == []


def test_guardians_are_private_to_their_owner(client, user_a, user_b):
    _, ha = user_a
    _, hb = user_b
    g = client.post("/api/guardians", json=G, headers=ha).json()
    assert client.get("/api/guardians", headers=hb).json() == []
    assert client.put(f"/api/guardians/{g['id']}", json=G, headers=hb).status_code == 404
    assert client.delete(f"/api/guardians/{g['id']}", headers=hb).status_code == 404
    assert client.get("/api/guardians").status_code == 401


# ------------------------------------------------------------------ risk areas
def test_risk_areas_are_the_467_geocoded_districts(client):
    rows = client.get("/api/risk/areas").json()
    assert len(rows) == 467
    assert {r["risk_tier"] for r in rows} == {"low", "medium", "high"}
    assert all(0 <= r["risk_score"] <= 100 for r in rows)


def test_tier_counts_match_published_metrics(client):
    rows = client.get("/api/risk/areas").json()
    counts = {t: sum(1 for r in rows if r["risk_tier"] == t) for t in ("low", "medium", "high")}
    assert counts == {"low": 278, "medium": 148, "high": 41}


# ------------------------------------------------------------------ routes
def test_route_plan_sorts_by_risk_and_flags_recommended(client, user_a):
    _, h = user_a
    r = client.post("/api/routes/plan", json={"origin_lat": 17, "origin_lng": 78, "dest_lat": 17.6, "dest_lng": 78}, headers=h)
    assert r.status_code == 200
    routes = r.json()["routes"]
    assert [x["recommended"] for x in routes] == [True, False]
    assert routes[0]["risk_score"] <= routes[1]["risk_score"]
    assert set(routes[0]["risk_tiers"]) == {"low", "medium", "high"}


def test_route_plan_needs_login(client):
    assert client.post("/api/routes/plan", json={"origin_lat": 1, "origin_lng": 1, "dest_lat": 2, "dest_lng": 2}).status_code == 401


def test_route_plan_service_failure_is_502(client, user_a, monkeypatch):
    from backend.app.services import osrm

    async def boom(*a):
        raise RuntimeError("down")
    monkeypatch.setattr(osrm, "get_route_alternatives", boom)
    _, h = user_a
    r = client.post("/api/routes/plan", json={"origin_lat": 1, "origin_lng": 1, "dest_lat": 2, "dest_lng": 2}, headers=h)
    assert r.status_code == 502


def test_route_plan_no_route_is_404(client, user_a, monkeypatch):
    from backend.app.services import osrm

    async def none(*a):
        return []
    monkeypatch.setattr(osrm, "get_route_alternatives", none)
    _, h = user_a
    assert client.post("/api/routes/plan", json={"origin_lat": 1, "origin_lng": 1, "dest_lat": 2, "dest_lng": 2}, headers=h).status_code == 404


# ------------------------------------------------------------------ SOS lifecycle
def test_sos_start_creates_session_and_tracking_link(client, user_a, sos):
    assert len(sos["share_token"]) == 32 and sos["tracking_url"].endswith("/track/" + sos["share_token"])
    _, h = user_a
    s = client.get(f"/api/sos/{sos['session_id']}", headers=h).json()
    assert s["status"] == "active" and s["trigger"] == "manual" and s["evidence_count"] == 0


def test_sos_alerts_each_guardian_on_every_configured_channel(client, user_a):
    _, h = user_a
    client.post("/api/guardians", json=G, headers=h)
    client.post("/api/guardians", json={"name": "NoChannel"}, headers=h)
    r = client.post("/api/sos/start", json={"lat": 17.0, "lng": 78.0, "trigger": "safephrase"}, headers=h).json()
    by_name = {d["guardian"]: d for d in r["delivery"]}
    assert by_name["Mother"] == {"guardian": "Mother", "telegram": True, "email": True}
    assert by_name["NoChannel"]["telegram"] is False and by_name["NoChannel"]["email"] is False
    assert len(SENT["telegram"]) == 1 and len(SENT["email"]) == 1
    assert r["share_token"] in SENT["telegram"][0][1] and "safephrase" in SENT["telegram"][0][1]


def test_location_updates_are_stored_in_order(client, user_a, sos):
    _, h = user_a
    sid = sos["session_id"]
    for i in range(3):
        assert client.post(f"/api/sos/{sid}/location", json={"lat": 17.4 + i / 100, "lng": 78.5}, headers=h).status_code == 200
    path = client.get(f"/api/track/{sos['share_token']}").json()["path"]
    assert len(path) == 4 and path[-1]["lat"] == pytest.approx(17.42)


def test_cancel_stops_updates_and_is_visible_to_guardians(client, user_a, sos):
    _, h = user_a
    sid = sos["session_id"]
    assert client.post(f"/api/sos/{sid}/cancel", headers=h).json() == {"ok": True}
    assert client.post(f"/api/sos/{sid}/location", json={"lat": 1, "lng": 1}, headers=h).status_code == 400
    t = client.get(f"/api/track/{sos['share_token']}").json()
    assert t["status"] == "cancelled" and t["ended_at"] is not None


def test_sessions_are_private_to_their_owner(client, user_a, user_b, sos):
    _, hb = user_b
    sid = sos["session_id"]
    assert client.get(f"/api/sos/{sid}", headers=hb).status_code == 404
    assert client.post(f"/api/sos/{sid}/location", json={"lat": 1, "lng": 1}, headers=hb).status_code == 404
    assert client.post(f"/api/sos/{sid}/cancel", headers=hb).status_code == 404
    assert client.get(f"/api/sos/{sid}/evidence", headers=hb).status_code == 404


def test_sos_requires_login_and_coordinates(client, user_a):
    _, h = user_a
    assert client.post("/api/sos/start", json={"lat": 1, "lng": 1}).status_code == 401
    assert client.post("/api/sos/start", json={"lng": 1}, headers=h).status_code == 422


# ------------------------------------------------------------------ tracking (guardian view)
def test_public_tracking_page_shows_owner_and_last_position(client, user_a, sos):
    t = client.get(f"/api/track/{sos['share_token']}").json()
    assert t["status"] == "active" and t["user_name"].startswith("User") and t["last_lat"] == pytest.approx(17.385)


def test_unknown_tracking_token_is_404(client):
    assert client.get("/api/track/" + "0" * 32).status_code == 404


def test_websocket_pushes_location_and_cancel(client, user_a, sos):
    _, h = user_a
    sid, tok = sos["session_id"], sos["share_token"]
    with client.websocket_connect(f"/ws/track/{tok}") as ws:
        client.post(f"/api/sos/{sid}/location", json={"lat": 17.5, "lng": 78.6}, headers=h)
        msg = ws.receive_json()
        assert msg["type"] == "location" and msg["lat"] == 17.5
        client.post(f"/api/sos/{sid}/cancel", headers=h)
        assert ws.receive_json() == {"type": "cancelled"}


# ------------------------------------------------------------------ evidence
def _upload(client, h, sid, data=b"\xff\xd8\xff-photo-bytes", kind="photo", name="p.jpg"):
    return client.post(f"/api/sos/{sid}/evidence", data={"kind": kind, "lat": "17.4", "lng": "78.5"},
                       files={"file": (name, data, "application/octet-stream")}, headers=h)


def test_evidence_is_hashed_and_stored(client, user_a, sos, tmp_root):
    _, h = user_a
    data = b"\xff\xd8\xff-photo-bytes" * 50
    r = _upload(client, h, sos["session_id"], data).json()
    assert r["sha256"] == hashlib.sha256(data).hexdigest() and len(r["sha256"]) == 64
    stored = next((tmp_root / "evidence" / str(sos["session_id"])).glob(r["sha256"][:16] + ".*"))
    assert hashlib.sha256(stored.read_bytes()).hexdigest() == r["sha256"]
    assert client.get(f"/api/sos/{sos['session_id']}/evidence", headers=h).json()[0]["sha256"] == r["sha256"]


def test_one_flipped_bit_changes_the_hash(client, user_a, sos, tmp_root):
    _, h = user_a
    r = _upload(client, h, sos["session_id"], b"A" * 4096).json()
    stored = next((tmp_root / "evidence" / str(sos["session_id"])).glob(r["sha256"][:16] + ".*"))
    raw = bytearray(stored.read_bytes())
    raw[100] ^= 1
    assert hashlib.sha256(bytes(raw)).hexdigest() != r["sha256"]


def test_audio_kind_accepted_other_kinds_rejected(client, user_a, sos):
    _, h = user_a
    assert _upload(client, h, sos["session_id"], b"aud", "audio", "a.webm").status_code == 200
    assert _upload(client, h, sos["session_id"], b"vid", "video", "a.mp4").status_code == 400


def test_empty_evidence_file_rejected(client, user_a, sos):
    _, h = user_a
    assert _upload(client, h, sos["session_id"], b"").status_code == 400


def test_evidence_count_on_session(client, user_a, sos):
    _, h = user_a
    _upload(client, h, sos["session_id"])
    _upload(client, h, sos["session_id"], b"second")
    assert client.get(f"/api/sos/{sos['session_id']}", headers=h).json()["evidence_count"] == 2


def test_evidence_upload_to_someone_elses_session_is_404(client, user_b, sos):
    _, hb = user_b
    assert _upload(client, hb, sos["session_id"]).status_code == 404


# ------------------------------------------------------------------ AI assistant
def test_ai_ask_returns_answer(client, user_a):
    _, h = user_a
    r = client.post("/api/ai/ask", json={"question": "Is it safe?", "lat": 17.0, "lng": 78.0}, headers=h)
    assert r.json() == {"answer": "Stub answer for: Is it safe?"}


def test_ai_ask_needs_login_and_a_question(client, user_a):
    _, h = user_a
    assert client.post("/api/ai/ask", json={"question": "x"}).status_code == 401
    assert client.post("/api/ai/ask", json={}, headers=h).status_code == 422


def test_ai_provider_error_is_502(client, user_a, monkeypatch):
    from backend.app.routes import ai as ai_routes

    async def bad(*a, **k):
        raise RuntimeError("Gemini API error 429")
    monkeypatch.setattr(ai_routes, "ask_gemini", bad)
    _, h = user_a
    assert client.post("/api/ai/ask", json={"question": "x"}, headers=h).status_code == 502


def test_gemini_without_key_raises_a_clear_error(monkeypatch):
    import asyncio

    from backend.app import config
    from backend.app.services import gemini
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        asyncio.run(gemini.ask_gemini("hi"))


# ------------------------------------------------------------------ places search
def test_places_search_needs_login(client):
    assert client.get("/api/places/search?q=hyderabad").status_code == 401


def test_places_search_rejects_one_character(client, user_a):
    _, h = user_a
    assert client.get("/api/places/search?q=h", headers=h).status_code == 422


# ------------------------------------------------------------------ known gaps (documented, expected to fail today)
@pytest.mark.xfail(strict=True, reason="a provider timeout is not caught: httpx.ReadTimeout surfaces as 500, not 502")
def test_gemini_timeout_should_be_502(client, user_a, monkeypatch):
    import httpx

    from backend.app.routes import ai as ai_routes

    async def slow(*a, **k):
        raise httpx.ReadTimeout("timed out")
    monkeypatch.setattr(ai_routes, "ask_gemini", slow)
    _, h = user_a
    try:
        status = client.post("/api/ai/ask", json={"question": "x"}, headers=h).status_code
    except httpx.ReadTimeout:
        status = 500  # the test client re-raises the unhandled server error
    assert status == 502


@pytest.mark.xfail(strict=True, reason="coordinates are not range-checked: latitude 999 is accepted")
def test_sos_rejects_impossible_latitude(client, user_a):
    _, h = user_a
    assert client.post("/api/sos/start", json={"lat": 999, "lng": 999}, headers=h).status_code == 422


@pytest.mark.xfail(strict=True, reason="trigger is a free string: any value is stored")
def test_sos_rejects_unknown_trigger(client, user_a):
    _, h = user_a
    assert client.post("/api/sos/start", json={"lat": 1, "lng": 1, "trigger": "bogus"}, headers=h).status_code == 422


@pytest.mark.xfail(strict=True, reason="WebSocket accepts any token, even one that matches no session")
def test_websocket_rejects_unknown_token(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/track/" + "0" * 32):
            pass


@pytest.mark.xfail(strict=True, reason="no upload size limit: a 12 MB 'photo' is accepted")
def test_evidence_has_a_size_limit(client, user_a, sos):
    _, h = user_a
    assert _upload(client, h, sos["session_id"], b"x" * 12_000_000).status_code in (400, 413)


@pytest.mark.xfail(strict=True, reason="stored files keep the client's extension; an .html upload is served back as text/html")
def test_evidence_files_not_served_as_html(client, user_a, sos, tmp_root):
    _, h = user_a
    r = _upload(client, h, sos["session_id"], b"<script>1</script>", "photo", "x.html").json()
    name = next((tmp_root / "evidence" / str(sos["session_id"])).glob(r["sha256"][:16] + ".*")).name
    ct = client.get(f"/evidence-files/{sos['session_id']}/{name}").headers["content-type"]
    assert "text/html" not in ct
