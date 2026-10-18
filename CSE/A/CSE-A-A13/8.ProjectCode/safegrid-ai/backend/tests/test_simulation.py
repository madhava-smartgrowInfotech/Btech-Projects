"""Engine, scenario, coordinator and experiment tests. Require pandapower (skipped otherwise)."""
import asyncio

import pytest

pytest.importorskip("pandapower")

from app.models.schemas import RunConfig  # noqa: E402
from app.safety.events import verify_chain  # noqa: E402
from app.simulation import coordinator  # noqa: E402
from app.simulation.engine import SimulationEngine  # noqa: E402
from app.simulation.experiment import run_experiment  # noqa: E402
from app.simulation.scenarios import SCENARIO_ORDER, SCENARIOS  # noqa: E402
from app.simulation.timestep import Profiles, build_timeline  # noqa: E402


def run(cfg):
    eng = SimulationEngine(RunConfig(**cfg))
    summary = asyncio.run(eng.run())
    return eng, summary


def test_all_seven_scenarios_defined():
    assert set(SCENARIO_ORDER) == {"normal", "high_solar", "peak_demand", "battery_stress", "line_congestion",
                                   "voltage_violation", "unsafe_ai_action"}


def test_timeline_and_profiles_are_seeded():
    from app.grid.network import DEFAULT_NODES
    tl = build_timeline("09:00", 24, 15)
    assert tl[0].label == "09:00" and tl[4].label == "10:00"
    a, b, c = Profiles(1, DEFAULT_NODES, tl), Profiles(1, DEFAULT_NODES, tl), Profiles(2, DEFAULT_NODES, tl)
    series = lambda p: [(p.at(i).pv_kw["node_3"], p.at(i).load_kw["node_1"]) for i in range(24)]
    assert series(a) == series(b)  # same seed -> identical
    assert series(a) != series(c)  # different seed -> different


def test_every_scenario_runs_and_shield_causes_no_violations():
    for sid in SCENARIO_ORDER:
        eng, s = run({"scenario_id": sid, "steps": 10, "step_delay_s": 0})
        assert s["steps_run"] == 10
        assert s["violations_caused_by_actions"] == 0, sid  # the property the shield is designed to give
        assert s["power_flow_failures"] == 0, sid
        assert s["safety_chain_valid"] is True


def test_unshielded_arm_does_cause_violations_in_congestion():
    _, s = run({"scenario_id": "line_congestion", "steps": 10, "shield_enabled": False, "step_delay_s": 0})
    assert s["violations_caused_by_actions"] > 0


def test_unsafe_scenario_intervenes_and_logs_original_request():
    eng, s = run({"scenario_id": "unsafe_ai_action", "steps": 8, "step_delay_s": 0})
    assert s["rejected"] + s["projected"] > 0
    big = [r for row in eng.rows for r in row["agents"] if r["proposal"]["power_kw"] >= 900]
    assert big
    for r in big:
        assert r["shield"]["requested_action"]["power_kw"] == r["proposal"]["power_kw"]  # original preserved
        assert r["executed_power_kw"] < 100  # never executed


def test_malformed_output_uses_labelled_fallback():
    eng, s = run({"scenario_id": "unsafe_ai_action", "steps": 8, "step_delay_s": 0})
    fb = [r for row in eng.rows for r in row["agents"] if r["decision_source"] == "fallback"]
    assert fb and "LLMOutputError" in fb[0]["fallback_reason"]


def test_runs_are_reproducible():
    _, a = run({"scenario_id": "high_solar", "steps": 8, "seed": 7, "step_delay_s": 0})
    _, b = run({"scenario_id": "high_solar", "steps": 8, "seed": 7, "step_delay_s": 0})
    for k in ("approved", "projected", "rejected", "total_cost", "import_kwh", "export_kwh"):
        assert a[k] == b[k]


def test_safety_chain_detects_tampering():
    from dataclasses import replace
    eng, _ = run({"scenario_id": "unsafe_ai_action", "steps": 6, "step_delay_s": 0})
    ev = eng.safety_events
    assert len(ev) > 1 and verify_chain(ev)
    bad = list(ev)
    bad[0] = replace(bad[0], payload_json=bad[0].payload_json.replace("rejected", "approved").replace("projected", "approved"))
    assert not verify_chain(bad)


def test_step_by_step_and_dry_run_does_not_mutate():
    eng = SimulationEngine(RunConfig(scenario_id="normal", steps=4, step_delay_s=0))
    asyncio.run(eng.step())
    soc = {n: s.soc for n, s in eng.sim.nodes.items()}
    d = asyncio.run(eng.dry_run("renewable_01"))
    assert d["executed"] is False
    assert {n: s.soc for n, s in eng.sim.nodes.items()} == soc and eng.step_index == 1


def test_coordinator_detects_peer_mismatch():
    from types import SimpleNamespace as NS
    mk = lambda a, t, p, n: NS(agent_id=a, node_id=n, action=NS(action_type=t, power_kw=p, target_node=None))
    c = coordinator.detect_conflicts([mk("a", "export_power", 5, "node_1"), mk("b", "import_power", 1, "node_2")])
    assert any(x["type"] == "PEER_MISMATCH" for x in c)


def test_experiment_runs_real_simulations():
    r = asyncio.run(run_experiment(["normal"], [0], 6))
    assert set(r["overall"]) == {"baseline_rule", "agents_unshielded", "safegrid_shielded"}
    assert r["overall"]["safegrid_shielded"]["violations_caused_by_actions"]["mean"] == 0
    assert len(r["runs"]) == 3
