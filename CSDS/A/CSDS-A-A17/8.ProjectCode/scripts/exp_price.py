"""Price-model experiments: shipped GBR, baselines, time-based holdout, noise floor, band coverage, forecast behaviour.

    venv\\Scripts\\python scripts/exp_price.py          -> experiments/price/metrics.json
"""
from __future__ import annotations

import time
from datetime import date

import numpy as np
import pandas as pd

from exp_common import save

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from app.ml.price.features import CROPS, FEATURE_COLUMNS, GRADES, REGIONS, true_price
from app.ml.price.generate_dataset import generate


def mape(y, p):
    return float(np.mean(np.abs(y - p) / y))


def metrics(y, p):
    return {"mae": float(mean_absolute_error(y, p)), "rmse": float(np.sqrt(mean_squared_error(y, p))), "r2": float(r2_score(y, p)), "mape": mape(y, p)}


def gbr(seed=42):
    return GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=seed)


def q(alpha, seed=42):
    return GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.06, loss="quantile", alpha=alpha, random_state=seed)


def main():
    t0 = time.time()
    df = generate()
    X = df[FEATURE_COLUMNS].values
    y = df["price"].values
    out = {"dataset": {
        "rows": int(len(df)), "crops": CROPS, "regions": len(REGIONS), "grades": GRADES, "feature_columns": len(FEATURE_COLUMNS),
        "date_from": df["date"].min(), "date_to": df["date"].max(), "sampling": "every 3rd day, 8 crops x 8 regions",
        "price_min": float(y.min()), "price_max": float(y.max()), "price_mean": float(y.mean()),
        "source": "synthetic: price = base x grade premium x region x demand/supply x season x weather x freshness x fuel^0.15 x trend, plus N(0, 3.5%) noise (features.py::true_price)",
        "generator_noise_sigma": 0.035,
    }}

    # ---- shipped split (random 85/15, random_state=42)
    Xtr, Xte, ytr, yte, dtr, dte = train_test_split(X, y, df.index.values, test_size=0.15, random_state=42)
    point = gbr().fit(Xtr, ytr)
    pred = point.predict(Xte)
    lo = q(0.15).fit(Xtr, ytr).predict(Xte)
    hi = q(0.85).fit(Xtr, ytr).predict(Xte)
    m = metrics(yte, pred)
    inside = (yte >= np.minimum(lo, hi)) & (yte <= np.maximum(lo, hi))
    out["shipped_gbr"] = {"split": "85/15 random, random_state=42", "train_rows": int(len(Xtr)), "test_rows": int(len(Xte)), **m,
                          "hyperparameters": {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.06},
                          "band_nominal_coverage": 0.70, "band_empirical_coverage": float(inside.mean()),
                          "band_mean_width": float(np.mean(np.abs(hi - lo))), "band_width_pct_of_price": float(np.mean(np.abs(hi - lo) / yte)),
                          "band_crossing_rows": int((lo > hi).sum())}

    # per crop
    test = df.loc[dte].copy()
    test["pred"] = pred
    per = {}
    for c in CROPS:
        t = test[test["crop_type"] == c]
        per[c] = {"rows": int(len(t)), "mae": float(mean_absolute_error(t["price"], t["pred"])), "mape": mape(t["price"].values, t["pred"].values)}
    out["per_crop"] = per
    per_g = {}
    for g in GRADES:
        t = test[test["grade"] == g]
        per_g[g] = {"rows": int(len(t)), "mae": float(mean_absolute_error(t["price"], t["pred"])), "mape": mape(t["price"].values, t["pred"].values)}
    out["per_grade"] = per_g

    # ---- noise floor: the noise-free generating function against the noisy observation / against the model
    truth = np.array([true_price(r.crop_type, r._asdict()) for r in df.loc[dte].itertuples()])
    out["noise_floor"] = {
        "generating_function_vs_observed": metrics(yte, truth),
        "model_vs_noise_free_truth": metrics(truth, pred),
        "note": "the observed price equals the noise-free formula x (1 + N(0, 0.035)); no model can beat the first line on this data",
    }

    # ---- baselines (same split)
    cropcol = df["crop_type"].values
    crop_mean = {c: ytr[(cropcol[dtr] == c)].mean() for c in CROPS}
    base_pred = np.array([crop_mean[c] for c in cropcol[dte]])
    cg = (df["crop_type"] + "|" + df["grade"]).values
    cg_mean = {k: ytr[cg[dtr] == k].mean() for k in set(cg)}
    cg_pred = np.array([cg_mean[k] for k in cg[dte]])
    lin = LinearRegression().fit(Xtr, ytr)
    rfm = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1).fit(Xtr, ytr)
    out["baselines"] = {
        "crop_mean": metrics(yte, base_pred),
        "crop_x_grade_mean": metrics(yte, cg_pred),
        "linear_regression": metrics(yte, lin.predict(Xte)),
        "random_forest_200": metrics(yte, rfm.predict(Xte)),
        "gradient_boosting_shipped": m,
    }

    # ---- time-based holdout: train 2022-2023, test 2024 (+ final partial days)
    dates = pd.to_datetime(df["date"])
    tr_mask = (dates < "2024-01-01").values
    te_mask = ~tr_mask
    pt = gbr().fit(X[tr_mask], y[tr_mask])
    out["time_holdout"] = {"train_rows": int(tr_mask.sum()), "test_rows": int(te_mask.sum()), "train_period": "2022-01-01 to 2023-12-31",
                           "test_period": "2024-01-01 to " + df["date"].max(), **metrics(y[te_mask], pt.predict(X[te_mask])),
                           "note": "year_trend in the generator is (year-2023)*0.03; 2024 values of that feature lie outside the 2022-2023 training range"}

    # ---- seeds
    rows = []
    for s in range(5):
        a, b = train_test_split(np.arange(len(df)), test_size=0.15, random_state=s)
        mm = gbr(s).fit(X[a], y[a])
        r = metrics(y[b], mm.predict(X[b]))
        rows.append({"seed": s, **r})
    out["seed_study"] = {"runs": rows, "mae_mean": float(np.mean([r["mae"] for r in rows])), "mae_std": float(np.std([r["mae"] for r in rows], ddof=1)),
                         "r2_mean": float(np.mean([r["r2"] for r in rows])), "r2_std": float(np.std([r["r2"] for r in rows], ddof=1)),
                         "mape_mean": float(np.mean([r["mape"] for r in rows]))}

    # ---- feature importance (grouped as the admin panel groups them)
    from app.ml.price.infer import readable_label
    grouped = {}
    for c, v in zip(FEATURE_COLUMNS, point.feature_importances_):
        grouped[readable_label(c)] = grouped.get(readable_label(c), 0.0) + float(v)
    out["feature_importance_grouped"] = [{"feature": k, "importance": v} for k, v in sorted(grouped.items(), key=lambda kv: -kv[1])]

    # ---- shipped artefact agrees
    try:
        from app.ml.price.train_model import train
        art = train()
        out["train_model_py"] = {"test_mae": float(art["test_mae"]), "test_r2": float(art["test_r2"]),
                                 "matches_replica": abs(art["test_mae"] - m["mae"]) < 1e-6}
    except Exception as e:  # pragma: no cover
        out["train_model_py"] = {"error": str(e)}

    # ---- forecast behaviour of the served predict_price() over every crop/region/grade
    from app.ml.price.infer import predict_price
    combos = []
    lat = []
    for c in CROPS:
        for r in REGIONS:
            for g in GRADES:
                t1 = time.perf_counter()
                res = predict_price(c, r, g)
                lat.append(time.perf_counter() - t1)
                f = np.array([res["forecast"][str(k)] for k in range(31)])
                combos.append({"crop": c, "region": r, "grade": g, "current": res["current_price"], "low": res["confidence_low"], "high": res["confidence_high"],
                               "best_day": res["best_sell_day"], "gain_pct": float((f[:15].max() / f[0] - 1) * 100), "range_pct_30d": float((f.max() - f.min()) / f.mean() * 100),
                               "day0_vs_current_pct": float((f[0] / res["current_price"] - 1) * 100)})
    cb = pd.DataFrame(combos)
    out["served_forecast"] = {
        "combinations": int(len(cb)),
        "best_sell_day_zero_share": float((cb["best_day"] == 0).mean()),
        "best_sell_day_mean": float(cb["best_day"].mean()),
        "best_sell_day_hist": {str(k): int(v) for k, v in cb["best_day"].value_counts().sort_index().items()},
        "mean_gain_pct_if_waiting_to_best_day": float(cb["gain_pct"].mean()), "median_gain_pct": float(cb["gain_pct"].median()), "max_gain_pct": float(cb["gain_pct"].max()),
        "mean_30d_range_pct": float(cb["range_pct_30d"].mean()),
        "price_by_grade_mean": {g: float(cb[cb.grade == g]["current"].mean()) for g in GRADES},
        "price_by_crop_mean": {c: float(cb[cb.crop == c]["current"].mean()) for c in CROPS},
        "latency_ms_median": float(np.median(lat) * 1000), "latency_ms_p95": float(np.percentile(lat, 95) * 1000), "latency_ms_max": float(max(lat) * 1000),
        "note": "market context (rain, temperature, demand, supply, fuel) in the forecast is a deterministic hash of crop/region/date, not an external feed",
    }
    # grade ordering sanity (A > B > C > Reject within every crop/region)
    ok = 0
    tot = 0
    for (c, r), g in cb.groupby(["crop", "region"]):
        p = dict(zip(g.grade, g.current))
        tot += 1
        ok += int(p["A"] > p["B"] > p["C"] > p["Reject"])
    out["served_forecast"]["grade_price_order_holds"] = {"ok": ok, "of": tot}

    out["computed_on"] = date.today().isoformat()
    out["runtime_seconds"] = round(time.time() - t0, 1)
    save("price", out)
    print("MAE", m["mae"], "R2", m["r2"], "MAPE", m["mape"])


if __name__ == "__main__":
    main()
