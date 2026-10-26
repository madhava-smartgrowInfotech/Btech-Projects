"""Delivery-scoring sensitivity and IoT-simulator behaviour.

    venv\\Scripts\\python scripts/exp_delivery_iot.py   -> experiments/delivery/metrics.json, experiments/iot/metrics.json
"""
from __future__ import annotations

import os
import time

import numpy as np

os.environ.setdefault("DATABASE_URL", "sqlite:///C:/cs17/exp_delivery.db")

from exp_common import save  # noqa: E402

from scipy.stats import spearmanr  # noqa: E402


def delivery():
    from app.core.database import Base, SessionLocal, engine
    from app import models  # noqa: F401
    from app.ml.delivery import recommend as R
    from app.ml.price.features import CROPS, GRADES, REGIONS
    from app.ml.price.infer import predict_price
    from app.models.market import Town
    from app.models.user import User

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    import importlib.util
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(os.environ.get("CS_BACKEND", r"C:\cs17\app\backend")) / "scripts"))
    seed = importlib.import_module("seed_db")
    seed.seed()

    db = SessionLocal()
    towns = db.query(Town).count()
    buyers = db.query(User).filter(User.role == "buyer").all()
    wsum = sum(R.WEIGHTS.values())
    rng = np.random.default_rng(0)
    results = []
    t_lat = []
    price_cache = {}
    for crop in CROPS:
        for region in REGIONS:
            for grade in GRADES:
                t = time.perf_counter()
                rec = R.recommend(db, crop, region, grade, 500)
                t_lat.append(time.perf_counter() - t)
                top = rec["ranked_buyers"]["buyers"]
                # replicate the score with its components
                key = (crop, region, grade)
                base = rec["reference_price"]
                origin = R._town_for_region(db, region)
                comps = []
                for b in buyers:
                    bt = R._town_for_region(db, b.region) or origin
                    dist = R._haversine_km(origin.lat, origin.lon, bt.lat, bt.lon) if origin and bt else 50 + R._hash_unit(b.email, "dist") * 400
                    offered = base * (0.9 + R._hash_unit(b.email, crop) * 0.28)
                    price_n = min(offered / (base * 1.2), 1.0)
                    dist_n = max(0.0, 1 - min(dist, 500) / 500)
                    qfit = {"A": 1.0, "B": 0.85, "C": 0.6, "Reject": 0.1}[grade]
                    rel = min(b.reliability_score / 5.0, 1.0)
                    sp = min((dist / 380 + 0.5) / (5 if crop in R.PERISHABLE_CROPS else 21), 1.0)
                    comps.append([price_n, dist_n, qfit, rel, 1 - sp])
                comps = np.array(comps)
                w0 = np.array([R.WEIGHTS[k] for k in ["price", "distance", "quality_fit", "reliability", "spoilage_risk"]])
                s0 = comps @ w0 * 100
                names0 = [b.name for b in buyers]
                order0 = list(np.argsort(-s0))
                same_top = names0[order0[0]] == top[0]["buyer_name"]
                # perturb weights: multiply each by U(0.5,1.5), renormalise
                agree = []
                rho = []
                for _ in range(100):
                    w = w0 * rng.uniform(0.5, 1.5, 5)
                    w = w / w.sum() * w0.sum()
                    s = comps @ w
                    agree.append(int(np.argmax(s) == order0[0]))
                    rho.append(spearmanr(s0, s).statistic if len(set(s)) > 1 else 1.0)
                results.append({"crop": crop, "region": region, "grade": grade, "replica_top1_matches": bool(same_top), "top1_stability": float(np.mean(agree)),
                                "rank_corr": float(np.nanmean(rho)), "top_score": top[0]["match_score"], "top_buyer": top[0]["buyer_name"],
                                "top_distance_km": top[0]["distance_km"], "score_spread": float(s0.max() - s0.min()),
                                "term_std": (comps * w0).std(axis=0).tolist()})
    db.close()
    import pandas as pd
    r = pd.DataFrame(results)
    term_std = np.array(r["term_std"].tolist()).mean(axis=0)
    out = {
        "weights": R.WEIGHTS, "weights_sum": wsum, "towns": towns, "buyers": len(buyers), "combinations": int(len(r)),
        "replica_matches_served_top1": f"{int(r.replica_top1_matches.sum())}/{len(r)}",
        "weight_perturbation": {"trials_per_combination": 100, "multiplier_range": [0.5, 1.5],
                                "top1_unchanged_mean": float(r.top1_stability.mean()), "top1_unchanged_min": float(r.top1_stability.min()),
                                "rank_correlation_mean": float(r.rank_corr.mean())},
        "top_buyer_share": {k: float(v) for k, v in (r.top_buyer.value_counts(normalize=True)).items()},
        "mean_top_score": float(r.top_score.mean()), "mean_score_spread_top_to_bottom": float(r.score_spread.mean()),
        "term_variation_across_buyers": dict(zip(["price", "distance", "quality_fit", "reliability", "spoilage_risk"], [float(x) for x in term_std])),
        "latency_ms_median": float(np.median(t_lat) * 1000), "latency_ms_p95": float(np.percentile(t_lat, 95) * 1000),
        "note": "buyer offers are base price x a hash-derived factor in [0.90, 1.18]; they are simulated, not quotes from real buyers",
    }
    save("delivery", out)
    print(out["replica_matches_served_top1"], out["weight_perturbation"])


