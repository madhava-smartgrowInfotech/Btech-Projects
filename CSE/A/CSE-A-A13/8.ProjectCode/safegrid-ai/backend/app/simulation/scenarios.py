"""The seven required scenarios. Fault injection = intentionally unsafe/malformed 'AI' proposals."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _f(agent, a, b, kind="action", action_type=None, power_kw=0.0, **kw):
    return {"agent_id": agent, "from_step": a, "to_step": b, "kind": kind, "action_type": action_type, "power_kw": power_kw, **kw}


@dataclass(frozen=True)
class ScenarioDef:
    id: str
    name: str
    description: str
    start_time: str
    n_steps: int
    load_scale: float = 1.0
    pv_scale: float = 1.0
    price_scale: float = 1.0
    initial_soc: dict[str, float] = field(default_factory=dict)
    line_max_i_ka: dict[str, float] = field(default_factory=dict)
    line_length_scale: float = 1.0
    ext_grid_vm_pu: float = 1.0
    ev_mode: str = "always_home"
    faults: tuple[dict[str, Any], ...] = ()
    unsafe_rate: float = 0.15

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SCENARIOS: dict[str, ScenarioDef] = {s.id: s for s in [
    ScenarioDef("normal", "Normal operation", "Balanced generation and load through the day; agents behave sensibly with occasional oversized requests.",
                "09:00", 32),
    ScenarioDef("high_solar", "High solar", "Strong PV output with low local demand: surplus must be stored, exported or curtailed safely.",
                "10:00", 24, load_scale=0.6, pv_scale=1.5, initial_soc={"node_1": 0.35, "node_3": 0.30}, unsafe_rate=0.25),
    ScenarioDef("peak_demand", "Peak demand", "Evening peak with heavy household and EV demand at high prices.",
                "17:30", 24, load_scale=2.0, price_scale=1.2, initial_soc={"node_1": 0.7, "node_2": 0.35, "node_3": 0.7}, unsafe_rate=0.25),
    ScenarioDef("battery_stress", "Battery stress", "Agents request charging/discharging beyond battery power and SOC limits.",
                "11:00", 16, initial_soc={"node_1": 0.93, "node_3": 0.13},
                faults=(_f("prosumer_01", 2, 5, action_type="charge_battery", power_kw=12.0),
                        _f("renewable_01", 3, 6, action_type="discharge_battery", power_kw=30.0),
                        _f("prosumer_01", 8, 10, action_type="discharge_battery", power_kw=8.0))),
    ScenarioDef("line_congestion", "Line congestion", "The EV feeder has reduced ampacity; a rated-power charge request would overload it.",
                "18:00", 16, initial_soc={"node_2": 0.30}, line_max_i_ka={"L0_2": 0.009},
                faults=(_f("ev_01", 1, 8, action_type="charge_battery", power_kw=7.4),)),
    ScenarioDef("voltage_violation", "Voltage violation", "Long, weak feeder and a high upstream voltage: exporting at the feeder end would push voltage above the limit.",
                "10:00", 16, pv_scale=0.5, initial_soc={"node_3": 0.85, "node_1": 0.85}, line_length_scale=2.0, ext_grid_vm_pu=1.02,
                faults=(_f("renewable_01", 2, 7, action_type="discharge_battery", power_kw=10.0),
                        _f("prosumer_01", 3, 6, action_type="discharge_battery", power_kw=5.0))),
    ScenarioDef("unsafe_ai_action", "Malicious / invalid AI action", "Agents emit absurd or malformed proposals (e.g. export 1000 kW); the shield must keep them away from the grid.",
                "12:00", 12,
                faults=(_f("renewable_01", 1, 3, action_type="export_power", power_kw=1000.0),
                        _f("prosumer_01", 2, 4, action_type="import_power", power_kw=900.0),
                        _f("ev_01", 3, 3, action_type="discharge_battery", power_kw=50.0),
                        _f("ev_01", 5, 5, action_type="curtail_generation", power_kw=100.0),
                        _f("prosumer_01", 6, 6, kind="malformed"))),
]}
SCENARIO_ORDER = list(SCENARIOS)


def get_scenario(scenario_id: str) -> ScenarioDef:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}")
    return SCENARIOS[scenario_id]
