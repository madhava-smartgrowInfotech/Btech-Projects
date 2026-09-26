#!/usr/bin/env python3
"""HubLocator command-line entry point.

    python run.py data                     (re)generate the historical logistics dataset
    python run.py forecast                 train the Random Forest demand model
    python run.py optimize [--period M]    plan hubs for a month with the matheuristic
    python run.py compare  [--period M]    proposed vs traditional methods
    python run.py rolling  [--months N]    month-by-month re-optimisation vs static plan
    python run.py benchmark                scalability: exact MIP vs matheuristic
    python run.py serve    [--port N]      start the web interface
    python run.py all                      data -> forecast -> compare -> rolling
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hublocator import config  # noqa: E402
from hublocator.data import dataset_summary, generate_dataset, load_dataset, save_dataset  # noqa: E402


def _vectors(regions, demand, period):
    from hublocator.forecast import forecast_for_period, forecast_next_period
    periods = sorted(demand.period.unique())
    if period is None or period > periods[-1]:
        fc = forecast_next_period(regions, demand)
        real, hist = None, demand.groupby("region_id")["orders"].mean()
    else:
        fc = forecast_for_period(regions, demand, period)
        real = demand[demand.period == period].set_index("region_id").loc[regions.region_id, "orders"].to_numpy(float)
        hist = demand[demand.period < period].groupby("region_id")["orders"].mean()
    return (fc.set_index("region_id").loc[regions.region_id, "forecast"].to_numpy(float), real,
            hist.loc[regions.region_id].to_numpy(float), fc.period[0])


def cmd_data(a):
    regions, demand = generate_dataset(seed=a.seed)
    save_dataset(regions, demand)
    print(json.dumps({k: v for k, v in dataset_summary(regions, demand).items() if k != "monthly_total"}, indent=2))


def cmd_forecast(a):
    from hublocator.forecast import train_forecaster
    regions, demand = load_dataset()
    train_forecaster(regions, demand, test_months=a.test_months)


def cmd_optimize(a):
    from hublocator.matheuristic import solve_matheuristic
    from hublocator.model import Instance, evaluate_solution, solve_exact
    regions, demand = load_dataset()
    fc, real, _, period = _vectors(regions, demand, a.period)
    inst = Instance.from_forecast(regions, fc, n_hubs=a.hubs, capacity_factor=a.capacity, time_limit=a.time_limit)
    print(f"Planning {period}: forecast demand {int(fc.sum()):,} orders, p={a.hubs}")
    sol = solve_exact(inst, time_limit=a.time_limit) if a.exact else solve_matheuristic(inst, verbose=True)
    kpi = evaluate_solution(inst, sol["hubs"], sol["assign"], real)
    print(f"\nHubs: {', '.join(kpi['hub_cities'])}   ({sol['status']}, {sol['seconds']}s)")
    print(f"Operating cost  : {kpi['total_cost']:,.0f}  (fixed {kpi['fixed_cost']:,.0f}, transport {kpi['transport_cost']:,.0f}, time {kpi['time_cost']:,.0f})")
    print(f"Avg delivery    : {kpi['avg_delivery_hours']} h  (max {kpi['max_delivery_hours']} h)")
    print(f"Fulfilment      : {kpi['fulfilment_rate']*100:.1f}%   Reliability (SLA): {kpi['reliability_sla']*100:.1f}%"
          + ("   [scored on realised demand]" if real is not None else ""))
    print("Utilisation     : " + ", ".join(f"{regions.city[h]} {u*100:.0f}%" for h, u in kpi["utilisation"].items()))
    if a.json:
        print(json.dumps({k: v for k, v in kpi.items() if k != "assignment"}, indent=2))


def cmd_compare(a):
    from hublocator.baselines import run_comparison
    regions, demand = load_dataset()
    periods = sorted(demand.period.unique())
    period = a.period or periods[-3]
    fc, real, hist, _ = _vectors(regions, demand, period)
    if real is None:
        sys.exit("compare needs a historical month so results can be scored on realised demand")
    print(f"Evaluating {period}: forecast {int(fc.sum()):,}  realised {int(real.sum()):,}  hist-avg {int(hist.sum()):,}")
    s = run_comparison(regions, fc, real, hist, exact_time_limit=a.time_limit)
    print(f"\n{'method':<12}{'cost':>16}{'vs prop':>9}{'avg h':>7}{'fulfil':>8}{'reliab':>8}{'secs':>7}")
    for k, m in s["methods"].items():
        print(f"{k:<12}{m['total_cost']:>16,.0f}{m['cost_vs_proposed_pct']:>8.2f}%{m['avg_delivery_hours']:>7}"
              f"{m['fulfilment_rate']:>8.3f}{m['reliability_sla']:>8.3f}{m['seconds']:>7}")


def cmd_rolling(a):
    from hublocator.rolling import rolling_reoptimisation
    regions, demand = load_dataset()
    s = rolling_reoptimisation(regions, demand, n_months=a.months)
    print("\nadaptive avg:", s["adaptive_avg"])
    print("static   avg:", s["static_avg"])


def cmd_benchmark(a):
    from hublocator.rolling import scalability_benchmark
    regions, demand = load_dataset()
    fc, _, _, _ = _vectors(regions, demand, a.period)
    scalability_benchmark(regions, fc, factors=tuple(a.factors), exact_time_limit=a.time_limit, append=a.append)


def cmd_serve(a):
    from hublocator.webapp import create_app
    print(f"HubLocator web interface -> http://{a.host}:{a.port}")
    create_app().run(host=a.host, port=a.port, debug=a.debug, threaded=True)


def cmd_all(a):
    cmd_data(argparse.Namespace(seed=config.RANDOM_STATE))
    cmd_forecast(argparse.Namespace(test_months=6))
    cmd_compare(argparse.Namespace(period=None, time_limit=30))
    cmd_rolling(argparse.Namespace(months=6))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("data"); s.add_argument("--seed", type=int, default=config.RANDOM_STATE); s.set_defaults(fn=cmd_data)
    s = sub.add_parser("forecast"); s.add_argument("--test-months", type=int, default=6); s.set_defaults(fn=cmd_forecast)
    s = sub.add_parser("optimize"); s.add_argument("--period"); s.add_argument("--hubs", type=int, default=config.DEFAULTS["n_hubs"])
    s.add_argument("--capacity", type=float, default=config.DEFAULTS["capacity_factor"]); s.add_argument("--time-limit", type=float, default=20)
    s.add_argument("--exact", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_optimize)
    s = sub.add_parser("compare"); s.add_argument("--period"); s.add_argument("--time-limit", type=float, default=30); s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("rolling"); s.add_argument("--months", type=int, default=6); s.set_defaults(fn=cmd_rolling)
    s = sub.add_parser("benchmark"); s.add_argument("--period"); s.add_argument("--factors", type=int, nargs="+", default=[1, 2, 3])
    s.add_argument("--time-limit", type=float, default=40); s.add_argument("--append", action="store_true"); s.set_defaults(fn=cmd_benchmark)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=5000)
    s.add_argument("--debug", action="store_true"); s.set_defaults(fn=cmd_serve)
    sub.add_parser("all").set_defaults(fn=cmd_all)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