def iot():
    from app.ml.iot.simulate import SAFE_HUMIDITY_RANGE, SAFE_TEMP_RANGE, SHOCK_ALERT_THRESHOLD, ShipmentSensorState

    seeds = list(range(1, 51))
    steps = 1200
    kinds = {"temp_spike": 0, "humidity_spike": 0, "shock": 0}
    flagged_by_step = np.zeros(steps)
    first_flag = []
    inj_total = 0
    flagged_total = 0
    flagged_at_injection = 0
    flagged_not_injection = 0
    trough_run = []
    temps_end = []
    hum_end = []
    temp_min = 99
    temp_max = -99
    ever_flag_without_injection = 0
    pre_inj_flag = 0
    for sd in seeds:
        st = ShipmentSensorState(sd)
        run = 0
        longest = 0
        first = None
        any_before_first_inj = False
        injected_yet = False
        for i in range(steps):
            before = st._anomaly_countdown
            r = st.step()
            injected = st._anomaly_countdown > before
            if injected:
                inj_total += 1
                injected_yet = True
            if r["is_anomaly"]:
                flagged_by_step[i] += 1
                flagged_total += 1
                if injected:
                    flagged_at_injection += 1
                else:
                    flagged_not_injection += 1
                if first is None:
                    first = i
                if not injected_yet:
                    any_before_first_inj = True
                run += 1
                longest = max(longest, run)
            else:
                run = 0
            temp_min = min(temp_min, r["temperature_c"])
            temp_max = max(temp_max, r["temperature_c"])
        trough_run.append(longest)
        first_flag.append(first if first is not None else steps)
        temps_end.append(r["temperature_c"])
        hum_end.append(r["humidity_pct"])
        if any_before_first_inj:
            pre_inj_flag += 1
    frac = flagged_by_step / len(seeds)
    out = {
        "simulator": {"seeds": len(seeds), "steps_per_seed": steps, "seconds_per_step_in_app": 1.4,
                      "safe_temp_c": list(SAFE_TEMP_RANGE), "safe_humidity_pct": list(SAFE_HUMIDITY_RANGE), "shock_alert_g": SHOCK_ALERT_THRESHOLD,
                      "alarm_band_temp_c": [SAFE_TEMP_RANGE[0] - 1.5, SAFE_TEMP_RANGE[1] + 1.5],
                      "alarm_band_humidity_pct": [SAFE_HUMIDITY_RANGE[0] - 8, SAFE_HUMIDITY_RANGE[1] + 8]},
        "share_of_steps_flagged_overall": flagged_total / (len(seeds) * steps),
        "share_flagged_at_step": {str(k): float(frac[k]) for k in (0, 25, 50, 100, 200, 400, 600, 900, 1199)},
        "median_first_flag_step": float(np.median(first_flag)), "mean_first_flag_step": float(np.mean(first_flag)),
        "median_first_flag_minutes": float(np.median(first_flag) * 1.4 / 60),
        "injected_events_total": inj_total, "injected_events_per_1000_steps": inj_total / (len(seeds) * steps) * 1000,
        "flagged_steps_on_injection": flagged_at_injection, "flagged_steps_not_on_injection": flagged_not_injection,
        "share_of_flags_that_are_persistent_drift": flagged_not_injection / max(flagged_total, 1),
        "median_longest_alarm_run_steps": float(np.median(trough_run)),
        "seeds_flagged_before_first_injection": pre_inj_flag,
        "temperature_range_seen_c": [temp_min, temp_max],
        "final_temperature_c_mean": float(np.mean(temps_end)), "final_humidity_pct_mean": float(np.mean(hum_end)),
        "note": "temperature and humidity are random walks without mean reversion, so a spike (or slow drift) leaves the reading outside the band and the alarm stays on",
    }
    save("iot", out)
    print({k: out[k] for k in ("share_of_steps_flagged_overall", "share_flagged_at_step", "median_first_flag_step")})


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "iot"):
        iot()
    if which in ("all", "delivery"):
        delivery()
