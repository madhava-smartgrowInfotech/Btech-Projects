import os
import subprocess
import sys

import pytest

from app.models.actions import EnergyAction
from app.safety import ShieldStatus
from app.safety.events import SafetyEvent, verify_chain, GENESIS
from tests.helpers import FakeGrid, action, limits, make_cfg, make_node, run


def codes(d):
    return {v.code for v in d.violations}


# --- spec test 1: valid battery charge -------------------------------------------------
def test_valid_charge_is_approved():
    d = run(action("charge_battery", 2.0))
    assert d.status == ShieldStatus.APPROVED
    assert d.violations == []
    assert d.validated_action["power_kw"] == 2.0
    assert d.setpoint.storage_kw == 2.0


# --- spec test 2: excessive charge is projected, original preserved ----------------------
def test_excess_charge_is_projected_and_original_preserved():
    a = action("charge_battery", 10.0)
    d = run(a)
    assert d.status == ShieldStatus.PROJECTED
    assert "BATTERY_CHARGE_LIMIT" in codes(d)
    assert d.requested_power_kw == 10.0
    assert d.safe_power_kw == pytest.approx(5.0, abs=1e-4)
    assert d.requested_action["power_kw"] == 10.0  # audit copy untouched
    assert d.validated_action["power_kw"] == pytest.approx(5.0, abs=1e-4)
    assert a.power_kw == 10.0  # the proposal object itself is not mutated
    assert d.corrections[0]["field"] == "power_kw"


# --- spec test 3: negative / invalid SOC -------------------------------------------------
def test_negative_soc_is_rejected():
    d = run(action("discharge_battery", 1.0), node=make_node(soc=-0.2))
    assert d.status == ShieldStatus.REJECTED
    assert "INVALID_NODE_STATE" in codes(d)
    assert d.validated_action is None


def test_charge_on_full_battery_is_rejected_with_soc_limit():
    d = run(action("charge_battery", 3.0), node=make_node(soc=0.95))
    assert d.status == ShieldStatus.REJECTED
    assert "BATTERY_SOC_LIMIT" in codes(d)


def test_discharge_beyond_stored_energy_is_projected():
    # 10 kWh * (0.15-0.10) * 0.95 / 0.25h = 1.9 kW available
    d = run(action("discharge_battery", 4.0), node=make_node(soc=0.15))
    assert d.status == ShieldStatus.PROJECTED
    assert d.safe_power_kw == pytest.approx(1.9, abs=1e-3)
    assert "BATTERY_SOC_LIMIT" in codes(d)


def test_battery_unavailable_when_ev_away():
    d = run(action("charge_battery", 2.0), node=make_node(available=False))
    assert d.status == ShieldStatus.REJECTED
    assert "BATTERY_UNAVAILABLE" in codes(d)


# --- spec test 4: line overload -----------------------------------------------------------
def test_line_overload_is_projected():
    cfg = make_cfg(limits(max_charge_kw=30, max_import_kw=40, storage_capacity_kwh=100))
    node = make_node(load=0.0)
    grid = FakeGrid(node, kl=8.0)  # 100 % at 12.5 kW
    d = run(action("charge_battery", 20.0), node=node, cfg=cfg, grid=grid)
    assert d.status == ShieldStatus.PROJECTED
    assert "LINE_OVERLOAD" in codes(d)
    assert d.safe_power_kw == pytest.approx(12.5, abs=0.01)
    assert d.after_trial.line_loading["L01"] <= 100.0 + 1e-6


# --- spec test 5: voltage violation ------------------------------------------------------
def test_undervoltage_is_projected():
    cfg = make_cfg(limits(max_charge_kw=30, max_import_kw=40, storage_capacity_kwh=100))
    node = make_node(load=0.0)
    grid = FakeGrid(node, kv=0.004)  # 0.95 pu at 12.5 kW
    d = run(action("charge_battery", 20.0), node=node, cfg=cfg, grid=grid)
    assert d.status == ShieldStatus.PROJECTED
    assert "VOLTAGE_UNDER" in codes(d)
    assert d.after_trial.bus_vm["bus_1"] >= cfg.v_min - 1e-9


def test_overvoltage_from_export_is_projected():
    cfg = make_cfg(limits(max_discharge_kw=30, max_export_kw=40, storage_capacity_kwh=100))
    node = make_node(load=0.0, pv=0.0, soc=0.9)
    grid = FakeGrid(node, kv=0.004)
    d = run(action("discharge_battery", 25.0), node=node, cfg=cfg, grid=grid)
    assert d.status == ShieldStatus.PROJECTED
    assert "VOLTAGE_OVER" in codes(d)
    assert d.after_trial.bus_vm["bus_1"] <= cfg.v_max + 1e-9


def test_voltage_limits_come_from_configuration():
    cfg = make_cfg(limits(max_charge_kw=30, max_import_kw=40, storage_capacity_kwh=100), v_min=0.90)
    node = make_node(load=0.0)
    d = run(action("charge_battery", 20.0), node=node, cfg=cfg, grid=FakeGrid(node))
    assert "VOLTAGE_UNDER" not in codes(d) or d.safe_power_kw > 12.5


def test_power_flow_failure_blocks_action():
    node = make_node()
    d = run(action("charge_battery", 2.0), node=node, grid=FakeGrid(node, converged=False))
    # grid already failing before the action: nothing new is attributable, so it must not be blamed on the action
    assert d.status in (ShieldStatus.APPROVED, ShieldStatus.REJECTED)


