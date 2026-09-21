"""Benchmark the SeatWise engine against manual seating methods.

    python -m ml.benchmark            # full run: every scenario, 3 seeds, predictability, budget tuning
    python -m ml.benchmark --quick    # small scenarios, 1 seed, no tuning (a fast smoke run)

Writes experiments/engine-benchmark-<date>/ (metrics.json, results.csv, PNG
plots, benchmark.log). A run with tuning also writes models/engine_profile.json,
which the product loads at start-up.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ml import ROOT
from ml import plots
from ml.baselines import BASELINES
from ml.predictability import evaluate_method
from ml.scenarios import SCENARIOS, SIZE_SCENARIOS, TYPICAL, Scenario, build, describe, spec_by_name
from app.services.engine import ENGINE_VERSION, EngineResult, solve, validate

log = logging.getLogger("benchmark")

SEEDS = [11, 12, 13]
PREDICTABILITY_SEEDS = [21, 22, 23, 24, 25, 26]
TUNING_BUDGETS = [0.1, 0.15, 0.25, 0.4, 0.6]
TUNING_SCENARIOS = ["m-600", "l-1000"]
TUNING_SEEDS = [31, 32]
# Department mix is a soft preference: take the fastest budget whose mix is within 10% of the best seen.
TUNING_TOLERANCE = 0.10


class EngineFailure(RuntimeError):
    pass


def seatwise(candidates, halls, rules, seed: int, budget: float | None = None):
    result: EngineResult = solve(candidates, halls, rules, seed=seed, budget=budget)
    if not result.ok:
        raise EngineFailure("; ".join(result.reasons) or "no plan found")
    return result.placements


METHODS = {"SeatWise": seatwise, **BASELINES}


def run_once(scenario: Scenario, method: str, seed: int, budget: float | None = None) -> dict:
    fn = METHODS[method]
    started = time.perf_counter()
    try:
        placements = fn(scenario.candidates, scenario.halls, scenario.rules, seed, budget) if method == "SeatWise" \
            else fn(scenario.candidates, scenario.halls, scenario.rules, seed)
    except EngineFailure as exc:
        elapsed = time.perf_counter() - started
        log.warning("%s %s seed=%s failed after %.2fs: %s", scenario.spec.name, method, seed, elapsed, exc)
        return {"scenario": scenario.spec.name, "method": method, "seed": seed, "budget": budget,
                "solved": False, "solve_s": elapsed, "reason": str(exc)}
    elapsed = time.perf_counter() - started
    card = validate(scenario.candidates, scenario.halls, placements, scenario.rules).to_dict()
    row = {"scenario": scenario.spec.name, "method": method, "seed": seed, "budget": budget,
           "solved": True, "solve_s": elapsed, "reason": ""}
    row.update({k: v for k, v in card.items() if not isinstance(v, (list, dict))})
    if method == "SeatWise" and scenario.spec.name == TYPICAL and seed == SEEDS[0]:
        row["_per_hall"] = card.get("per_hall", [])
    log.info("%-11s %-14s seed=%-3s %6.2fs same_paper=%-5s roll=%-4s access=%-3s dept=%s",
             scenario.spec.name, method, seed, elapsed, card["same_paper_pairs"],
             card["roll_gap_violations"], card["accessible_violations"], card["same_department_pairs"])
    return row


def summarise(df: pd.DataFrame) -> list[dict]:
    summary = []
    for (scenario, method), group in df.groupby(["scenario", "method"], sort=False):
        solved = group[group["solved"]]
        entry = {
            "scenario": scenario,
            "method": method,
            "runs": int(len(group)),
            "solved_rate": float(group["solved"].mean()),
            "solve_s_mean": float(group["solve_s"].mean()),
            "solve_s_min": float(group["solve_s"].min()),
            "solve_s_max": float(group["solve_s"].max()),
        }
        for column in ("same_paper_pairs", "roll_gap_violations", "accessible_violations",
                       "capacity_violations", "same_department_pairs", "neighbour_pairs",
                       "halls_used", "utilisation"):
            if column in solved:
                entry[f"{column}_mean"] = float(solved[column].mean()) if len(solved) else None
        entry["hard_rules_satisfied_rate"] = float(solved["hard_ok"].mean()) if len(solved) else 0.0
        summary.append(entry)
    return summary


def tune(out_dir: Path) -> dict:
    log.info("Tuning the per-hall budget on %s with seeds %s", TUNING_SCENARIOS, TUNING_SEEDS)
    scenarios = [build(spec_by_name(name)) for name in TUNING_SCENARIOS]
    rows = [run_once(sc, "SeatWise", seed, budget)
            for budget in TUNING_BUDGETS for sc in scenarios for seed in TUNING_SEEDS]
    df = pd.DataFrame(rows)
    table = []
    for budget, group in df.groupby("budget"):
        table.append({
            "budget": float(budget),
            "all_hard_rules_satisfied": bool(group["solved"].all() and group["hard_ok"].fillna(False).all()),
            "same_department_pairs_mean": float(group["same_department_pairs"].mean()),
            "session_solve_s_mean": float(group["solve_s"].mean()),
        })
    valid = [t for t in table if t["all_hard_rules_satisfied"]]
    if not valid:
        raise SystemExit("No budget satisfied every hard rule - the engine needs attention before release.")
    best = min(t["same_department_pairs_mean"] for t in valid)
    chosen = min(t["budget"] for t in valid if t["same_department_pairs_mean"] <= best * (1 + TUNING_TOLERANCE) + 1)
    plots.budget_tuning([t["budget"] for t in table], [t["same_department_pairs_mean"] for t in table],
                        [t["session_solve_s_mean"] for t in table], chosen, out_dir / "budget_tuning.png")
    log.info("Chosen per-hall budget: %s", chosen)
    return {"budgets": table, "chosen_budget": chosen, "scenarios": TUNING_SCENARIOS, "seeds": TUNING_SEEDS,
            "tolerance": TUNING_TOLERANCE}


def make_plots(df: pd.DataFrame, summary: list[dict], predictability: dict, out_dir: Path, names: list[str]) -> list[str]:
    files = []
    sw = [s for s in summary if s["method"] == "SeatWise" and s["scenario"] in names and s["scenario"] in SIZE_SCENARIOS]
    sw.sort(key=lambda s: spec_by_name(s["scenario"]).candidates)
    if sw:
        files.append(plots.solve_time_by_size(
            [spec_by_name(s["scenario"]).candidates for s in sw],
            [s["solve_s_mean"] for s in sw], [s["solve_s_min"] for s in sw], [s["solve_s_max"] for s in sw],
            out_dir / "solve_time_by_size.png").name)

    sizes = [n for n in SIZE_SCENARIOS if n in names]
    lookup = {(s["scenario"], s["method"]): s for s in summary}
    conflicts = {m: [lookup[(n, m)].get("same_paper_pairs_mean") or 0 for n in sizes] for m in METHODS}
    files.append(plots.grouped_columns(
        [f"{spec_by_name(n).candidates:,}" for n in sizes], conflicts,
        "Same-paper neighbour pairs", "Pairs of neighbours writing the same paper, by session size (lower is better)",
        "Neighbour pairs", out_dir / "conflicts_by_method.png").name)

    typical = {m: lookup[(TYPICAL, m)] for m in METHODS if (TYPICAL, m) in lookup}
    if typical:
        mix = {m: 100 * (s.get("same_department_pairs_mean") or 0) / max(s.get("neighbour_pairs_mean") or 1, 1)
               for m, s in typical.items()}
        files.append(plots.method_bars(
            mix, "Neighbours from the same department", f"Share of all neighbour pairs, {spec_by_name(TYPICAL).candidates} candidates (lower is better)",
            "Same-department pairs (%)", out_dir / "department_mix_by_method.png", "{:.1f}%").name)

    if predictability:
        files.append(plots.method_bars(
            {m: v["abs_roll_seat_correlation"] for m, v in predictability.items()},
            "Can the seat be guessed from the roll number?", "Absolute rank correlation between roll order and seat order (0 = unpredictable)",
            "|Spearman correlation|", out_dir / "roll_seat_correlation.png").name)
        files.append(plots.method_bars(
            {m: v["neighbour_overlap"] for m, v in predictability.items() if v["neighbour_overlap"] is not None},
            "Do the same people sit together again?", "Share of neighbour pairs repeated between two plans made with different seeds",
            "Repeated neighbour pairs (share)", out_dir / "neighbour_overlap.png").name)

    per_hall = next((r["_per_hall"] for r in df.to_dict("records") if isinstance(r.get("_per_hall"), list)), [])
    if per_hall:
        files.append(plots.hall_utilisation([h["hall"] for h in per_hall], [100 * h["utilisation"] for h in per_hall],
                                            out_dir / "hall_utilisation.png").name)
    return files


def next_run_dir() -> Path:
    base = ROOT / "experiments" / f"engine-benchmark-{datetime.now():%Y%m%d}"
    out, n = base, 2
    while out.exists():
        out, n = base.with_name(f"{base.name}-{n}"), n + 1
    out.mkdir(parents=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the SeatWise seating engine.")
    parser.add_argument("--quick", action="store_true", help="small scenarios, one seed, no tuning")
    parser.add_argument("--no-tune", action="store_true", help="skip the per-hall budget tuning")
    args = parser.parse_args()

    out_dir = next_run_dir()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(out_dir / "benchmark.log", encoding="utf-8")])
    import ortools

    names = ["xs-150", "s-300", "m-600"] if args.quick else [s.name for s in SCENARIOS]
    seeds = SEEDS[:1] if args.quick else SEEDS
    log.info("SeatWise engine %s, OR-Tools %s, %s CPU threads", ENGINE_VERSION, ortools.__version__, os.cpu_count())

    tuning = None if (args.quick or args.no_tune) else tune(out_dir)
    budget = tuning["chosen_budget"] if tuning else None

    scenarios = [build(spec_by_name(n)) for n in names]
    rows = [run_once(sc, m, seed, budget if m == "SeatWise" else None)
            for sc in scenarios for m in METHODS for seed in seeds]
    df = pd.DataFrame(rows)
    df.drop(columns=["_per_hall"], errors="ignore").to_csv(out_dir / "results.csv", index=False)
    summary = summarise(df)

    typical = next((sc for sc in scenarios if sc.spec.name == TYPICAL), None)
    predictability = {}
    if typical:
        log.info("Measuring predictability on %s over %s seeds", TYPICAL, len(PREDICTABILITY_SEEDS))
        for method, fn in METHODS.items():
            runner = (lambda c, h, r, s, fn=fn: fn(c, h, r, s, budget)) if method == "SeatWise" else fn
            predictability[method] = evaluate_method(typical, runner, PREDICTABILITY_SEEDS)
            log.info("%-14s %s", method, predictability[method])

    plot_files = make_plots(df, summary, predictability, out_dir, names)

    lookup = {(s["scenario"], s["method"]): s for s in summary}
    headline = {}
    if (TYPICAL, "SeatWise") in lookup:
        sw, seq = lookup[(TYPICAL, "SeatWise")], lookup[(TYPICAL, "Sequential")]
        headline = {
            "scenario": TYPICAL,
            "candidates": spec_by_name(TYPICAL).candidates,
            "solve_s_mean": sw["solve_s_mean"],
            "hard_rules_satisfied_rate": sw["hard_rules_satisfied_rate"],
            "same_paper_pairs": sw.get("same_paper_pairs_mean"),
            "conflicts_avoided_vs_sequential": (seq.get("same_paper_pairs_mean") or 0) - (sw.get("same_paper_pairs_mean") or 0),
            "abs_roll_seat_correlation": predictability.get("SeatWise", {}).get("abs_roll_seat_correlation"),
            "neighbour_overlap": predictability.get("SeatWise", {}).get("neighbour_overlap"),
        }
    all_sw = [s for s in summary if s["method"] == "SeatWise"]
    headline["all_scenarios_solved"] = all(s["solved_rate"] == 1.0 for s in all_sw)
    headline["all_hard_rules_satisfied"] = all(s["hard_rules_satisfied_rate"] == 1.0 for s in all_sw)
    headline["max_solve_s"] = max((s["solve_s_max"] for s in all_sw), default=None)

    run_date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metrics = {
        "run": out_dir.name,
        "run_date": run_date,
        "kind": "optimisation engine benchmark (no model training)",
        "engine_version": ENGINE_VERSION,
        "ortools_version": ortools.__version__,
        "machine": {"platform": platform.platform(), "processor": platform.processor(),
                    "cpu_threads": os.cpu_count(), "python": platform.python_version()},
        "dataset": {
            "type": "synthetic exam sessions from the seeded generator ml/scenarios.py",
            "split": "not applicable - nothing is trained; every scenario is an evaluation case",
            "scenarios": [describe(sc) for sc in scenarios],
            "seeds": seeds,
            "predictability_seeds": PREDICTABILITY_SEEDS if typical else [],
        },
        "per_hall_budget": budget,
        "headline": headline,
        "summary": summary,
        "predictability": predictability,
        "tuning": tuning,
        "plots": plot_files + (["budget_tuning.png"] if tuning else []),
        "quick": args.quick,
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    log.info("Wrote %s", (out_dir / "metrics.json").relative_to(ROOT).as_posix())

    if tuning:
        profile = {
            "engine_version": ENGINE_VERSION,
            "ortools_version": ortools.__version__,
            "hall_budget": budget,
            "threads": "auto",
            "tuned_at": run_date,
            "tuned_on": TUNING_SCENARIOS,
            "experiment": out_dir.name,
        }
        profile_path = ROOT / "models" / "engine_profile.json"
        profile_path.parent.mkdir(exist_ok=True)
        profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        log.info("Wrote %s", profile_path.relative_to(ROOT).as_posix())

    if not headline["all_hard_rules_satisfied"] or not headline["all_scenarios_solved"]:
        raise SystemExit("The engine missed a hard rule or a scenario - see benchmark.log.")
    log.info("Headline: %s", headline)


if __name__ == "__main__":
    main()
