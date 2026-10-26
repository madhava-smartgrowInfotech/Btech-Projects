"""API and integration tests: every endpoint group is driven through the real FastAPI app."""
from datetime import datetime, timedelta, timezone

import pytest

NOW = datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat()


def H(token):
    return {"Authorization": "Bearer " + token}


def login(c, email, pw):
    return c.post("/api/auth/login", json={"email": email, "password": pw})


@pytest.fixture(scope="module")
def admin(client):
    return H(login(client, "admin@parksure.app", "admin123").json()["token"])


@pytest.fixture(scope="module")
def driver(client):
    r = client.post("/api/auth/register", json={"name": "Api Driver", "email": "api.driver@example.com",
                                                "password": "secret123"})
    assert r.status_code == 200
    return H(r.json()["token"])


def make_location(client, admin, cap=2, buf=0, name="Test Lot", lat=12.9, lon=77.5, price=4.0):
    body = {"name": name, "address": "1 Test Way", "latitude": lat, "longitude": lon, "capacity": cap,
            "price_per_hour": price, "buffer_size": buf}
    r = client.post("/api/locations", json=body, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()


def book(client, hdr, loc_id, s, e):
    return client.post("/api/reservations", json={"location_id": loc_id, "start_time": iso(s),
                                                  "end_time": iso(e)}, headers=hdr)


# ------------------------------------------------------------------ auth
def test_login_seeded_admin_and_driver(client):
    assert login(client, "admin@parksure.app", "admin123").json()["user"]["role"] == "admin"
    assert login(client, "driver1@parksure.app", "driver123").json()["user"]["role"] == "driver"


def test_login_rejects_bad_password(client):
    r = login(client, "driver1@parksure.app", "nope")
    assert r.status_code == 401 and "Incorrect" in r.json()["detail"]


def test_login_rejects_unknown_user(client):
    assert login(client, "ghost@example.com", "whatever").status_code == 401


def test_register_duplicate_email_refused(client, driver):
    r = client.post("/api/auth/register", json={"name": "Api Driver", "email": "API.driver@example.com",
                                                "password": "secret123"})
    assert r.status_code == 400


@pytest.mark.parametrize("body", [
    {"name": "A", "email": "a@example.com", "password": "secret123"},            # name too short
    {"name": "Okay Name", "email": "not-an-email", "password": "secret123"},      # bad email
    {"name": "Okay Name", "email": "b@example.com", "password": "123"},           # password too short
])
def test_register_validation_errors(client, body):
    assert client.post("/api/auth/register", json=body).status_code == 422


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=H("garbage")).status_code == 401


def test_new_driver_starts_at_trust_three(client, driver):
    me = client.get("/api/auth/me", headers=driver).json()
    assert me["role"] == "driver" and me["trust_score"] == 3.0


def test_passwords_are_stored_hashed():
    from app.auth import hash_password, verify_password
    h = hash_password("secret123")
    assert h != "secret123" and h.startswith("$2") and verify_password("secret123", h)
    assert not verify_password("secret124", h)


# ------------------------------------------------------------------ role guards
def test_driver_cannot_use_admin_endpoints(client, driver):
    for path in ("/api/admin/overview", "/api/admin/users", "/api/admin/bookings", "/api/admin/insights"):
        assert client.get(path, headers=driver).status_code == 403
    assert client.post("/api/admin/reset-buffers", headers=driver).status_code == 403
    assert client.post("/api/locations", json={}, headers=driver).status_code in (403, 422)


def test_anonymous_cannot_reserve(client):
    r = client.post("/api/reservations", json={"location_id": 1, "start_time": iso(NOW), "end_time": iso(NOW + timedelta(hours=1))})
    assert r.status_code == 401


# ------------------------------------------------------------------ locations CRUD
def test_location_crud_and_validation(client, admin):
    loc = make_location(client, admin, cap=7, name="Crud Lot")
    assert any(x["id"] == loc["id"] for x in client.get("/api/locations").json())
    r = client.put(f"/api/locations/{loc['id']}", json={"name": "Crud Lot", "address": "x", "latitude": 12.9,
                                                       "longitude": 77.5, "capacity": 9, "price_per_hour": 4.0,
                                                       "buffer_size": 1}, headers=admin)
    assert r.json()["capacity"] == 9
    bad = {"name": "Bad", "address": "", "latitude": 95, "longitude": 0, "capacity": 5, "price_per_hour": 3}
    assert client.post("/api/locations", json=bad, headers=admin).status_code == 422
    assert client.put("/api/locations/99999", json={**bad, "latitude": 10}, headers=admin).status_code == 404
    assert client.delete(f"/api/locations/{loc['id']}", headers=admin).json() == {"ok": True}
    assert client.delete(f"/api/locations/{loc['id']}", headers=admin).status_code == 404


