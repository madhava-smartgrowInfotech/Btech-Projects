"""Experiment runner: real simulations only, nothing is hard-coded or fabricated.

Arms (each run on identical scenario + seed so differences come from the controller/safety layer):
  baseline_rule       non-LLM time-of-use rule controller, no shield
  agents_unshielded   agent proposals (mock LLM + fault injection) applied as requested (ablation)
  safegrid_shielded   the proposed system: agent proposals -> Symbolic Safety Shield -> grid

Scenario fault injection is applied to the two agent arms only (the baseline has no LLM to misbehave).
"""
from __future__ import annotations

import asyncio
import statistics
from typing import Any

from app.config import Settings, get_settings
from app.models.schemas import RunConfig
from app.simulation.engine import SimulationEngine
from app.simulation.scenarios import SCENARIO_ORDER

ARMS: dict[str, dict[str, Any]] = {
    "baseline_rule": {"provider": "baseline", "shield_enabled": False, "label": "Baseline (rule-based, no shield)"},
    "agents_unshielded": {"provider": "mock", "shield_enabled": False, "label": "Agents, no shield (ablation)"},
    "safegrid_shielded": {"provider": "mock", "shield_enabled": True, "label": "SafeGrid-AI (agents + shield)"},
}
ARM_ORDER = list(ARMS)
METRICS = ["violation_steps_caused_by_actions", "violations_caused_by_actions", "violation_steps_no_action", "violation_steps_executed", "violations_executed", "voltage_violation_steps", "line_overload_events",
           "trafo_overload_events", "total_cost", "renewable_utilization", "battery_utilization",
           "intervention_rate", "fallback_rate", "avg_decision_latency_ms", "avg_step_time_ms",
           "proposals", "approved", "projected", "rejected", "violation_steps_without_shield", "violations_without_shield"]


async def run_one(scenario: str, arm: str, seed: int, steps: int | None, dt: int, settings: Settings) -> dict[str, Any]:
    a = ARMS[arm]
    cfg = RunConfig(scenario_id=scenario, seed=seed, steps=steps, time_step_minutes=dt, provider=a["provider"],
                    shield_enabled=a["shield_enabled"], inject_faults=arm != "baseline_rule", step_delay_s=0.0)
    eng = SimulationEngine(cfg, settings)
    return await eng.run(realtime=False)


def _agg(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for m in METRICS:
        vals = [r[m] for r in rows if r.get(m) is not None]
        if not vals:
            out[m] = None
            continue
        out[m] = {"mean": round(statistics.fmean(vals), 4), "min": round(min(vals), 4), "max": round(max(vals), 4),
                  "stdev": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0.0}
    return out


async def run_experiment(scenarios: list[str] | None = None, seeds: list[int] | None = None, steps: int | None = None,
                         arms: list[str] | None = None, dt: int = 15, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    scenarios = scenarios or list(SCENARIO_ORDER)
    seeds = seeds if seeds is not None else [0, 1, 2]
    arms = arms or list(ARM_ORDER)
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        raise ValueError(f"unknown arms: {unknown}")
    runs: list[dict[str, Any]] = []
    for sc in scenarios:
        for arm in arms:
            for seed in seeds:
                s = await run_one(sc, arm, seed, steps, dt, settings)
                runs.append({"scenario": sc, "arm": arm, "seed": seed, "summary": s})
                await asyncio.sleep(0)
    table: dict[str, dict[str, Any]] = {}
    for sc in scenarios:
        table[sc] = {arm: _agg([r["summary"] for r in runs if r["scenario"] == sc and r["arm"] == arm]) for arm in arms}
    overall = {arm: _agg([r["summary"] for r in runs if r["arm"] == arm]) for arm in arms}
    return {"spec": {"scenarios": scenarios, "seeds": seeds, "steps": steps, "arms": arms, "time_step_minutes": dt,
                     "arm_definitions": {a: ARMS[a]["label"] for a in arms}},
            "runs": runs, "by_scenario": table, "overall": overall,
            "notes": ["All numbers come from simulation runs on a small illustrative 3-node LV feeder; they are not field results.",
                      "The mock LLM provider is deterministic and rule-driven; results with a real LLM will differ.",
                      "'violations_caused_by_actions' counts limit violations that are new or worse than the grid state with all agents idle "
                      "(what the shield is designed to prevent); 'violations_executed' also includes pre-existing stress no action caused; "
                      "'violations_without_shield' counts violations the raw proposals would have caused."]}
