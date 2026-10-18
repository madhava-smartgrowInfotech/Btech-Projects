"""CLI: python -m app.simulation.run_scenario unsafe_ai_action --seed 42 --provider mock [--no-shield]"""
from __future__ import annotations

import argparse
import asyncio
import json

from app.models.schemas import RunConfig
from app.simulation.engine import SimulationEngine
from app.simulation.scenarios import SCENARIO_ORDER


async def _run(cfg: RunConfig, verbose: bool) -> None:
    eng = SimulationEngine(cfg)
    summary = await eng.run(realtime=False)
    if verbose:
        for row in eng.rows:
            for a in row["agents"]:
                s = a["shield"]
                flag = "" if s["status"] == "approved" else f"  <-- {s['status'].upper()} " + ",".join(v["code"] for v in s["violations"])
                print(f"{row['time']} {a['agent_id']:<13}{a['proposal']['action_type']:<19}{a['proposal']['power_kw']:>8.2f} kW -> "
                      f"executed {a['executed_power_kw']:>6.2f} kW [{a['decision_source']}]{flag}")
    print(json.dumps(summary, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", choices=SCENARIO_ORDER)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--provider", default="mock", choices=["mock", "api", "failing", "baseline"])
    ap.add_argument("--no-shield", action="store_true", help="ablation: apply proposals without the shield")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    cfg = RunConfig(scenario_id=a.scenario, seed=a.seed, steps=a.steps, provider=a.provider,
                    shield_enabled=not a.no_shield, step_delay_s=0.0)
    asyncio.run(_run(cfg, not a.quiet))


if __name__ == "__main__":
    main()
