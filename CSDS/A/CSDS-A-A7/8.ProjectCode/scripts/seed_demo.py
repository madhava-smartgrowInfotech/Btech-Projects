"""Create a demo account (idempotent) so anyone running the app has a ready
login to explore with, per docs/03_HOW_TO_RUN.md.

Usage: python scripts/seed_demo.py  (backend must already be running on :8107)
"""
import httpx

BASE = "http://localhost:8107"
DEMO_EMAIL = "demo@sheguard.app"
DEMO_PASSWORD = "Demo@1234"


def main():
    client = httpx.Client(base_url=BASE, timeout=15)

    r = client.post("/api/auth/register", json={"name": "Demo User", "email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"Created demo account: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    elif r.status_code == 400:
        r = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        r.raise_for_status()
        token = r.json()["access_token"]
        print(f"Demo account already exists: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    else:
        r.raise_for_status()
        return

    client.headers["Authorization"] = f"Bearer {token}"
    guardians = client.get("/api/guardians").json()
    if not guardians:
        client.post("/api/guardians", json={
            "name": "Sample Guardian",
            "phone": "+910000000000",
            "email": None,
            "telegram_chat_id": None,
        })
        print("Added a sample guardian - edit it with a real phone/email/Telegram chat ID to test live alerts.")


if __name__ == "__main__":
    main()
