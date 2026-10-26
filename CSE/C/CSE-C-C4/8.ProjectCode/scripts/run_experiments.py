"""Documentation experiments for QuantPulse (everything here is measured, nothing is typed in).

Three parts, each written to ``experiments/<name>/metrics.json``:

  shipped_summary      what the shipped ``artifacts/metrics.json`` says, aggregated over the ten tickers
  forward_test_shipped the shipped 5- and 30-day forecasts (made from data ending 2026-09-08) scored against the
                       closes that actually followed (pinned snapshot ``experiments/data_snapshot``)
  rerun                the shipped pipeline re-run on the same 501 training rows with five seeds, plus a persistence
                       baseline, a shuffled-sentiment placebo and diagnostics (scaler clipping, empty sentiment channel)

Run from 8.ProjectCode with the project venv (TensorFlow must be imported first on this machine):

    set PYTHONHASHSEED=0
    .venv\\Scripts\\python.exe scripts\\run_experiments.py [--seeds 42 43 44 45 46] [--parts rerun]
"""
import argparse
import json
import os
import sys
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf  # noqa: E402  (must precede sklearn/scipy here)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.app import baselines as bl  # noqa: E402
from backend.app import config, federated as fed, forecast as fc  # noqa: E402
from backend.app import models_dl as mdl  # noqa: E402
from backend.app import sentiment as sent  # noqa: E402

SNAP = os.path.join(ROOT, "experiments", "data_snapshot")
EXP = os.path.join(ROOT, "experiments")
TRAIN_END = "2026-09-08"          # last row the shipped models were trained on (all ten last_close values match this date)
TICKERS = config.DEFAULT_TICKERS
TIERS = ("lstm", "lstm_attention", "lstm_attention_sentiment", "attention_shuffled_sentiment")


def write(name, obj):
    d = os.path.join(EXP, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=float)
    print("wrote", name, flush=True)


def load(t):
    df = pd.read_csv(os.path.join(SNAP, f"{t}.csv"), index_col=0, parse_dates=True)
    train = df.loc[:TRAIN_END]
    fwd = df.loc[TRAIN_END:].iloc[1:]
    return train, fwd


# ---------------------------------------------------------------------------------------------------- part 1
def shipped_summary():
    m = json.load(open(os.path.join(ROOT, "artifacts", "metrics.json")))
    rows = {}
    keys = [("baseline", k) for k in ("arima", "sarimax", "prophet", "random_forest", "svr")] + [("deep", k) for k in ("lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated")]
    for kind, k in keys:
        vals = []
        for t in TICKERS:
            r = m[t]["baselines"][k]["metrics"] if kind == "baseline" else m[t]["deep"][k]
            if r:
                vals.append((t, r))
        rows[k] = {"n_tickers": len(vals)}
        for met in ("mae", "rmse", "r2", "directional_accuracy"):
            a = np.array([v[met] for _, v in vals], float)
            rows[k][met] = {"mean": float(a.mean()), "median": float(np.median(a)), "min": float(a.min()), "max": float(a.max())}
        rows[k]["per_ticker"] = {t: v for t, v in vals}
    best = {}
    for t in TICKERS:
        cand = {k: (m[t]["baselines"][k]["metrics"] if kd == "baseline" else m[t]["deep"][k]) for kd, k in keys}
        cand = {k: v["mae"] for k, v in cand.items() if v}
        best[t] = min(cand, key=cand.get)
    wins = {}
    for t, k in best.items():
        wins[k] = wins.get(k, 0) + 1
    out = {"models": rows, "best_mae_per_ticker": best, "best_mae_wins": wins,
           "n_rows": {t: m[t]["n_rows"] for t in TICKERS}, "modes": {t: m[t]["mode"] for t in TICKERS},
           "sentiment_meta": {t: m[t]["sentiment"] for t in TICKERS},
           "last_close": {t: m[t]["last_close"] for t in TICKERS},
           "trend": {t: m[t]["trend"] for t in TICKERS},
           "forecast_5d_change_pct": {t: (m[t]["forecast_short"][-1]["predicted_close"] / m[t]["last_close"] - 1) * 100 for t in TICKERS},
           "forecast_30d_change_pct": {t: (m[t]["forecast_long"][-1]["predicted_close"] / m[t]["last_close"] - 1) * 100 for t in TICKERS},
           "federated_rounds": m["TSLA"]["federated_rounds"]}
    write("shipped_summary", out)
    return m