# ------------------------------------------------------------------ search
def test_search_counts_bookable_bays(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=1, name="Search Lot")
    s = NOW + timedelta(days=12)
    e = s + timedelta(hours=2)
    row = lambda: next(x for x in client.get("/api/search", params={"start_time": iso(s), "end_time": iso(e)}).json() if x["id"] == loc["id"])
    assert row()["bookable"] == 4 and row()["available"]
    assert book(client, driver, loc["id"], s, e).status_code == 200
    assert row()["bookable"] == 3 and row()["overlapping"] == 1


def test_search_validation(client):
    s = NOW + timedelta(days=1)
    assert client.get("/api/search", params={"start_time": iso(s), "end_time": iso(s - timedelta(hours=1))}).status_code == 400
    assert client.get("/api/search", params={"start_time": iso(s), "end_time": iso(s + timedelta(days=31))}).status_code == 400
    assert client.get("/api/search").status_code == 422


# ------------------------------------------------------------------ reservations
def test_reservation_fee_uses_trust_multiplier(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=0, name="Fee API Lot", price=5.0)
    s = NOW + timedelta(days=13)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=2)).json()
    assert r["status"] == "reserved" and r["fee"] == 10.0 and r["fee_multiplier"] == 1.0
    assert r["amount_due"] == 10.0 and r["checkout"]["provider"] in ("demo", "stripe")


def test_full_window_is_declined_with_409(client, admin, driver):
    loc = make_location(client, admin, cap=2, buf=1, name="Full Lot")      # one bookable bay
    s = NOW + timedelta(days=14)
    e = s + timedelta(hours=2)
    assert book(client, driver, loc["id"], s, e).status_code == 200
    r = book(client, driver, loc["id"], s, e)
    assert r.status_code == 409 and "fully reserved" in r.json()["detail"]
    mine = client.get("/api/reservations", headers=driver).json()
    assert any(x["status"] == "declined" and x["location_id"] == loc["id"] for x in mine)


def test_end_before_start_rejected(client, driver):
    s = NOW + timedelta(days=15)
    assert book(client, driver, 1, s, s - timedelta(hours=1)).status_code == 422


def test_unknown_location_404(client, driver):
    s = NOW + timedelta(days=15)
    assert book(client, driver, 987654, s, s + timedelta(hours=1)).status_code == 404


def test_thirty_day_limit(client, driver):
    s = NOW + timedelta(days=1)
    assert book(client, driver, 1, s, s + timedelta(days=31)).status_code == 400


def test_cancel_refunds_credit_and_blocks_second_cancel(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=0, name="Cancel Lot", price=4.0)
    s = NOW + timedelta(days=16)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=2)).json()
    assert client.post(f"/api/payments/{r['id']}/confirm", headers=driver).json()["status"] == "paid"
    before = client.get("/api/auth/me", headers=driver).json()["account_credit"]
    c = client.post(f"/api/reservations/{r['id']}/cancel", headers=driver).json()
    assert c["status"] == "cancelled" and c["payment_status"] == "refunded"
    assert client.get("/api/auth/me", headers=driver).json()["account_credit"] == pytest.approx(before + 8.0)
    assert client.post(f"/api/reservations/{r['id']}/cancel", headers=driver).status_code == 400


def test_credit_offsets_the_next_fee(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=0, name="Credit Lot", price=2.0)
    s = NOW + timedelta(days=17)
    credit = client.get("/api/auth/me", headers=driver).json()["account_credit"]
    assert credit > 0
    r = book(client, driver, loc["id"], s, s + timedelta(hours=1)).json()
    assert r["credit_applied"] == pytest.approx(min(credit, 2.0))


def test_other_users_reservation_is_hidden(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=0, name="Owner Lot")
    s = NOW + timedelta(days=18)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=1)).json()
    other = client.post("/api/auth/register", json={"name": "Other Person", "email": "other.person@example.com",
                                                    "password": "secret123"}).json()
    assert client.post(f"/api/reservations/{r['id']}/cancel", headers=H(other["token"])).status_code == 404
    assert client.post(f"/api/reservations/{r['id']}/checkin", headers=H(other["token"])).status_code == 404


