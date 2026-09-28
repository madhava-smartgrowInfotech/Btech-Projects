"""Evaluation of HospiSense on held-out data (Oct-Dec admissions, never seen in training).

1. Length of stay   - MAE / RMSE / R2 vs a mean baseline; long-stay accuracy / F1 / AUC; MAE per ward.
2. Census forecast  - rolling back-tests every 3 days: MAE by horizon vs persistence and a 28-day-mean
                      baseline, 90% band coverage, and ICU early-warning precision / recall.
3. Resource use     - for each back-test origin, the static allocation vs the optimiser's plan built from
                      the forecast, both scored against the census that actually happened over 7 days.
Output: experiments/eval/metrics.json
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import (EQUIPMENT, EXPERIMENTS_DIR, FACILITIES, LONG_STAY_DAYS, NURSE_RATIO, OPERATING_DAY,  # noqa: E402
                        SHIFTS, WARDS)
from app.services.engine import TRAIN_END_DAY, WARN_Z, Z90, get_engine, los_frame  # noqa: E402
from app.services.optimizer import apply_actions, optimize  # noqa: E402

HORIZON = 14
PLAN_DAYS = 7
ORIGINS = list(range(TRAIN_END_DAY + 18, OPERATING_DAY - HORIZON + 1, 3))  # no in-house patient from training


def eval_los(eng):
    te = eng.patients[eng.patients.admit_day >= TRAIN_END_DAY]
    X = los_frame(te)
    y = te.lengthofstay.values
    pred = eng.reg.predict(X).clip(1, None)
    prob = eng.clf.predict_proba(X)[:, 1]
    ylong = (y > LONG_STAY_DAYS).astype(int)
    tr_mean = eng.patients[eng.patients.admit_day < TRAIN_END_DAY].lengthofstay.mean()
    per_ward = {w: round(float(mean_absolute_error(y[te.ward.values == w], pred[te.ward.values == w])), 3) for w in WARDS}
    return {"test_patients": int(len(te)), "mae_days": float(mean_absolute_error(y, pred)),
            "rmse_days": float(np.sqrt(mean_squared_error(y, pred))), "r2": float(r2_score(y, pred)),
            "baseline_mean_mae_days": float(mean_absolute_error(y, np.full(len(y), tr_mean))),
            "within_1_day": float((np.abs(y - pred) <= 1).mean()),
            "long_stay_accuracy": float(accuracy_score(ylong, prob >= 0.5)),
            "long_stay_f1": float(f1_score(ylong, prob >= 0.5)), "long_stay_auc": float(roc_auc_score(ylong, prob)),
            "mae_by_ward": per_ward}


def actual_matrix(eng, days):
    return {d: eng.actual_census(d) for d in days}


def eval_forecast(eng, actual, forecasts):
    err = {h: {"model": [], "persistence": [], "mean_28d": []} for h in range(1, HORIZON + 1)}
    covered, total = 0, 0
    icu = {lvl: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for lvl in ("over_capacity", "early_warning")}
    cap = eng.config["capacity"]
    for o in ORIGINS:
        fc = forecasts[o]
        for (f, w), x in fc.items():
            hist = [actual[d][(f, w)] for d in range(o - 27, o + 1)]
            sd = np.sqrt(x["var"])
            for h in range(1, HORIZON + 1):
                a = actual[o + h][(f, w)]
                m = x["mean"][h - 1]
                err[h]["model"].append(abs(a - m))
                err[h]["persistence"].append(abs(a - x["current"]))
                err[h]["mean_28d"].append(abs(a - np.mean(hist)))
                covered += (m - Z90 * sd[h - 1]) <= a <= (m + Z90 * sd[h - 1])
                total += 1
            if w == "ICU":  # alert raised within 7 days vs ICU census actually above capacity within 7 days
                act_over = any(actual[o + h][(f, "ICU")] > cap[f]["ICU"] for h in range(1, PLAN_DAYS + 1))
                for lvl, curve in (("over_capacity", x["mean"]), ("early_warning", x["mean"] + WARN_Z * sd)):
                    pred_over = bool((curve[:PLAN_DAYS] > cap[f]["ICU"]).any())
                    cell = {(True, True): "tp", (True, False): "fp", (False, True): "fn", (False, False): "tn"}
                    icu[lvl][cell[(pred_over, act_over)]] += 1
    by_h = {h: {k: round(float(np.mean(v)), 3) for k, v in err[h].items()} for h in (1, 3, 7, 14)}
    overall = {k: float(np.mean([e for h in err for e in err[h][k]])) for k in ("model", "persistence", "mean_28d")}
    return {"origins": len(ORIGINS), "series": len(FACILITIES) * len(WARDS), "horizon_days": HORIZON,
            "mae_by_horizon": by_h, "mae_overall": overall,
            "improvement_vs_persistence": 1 - overall["model"] / overall["persistence"],
            "improvement_vs_mean_28d": 1 - overall["model"] / overall["mean_28d"],
            "band_90_coverage": covered / total,
            "icu_alerts": {lvl: {**c, "precision": c["tp"] / max(1, c["tp"] + c["fp"]),
                                 "recall": c["tp"] / max(1, c["tp"] + c["fn"])} for lvl, c in icu.items()}}


def score(load, cap, ros, inv, rates):
    beds = sum(max(0, load[f][w] - cap[f][w]) for f in FACILITIES for w in WARDS)
    short = idle = 0
    for f in FACILITIES:
        for w in WARDS:
            for s in SHIFTS:
                need = math.ceil(load[f][w] / NURSE_RATIO[w][s])
                short += max(0, need - ros[f][w][s])
                idle += max(0, ros[f][w][s] - need)
    equip = sum(max(0, math.ceil(sum(load[f][w] * rates[w][e] for w in WARDS) - 1e-9) - inv[f][e])
                for f in FACILITIES for e in EQUIPMENT)
    rostered = sum(ros[f][w][s] for f in FACILITIES for w in WARDS for s in SHIFTS)
    return np.array([beds, short, idle, equip, rostered])


def eval_resources(eng, actual, forecasts):
    c = eng.config
    rates = c["equipment_rates"]
    tot = {"static": np.zeros(5), "optimised": np.zeros(5)}
    solve = []
    for o in ORIGINS:
        fc = forecasts[o]
        demand = {f: {w: int(math.ceil(fc[(f, w)]["mean"][:PLAN_DAYS].max() - 1e-9)) for w in WARDS} for f in FACILITIES}
        t0 = time.time()
        plan = optimize(demand, c["capacity"], c["roster"], c["inventory"], rates)
        solve.append(time.time() - t0)
        cap, ros, inv, _ = apply_actions(plan["actions"], None, c["capacity"], c["roster"], c["inventory"])
        diversions = [a for a in plan["actions"] if a["type"] == "diversion"]
        for d in range(o + 1, o + PLAN_DAYS + 1):
            load = {f: {w: actual[d][(f, w)] for w in WARDS} for f in FACILITIES}
            tot["static"] += score(load, c["capacity"], c["roster"], c["inventory"], rates)
            for a in diversions:  # diverted admissions move with the patients that actually arrived
                q = min(a["quantity"], load[a["facility"]][a["ward"]])
                load[a["facility"]][a["ward"]] -= q
                load[a["to_facility"]][a["ward"]] += q
            tot["optimised"] += score(load, cap, ros, inv, rates)
    names = ["patient_days_without_bed", "nurse_shifts_short", "nurse_shifts_idle", "equipment_unit_days_short",
             "nurse_shifts_rostered"]
    out = {k: dict(zip(names, map(int, v))) for k, v in tot.items()}
    out["reduction"] = {n: round(1 - tot["optimised"][i] / tot["static"][i], 4) if tot["static"][i] else None
                        for i, n in enumerate(names[:4])}
    out["plans"] = len(ORIGINS)
    out["days_scored_per_plan"] = PLAN_DAYS
    out["mean_solve_seconds"] = round(float(np.mean(solve)), 3)
    return out


def main():
    t0 = time.time()
    eng = get_engine()
    days = range(ORIGINS[0] - 28, ORIGINS[-1] + HORIZON + 1)
    actual = actual_matrix(eng, days)
    forecasts = {o: eng.forecast_census(o, HORIZON) for o in ORIGINS}
    result = {"length_of_stay": eval_los(eng), "census_forecast": eval_forecast(eng, actual, forecasts),
              "resource_use": eval_resources(eng, actual, forecasts),
              "backtest_origin_days": [ORIGINS[0], ORIGINS[-1]]}
    result["eval_seconds"] = round(time.time() - t0, 1)
    out = EXPERIMENTS_DIR / "eval"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
