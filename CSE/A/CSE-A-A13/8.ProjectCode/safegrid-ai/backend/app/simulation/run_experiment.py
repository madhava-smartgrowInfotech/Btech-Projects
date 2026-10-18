"""CLI: python -m app.simulation.run_experiment --seeds 0 1 2 --steps 24 --out results/experiment.json"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.simulation.experiment import ARM_ORDER, run_experiment
from app.simulation.scenarios import SCENARIO_ORDER


def main() -> None:
    ap = argparse.ArgumentParser(description="Baseline vs. SafeGrid-AI experiment (real simulation runs).")
    ap.add_argument("--scenarios", nargs="*", default=None, choices=SCENARIO_ORDER)
    ap.add_argument("--seeds", nargs="*", type=int, default=[0, 1, 2])
    ap.add_argument("--steps", type=int, default=None, help="steps per run (default: scenario length)")
    ap.add_argument("--arms", nargs="*", default=None, choices=ARM_ORDER)
    ap.add_argument("--dt", type=int, default=15, help="time step in minutes")
    ap.add_argument("--out", default=None, help="write full JSON results here")
    a = ap.parse_args()
    res = asyncio.run(run_experiment(a.scenarios, a.seeds, a.steps, a.arms, a.dt))
    arms = res["spec"]["arms"]
    cols = [("violation_steps_caused_by_actions", "caused-viol steps"), ("violations_without_shield", "raw-viol"),
            ("voltage_violation_steps", "V-viol steps"), ("line_overload_events", "line-overload"), ("total_cost", "cost"),
            ("renewable_utilization", "RES util")]
    print(f"{'scenario':<18}{'arm':<20}" + "".join(f"{c[1]:>18}" for c in cols))
    for sc, per_arm in res["by_scenario"].items():
        for arm in arms:
            row = per_arm[arm]
            vals = "".join(f"{(row[k]['mean'] if row[k] else float('nan')):>18.3f}" for k, _ in cols)
            print(f"{sc:<18}{arm:<20}{vals}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=2, default=str))
        print(f"\nfull results written to {a.out}")
    for n in res["notes"]:
        print("note:", n)


if __name__ == "__main__":
    main()
