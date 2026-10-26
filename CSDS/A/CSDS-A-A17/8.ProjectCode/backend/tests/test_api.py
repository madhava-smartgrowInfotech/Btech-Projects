"""API and pipeline tests for CropSight.  Run from backend/:  python -m pytest tests -q

Tests marked xfail document behaviour that is a known gap of the shipped code (see docs/REPORT_FACTS.md); they assert the
behaviour a hardened system should have, and fail today, so they are reported as expected failures rather than hidden.
"""
from __future__ import annotations

import math

import pytest

from conftest import make_photo


def upload(client, headers, photo, crop="Tomato", region="Sunridge Valley", qty=300, ctype="image/jpeg"):
    return client.post("/api/crops/upload", headers=headers, data={"crop_type": crop, "region": region, "quantity_kg": qty},
                       files={"image": ("crop.jpg", photo, ctype)})


# ------------------------------------------------------------------ health & auth
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_signup_and_login_roundtrip(client):
    body = {"name": "Test Farmer", "email": "tf1@cropsight.dev", "password": "secret1", "role": "farmer", "region": "Millstone Basin"}
    r = client.post("/api/auth/signup", json=body)
    assert r.status_code == 200
    tok = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200 and me.json()["email"] == "tf1@cropsight.dev" and me.json()["role"] == "farmer"
    r2 = client.post("/api/auth/login", json={"email": body["email"], "password": body["password"]})
    assert r2.status_code == 200 and r2.json()["user"]["role"] == "farmer"


def test_signup_duplicate_email_rejected(client):
    body = {"name": "Dup", "email": "dup@cropsight.dev", "password": "secret1", "role": "buyer"}
    assert client.post("/api/auth/signup", json=body).status_code == 200
    assert client.post("/api/auth/signup", json=body).status_code == 400


def test_signup_cannot_create_admin(client):
    r = client.post("/api/auth/signup", json={"name": "X", "email": "adm@cropsight.dev", "password": "secret1", "role": "admin"})
    assert r.status_code == 400


def test_signup_validation_errors(client):
    assert client.post("/api/auth/signup", json={"name": "X", "email": "bad-email", "password": "secret1", "role": "buyer"}).status_code == 422
    assert client.post("/api/auth/signup", json={"name": "X", "email": "s@cropsight.dev", "password": "123", "role": "buyer"}).status_code == 422


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "farmer@cropsight.dev", "password": "nope-nope"})
    assert r.status_code == 401


def test_protected_routes_need_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/marketplace/listings").status_code == 401
    assert client.post("/api/prices/predict", json={"crop_type": "Tomato", "region": "Sunridge Valley"}).status_code == 401


def test_tampered_token_rejected(client, farmer):
    tok = farmer["Authorization"].split()[1]
    bad = tok[:-4] + ("AAAA" if not tok.endswith("AAAA") else "BBBB")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401


# ------------------------------------------------------------------ role guards
def test_role_guards(client, farmer, buyer, distributor):
    assert upload(client, buyer, make_photo()).status_code == 403
    assert client.post("/api/marketplace/orders", headers=farmer, json={"listing_id": 1, "quantity_kg": 10, "agreed_price": 1000}).status_code == 403
    assert client.get("/api/admin/overview", headers=farmer).status_code == 403
    assert client.get("/api/admin/model-insights", headers=buyer).status_code == 403
    assert client.get("/api/delivery/1/recommend", headers=distributor).status_code == 403


# ------------------------------------------------------------------ quality grading
def test_upload_grades_image(client, farmer, good_photo):
    r = upload(client, farmer, good_photo)
    assert r.status_code == 200
    q = r.json()["quality_grade"]
    assert q["grade"] in {"A", "B", "C", "Reject"}
    assert math.isclose(sum(q["probabilities"].values()), 1.0, abs_tol=1e-6)
    assert len(q["features"]) == 11 and all(0.0 <= v <= 1.0 for v in q["features"].values())
    assert 1 <= len(q["shap_explanation"]["top_features"]) <= 6
    assert r.json()["status"] == "draft"


def test_blemished_photo_grades_no_higher_than_clean(client, farmer, good_photo, bad_photo):
    order = {"A": 3, "B": 2, "C": 1, "Reject": 0}
    g = upload(client, farmer, good_photo).json()["quality_grade"]["grade"]
    b = upload(client, farmer, bad_photo).json()["quality_grade"]["grade"]
    assert order[b] <= order[g]


