"""Thin FastAPI layer over the existing `hublocator` package, used by the React frontend.

It only imports and exposes the functions the Flask app (hublocator/webapp.py) already uses;
no forecasting or optimisation logic lives here. The four original JSON endpoints
(/api/forecast, /api/optimize, /api/compare, /api/rolling) keep their response shapes.

    cd 8.ProjectCode
    python -m uvicorn backend.main:app --port 8104
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hublocator import __version__, config  # noqa: E402
from hublocator.baselines import load_comparison, run_comparison  # noqa: E402
from hublocator.data import dataset_summary, load_dataset  # noqa: E402
from hublocator.forecast import (forecast_for_period, forecast_next_period, load_forecast_metrics,  # noqa: E402
                                 load_forecaster, train_forecaster)
from hublocator.matheuristic import solve_matheuristic  # noqa: E402
from hublocator.model import HAS_PULP, Instance, evaluate_solution, solve_exact  # noqa: E402
from hublocator.rolling import load_rolling, load_scalability, rolling_reoptimisation, scalability_benchmark  # noqa: E402

app = FastAPI(title="HubOptima API", version=__version__,
              description="JSON API over the HubLocator predict-then-optimise pipeline.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5104", "http://127.0.0.1:5104"],
                   allow_methods=["*"], allow_headers=["*"])

regions, demand = load_dataset()
names = dict(zip(regions.region_id, regions.city))
periods_hist = sorted(demand.period.unique())
next_period = str(np.datetime64(periods_hist[-1] + "-01", "M") + 1)
jobs = {k: {"running": False, "kind": None, "started_at": None, "finished_at": None, "error": None}
        for k in ("compare", "rolling", "train")}
lock = threading.Lock()


def clean(o):
    """Make numpy scalars/arrays JSON-serialisable."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None   # JSON has no inf/nan
    return o


def ok(payload, status: int = 200):
    return JSONResponse(clean(payload), status_code=status)


def demand_vectors(period: str):
    """(forecast, realized or None, hist_avg) for a planning period - same as the Flask app."""
    if period == next_period:
        fc = forecast_next_period(regions, demand)
        real = None
        hist = demand.groupby("region_id")["orders"].mean()
    else:
        fc = forecast_for_period(regions, demand, period)
        real = demand[demand.period == period].set_index("region_id").loc[regions.region_id, "orders"].to_numpy(float)
        hist = demand[demand.period < period].groupby("region_id")["orders"].mean()
    fc = fc.set_index("region_id").loc[regions.region_id, "forecast"].to_numpy(float)
    return fc, real, hist.loc[regions.region_id].to_numpy(float)


def start_job(name: str, kind: str, fn) -> bool:
    with lock:
        if jobs[name]["running"]:
            return False
        jobs[name].update(running=True, kind=kind, started_at=time.time(), finished_at=None, error=None)

    def run():
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            jobs[name]["error"] = str(exc)
        finally:
            jobs[name].update(running=False, finished_at=time.time())
    threading.Thread(target=run, daemon=True).start()
    return True


# ------------------------------------------------------------------ read-only
@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "solver": "CBC via PuLP" if HAS_PULP else "greedy fallback",
            "has_pulp": HAS_PULP, "forecaster_trained": config.FORECAST_MODEL.exists()}


@app.get("/api/summary")
def summary():
    ds = dataset_summary(regions, demand)
    fm, cmp, ro, scal = load_forecast_metrics(), load_comparison(), load_rolling(), load_scalability()
    keep = ("label", "hub_cities", "total_cost", "cost_vs_proposed_pct", "avg_delivery_hours",
            "fulfilment_rate", "reliability_sla", "seconds")
    return ok({
        "dataset": {**ds, "top_regions": [{"region_id": k, "city": names[k], "avg_orders": v}
                                          for k, v in ds["top_regions"].items()]},
        "has_pulp": HAS_PULP,
        "forecaster": {"trained": bool(fm), "trained_at": fm.get("trained_at"),
                       "random_forest": fm.get("random_forest")},
        "comparison": {"period_params": cmp.get("params"), "methods": {k: {f: m.get(f) for f in keep}
                                                                       for k, m in cmp.get("methods", {}).items()}}
        if cmp else None,
        "rolling": {"months": len(ro["periods"]), "adaptive_avg": ro["adaptive_avg"], "static_avg": ro["static_avg"],
                    "hub_changes": ro["hub_changes"]} if ro else None,
        "scalability_runs": len(scal),
    })


@app.get("/api/regions")
def get_regions():
    cols = [c for c in ("region_id", "city", "state", "lat", "lon", "population", "tier", "parent") if c in regions]
    avg = demand.groupby("region_id")["orders"].mean().round(0)
    rows = regions[cols].to_dict("records")
    for r in rows:
        r["avg_orders"] = int(avg.get(r["region_id"], 0))
    return ok({"regions": rows})


@app.get("/api/options")
def options():
    return ok({"next_period": next_period, "plan_periods": [next_period] + periods_hist[::-1][:18],
               "eval_periods": periods_hist[::-1][:18],
               "default_eval_period": periods_hist[-3] if len(periods_hist) > 3 else periods_hist[-1],
               "defaults": config.DEFAULTS, "has_pulp": HAS_PULP})


@app.get("/api/forecast")
def api_forecast():
    f = forecast_next_period(regions, demand)
    return ok({"period": f.period[0], "total": int(f.forecast.sum()), "regions": f.to_dict("records"),
               "metrics": load_forecast_metrics().get("random_forest")})


