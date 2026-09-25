"""End-to-end smoke test against the real running SHEGUARD API. Exercises the
full user flow: register -> login -> add guardian -> plan a safe route (real
OSRM call) -> read risk areas -> start SOS (real alert attempt) -> push a
location update -> upload evidence -> cancel -> read the public tracking page.

The AI assistant call is attempted but only warns (not fails) if GEMINI_API_KEY
isn't configured yet, since that's an optional user-supplied secret.

Usage: python scripts/smoke_test.py  (backend must already be running on :8107)
"""
import io
import sys
import time
import uuid

import httpx

BASE = "http://localhost:8107"


def step(name):
    print(f"\n--- {name} ---")


def main():
    client = httpx.Client(base_url=BASE, timeout=30)

    step("health check")
    r = client.get("/api/health")
    assert r.status_code == 200, r.text
    print("OK", r.json())

    step("register")
    email = f"smoketest_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Smoke Test", "email": email, "password": "testpass123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    print("OK registered", email)

    step("login")
    r = client.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200, r.text
    print("OK login")

    step("add guardian")
    r = client.post("/api/guardians", json={"name": "Test Guardian", "phone": "+911234567890", "email": None, "telegram_chat_id": None})
    assert r.status_code == 200, r.text
    print("OK guardian added:", r.json())

    step("risk areas")
    r = client.get("/api/risk/areas")
    assert r.status_code == 200, r.text
    areas = r.json()
    assert len(areas) > 0, "district_risk table is empty - run ml/train_risk_model.py first"
    print(f"OK {len(areas)} district risk areas loaded")

    step("plan route (real OSRM call)")
    r = client.post("/api/routes/plan", json={
        "origin_lat": 17.3850, "origin_lng": 78.4867,   # Hyderabad
        "dest_lat": 17.4399, "dest_lng": 78.4983,        # Secunderabad
    })
    assert r.status_code == 200, r.text
    routes = r.json()["routes"]
    assert len(routes) > 0
    print(f"OK {len(routes)} route(s), safest risk_score={routes[0]['risk_score']}")

    step("start SOS")
    r = client.post("/api/sos/start", json={"lat": 17.3850, "lng": 78.4867, "trigger": "manual"})
    assert r.status_code == 200, r.text
    session = r.json()
    session_id = session["session_id"]
    share_token = session["share_token"]
    print("OK session", session_id, "share_token", share_token)
    print("  guardian delivery attempts:", session["delivery"])

    step("push location update")
    r = client.post(f"/api/sos/{session_id}/location", json={"lat": 17.386, "lng": 78.487})
    assert r.status_code == 200, r.text
    print("OK location pushed")

    step("upload evidence (photo)")
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0FAKEJPEGDATAFORSMOKETEST" * 10)
    r = client.post(
        f"/api/sos/{session_id}/evidence",
        data={"kind": "photo", "lat": "17.386", "lng": "78.487"},
        files={"file": ("test.jpg", fake_image, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    ev = r.json()
    assert len(ev["sha256"]) == 64
    print("OK evidence uploaded, sha256=", ev["sha256"][:16], "...")

    step("public tracking page")
    r = client.get(f"/api/track/{share_token}")
    assert r.status_code == 200, r.text
    track = r.json()
    assert track["status"] == "active"
    print("OK tracking page shows", len(track["path"]), "location point(s)")

    step("cancel SOS")
    r = client.post(f"/api/sos/{session_id}/cancel")
    assert r.status_code == 200, r.text
    print("OK cancelled")

    r = client.get(f"/api/track/{share_token}")
    assert r.json()["status"] == "cancelled"
    print("OK tracking page reflects cancellation")

    step("AI assistant (Gemini)")
    r = client.post("/api/ai/ask", json={"question": "What should I do if I feel unsafe walking alone at night?"})
    if r.status_code == 200:
        print("OK Gemini answered:", r.json()["answer"][:120], "...")
    else:
        print(f"WARN Gemini call failed ({r.status_code}): {r.text[:200]}")
        print("     Set GEMINI_API_KEY in .env to exercise this feature.")

    print("\nAll smoke test steps passed.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nSMOKE TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.ConnectError:
        print(f"\nCould not connect to {BASE} - is the backend running?", file=sys.stderr)
        sys.exit(1)
