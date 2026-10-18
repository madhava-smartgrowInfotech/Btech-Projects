"""HTTP/WebSocket API tests. Require fastapi + pandapower (skipped otherwise)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pandapower")

from fastapi.testclient import TestClient  # noqa: E402

from app.database.store import SQLiteStore  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.simulation_service import SimulationService  # noqa: E402


def client(tmp_path):
    svc = SimulationService(store=SQLiteStore(f"sqlite:///{tmp_path}/t.db"))
    return TestClient(create_app(svc))


def test_health_and_grid(tmp_path):
    with client(tmp_path) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        assert len(c.get("/api/grid/state").json()["nodes"]) == 3
        assert len(c.get("/api/grid/topology").json()["edges"]) == 4
        assert len(c.get("/api/agents").json()) == 3


def test_scenario_run_and_safety_events(tmp_path):
    with client(tmp_path) as c:
        r = c.post("/api/scenarios/unsafe_ai_action/run", json={"steps": 8, "step_delay_s": 0})
        assert r.status_code == 200 and r.json()["summary"]["violations_caused_by_actions"] == 0
        ev = c.get("/api/safety/events").json()
        assert ev["chain_valid"] is True and ev["events"]
        assert c.get("/api/metrics").json()["series"]
        assert c.post("/api/scenarios/nope/run").status_code == 404


def test_step_reset_and_dry_run(tmp_path):
    with client(tmp_path) as c:
        assert c.post("/api/simulation/step").status_code == 200
        assert c.get("/api/simulation/status").json()["step"] == 1
        body = {"action": {"agent_id": "renewable_01", "action_type": "export_power", "power_kw": 1000,
                           "duration_minutes": 15, "reason_codes": ["TEST"], "confidence": 0.9}}
        d = c.post("/api/agents/renewable_01/decision", json=body).json()
        assert d["shield"]["status"] in ("rejected", "projected") and d["executed"] is False
        bad = {"action": {**body["action"], "run_code": "rm -rf /"}}
        assert c.post("/api/agents/renewable_01/decision", json=bad).status_code == 422
        assert c.post("/api/simulation/reset").json()["step"] == 0


def test_websocket_receives_events(tmp_path):
    with client(tmp_path) as c:
        with c.websocket_connect("/ws/simulation") as ws:
            assert ws.receive_json()["type"] == "connected"
            c.post("/api/simulation/step")
            types = {ws.receive_json()["type"] for _ in range(6)}
            assert "agent_action" in types