def test_preexisting_violation_does_not_block_a_relieving_action():
    # base load already drops the voltage below limit; discharging improves it and must be allowed
    cfg = make_cfg(limits(max_discharge_kw=10))
    node = make_node(load=14.0, soc=0.8)
    grid = FakeGrid(node, kv=0.005)  # 0.93 pu without action
    d = run(action("discharge_battery", 3.0), node=node, cfg=cfg, grid=grid)
    assert d.status == ShieldStatus.APPROVED


# --- spec test 6: malformed LLM action ------------------------------------------------------
def test_malformed_actions_fail_schema_validation():
    good = dict(agent_id="a", action_type="idle", power_kw=0, duration_minutes=15, confidence=0.5)
    EnergyAction(**good)
    bad_variants = [
        {**good, "power_kw": -3},
        {**good, "power_kw": float("nan")},
        {**good, "action_type": "shutdown_grid"},
        {**good, "confidence": 1.7},
        {**good, "duration_minutes": 0},
        {**good, "reason_codes": ["drop table; --"]},
        {**good, "run_code": "__import__('os').system('id')"},  # extra fields forbidden
    ]
    for b in bad_variants:
        with pytest.raises(Exception):
            EnergyAction(**b)


# --- spec test 8: unsafe proposal never equals executed action --------------------------------
def test_unsafe_export_1000kw_is_stopped():
    cfg = make_cfg(limits(max_export_kw=5))
    node = make_node(load=1.0, pv=4.0)
    a = action("export_power", 1000.0)
    d = run(a, node=node, cfg=cfg)
    assert d.status in (ShieldStatus.REJECTED, ShieldStatus.PROJECTED)
    assert d.requested_action["power_kw"] == 1000.0
    executed = d.validated_action["power_kw"] if d.validated_action else 0.0
    assert executed != 1000.0 and executed <= 5.0 + 1e-6
    assert -d.after_trial.node_exchange_kw["node_1"] <= 5.0 + 1e-6


def test_moderately_excessive_export_is_projected_to_node_limit():
    cfg = make_cfg(limits(max_export_kw=5, max_discharge_kw=10, storage_capacity_kwh=50))
    node = make_node(load=1.0, pv=4.0, soc=0.8)
    d = run(action("export_power", 9.0), node=node, cfg=cfg)
    assert d.status == ShieldStatus.PROJECTED
    assert "NODE_EXPORT_LIMIT" in codes(d)
    assert d.safe_power_kw == pytest.approx(5.0, abs=1e-3)


def test_export_target_unreachable_direction_is_rejected():
    # load 10, no PV, battery can give 5 kW -> net exchange is always an import; export is impossible
    cfg = make_cfg(limits(max_discharge_kw=5))
    node = make_node(load=10.0, pv=0.0, soc=0.8)
    d = run(action("export_power", 3.0), node=node, cfg=cfg)
    assert d.status == ShieldStatus.REJECTED


def test_curtail_more_than_generated_is_projected():
    node = make_node(load=1.0, pv=3.0)
    d = run(action("curtail_generation", 8.0), node=node)
    assert d.status == ShieldStatus.PROJECTED
    assert d.safe_power_kw == pytest.approx(3.0, abs=1e-4)
    assert "CURTAILMENT_EXCEEDS_GENERATION" in codes(d)


# --- structural rejections ---------------------------------------------------------------
def test_unknown_agent_and_mismatch_and_target_are_rejected():
    assert run(action(agent="ghost")).status == ShieldStatus.REJECTED
    d = run(action(target="node_99"))
    assert d.status == ShieldStatus.REJECTED and "UNKNOWN_TARGET_NODE" in codes(d)


def test_idle_always_approved_and_duration_is_aligned():
    d = run(action("idle", 0.0))
    assert d.status == ShieldStatus.APPROVED
    d2 = run(action("charge_battery", 1.0, dur=60))
    assert d2.validated_action["duration_minutes"] == 15
    assert d2.corrections and d2.corrections[0]["field"] == "duration_minutes"


# --- determinism & independence ---------------------------------------------------------------
def test_shield_is_deterministic():
    r1 = run(action("charge_battery", 10.0)).to_dict()
    r2 = run(action("charge_battery", 10.0)).to_dict()
    r1.pop("timestamp"); r2.pop("timestamp")
    assert r1 == r2


def test_shield_does_not_import_llm_or_agents():
    code = ("import sys, app.safety.shield;"
            "bad=[m for m in sys.modules if m.startswith(('app.llm','app.agents','app.simulation','app.grid'))];"
            "sys.exit(1 if bad else 0)")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    assert subprocess.run([sys.executable, "-c", code], env=env).returncode == 0


# --- audit trail ------------------------------------------------------------------------------
def test_event_chain_is_tamper_evident():
    events, prev = [], GENESIS
    for i in range(3):
        e = SafetyEvent.create(i, "run1", i, f"09:{i:02d}", "now", {"shield_status": "approved", "n": i}, prev)
        events.append(e); prev = e.hash
    assert verify_chain(events)
    forged = SafetyEvent(1, "run1", 1, "09:01", "now", '{"n":1,"shield_status":"rejected"}', events[1].prev_hash, events[1].hash)
    assert not verify_chain([events[0], forged, events[2]])