def test_upload_rejects_non_image_content_type(client, farmer):
    assert upload(client, farmer, b"hello", ctype="text/plain").status_code == 400


def test_upload_rejects_oversize(client, farmer):
    assert upload(client, farmer, b"\xff\xd8" + b"0" * (8 * 1024 * 1024 + 10)).status_code == 400


@pytest.mark.xfail(reason="known gap: a corrupt file with an image content type raises inside grade_image() -> HTTP 500, and a draft listing row is left behind", strict=False)
def test_upload_corrupt_image_is_a_client_error(client, farmer):
    r = upload(client, farmer, b"this is not a jpeg at all")
    assert r.status_code == 400


def test_my_listings_and_publish(client, farmer):
    lst = client.get("/api/crops/mine", headers=farmer).json()
    assert len(lst) >= 1
    lid = lst[0]["id"]
    r = client.post(f"/api/crops/{lid}/list", headers=farmer, params={"asking_price": 2100})
    assert r.status_code == 200 and r.json()["status"] == "listed" and r.json()["asking_price"] == 2100


def test_publish_unknown_or_foreign_listing_is_404(client, farmer):
    assert client.post("/api/crops/999999/list", headers=farmer, params={"asking_price": 1}).status_code == 404
    other = client.post("/api/auth/signup", json={"name": "Other", "email": "other-farmer@cropsight.dev", "password": "secret1", "role": "farmer"}).json()
    h = {"Authorization": f"Bearer {other['access_token']}"}
    lid = client.get("/api/crops/mine", headers=farmer).json()[0]["id"]
    assert client.post(f"/api/crops/{lid}/list", headers=h, params={"asking_price": 1}).status_code == 404


def test_get_unknown_listing_404(client, farmer):
    assert client.get("/api/crops/987654", headers=farmer).status_code == 404


# ------------------------------------------------------------------ price intelligence
def test_price_options(client, farmer):
    r = client.get("/api/prices/options").json()
    assert len(r["crops"]) == 8 and len(r["regions"]) == 8 and r["grades"] == ["A", "B", "C", "Reject"]


def test_price_prediction_shape(client, farmer):
    r = client.post("/api/prices/predict", headers=farmer, json={"crop_type": "Tomato", "region": "Sunridge Valley", "grade": "A"})
    assert r.status_code == 200
    j = r.json()
    assert len(j["forecast"]) == 31
    assert j["confidence_low"] <= j["current_price"] <= j["confidence_high"]
    assert 0 <= j["best_sell_day"] <= 14
    assert 1 <= len(j["shap_explanation"]["top_features"]) <= 6


def test_better_grade_never_priced_lower(client, farmer):
    p = {g: client.post("/api/prices/predict", headers=farmer, json={"crop_type": "Wheat", "region": "Palmgrove Delta", "grade": g}).json()["current_price"]
         for g in ["A", "B", "C", "Reject"]}
    assert p["A"] > p["B"] > p["C"] > p["Reject"]


def test_price_uses_listing_grade(client, farmer):
    lid = next(l["id"] for l in client.get("/api/crops/mine", headers=farmer).json() if l["quality_grade"])
    g = client.get(f"/api/crops/{lid}", headers=farmer).json()["quality_grade"]["grade"]
    direct = client.post("/api/prices/predict", headers=farmer, json={"crop_type": "Tomato", "region": "Sunridge Valley", "grade": g}).json()
    via = client.post("/api/prices/predict", headers=farmer, json={"crop_type": "Tomato", "region": "Sunridge Valley", "grade": "Reject", "listing_id": lid}).json()
    assert via["grade"] == g and via["current_price"] == direct["current_price"]


@pytest.mark.xfail(reason="known gap: crop_type and region are not validated against the catalogue; an unknown crop is priced from an all-zero crop one-hot", strict=False)
def test_unknown_crop_is_rejected(client, farmer):
    r = client.post("/api/prices/predict", headers=farmer, json={"crop_type": "Dragonfruit", "region": "Nowhere", "grade": "A"})
    assert r.status_code in (400, 422)


