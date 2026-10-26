import time

import pytest

from tests.conftest import attack_context, attack_features, benign_features


def test_status_idle_shape(client):
    r = client.get("/api/status")
    j = r.get_json()
    assert r.status_code == 200 and j["mode"] == "stopped" and j["model_trained"] is True
    assert {"product", "monitoring", "window_seconds", "windows_completed", "latest", "active_mitigations"} <= set(j)


def test_unknown_endpoint_returns_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and "error" in r.get_json()


def test_interfaces_listed(client):
    j = client.get("/api/interfaces").get_json()
    assert isinstance(j["interfaces"], list) and j["interfaces"] and "name" in j["interfaces"][0]


@pytest.mark.parametrize("body", [{"window_seconds": 1}, {"window_seconds": 121}, {"window_seconds": "x"},
                                  {"quarantine_seconds": 4}, {"quarantine_seconds": 3601}, {"quarantine_seconds": "x"}])
def test_settings_reject_out_of_range_values(client, body):
    r = client.post("/api/settings", json=body)
    assert r.status_code == 400 and "error" in r.get_json()


def test_settings_accept_and_persist_valid_values(client):
    r = client.post("/api/settings", json={"window_seconds": 12, "quarantine_seconds": 45})
    assert r.status_code == 200
    j = client.get("/api/settings").get_json()
    assert j["window_seconds"] == 12 and j["quarantine_seconds"] == 45


def test_settings_ignore_malformed_json(client):
    r = client.post("/api/settings", data="not json", content_type="application/json")
    assert r.status_code == 200


def test_detections_invalid_limit_is_400(client):
    assert client.get("/api/detections?limit=abc").status_code == 400


def test_detections_limit_is_clamped_and_empty_is_ok(client):
    j = client.get("/api/detections?limit=100000").get_json()
    assert j["detections"] == [] and j["by_prediction"] == {}


def test_latest_empty_message(client):
    j = client.get("/api/detections/latest").get_json()
    assert j["detection"] is None and "No detections" in j["message"]


def test_model_metrics_endpoint_reports_synthetic_provenance(client):
    j = client.get("/api/model/metrics").get_json()
    assert j["trained"] is True and j["metrics"]["is_synthetic"] is True
    assert len(j["feature_importance"]) == 10 and j["confusion_matrix"]["labels"] == ["Benign", "Attack"]


def test_result_images_are_served(client):
    r = client.get("/static/results/confusion_matrix.png")
    assert r.status_code == 200 and r.data[:4] == b"\x89PNG"


def test_process_window_flood_is_attack_critical_and_quarantines(flask_app):
    rec = flask_app.process_window(attack_features(), attack_context(), "simulation", "simulation")
    assert rec["prediction"] == "Attack" and rec["severity"] in ("High", "Critical")
    assert rec["mitigation_status"] == "quarantine" and rec["id"] is not None
    assert len(flask_app.mitigation.get_active()) == 3


def test_process_window_benign_is_low_and_monitors(flask_app):
    ctx = {"unique_sources": 2, "unique_destinations": 2, "top_sources": [], "packet_count": 3000}
    rec = flask_app.process_window(benign_features(), ctx, "simulation", "simulation")
    assert rec["severity"] in ("Low", "Medium") and rec["mitigation_status"] in ("monitor", "rate_limit_recommended")
    assert flask_app.mitigation.get_active() == []


def test_process_window_reports_capture_error(flask_app):
    assert flask_app.process_window({}, {"error": "Npcap missing"}, "live-error", "eth0") == {"error": "Npcap missing"}


def test_process_window_reports_feature_validation_error(flask_app):
    r = flask_app.process_window({"received_packets": 1}, {}, "simulation", "simulation")
    assert "Feature validation failed" in r["error"]


def test_detections_visible_through_api_after_processing(flask_app, client):
    flask_app.process_window(attack_features(), attack_context(), "simulation", "simulation")
    j = client.get("/api/detections?limit=5").get_json()
    assert j["by_prediction"]["Attack"] == 1 and j["detections"][0]["detail"]["severity"]["factors"]
    assert client.get("/api/detections/latest").get_json()["detection"]["prediction"] == "Attack"
    m = client.get("/api/mitigations").get_json()
    assert len(m["active"]) == 3 and len(m["history"]) == 3 and m["quarantine_seconds"] == 40


def test_demo_start_conflict_and_stop(client):
    assert client.post("/api/demo/start", json={"window_seconds": 2}).status_code == 200
    r = client.post("/api/demo/start", json={})
    assert r.status_code == 409
    assert client.post("/api/monitor/start", json={}).status_code == 409
    assert client.post("/api/demo/stop").status_code == 200
    assert client.get("/api/status").get_json()["mode"] == "stopped"


@pytest.mark.parametrize("path", ["/api/demo/start", "/api/monitor/start"])
@pytest.mark.parametrize("w", [1, 500, "x"])
def test_start_rejects_bad_window(client, path, w):
    assert client.post(path, json={"window_seconds": w}).status_code == 400


def test_simulation_end_to_end_produces_scored_windows(flask_app, client):
    client.post("/api/demo/start", json={"window_seconds": 2})
    deadline = time.time() + 6
    while time.time() < deadline and not client.get("/api/detections").get_json()["detections"]:
        time.sleep(0.2)
    client.post("/api/demo/stop")
    d = client.get("/api/detections").get_json()["detections"]
    assert d and d[0]["source"] == "simulation" and d[0]["prediction"] in ("Attack", "Benign")


def test_monitor_stop_is_idempotent(client):
    assert client.post("/api/monitor/stop").status_code == 200
    assert client.post("/api/monitor/stop").status_code == 200


def test_health_endpoint_shape(client):
    j = client.get("/api/health").get_json()
    assert {"current", "recent", "history"} <= set(j)


def test_dashboard_page_served(client):
    r = client.get("/")
    assert r.status_code == 200 and b"SentinelFlow" in r.data