# ------------------------------------------------------------------ check-in / check-out
def test_checkin_checkout_on_time_updates_trust_and_buffer(client, admin, driver):
    loc = make_location(client, admin, cap=6, buf=1, name="Flow Lot")
    s = NOW + timedelta(minutes=5)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=2)).json()
    ci = client.post(f"/api/reservations/{r['id']}/checkin", headers=driver).json()
    assert ci["reservation"]["status"] == "active" and ci["moved"] is False
    co = client.post(f"/api/reservations/{r['id']}/checkout", headers=driver).json()
    assert co["on_time"] is True and co["reservation"]["status"] == "completed"
    now_loc = next(x for x in client.get("/api/locations").json() if x["id"] == loc["id"])
    assert now_loc["buffer_size"] == 2                      # grew by one on the on-time checkout
    t = client.get("/api/trust", headers=driver).json()
    assert any(e["kind"] == "benefit" for e in t["events"])


def test_checkin_twice_and_checkout_without_checkin_refused(client, admin, driver):
    loc = make_location(client, admin, cap=6, buf=0, name="Guard Lot")
    s = NOW + timedelta(minutes=5)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=1)).json()
    assert client.post(f"/api/reservations/{r['id']}/checkout", headers=driver).status_code == 400
    assert client.post(f"/api/reservations/{r['id']}/checkin", headers=driver).status_code == 200
    assert client.post(f"/api/reservations/{r['id']}/checkin", headers=driver).status_code == 400


def test_late_checkout_is_recorded_as_warning(client, admin):
    reg = client.post("/api/auth/register", json={"name": "Late Larry", "email": "late.larry@example.com", "password": "secret123"}).json()
    hdr = H(reg["token"])
    loc = make_location(client, admin, cap=6, buf=1, name="Late Lot")
    s = NOW - timedelta(hours=3)
    r = book(client, hdr, loc["id"], s, s + timedelta(hours=1)).json()     # window already over
    client.post(f"/api/reservations/{r['id']}/checkin", headers=hdr)
    co = client.post(f"/api/reservations/{r['id']}/checkout", headers=hdr).json()
    assert co["on_time"] is False
    t = client.get("/api/trust", headers=hdr).json()
    assert t["warning_count"] == 1 and any(e["kind"] == "warning" for e in t["events"])


def test_full_site_moves_driver_to_nearest_alternate(client, admin):
    a = client.post("/api/auth/register", json={"name": "Driver A", "email": "alt.a@example.com", "password": "secret123"}).json()
    b = client.post("/api/auth/register", json={"name": "Driver B", "email": "alt.b@example.com", "password": "secret123"}).json()
    one = make_location(client, admin, cap=1, buf=0, name="One Bay", lat=21.0, lon=71.0)
    near = make_location(client, admin, cap=5, buf=0, name="Near Alt", lat=21.01, lon=71.0)
    s = NOW + timedelta(minutes=1)
    e = s + timedelta(hours=2)
    ra = book(client, H(a["token"]), one["id"], s, e).json()
    assert client.post(f"/api/reservations/{ra['id']}/checkin", headers=H(a["token"])).json()["reservation"]["status"] == "active"
    # a second booking in a later window passes admission; the bay is still physically occupied on arrival
    rb = book(client, H(b["token"]), one["id"], e + timedelta(hours=1), e + timedelta(hours=2)).json()
    out = client.post(f"/api/reservations/{rb['id']}/checkin", headers=H(b["token"])).json()
    assert out["moved"] is True and out["alternate"]["id"] == near["id"]
    assert 0.5 < out["distance_km"] < 2.0
    assert out["reservation"]["parent_id"] == rb["id"]