# ------------------------------------------------------------------ delivery recommendation
def test_delivery_recommendation(client, farmer):
    lid = client.get("/api/crops/mine", headers=farmer).json()[0]["id"]
    r = client.get(f"/api/delivery/{lid}/recommend", headers=farmer)
    assert r.status_code == 200
    buyers = r.json()["ranked_buyers"]["buyers"]
    assert 1 <= len(buyers) <= 5
    scores = [b["match_score"] for b in buyers]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 100 for s in scores)
    assert 0 <= r.json()["best_sell_day"] <= 14 and r.json()["best_route"]["buyer_name"] == buyers[0]["buyer_name"]


def test_delivery_weights_sum_to_one():
    from app.ml.delivery.recommend import WEIGHTS

    assert math.isclose(sum(WEIGHTS.values()), 1.0)


def test_delivery_foreign_listing_404(client):
    other = client.post("/api/auth/signup", json={"name": "O2", "email": "other-farmer2@cropsight.dev", "password": "secret1", "role": "farmer"}).json()
    h = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get("/api/delivery/1/recommend", headers=h).status_code == 404


# ------------------------------------------------------------------ marketplace and order lifecycle
def test_marketplace_browse_and_filter(client, buyer):
    all_l = client.get("/api/marketplace/listings", headers=buyer).json()
    assert len(all_l) >= 1 and all(l["status"] == "listed" for l in all_l)
    assert client.get("/api/marketplace/listings", headers=buyer, params={"crop_type": "NoSuchCrop"}).json() == []


def test_order_lifecycle_end_to_end(client, farmer, buyer, distributor):
    r = upload(client, farmer, make_photo())
    lid = r.json()["id"]
    client.post(f"/api/crops/{lid}/list", headers=farmer, params={"asking_price": 1900})
    o = client.post("/api/marketplace/orders", headers=buyer, json={"listing_id": lid, "quantity_kg": 300, "agreed_price": 1900})
    assert o.status_code == 200 and o.json()["status"] == "placed"
    oid = o.json()["id"]
    # listing is now sold; a second order must fail
    assert client.post("/api/marketplace/orders", headers=buyer, json={"listing_id": lid, "quantity_kg": 1, "agreed_price": 1}).status_code == 400
    # skipping a stage is rejected
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=distributor, json={"status": "delivered"}).status_code == 400
    # the buyer cannot confirm, the owning farmer can
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=buyer, json={"status": "confirmed"}).status_code == 403
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=farmer, json={"status": "confirmed"}).json()["status"] == "confirmed"
    # a farmer cannot start transit
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=farmer, json={"status": "in_transit"}).status_code == 403
    t = client.patch(f"/api/marketplace/orders/{oid}/status", headers=distributor, json={"status": "in_transit"})
    assert t.status_code == 200 and t.json()["distributor_id"] is not None
    ships = client.get("/api/iot/shipments", headers=distributor).json()
    assert any(s["order_id"] == oid for s in ships)
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=farmer, json={"status": "delivered"}).status_code == 403
    d = client.patch(f"/api/marketplace/orders/{oid}/status", headers=distributor, json={"status": "delivered"})
    assert d.status_code == 200 and d.json()["status"] == "delivered"
    # finished orders do not move again
    assert client.patch(f"/api/marketplace/orders/{oid}/status", headers=distributor, json={"status": "in_transit"}).status_code == 400
    assert not any(s["order_id"] == oid for s in client.get("/api/iot/shipments", headers=distributor).json())


def test_order_on_unlisted_listing_rejected(client, farmer, buyer, good_photo):
    lid = upload(client, farmer, good_photo).json()["id"]  # stays draft
    assert client.post("/api/marketplace/orders", headers=buyer, json={"listing_id": lid, "quantity_kg": 5, "agreed_price": 100}).status_code == 400


def test_my_orders_scoped_by_role(client, farmer, buyer):
    assert len(client.get("/api/marketplace/orders/mine", headers=buyer).json()) >= 1
    assert len(client.get("/api/marketplace/orders/mine", headers=farmer).json()) >= 1


@pytest.mark.xfail(reason="known gap: order quantity and price are not validated (zero, negative or larger than the listing are accepted)", strict=False)
def test_order_rejects_nonpositive_quantity(client, farmer, buyer, good_photo):
    lid = upload(client, farmer, good_photo).json()["id"]
    client.post(f"/api/crops/{lid}/list", headers=farmer, params={"asking_price": 1900})
    r = client.post("/api/marketplace/orders", headers=buyer, json={"listing_id": lid, "quantity_kg": -50, "agreed_price": 0})
    assert r.status_code in (400, 422)