@app.get("/api/forecast/metrics")
def forecast_metrics():
    fm = load_forecast_metrics()
    if fm:
        fm["last_period_detail"] = [{**r, "city": names.get(r["region_id"], r["region_id"])}
                                    for r in fm["last_period_detail"]]
    return ok(fm)


@app.get("/api/compare")
def api_compare():
    return ok(load_comparison())


@app.get("/api/scalability")
def api_scalability():
    return ok(load_scalability())


@app.get("/api/rolling")
def api_rolling():
    return ok(load_rolling())


@app.get("/api/jobs")
def api_jobs():
    return jobs


# ------------------------------------------------------------------ actions
@app.post("/api/train")
def api_train():
    if jobs["train"]["running"]:
        return ok({"error": "Training is already running."}, 409)
    jobs["train"].update(running=True, kind="train", started_at=time.time(), error=None)
    try:
        res = train_forecaster(regions, demand, verbose=False)
    except Exception as exc:  # noqa: BLE001
        jobs["train"]["error"] = str(exc)
        return ok({"error": str(exc)}, 500)
    finally:
        jobs["train"].update(running=False, finished_at=time.time())
    return ok({"message": "Forecaster retrained.", "random_forest": res["random_forest"],
               "trained_at": res["trained_at"], "train_seconds": res["train_seconds"]})


class OptimizeBody(BaseModel):
    period: str | None = None
    method: str = Field("matheuristic", pattern="^(matheuristic|exact)$")
    n_hubs: int = Field(config.DEFAULTS["n_hubs"], ge=1, le=20)
    capacity_factor: float = Field(config.DEFAULTS["capacity_factor"], ge=1)
    transport_rate: float = Field(config.DEFAULTS["transport_rate"], ge=0)
    fixed_cost_per_hub: float = Field(config.DEFAULTS["fixed_cost_per_hub"], ge=0)
    time_penalty: float = Field(config.DEFAULTS["time_penalty"], ge=0)
    truck_speed_kmph: float = Field(config.DEFAULTS["truck_speed_kmph"], gt=0)
    hub_handling_hours: float = Field(config.DEFAULTS["hub_handling_hours"], ge=0)
    sla_hours: float = Field(config.DEFAULTS["sla_hours"], gt=0)
    sla_hard: bool = config.DEFAULTS["sla_hard"]
    time_limit: int = Field(config.DEFAULTS["time_limit"], ge=2, le=300)


@app.post("/api/optimize")
def api_optimize(body: OptimizeBody):
    f = body.model_dump()
    f["period"] = f["period"] or next_period
    if f["period"] != next_period and f["period"] not in periods_hist[3:]:
        return ok({"error": f"Unknown planning month {f['period']}."}, 400)
    try:
        fc, real, _ = demand_vectors(f["period"])
        inst = Instance.from_forecast(regions, fc, **{k: f[k] for k in config.DEFAULTS})
        sol = solve_exact(inst, time_limit=f["time_limit"]) if (f["method"] == "exact" and HAS_PULP) \
            else solve_matheuristic(inst)
        if sol.get("assign") is None or not np.isfinite(sol.get("objective", 0)):
            return ok({"error": "No feasible solution (try more hubs, a larger capacity factor or a soft SLA)."})
        kpi = evaluate_solution(inst, sol["hubs"], sol["assign"], real)
    except Exception as exc:  # noqa: BLE001
        return ok({"error": str(exc)}, 400)
    sol_public = {k: v for k, v in sol.items() if k != "assign"}
    sol_public["hubs"] = [int(h) for h in sol["hubs"]]
    return ok({"sol": sol_public, "kpi": kpi, "realized": real is not None, "period": f["period"],
               "demand_used": (real if real is not None else fc).round(0)})


class CompareBody(BaseModel):
    period: str | None = None
    exact_limit: float = Field(30, ge=5, le=300)
    scalability: bool = False


@app.post("/api/compare/run")
def compare_run(body: CompareBody):
    sel = body.period or (periods_hist[-3] if len(periods_hist) > 3 else periods_hist[-1])
    if sel not in periods_hist[3:]:
        return ok({"error": f"Unknown evaluation month {sel}."}, 400)

    def job():
        fc, real, hist = demand_vectors(sel)
        if body.scalability:
            scalability_benchmark(regions, fc, factors=(1, 2, 3), exact_time_limit=body.exact_limit, verbose=False)
        else:
            run_comparison(regions, fc, real, hist, exact_time_limit=body.exact_limit, verbose=False)
    kind = "scalability" if body.scalability else "comparison"
    if not start_job("compare", kind, job):
        return ok({"error": "A comparison job is already running."}, 409)
    return ok({"started": kind, "period": sel})


class RollingBody(BaseModel):
    n_months: int = Field(6, ge=2, le=12)


@app.post("/api/rolling/run")
def rolling_run(body: RollingBody):
    if not start_job("rolling", "rolling", lambda: rolling_reoptimisation(regions, demand, n_months=body.n_months,
                                                                          verbose=False)):
        return ok({"error": "A rolling job is already running."}, 409)
    return ok({"started": "rolling", "n_months": body.n_months})


if load_forecaster() is None:   # same behaviour as the CLI: the forecast pages need a trained model
    train_forecaster(regions, demand, verbose=False)
