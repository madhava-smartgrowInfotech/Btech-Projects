"""
run_experiments.py
-------------------
Measures TrendCast on the REAL H&M subset (data/real_hm, built by make_real_subset.py) using the
project's own `src/` functions, and writes every number to experiments/<name>/metrics.json.

    python scripts/run_experiments.py [--data data/real_hm] [--only forecasting,domain,explain,inventory,cold,recursive]

Experiments
  forecasting  moving average / naive / RF / LightGBM / XGBoost (5 seeds) / tuned XGBoost, chronological 80/20,
               feature-group ablation, rolling-origin backtest
  recursive    the app's recursive 7/14/30-day forecast, scored against held-out actuals (app-faithful and with the
               calendar features refreshed), vs flat baselines
  domain       the app's importance-weighted adaptation on 6 source->target pairs x 5 seeds, plus controls
               (target-only oracle, pooled source+target, shuffled weights, time-clean source)
  explain      gain importance vs exact TreeSHAP (xgboost pred_contribs) on the test set
  inventory    forecast error expressed as under-stock / over-stock units
  cold         unseen-article (cold start) forecast from attributes + calendar only, GroupKFold by article
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:  # LightGBM 4.7 crashes (access violation) on this machine if pandas/xgboost are imported first
    import lightgbm as lgb_lib
except ImportError:  # pragma: no cover
    lgb_lib = None
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import xgboost as xgb  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.ensemble import RandomForestRegressor  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402

from src import (  # noqa: E402
    baseline_models,
    demand_forecasting,
    domain_adaptation,
    evaluation,
    feature_engineering,
    preprocessing,
    xgboost_model,
)

OUT = ROOT / "experiments"
SEEDS = [42, 43, 44, 45, 46]
CALENDAR = ["year", "month", "day", "day_of_week", "week_of_year", "day_of_year", "quarter", "is_weekend",
            "is_month_start", "is_month_end", "month_sin", "month_cos", "dow_sin", "dow_cos"]
LAGS = ["lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
        "rolling_std_7", "rolling_std_28"]
ATTRS = ["product_type_name", "product_group_name", "colour_group_name", "department_name", "section_name",
         "garment_group_name"]


def save(name: str, obj: dict, tables: dict | None = None) -> None:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(obj, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    for fname, df in (tables or {}).items():
        df.to_csv(d / fname, index=False)
    print(f"[saved] experiments/{name}/metrics.json")


def met(y, p) -> dict:
    m = evaluation.evaluate_model(y, p)
    y = np.asarray(y, float)
    m["WAPE (%)"] = float(np.abs(y - np.asarray(p, float)).sum() / y.sum() * 100)
    return m


def agg(runs: list[dict]) -> dict:
    keys = [k for k in runs[0] if isinstance(runs[0][k], (int, float))]
    out = {}
    for k in keys:
        v = np.array([r[k] for r in runs], float)
        out[k] = {"mean": float(np.nanmean(v)), "std": float(np.nanstd(v, ddof=1)) if len(v) > 1 else 0.0,
                  "values": [float(x) for x in v]}
    return out


def load(data: Path):
    tx = pd.read_csv(data / "transactions_train.csv")
    ar = pd.read_csv(data / "articles.csv")
    raw_rows = len(tx)
    tx = preprocessing.clean_transactions(tx)
    ar = preprocessing.clean_articles(ar)
    merged = preprocessing.merge_datasets(tx, ar)
    daily = demand_forecasting.aggregate_daily_demand(merged)
    filled = demand_forecasting.fill_missing_dates_per_article(daily)
    ft, mappings = feature_engineering.build_feature_table(filled)
    info = {
        "raw_rows": raw_rows, "clean_rows": len(tx), "articles": int(tx.article_id.nunique()),
        "customers": int(tx.customer_id.nunique()), "date_min": str(tx.t_dat.min().date()), "date_max": str(tx.t_dat.max().date()),
        "daily_rows": len(daily), "feature_rows": len(ft), "feature_cols": len(feature_engineering.get_feature_columns(ft)),
        "zero_demand_share_pct": float((ft.demand == 0).mean() * 100),
        "channel_rows_raw": {str(k): int(v) for k, v in tx.groupby("sales_channel_id").size().items()},
    }
    return ft, mappings, daily, info


def fit(X, y, seed, w=None, **kw):
    p = {"random_state": seed}
    p.update(kw)
    return xgboost_model.train_xgboost(X, y, params=p, sample_weight=w)


# ---------------------------------------------------------------------------------------------------------------------
def exp_forecasting(ft, info):
    cols = feature_engineering.get_feature_columns(ft)
    train, test = baseline_models.chronological_split(ft, train_fraction=0.8)
    summ = baseline_models.split_summary(train, test)
    Xtr, ytr, Xte, yte = train[cols], train["demand"], test[cols], test["demand"]
    res: dict = {"split": {k: str(v) for k, v in summ.items()}, "n_features": len(cols), "models": {}}

    res["models"]["Moving average (7d)"] = met(yte, baseline_models.moving_average_forecast(train, test))
    res["models"]["Naive (lag 1)"] = met(yte, test["lag_1"])
    res["models"]["Seasonal naive (lag 7)"] = met(yte, test["lag_7"])
    res["models"]["Rolling mean 7 (shifted)"] = met(yte, test["rolling_mean_7"])
    t0 = time.time()
    rf = baseline_models.train_random_forest(Xtr, ytr)
    res["models"]["Random forest"] = met(yte, rf.predict(Xte))
    res["models"]["Random forest"]["fit_seconds"] = time.time() - t0
    # src.baseline_models.train_lightgbm passes pandas objects, which crash LightGBM 4.7 here (access violation);
    # same hyper-parameters, numpy inputs.
    if lgb_lib is not None:
        lgb = lgb_lib.LGBMRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, random_state=42, verbose=-1)
        lgb.fit(Xtr.values, ytr.values)
        res["models"]["LightGBM"] = met(yte, lgb.predict(Xte.values))

    runs, preds, fit_t = [], [], []
    for s in SEEDS:
        t0 = time.time()
        m = fit(Xtr, ytr, s)
        fit_t.append(time.time() - t0)
        p = m.predict(Xte)
        preds.append(p)
        runs.append(met(yte, p))
        if s == SEEDS[0]:
            first = m
    res["models"]["XGBoost (default, 5 seeds)"] = {k: v["mean"] for k, v in agg(runs).items()}
    res["xgboost_seed_stats"] = agg(runs)
    res["xgboost_fit_seconds_mean"] = float(np.mean(fit_t))
    res["xgboost_prediction_us_per_row"] = None
    t0 = time.time()
    first.predict(Xte)
    res["xgboost_prediction_us_per_row"] = (time.time() - t0) / len(Xte) * 1e6

    t0 = time.time()
    tuned, best = xgboost_model.tune_xgboost(Xtr, ytr, n_iter=10, cv_splits=3)
    res["models"]["XGBoost (tuned, 10 iters x 3 TS-CV)"] = met(yte, tuned.predict(Xte))
    res["tuned_best_params"] = {k: (v.item() if hasattr(v, "item") else v) for k, v in best.items()}
    res["tuning_seconds"] = time.time() - t0

    # feature-group ablation (XGBoost default, 3 seeds)
    groups = {
        "all features (as shipped)": cols,
        "no lag / rolling": [c for c in cols if c not in LAGS],
        "no price, no channel": [c for c in cols if c not in ("price", "sales_channel_id")],
        "no product attributes": [c for c in cols if c not in ATTRS],
        "calendar only": [c for c in cols if c in CALENDAR],
        "lag / rolling only": [c for c in cols if c in LAGS],
        "lag / rolling + price": [c for c in cols if c in LAGS or c == "price"],
    }
    ab = {}
    for name, cs in groups.items():
        r = [met(yte, fit(train[cs], ytr, s).predict(test[cs])) for s in SEEDS[:3]]
        ab[name] = {"n_features": len(cs), **{k: v["mean"] for k, v in agg(r).items()}}
    res["ablation"] = ab

    # rolling-origin backtest
    dates = np.sort(ft["t_dat"].unique())
    bt = []
    for lo, hi in ((0.60, 0.72), (0.70, 0.82), (0.80, 0.92)):
        d_lo, d_hi = dates[int(len(dates) * lo)], dates[min(int(len(dates) * hi), len(dates) - 1)]
        tr, te = ft[ft.t_dat < d_lo], ft[(ft.t_dat >= d_lo) & (ft.t_dat < d_hi)]
        m = fit(tr[cols], tr["demand"], 42)
        bt.append({"train_until": str(pd.Timestamp(d_lo).date()), "test_until": str(pd.Timestamp(d_hi).date()),
                   "train_rows": len(tr), "test_rows": len(te),
                   "xgboost": met(te["demand"], m.predict(te[cols])),
                   "moving_average": met(te["demand"], baseline_models.moving_average_forecast(tr, te)),
                   "seasonal_naive": met(te["demand"], te["lag_7"]),
                   "naive_lag1": met(te["demand"], te["lag_1"])})
    res["rolling_origin"] = bt

    # daily aggregate series for the chart
    mean_pred = np.mean(preds, axis=0)
    ser = test[["t_dat", "article_id", "demand"]].copy()
    ser["xgb"] = mean_pred
    ser["ma"] = baseline_models.moving_average_forecast(train, test)
    day = ser.groupby("t_dat")[["demand", "xgb", "ma"]].sum().reset_index()
    feat_imp = xgboost_model.get_feature_importance(first, cols, top_n=15)
    res["gain_importance_top15"] = [{"feature": f, "importance": float(i)} for f, i in feat_imp]
    res["test_daily_totals_error"] = {
        "xgb_daily_wape_pct": float(np.abs(day.demand - day.xgb).sum() / day.demand.sum() * 100),
        "ma_daily_wape_pct": float(np.abs(day.demand - day.ma).sum() / day.demand.sum() * 100),
    }
    pd.to_pickle({"test": test, "pred_xgb": mean_pred, "model": first, "cols": cols}, OUT / "_cache_forecasting.pkl")
    save("forecasting", res, {"test_daily_series.csv": day,
                              "test_predictions_sample.csv": ser.sample(3000, random_state=1)})


# ---------------------------------------------------------------------------------------------------------------------
def recursive_forecast(model, cols, hist: pd.DataFrame, horizon: int, fix_calendar: bool) -> np.ndarray:
    """Copy of the loop in backend/main.py::forecast; with fix_calendar=True the remaining calendar features are refreshed too."""
    last = hist.iloc[-1].copy()
    last_date = last["t_dat"]
    recent = hist["demand"].tolist()
    out = []
    for step in range(1, horizon + 1):
        d = last_date + pd.Timedelta(days=step)
        row = last.copy()
        row["t_dat"] = d
        row["year"], row["month"], row["day"] = d.year, d.month, d.day
        row["day_of_week"] = d.dayofweek
        row["is_weekend"] = int(d.dayofweek >= 5)
        row["month_sin"], row["month_cos"] = np.sin(2 * np.pi * d.month / 12), np.cos(2 * np.pi * d.month / 12)
        row["dow_sin"], row["dow_cos"] = np.sin(2 * np.pi * d.dayofweek / 7), np.cos(2 * np.pi * d.dayofweek / 7)
        if fix_calendar:
            row["week_of_year"] = int(d.isocalendar()[1])
            row["day_of_year"] = d.dayofyear
            row["quarter"] = d.quarter
            row["is_month_start"] = int(d.is_month_start)
            row["is_month_end"] = int(d.is_month_end)
        for lag in (1, 7, 14, 28):
            row[f"lag_{lag}"] = recent[-lag] if len(recent) >= lag else 0
        for w in (7, 14, 28):
            row[f"rolling_mean_{w}"] = np.mean(recent[-w:])
        for w in (7, 28):
            row[f"rolling_std_{w}"] = np.std(recent[-w:]) if len(recent) > 1 else 0
        pred = max(0.0, float(model.predict(pd.DataFrame([row[cols]]))[0]))
        out.append(pred)
        recent.append(pred)
    return np.array(out)


def exp_recursive(ft, info):
    cols = feature_engineering.get_feature_columns(ft)
    dates = np.sort(ft["t_dat"].unique())
    origin_idx = len(dates) - 31
    split = dates[origin_idx + 1]
    train = ft[ft.t_dat < split]
    model = fit(train[cols], train["demand"], 42)
    H = 30
    rows = {"xgb_app": [], "xgb_fixed": [], "flat_ma7": [], "repeat_last_week": []}
    act, hz = [], []
    for aid, g in ft.groupby("article_id"):
        hist = g[g.t_dat < split].sort_values("t_dat")
        fut = g[g.t_dat >= split].sort_values("t_dat").head(H)
        if len(hist) < 28 or len(fut) < 7:
            continue
        n = len(fut)
        pa = recursive_forecast(model, cols, hist, n, False)
        pf = recursive_forecast(model, cols, hist, n, True)
        last7 = hist["demand"].tail(7).values
        rows["xgb_app"].append(pa)
        rows["xgb_fixed"].append(pf)
        rows["flat_ma7"].append(np.full(n, last7.mean()))
        rows["repeat_last_week"].append(np.array([last7[i % 7] for i in range(n)]))
        act.append(fut["demand"].values)
        hz.append(np.arange(1, n + 1))
    act, hz = np.concatenate(act), np.concatenate(hz)
    res = {"origin": str(pd.Timestamp(split).date()), "articles_scored": len(rows["xgb_app"]),
           "horizon_days": H, "results": {}}
    for name, parts in rows.items():
        p = np.concatenate(parts)
        res["results"][name] = {}
        for lab, hmax in (("days 1-7", 7), ("days 1-14", 14), ("days 1-30", 30)):
            m = hz <= hmax
            res["results"][name][lab] = met(act[m], p[m])
        by = []
        for h0, h1 in ((1, 7), (8, 14), (15, 30)):
            m = (hz >= h0) & (hz <= h1)
            by.append({"band": f"{h0}-{h1}", "WAPE (%)": met(act[m], p[m])["WAPE (%)"], "rows": int(m.sum())})
        res["results"][name]["by_band"] = by
    save("recursive", res)


# ---------------------------------------------------------------------------------------------------------------------
_CLF_CACHE: dict = {}


def domain_run(ft, col, src, tgt, seed, cols, time_clean=False):
    """The same procedure as backend/main.py::run_domain, returning every intermediate we want to compare."""
    fcols = [c for c in cols if c != col]
    s_df, t_df = domain_adaptation.split_domains(ft, col, src, tgt)
    t_tr, t_te = baseline_models.chronological_split(t_df, train_fraction=0.5)
    test_start = t_te["t_dat"].min()
    if time_clean:
        s_df = s_df[s_df["t_dat"] < test_start]
    sX, sy = s_df[fcols], s_df["demand"]
    tX, ty = t_te[fcols], t_te["demand"]
    out = {}
    src_m = fit(sX, sy, seed)
    out["before"] = met(ty, src_m.predict(tX))
    key = (col, src, tgt, time_clean)
    if key not in _CLF_CACHE:  # the classifier and weights do not depend on the XGBoost seed
        t0 = time.time()
        clf, acc = domain_adaptation.train_domain_classifier(sX, t_df[fcols])
        _CLF_CACHE[key] = (acc, domain_adaptation.compute_instance_weights(clf, sX), time.time() - t0)
    acc, w, _ = _CLF_CACHE[key]
    out["adapted"] = met(ty, fit(sX, sy, seed, w).predict(tX))
    out["adapted_normalised"] = met(ty, fit(sX, sy, seed, w / w.mean()).predict(tX))  # same weights rescaled to mean 1
    rng = np.random.default_rng(seed)
    out["shuffled_weights"] = met(ty, fit(sX, sy, seed, rng.permutation(w)).predict(tX))
    out["target_only_oracle"] = met(ty, fit(t_tr[fcols], t_tr["demand"], seed).predict(tX))
    pool = pd.concat([sX, t_tr[fcols]])
    out["pooled_unweighted"] = met(ty, fit(pool, pd.concat([sy, t_tr["demand"]]), seed).predict(tX))
    diag = {"clf_accuracy": float(acc), "source_rows": len(s_df), "target_rows": len(t_df), "target_test_rows": len(t_te),
            "w_mean": float(w.mean()), "w_max": float(w.max()), "w_min": float(w.min()),
            "clipped_share_pct": float((w >= 20.0 - 1e-9).mean() * 100),
            "effective_sample_size": float(w.sum() ** 2 / (w ** 2).sum()),
            "ess_share_pct": float(w.sum() ** 2 / (w ** 2).sum() / len(w) * 100)}
    return out, diag


def exp_domain(ft, mappings, info):
    cols = feature_engineering.get_feature_columns(ft)
    code = lambda c, name: next(k for k, v in mappings[c].items() if v == name)  # noqa: E731
    pairs = [
        ("sales_channel_id", 2.0, 1.0, "Online -> Store (channel 2 -> 1)"),
        ("sales_channel_id", 1.0, 2.0, "Store -> Online (channel 1 -> 2)"),
        ("product_group_name", code("product_group_name", "Garment Upper body"), code("product_group_name", "Garment Lower body"),
         "Upper body -> Lower body"),
        ("product_group_name", code("product_group_name", "Garment Lower body"), code("product_group_name", "Garment Upper body"),
         "Lower body -> Upper body"),
        ("department_name", code("department_name", "Knitwear"), code("department_name", "Trouser"), "Knitwear -> Trouser"),
        ("department_name", code("department_name", "Jersey Basic"), code("department_name", "Blouse"), "Jersey Basic -> Blouse"),
    ]
    res = {"seeds": SEEDS, "pairs": []}
    for col, s, t, label in pairs:
        runs = {"app": [], "time_clean": []}
        diag = diag_tc = None
        for seed in SEEDS:
            r, diag = domain_run(ft, col, s, t, seed, cols)
            runs["app"].append(r)
            r2, diag_tc = domain_run(ft, col, s, t, seed, cols, time_clean=True)
            runs["time_clean"].append(r2)
        entry = {"label": label, "domain_col": col, "source": float(s), "target": float(t), "diagnostics": diag,
                 "diagnostics_time_clean": diag_tc}
        for proto in ("app", "time_clean"):
            entry[proto] = {}
            for variant in runs[proto][0]:
                entry[proto][variant] = agg([r[variant] for r in runs[proto]])
            b = np.array([r["before"]["RMSE"] for r in runs[proto]])
            a = np.array([r["adapted"]["RMSE"] for r in runs[proto]])
            sh = np.array([r["shuffled_weights"]["RMSE"] for r in runs[proto]])
            nrm = np.array([r["adapted_normalised"]["RMSE"] for r in runs[proto]])
            entry[proto]["normalised_improvement_pct_mean"] = float(np.mean((b - nrm) / b * 100))
            entry[proto]["rmse_improvement_pct_per_seed"] = [float(x) for x in (b - a) / b * 100]
            entry[proto]["rmse_improvement_pct_mean"] = float(np.mean((b - a) / b * 100))
            entry[proto]["shuffled_improvement_pct_mean"] = float(np.mean((b - sh) / b * 100))
            entry[proto]["adapted_beats_before_in_seeds"] = int((a < b).sum())
        res["pairs"].append(entry)
        e = entry["app"]
        print(f"[domain] {label:36s} before {e['before']['RMSE']['mean']:.3f} adapted {e['adapted']['RMSE']['mean']:.3f} "
              f"({e['rmse_improvement_pct_mean']:+.2f}%, normalised {e['normalised_improvement_pct_mean']:+.2f}%)  oracle {e['target_only_oracle']['RMSE']['mean']:.3f}  clf {diag['clf_accuracy']:.3f}")
    imp = [p["app"]["rmse_improvement_pct_mean"] for p in res["pairs"]]
    res["summary"] = {"pairs_where_adaptation_helped": int(sum(i > 0 for i in imp)), "pairs_total": len(imp),
                      "mean_rmse_improvement_pct": float(np.mean(imp)), "min": float(np.min(imp)), "max": float(np.max(imp)),
                      "time_clean_mean_rmse_improvement_pct": float(np.mean([p["time_clean"]["rmse_improvement_pct_mean"] for p in res["pairs"]])),
                      "normalised_mean_rmse_improvement_pct": float(np.mean([p["app"]["normalised_improvement_pct_mean"] for p in res["pairs"]])),
                      "normalised_time_clean_mean_rmse_improvement_pct": float(np.mean([p["time_clean"]["normalised_improvement_pct_mean"] for p in res["pairs"]]))}
    save("domain_adaptation", res)


# ---------------------------------------------------------------------------------------------------------------------
def exp_explain(ft, info):
    cols = feature_engineering.get_feature_columns(ft)
    train, test = baseline_models.chronological_split(ft, train_fraction=0.8)
    m = fit(train[cols], train["demand"], 42)
    contrib = m.get_booster().predict(xgb.DMatrix(test[cols]), pred_contribs=True)
    shap = np.abs(contrib[:, :-1]).mean(axis=0)
    gain = m.feature_importances_
    tab = pd.DataFrame({"feature": cols, "mean_abs_shap": shap, "gain_importance": gain}).sort_values("mean_abs_shap", ascending=False)
    rho = spearmanr(tab["mean_abs_shap"], tab["gain_importance"]).correlation
    recon = float(np.abs(contrib.sum(axis=1) - m.predict(test[cols])).max())
    res = {"top10_by_shap": tab.head(10).to_dict("records"), "spearman_rank_corr_shap_vs_gain": float(rho),
           "shap_additivity_max_abs_error": recon, "n_test_rows": len(test),
           "top3_share_of_total_abs_shap_pct": float(tab["mean_abs_shap"].head(3).sum() / tab["mean_abs_shap"].sum() * 100),
           "top3_by_gain": tab.sort_values("gain_importance", ascending=False).head(3)["feature"].tolist(),
           "note": "SHAP values come from XGBoost's built-in exact TreeSHAP (pred_contribs); the web app itself shows gain importance only."}
    contrib_df = pd.DataFrame(contrib[:, :-1], columns=cols)
    # dependence of the attribution on the weekday (sanity check of the calendar signal)
    dep = pd.DataFrame({"day_of_week": test["day_of_week"].values, "shap_dow": contrib_df["dow_sin"].values + contrib_df["dow_cos"].values + contrib_df["day_of_week"].values})
    res["weekday_mean_shap_calendar"] = dep.groupby("day_of_week")["shap_dow"].mean().round(4).to_dict()
    save("explainability", res, {"importance_table.csv": tab})


def exp_inventory(ft, info):
    cache = pd.read_pickle(OUT / "_cache_forecasting.pkl")
    test, pred = cache["test"], cache["pred_xgb"]
    ma = baseline_models.moving_average_forecast(*baseline_models.chronological_split(ft, train_fraction=0.8))
    y = test["demand"].values
    out = {"test_rows": len(y), "actual_units": float(y.sum())}
    for name, p in (("XGBoost", pred), ("Moving average (7d)", ma), ("Seasonal naive (lag 7)", test["lag_7"].values)):
        p = np.asarray(p, float)
        short, excess = np.maximum(y - p, 0).sum(), np.maximum(p - y, 0).sum()
        out[name] = {"predicted_units": float(p.sum()), "bias_pct": float((p.sum() - y.sum()) / y.sum() * 100),
                     "understock_units": float(short), "overstock_units": float(excess),
                     "understock_pct_of_demand": float(short / y.sum() * 100), "overstock_pct_of_demand": float(excess / y.sum() * 100),
                     "wape_pct": float((short + excess) / y.sum() * 100)}
        # a simple safety-stock rule: add z * residual std (residuals from the same forecast, so this is an in-sample illustration)
        sd = float(np.std(y - p))
        for z, lab in ((1.28, "p90"), (1.64, "p95")):
            q = p + z * sd
            out[name][f"{lab}_buffer"] = {"understock_pct_of_demand": float(np.maximum(y - q, 0).sum() / y.sum() * 100),
                                          "overstock_pct_of_demand": float(np.maximum(q - y, 0).sum() / y.sum() * 100)}
    out["note"] = "Units are daily article units in the 20% test window; the buffer rows use the test residual std (illustrative, not out-of-sample)."
    save("inventory", out)


def exp_cold(ft, info):
    attr_cols = ["price", "sales_channel_id"] + ATTRS + CALENDAR
    all_cols = feature_engineering.get_feature_columns(ft)
    gkf = GroupKFold(n_splits=5)
    y = ft["demand"].values
    pred_cold, pred_lag, pred_base = np.zeros(len(ft)), np.zeros(len(ft)), np.zeros(len(ft))
    for tr, te in gkf.split(ft, y, ft["article_id"]):
        a, b = ft.iloc[tr], ft.iloc[te]
        pred_cold[te] = fit(a[attr_cols], a["demand"], 42).predict(b[attr_cols])
        pred_lag[te] = fit(a[all_cols], a["demand"], 42).predict(b[all_cols])
        grp = a.groupby("product_type_name")["demand"].mean()
        pred_base[te] = b["product_type_name"].map(grp).fillna(a["demand"].mean()).values
    res = {"folds": 5, "articles": int(ft.article_id.nunique()), "rows": len(ft),
           "attributes_calendar_only_unseen_article": met(y, pred_cold),
           "product_type_mean_baseline_unseen_article": met(y, pred_base),
           "full_features_unseen_article_lags_assumed_known": met(y, pred_lag),
           "note": "Articles in the test fold are never in the training fold. The third row still uses the held-out article's own lag features, so it is not a cold-start result - it shows what history is worth."}
    save("cold_start", res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "real_hm"))
    ap.add_argument("--only", default="forecasting,recursive,domain,explain,inventory,cold")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    ft, mappings, daily, info = load(Path(a.data))
    save("dataset", info)
    print(info)
    todo = a.only.split(",")
    if "forecasting" in todo:
        exp_forecasting(ft, info)
    if "recursive" in todo:
        exp_recursive(ft, info)
    if "domain" in todo:
        exp_domain(ft, mappings, info)
    if "explain" in todo:
        exp_explain(ft, info)
    if "inventory" in todo:
        exp_inventory(ft, info)
    if "cold" in todo:
        exp_cold(ft, info)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