def test_full_site_without_alternate_fails_and_credits_fee(client, admin):
    c1 = client.post("/api/auth/register", json={"name": "Driver C", "email": "fail.c@example.com", "password": "secret123"}).json()
    c2 = client.post("/api/auth/register", json={"name": "Driver D", "email": "fail.d@example.com", "password": "secret123"}).json()
    # Make every other location inadmissible (0 + 50 < 1 is False) so no alternate exists on arrival.
    from app.database import SessionLocal
    from app.models import ParkingLocation
    db = SessionLocal()
    try:
        keep = make_location(client, admin, cap=1, buf=0, name="Lonely Bay", lat=-45.0, lon=170.0)
        others = db.query(ParkingLocation).filter(ParkingLocation.id != keep["id"]).all()
        saved = [(o.id, o.buffer_size, o.capacity) for o in others]
        for o in others:
            o.buffer_size, o.capacity = 50, 1          # forecast_free is False everywhere: 0 + 50 < 1 fails
        db.commit()
        s = NOW + timedelta(minutes=1)
        e = s + timedelta(hours=2)
        r1 = book(client, H(c1["token"]), keep["id"], s, e).json()
        client.post(f"/api/reservations/{r1['id']}/checkin", headers=H(c1["token"]))
        r2 = book(client, H(c2["token"]), keep["id"], e + timedelta(hours=1), e + timedelta(hours=2)).json()
        out = client.post(f"/api/reservations/{r2['id']}/checkin", headers=H(c2["token"])).json()
        assert out["failed"] is True and out["moved"] is False
        assert client.get("/api/auth/me", headers=H(c2["token"])).json()["account_credit"] == pytest.approx(r2["fee"])
    finally:
        for oid, buf, cap in saved:
            o = db.query(ParkingLocation).filter(ParkingLocation.id == oid).first()
            o.buffer_size, o.capacity = buf, cap
        db.commit()
        db.close()


# ------------------------------------------------------------------ suspension through the API
def test_low_trust_driver_with_recent_warning_is_refused(client, admin):
    from app.database import SessionLocal
    from app.models import TrustEvent, User
    reg = client.post("/api/auth/register", json={"name": "Risky Rita", "email": "risky.rita@example.com", "password": "secret123"}).json()
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "risky.rita@example.com").first()
        u.trust_score = 1.0
        db.add(TrustEvent(user_id=u.id, kind="warning", detail="seeded"))
        db.commit()
    finally:
        db.close()
    loc = make_location(client, admin, cap=5, buf=0, name="Suspend Lot")
    s = NOW + timedelta(days=20)
    r = book(client, H(reg["token"]), loc["id"], s, s + timedelta(hours=1))
    assert r.status_code == 403 and "paused" in r.json()["detail"].lower()


# ------------------------------------------------------------------ payments
def test_demo_payment_confirmation(client, admin, driver):
    loc = make_location(client, admin, cap=5, buf=0, name="Pay Lot", price=3.0)
    s = NOW + timedelta(days=21)
    r = book(client, driver, loc["id"], s, s + timedelta(hours=1)).json()
    if r["amount_due"] > 0:
        assert r["payment_status"] == "pending"
    out = client.post(f"/api/payments/{r['id']}/confirm", headers=driver).json()
    assert out == {"ok": True, "status": "paid"}


def test_stripe_webhook_inert_without_keys(client):
    r = client.post("/api/stripe/webhook", content=b"{}")
    assert r.status_code == 200 and r.json()["received"] is False


# ------------------------------------------------------------------ admin
def test_admin_overview_and_listings(client, admin):
    ov = client.get("/api/admin/overview", headers=admin).json()
    assert {"users", "locations", "reservations", "revenue", "unable_to_park", "declined"} <= set(ov)
    assert ov["users"] >= 9
    assert len(client.get("/api/admin/users", headers=admin).json()) == ov["users"]
    assert len(client.get("/api/admin/bookings", headers=admin).json()) <= 300


def test_admin_insights_has_four_strategies(client, admin):
    ins = client.get("/api/admin/insights", params={"window_days": 60}, headers=admin).json()
    assert set(ins["totals"]) == {"fixed_0", "fixed_1", "fixed_3", "dynamic"}
    assert ins["policy"] == {"init": 1, "max": 5, "reset_hours": 24}


def test_insights_are_deterministic(client, admin):
    a = client.get("/api/admin/insights", params={"window_days": 60}, headers=admin).json()["totals"]
    b = client.get("/api/admin/insights", params={"window_days": 60}, headers=admin).json()["totals"]
    assert a == b


def test_admin_reset_buffers_forces_init(client, admin):
    client.post("/api/admin/reset-buffers", headers=admin)
    assert all(x["buffer_size"] == 1 for x in client.get("/api/locations").json())


def test_first_registered_account_would_be_admin_only_on_empty_db(client):
    # the test database was seeded, so a new registration is a driver
    r = client.post("/api/auth/register", json={"name": "Late Joiner", "email": "joiner@example.com", "password": "secret123"})
    assert r.json()["user"]["role"] == "driver"
