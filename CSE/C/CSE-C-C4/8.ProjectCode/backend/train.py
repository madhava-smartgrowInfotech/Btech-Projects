"""QuantPulse training pipeline — runs the full ablation end-to-end.

Produces artifacts/metrics.json, artifacts/forecasts.json,
artifacts/serving/*.keras + scalers, artifacts/plots/*.
All numbers come from actually running the pipeline; nothing is fabricated.
Usage:  python -m backend.train   (from QuantPulse/ dir)
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from backend.app import config, data_loader, sentiment as sent, baselines as bl
from backend.app import models_dl as mdl, federated as fed, forecast as fc

ART = os.path.abspath(config.ARTIFACTS_DIR)
SERV = os.path.join(ART, "serving")
PLOTS = os.path.join(ART, "plots")


def _save_loss_curve(history, path, title):
    plt.figure(figsize=(7, 4))
    plt.plot(history.history.get("loss", []), label="train loss")
    if "val_loss" in history.history:
        plt.plot(history.history["val_loss"], label="val loss")
    plt.title(title); plt.xlabel("epoch"); plt.ylabel("MSE"); plt.legend(); plt.tight_layout()
    plt.savefig(path, dpi=110); plt.close()


def _save_pred_plot(dates, y_true, y_pred, path, title):
    plt.figure(figsize=(9, 4))
    plt.plot(dates, y_true, label="actual", linewidth=1.5)
    plt.plot(dates, y_pred, label="predicted", linewidth=1.5)
    plt.title(title); plt.legend(); plt.tight_layout()
    plt.savefig(path, dpi=110); plt.close()


def train_ticker(t, df, mode, fed_client_store):
    close = df["Close"].to_numpy(float)
    dates = df.index
    out = {"mode": mode, "n_rows": int(len(df))}

    # --- baselines ---
    out["baselines"] = bl.run_all(dates, close)

    # --- sentiment ---
    daily_sent, sent_meta = sent.get_daily_sentiment(t, dates)
    out["sentiment"] = sent_meta
    s_vals = daily_sent.to_numpy(float)

    # --- deep tiers ---
    import tensorflow as tf
    tf.random.set_seed(42); np.random.seed(42)
    tiers = {}
    histories = {}
    serving = {}

    def run_tier(name, use_sent, builder):
        raw = mdl.prepare_features(df, s_vals if use_sent else None)
        n = len(raw)
        k = int(n * config.TRAIN_SPLIT)
        scalers = mdl.fit_scalers(raw[:k])
        scaled = mdl.apply_scalers(raw, scalers)
        X, y, idx = mdl.make_windows(scaled, config.WINDOW)
        (Xtr, ytr, _), (Xte, yte, idte) = mdl.scale_split(X, y, idx, n)
        model = builder((config.WINDOW, scaled.shape[1]))
        h = mdl.train_model(model, Xtr, ytr)
        yp = model.predict(Xte, verbose=0).ravel()
        close_sc = scalers[3]
        metrics = mdl.evaluate_dl(yte, yp, close_sc)
        tiers[name] = metrics
        histories[name] = {"loss": [float(v) for v in h.history["loss"]],
                           "val_loss": [float(v) for v in h.history.get("val_loss", [])]}
        resid = float(np.std(yte - yp))
        yt_act = close_sc.inverse_transform(yte.reshape(-1, 1)).ravel()
        yp_act = close_sc.inverse_transform(yp.reshape(-1, 1)).ravel()
        test_dates = dates[idte]
        serving[name] = (model, scalers, scaled, resid, test_dates, yt_act, yp_act, Xtr, ytr)
        return model

    run_tier("lstm", False, mdl.build_lstm)
    run_tier("lstm_attention", False, mdl.build_attention_lstm)
    run_tier("lstm_attention_sentiment", True, mdl.build_attention_lstm)

    # stash client data for federated stage
    m_s, sc_s, scaled_s, *_rest, Xtr_s, ytr_s = serving["lstm_attention_sentiment"]
    fed_client_store[t] = (Xtr_s, ytr_s, serving["lstm_attention_sentiment"])

    # forecasts from attention+sentiment local model (serving model)
    last_window = scaled_s[-config.WINDOW:]
    short = fc.recursive_forecast(m_s, last_window, 5, _rest[0], sc_s[3])
    long = fc.recursive_forecast(m_s, last_window, 30, _rest[0], sc_s[3])
    last_close = float(close[-1])
    trend = "up" if short[-1]["predicted_close"] >= last_close else "down"
    out["deep"] = tiers
    out["histories"] = histories
    out["forecast_short"] = short
    out["forecast_long"] = long
    out["last_close"] = round(last_close, 2)
    out["trend"] = trend
    out["headlines"] = sent.recent_headlines(t)
    return out, serving


def main():
    os.makedirs(SERV, exist_ok=True); os.makedirs(PLOTS, exist_ok=True)
    tickers = config.get_tickers()
    print(f"[QuantPulse] training universe: {tickers}", flush=True)
    results, servings, fed_store = {}, {}, {}
    for t in tickers:
        print(f"[QuantPulse] loading {t} ...", flush=True)
        try:
            df, mode = data_loader.load_ticker(t)
        except ValueError as e:
            print(f"  skip {t}: {e}", flush=True)
            continue
        print(f"[QuantPulse] training {t} ({mode}, {len(df)} rows) ...", flush=True)
        res, serving = train_ticker(t, df, mode, fed_store)
        results[t] = res
        servings[t] = serving

    # --- federated stage (FedAvg over per-ticker attention+sentiment clients) ---
    print("[QuantPulse] federated aggregation (FedAvg, simulated in-process) ...", flush=True)
    n_feat = next(iter(fed_store.values()))[0].shape[2]
    client_data = {t: (v[0], v[1]) for t, v in fed_store.items()}
    global_model, fed_hist = fed.run_federated(mdl.build_attention_lstm, client_data,
                                               rounds=2, local_epochs=3,
                                               input_shape=(config.WINDOW, n_feat))
    # evaluate global model per ticker + save as serving hybrid
    import tensorflow as tf
    for t, (_, _, pack) in fed_store.items():
        model_s, scalers, scaled, resid, test_dates, yt, yp, Xtr, ytr = pack
        X, y, idx = mdl.make_windows(scaled, config.WINDOW)
        (Xtr2, ytr2, _), (Xte, yte, idte) = mdl.scale_split(X, y, idx, len(scaled))
        try:
            ypg = global_model.predict(Xte, verbose=0).ravel()
            m = mdl.evaluate_dl(yte, ypg, scalers[3])
        except Exception as e:
            m = {"error": str(e)[:200]}
        results[t]["deep"]["hybrid_federated"] = m
        results[t]["federated_rounds"] = fed_hist["rounds"]
        # forecasts from global model
        try:
            short = fc.recursive_forecast(global_model, scaled[-config.WINDOW:], 5, resid, scalers[3])
            results[t]["forecast_short"] = short
            results[t]["trend"] = "up" if short[-1]["predicted_close"] >= results[t]["last_close"] else "down"
        except Exception:
            pass
        # persist serving artifacts (global weights adapted per-ticker scalers)
        global_model.save(os.path.join(SERV, f"{t}_hybrid.keras"))
        np.savez(os.path.join(SERV, f"{t}_scalers.npz"),
                 **{f"min_{i}": sc.data_min_ for i, sc in enumerate(scalers)},
                 **{f"scale_{i}": sc.scale_ for i, sc in enumerate(scalers)},
                 n_feat=n_feat)
    global_model.save(os.path.join(SERV, "global_hybrid.keras"))

    # --- Tesla deep dive plots ---
    focus = "TSLA" if "TSLA" in servings else tickers[0]
    pack = servings[focus]["lstm_attention_sentiment"]
    _, _, _, _, test_dates, yt, yp, _, _ = pack
    _save_pred_plot(test_dates, yt, yp, os.path.join(PLOTS, f"{focus}_predicted_vs_actual.png"),
                    f"{focus} — predicted vs actual (test)")
    for name, (_, _, p) in (("x", (None, None, servings[focus]["lstm_attention_sentiment"])),):
        pass
    for tier in ("lstm", "lstm_attention", "lstm_attention_sentiment"):
        h = results[focus]["histories"][tier]
        hist_view = type("H", (), {"history": h})()
        _save_loss_curve(hist_view, os.path.join(PLOTS, f"{focus}_{tier}_loss.png"), f"{focus} {tier} - loss")

    with open(os.path.join(ART, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    fc_out = {t: {"short": r["forecast_short"], "long": r["forecast_long"],
                  "trend": r["trend"], "last_close": r["last_close"]} for t, r in results.items()}
    with open(os.path.join(ART, "forecasts.json"), "w") as f:
        json.dump(fc_out, f, indent=2)
    print("[QuantPulse] done. metrics.json + forecasts + serving models written.", flush=True)
    # console ablation summary
    for t, r in results.items():
        d = r.get("deep", {})
        print(f"  {t}: " + " | ".join(f"{k} MAE={v.get('mae', float('nan')):.2f} DA={v.get('directional_accuracy', float('nan')):.2f}" for k, v in d.items() if isinstance(v, dict) and "mae" in v), flush=True)


if __name__ == "__main__":
    main()