# ------------------------------------------------------------------ IoT
def test_iot_history_and_websocket(client, farmer, buyer, distributor):
    lid = upload(client, farmer, make_photo()).json()["id"]
    client.post(f"/api/crops/{lid}/list", headers=farmer, params={"asking_price": 1800})
    oid = client.post("/api/marketplace/orders", headers=buyer, json={"listing_id": lid, "quantity_kg": 100, "agreed_price": 1800}).json()["id"]
    client.patch(f"/api/marketplace/orders/{oid}/status", headers=farmer, json={"status": "confirmed"})
    client.patch(f"/api/marketplace/orders/{oid}/status", headers=distributor, json={"status": "in_transit"})
    sid = next(s["id"] for s in client.get("/api/iot/shipments", headers=distributor).json() if s["order_id"] == oid)
    with client.websocket_connect(f"/api/iot/ws/iot/{sid}") as ws:
        msgs = [ws.receive_json() for _ in range(3)]
    for m in msgs:
        assert set(m) == {"temperature_c", "humidity_pct", "shock_g", "is_anomaly"}
    h = client.get(f"/api/iot/shipments/{sid}/history", headers=distributor)
    assert h.status_code == 200 and len(h.json()) >= 3


def test_iot_unknown_shipment(client, distributor):
    assert client.get("/api/iot/shipments/424242/history", headers=distributor).status_code == 404


def test_simulator_is_deterministic_per_seed():
    from app.ml.iot.simulate import ShipmentSensorState

    a, b = ShipmentSensorState(5), ShipmentSensorState(5)
    assert [a.step() for _ in range(50)] == [b.step() for _ in range(50)]
    c = ShipmentSensorState(6)
    assert [c.step() for _ in range(50)] != [ShipmentSensorState(5).step() for _ in range(50)]


def test_simulator_bounds_and_anomaly_flag():
    from app.ml.iot.simulate import ShipmentSensorState

    s = ShipmentSensorState(11)
    flagged = 0
    for _ in range(800):
        r = s.step()
        assert -5.0 <= r["temperature_c"] <= 35.0 and 20.0 <= r["humidity_pct"] <= 98.0 and r["shock_g"] >= 0
        flagged += r["is_anomaly"]
    assert flagged > 0


# ------------------------------------------------------------------ admin
def test_admin_overview_and_model_insights(client, admin):
    o = client.get("/api/admin/overview", headers=admin).json()
    assert set(o["users_by_role"]) == {"farmer", "buyer", "distributor", "admin"} and o["orders"] >= 1
    m = client.get("/api/admin/model-insights", headers=admin).json()
    assert 0.5 < m["quality_model"]["test_accuracy"] <= 1.0 and 0.5 < m["price_model"]["test_r2"] <= 1.0
    assert len(m["quality_model"]["feature_importance"]) == 11
    assert "Synthetically" in m["quality_model"]["training_data"] and "Synthetically" in m["price_model"]["training_data"]


# ------------------------------------------------------------------ CV feature extraction
def test_feature_vector_contract(good_photo):
    from app.ml.quality.feature_extraction import FEATURE_NAMES, extract_features

    f = extract_features(good_photo)
    assert list(f) == FEATURE_NAMES and all(0.0 <= v <= 1.0 for v in f.values())


def test_blemishes_raise_blemish_ratio_and_edges(good_photo, bad_photo):
    from app.ml.quality.feature_extraction import extract_features

    g, b = extract_features(good_photo), extract_features(bad_photo)
    assert b["blemish_ratio"] > g["blemish_ratio"] and b["edge_density"] > g["edge_density"]


def test_blank_image_does_not_crash():
    from app.ml.quality.infer import grade_image

    out = grade_image(make_photo("good", (64, 64)))
    assert out["grade"] in {"A", "B", "C", "Reject"}


def test_grading_is_deterministic(good_photo):
    from app.ml.quality.infer import grade_image

    a, b = grade_image(good_photo)["probabilities"], grade_image(good_photo)["probabilities"]
    assert a.keys() == b.keys() and all(math.isclose(a[k], b[k], abs_tol=1e-9) for k in a)