# ---------------------------------------------------------------------------------------------------- part 2
def _fwd_metrics(pred, actual, last_close):
    pred, actual = np.asarray(pred, float), np.asarray(actual, float)
    n = min(len(pred), len(actual))
    pred, actual = pred[:n], actual[:n]
    return {"n": int(n), "mae": float(np.abs(pred - actual).mean()), "mape": float((np.abs(pred - actual) / actual).mean() * 100),
            "persistence_mae": float(np.abs(last_close - actual).mean()),
            "end_pct_error": float((pred[-1] / actual[-1] - 1) * 100),
            "pred_end_pct_change": float((pred[-1] / last_close - 1) * 100), "actual_end_pct_change": float((actual[-1] / last_close - 1) * 100),
            "trend_hit": bool(np.sign(pred[-1] - last_close) == np.sign(actual[-1] - last_close))}


def forward_test_shipped(m):
    out = {"train_end": TRAIN_END, "tickers": {}}
    for t in TICKERS:
        train, fwd = load(t)
        assert abs(float(train.Close.iloc[-1]) - m[t]["last_close"]) < 0.011, (t, train.Close.iloc[-1], m[t]["last_close"])
        lc = m[t]["last_close"]
        act = fwd.Close.to_numpy(float)[:30]
        r = {"last_close": lc, "n_forward_days": int(len(fwd)), "forward_start": str(fwd.index[0].date()), "forward_end": str(fwd.index[min(29, len(fwd) - 1)].date()),
             "app_trend": m[t]["trend"], "actual": act.tolist(),
             "short_pred": [x["predicted_close"] for x in m[t]["forecast_short"]], "long_pred": [x["predicted_close"] for x in m[t]["forecast_long"]]}
        r["short"] = _fwd_metrics(r["short_pred"], act[:5], lc)
        r["long"] = _fwd_metrics(r["long_pred"], act, lc)
        out["tickers"][t] = r
    for h in ("short", "long"):
        out[h] = {"mean_mae": float(np.mean([out["tickers"][t][h]["mae"] for t in TICKERS])),
                  "mean_mape": float(np.mean([out["tickers"][t][h]["mape"] for t in TICKERS])),
                  "mean_persistence_mae": float(np.mean([out["tickers"][t][h]["persistence_mae"] for t in TICKERS])),
                  "trend_hits": int(sum(out["tickers"][t][h]["trend_hit"] for t in TICKERS)),
                  "mean_pred_change_pct": float(np.mean([out["tickers"][t][h]["pred_end_pct_change"] for t in TICKERS])),
                  "mean_actual_change_pct": float(np.mean([out["tickers"][t][h]["actual_end_pct_change"] for t in TICKERS]))}
    write("forward_test_shipped", out)


# ---------------------------------------------------------------------------------------------------- part 3
def _tier_data(df, s_vals):
    raw = mdl.prepare_features(df, s_vals)
    n = len(raw)
    k = int(n * config.TRAIN_SPLIT)
    scalers = mdl.fit_scalers(raw[:k])
    scaled = mdl.apply_scalers(raw, scalers)
    X, y, idx = mdl.make_windows(scaled, config.WINDOW)
    (Xtr, ytr, _), (Xte, yte, idte) = mdl.scale_split(X, y, idx, n)
    return scaled, scalers, Xtr, ytr, Xte, yte, idte


def _true_metrics(close, idte, yp_scaled, close_scaler, yte_scaled):
    """Errors against the real closes. ``evaluate_dl`` scores against the *clipped* scaled targets, which are flat at the training maximum when the test prices rise above it."""
    yp = close_scaler.inverse_transform(np.asarray(yp_scaled).reshape(-1, 1)).ravel()
    yt, prev = close[idte], close[idte - 1]
    err = yp - yt
    return {"mae_true": float(np.abs(err).mean()), "rmse_true": float(np.sqrt((err ** 2).mean())),
            "r2_true": float(1 - (err ** 2).sum() / ((yt - yt.mean()) ** 2).sum()), "bias_true": float(err.mean()),
            "da_true": float(((yt - prev > 0) == (yp - prev > 0)).mean()),
            "target_clipped_pct": float((np.asarray(yte_scaled) >= 0.999).mean() * 100)}


def _forward(model, scaled, scalers, resid, fwd_close, last_close):
    f = fc.recursive_forecast(model, scaled[-config.WINDOW:], 30, resid, scalers[3])
    pred = [x["predicted_close"] for x in f]
    return {"short": _fwd_metrics(pred[:5], fwd_close[:5], last_close), "long": _fwd_metrics(pred, fwd_close, last_close)}


def rerun(seeds):
    t0 = time.time()
    out = {"seeds": seeds, "train_end": TRAIN_END, "tf": tf.__version__, "tickers": {}}
    cache = {}
    # data + sentiment + deterministic baselines once per ticker
    for t in TICKERS:
        train, fwd = load(t)
        close = train.Close.to_numpy(float)
        dates = train.index
        s_series, meta = sent.get_daily_sentiment(t, dates)
        s_vals = s_series.to_numpy(float)
        rng = np.random.default_rng(7)
        shuffled = rng.permutation(s_vals)
        raw_n = len(train)
        k_raw = int(raw_n * config.TRAIN_SPLIT)
        d = {"n_rows": raw_n, "sentiment_source": meta["source"], "sentiment_scorer": meta["scorer"], "n_headlines": meta["n_headlines"],
             "sentiment_nonzero_rows": int((s_vals != 0).sum()), "sentiment_nonzero_in_train_part": int((s_vals[:k_raw] != 0).sum()),
             "sentiment_nonzero_in_test_part": int((s_vals[k_raw:] != 0).sum())}
        tr_close, te_close = close[:k_raw], close[k_raw:]
        d["test_close_above_train_max_pct"] = float((te_close > tr_close.max()).mean() * 100)
        d["train_close_range"] = [float(tr_close.min()), float(tr_close.max())]
        d["test_close_range"] = [float(te_close.min()), float(te_close.max())]
        # persistence on the same targets the deep tiers are scored on
        scaled, scalers, Xtr, ytr, Xte, yte, idte = _tier_data(train, None)
        y_act = close[config.WINDOW:][int(len(range(config.WINDOW, raw_n)) * config.TRAIN_SPLIT):]
        prev = close[config.WINDOW - 1:-1][int(len(range(config.WINDOW, raw_n)) * config.TRAIN_SPLIT):]
        d["persistence"] = {"mae": float(np.abs(y_act - prev).mean()), "rmse": float(np.sqrt(((y_act - prev) ** 2).mean())),
                            "n_test": int(len(y_act)), "up_day_share": float((np.diff(y_act) > 0).mean())}
        d["clipped_test_windows_pct"] = float(((Xte >= 0.999).any(axis=(1, 2))).mean() * 100)
        d["baselines"] = {}
        for name, fn in (("arima", lambda: bl.run_arima(close)), ("random_forest", lambda: bl.run_rf(close)), ("svr", lambda: bl.run_svr(close))):
            try:
                r = fn()
                d["baselines"][name] = r["metrics"]
            except Exception as e:  # keep going, record the failure
                d["baselines"][name] = {"error": str(e)[:200]}
        d["models"] = {k: [] for k in (*TIERS, "hybrid_federated")}
        d["forward"] = {k: [] for k in (*TIERS, "hybrid_federated")}
        out["tickers"][t] = d
        cache[t] = {"train": train, "fwd": fwd, "s": s_vals, "shuf": shuffled}
        print(f"[{time.time() - t0:6.0f}s] prepared {t}", flush=True)

    for seed in seeds:
        fed_clients, fed_pack = {}, {}
        for t in TICKERS:
            c = cache[t]
            df, fwd = c["train"], c["fwd"]
            close = df.Close.to_numpy(float)
            lastc = float(close[-1])
            fwd_close = fwd.Close.to_numpy(float)[:30]
            for tier, sv, builder in (("lstm", None, mdl.build_lstm), ("lstm_attention", None, mdl.build_attention_lstm),
                                      ("lstm_attention_sentiment", c["s"], mdl.build_attention_lstm),
                                      ("attention_shuffled_sentiment", c["shuf"], mdl.build_attention_lstm)):
                tf.keras.utils.set_random_seed(seed)
                scaled, scalers, Xtr, ytr, Xte, yte, idte = _tier_data(df, sv)
                model = builder((config.WINDOW, scaled.shape[1]))
                h = mdl.train_model(model, Xtr, ytr)
                yp = model.predict(Xte, verbose=0).ravel()
                met = mdl.evaluate_dl(yte, yp, scalers[3])
                met.update(_true_metrics(close, idte, yp, scalers[3], yte))
                met["epochs"] = len(h.history["loss"])
                out["tickers"][t]["models"][tier].append(met)
                resid = float(np.std(yte - yp))
                out["tickers"][t]["forward"][tier].append(_forward(model, scaled, scalers, resid, fwd_close, lastc))
                if tier == "lstm_attention_sentiment":
                    fed_clients[t] = (Xtr, ytr)
                    fed_pack[t] = (scaled, scalers, Xte, yte, resid, lastc, fwd_close, idte, close)
            print(f"[{time.time() - t0:6.0f}s] seed {seed} {t} done", flush=True)
        tf.keras.utils.set_random_seed(seed)
        n_feat = next(iter(fed_clients.values()))[0].shape[2]
        gm, hist = fed.run_federated(mdl.build_attention_lstm, fed_clients, rounds=2, local_epochs=3, input_shape=(config.WINDOW, n_feat))
        for t, (scaled, scalers, Xte, yte, resid, lastc, fwd_close, idte, close) in fed_pack.items():
            yp = gm.predict(Xte, verbose=0).ravel()
            met = mdl.evaluate_dl(yte, yp, scalers[3])
            met.update(_true_metrics(close, idte, yp, scalers[3], yte))
            met["mean_local_loss_rounds"] = [r["mean_local_loss"] for r in hist["rounds"]]
            out["tickers"][t]["models"]["hybrid_federated"].append(met)
            out["tickers"][t]["forward"]["hybrid_federated"].append(_forward(gm, scaled, scalers, resid, fwd_close, lastc))
        print(f"[{time.time() - t0:6.0f}s] seed {seed} federated done", flush=True)
        write("rerun", out)       # checkpoint after every seed
    out["seconds"] = time.time() - t0
    write("rerun", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[42, 43, 44, 45, 46])
    ap.add_argument("--parts", nargs="*", default=["shipped", "forward", "rerun"])
    a = ap.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        sys.exit("set PYTHONHASHSEED=0 first (the synthetic-headline fallback seeds its generator with hash(ticker))")
    m = None
    if "shipped" in a.parts or "forward" in a.parts:
        m = shipped_summary()
    if "forward" in a.parts:
        forward_test_shipped(m)
    if "rerun" in a.parts:
        rerun(a.seeds)


if __name__ == "__main__":
    main()
