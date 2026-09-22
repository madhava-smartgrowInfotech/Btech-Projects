"""Learn and evaluate the Gaussian Process used for better-signal suggestions.

    python ml/train_gp.py            # full run -> experiments/gp_<stamp>/ + models/gp_signal.*
    python ml/train_gp.py --quick    # smoke run on one area (does not touch models/)

Two targets, both from the Cork drive-test traces:
    rsrp    LTE signal level (dBm) - for readings that carry radio metrics
    log_dl  log10 download speed (Mbps) - for phone-probe readings
Readings are averaged into 10 m cells. Two-scale kernel hyperparameters are learned per target (and operator)
on the densest 2 km areas; evaluation holds out whole 200 m blocks (spatial block cross-validation)
and predicts them exactly as the live service does: a local GP on training points within 1.5 km.
Baselines: inverse-distance weighting, k-nearest neighbours, local mean and area mean.
"""
from __future__ import annotations

import argparse
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.model_selection import GroupKFold, KFold

import _plots as P
from _common import EXPERIMENTS, MODELS, PROCESSED, SEED, new_run, seed_everything, write_json
from app.ml.gp import GPParams, aggregate, fit_predict, learn_params, local_training_set, project

TARGETS = {
    "rsrp": {"label": "LTE signal level (RSRP)", "unit": "dBm", "strong_threshold": -100.0, "transform": "identity"},
    "log_dl": {"label": "Download speed (log10 Mbps)", "unit": "log10 Mbps", "strong_threshold": float(np.log10(2.0)),
               "transform": "log10(max(Mbps, 0.05))"},
}
CELL_M, BLOCK_M, RADIUS_M, MAX_POINTS = 10.0, 200.0, 1500.0, 1500
METHODS = ["Gaussian Process", "Inverse distance", "Nearest neighbours", "Local mean", "Area mean"]


def target_points(df: pd.DataFrame, target: str) -> pd.DataFrame:
    if target == "rsrp":
        d = df[(df.family == "lte_nr") & df.level.notna()].assign(value=lambda x: x.level)
    else:
        d = df[(df.state == "D") & df.dl_kbps.notna()].assign(value=lambda x: np.log10(np.maximum(x.dl_kbps / 1000.0, 0.05)))
    parts = []
    for op, g in d.groupby("operator"):
        a = aggregate(g.lat.to_numpy(), g.lon.to_numpy(), g.value.to_numpy(), CELL_M)
        parts.append(a.assign(operator=op))
    return pd.concat(parts, ignore_index=True)


def dense_areas(points: pd.DataFrame, n_areas: int, min_points: int = 300) -> list[tuple[str, pd.DataFrame]]:
    """Densest ~2 km x 2 km areas per operator."""
    pts = points.assign(tile=(np.floor(points.lat / 0.018)).astype(int).astype(str) + "_" + (np.floor(points.lon / 0.029)).astype(int).astype(str))
    out = []
    for op, g in pts.groupby("operator"):
        counts = g.tile.value_counts()
        for tile in counts[counts >= min_points].index[:n_areas]:
            out.append((f"{op} / area {tile}", g[g.tile == tile].reset_index(drop=True)))
    return out


def idw(xy_tr, y_tr, xy_q, k=16, power=2.0):
    d = np.hypot(xy_q[:, None, 0] - xy_tr[None, :, 0], xy_q[:, None, 1] - xy_tr[None, :, 1])
    idx = np.argsort(d, axis=1)[:, :k]
    dk = np.take_along_axis(d, idx, axis=1)
    w = 1.0 / np.maximum(dk, 1.0) ** power
    return (w * y_tr[idx]).sum(axis=1) / w.sum(axis=1)


def knn(xy_tr, y_tr, xy_q, k=8):
    d = np.hypot(xy_q[:, None, 0] - xy_tr[None, :, 0], xy_q[:, None, 1] - xy_tr[None, :, 1])
    return y_tr[np.argsort(d, axis=1)[:, :k]].mean(axis=1)


def evaluate_area(area: pd.DataFrame, params: GPParams, threshold: float, seed: int, max_blocks: int) -> dict:
    lat0, lon0 = float(area.lat.mean()), float(area.lon.mean())
    xy = project(area.lat, area.lon, lat0, lon0)
    y = area.value.to_numpy()
    blocks = (np.floor(xy[:, 0] / BLOCK_M).astype(int) * 100003 + np.floor(xy[:, 1] / BLOCK_M).astype(int))
    preds = {m: np.full(len(y), np.nan) for m in METHODS}
    gp_sd = np.full(len(y), np.nan)
    rng = np.random.default_rng(seed)
    unique_blocks = np.unique(blocks)
    keep = set(rng.choice(unique_blocks, size=min(max_blocks, len(unique_blocks)), replace=False).tolist())
    for train_idx, test_idx in GroupKFold(n_splits=5).split(xy, y, blocks):
        area_mean = float(y[train_idx].mean())
        for b in np.unique(blocks[test_idx]):
            if b not in keep:
                continue
            q = test_idx[blocks[test_idx] == b]
            local = train_idx[local_training_set(xy[train_idx], xy[q].mean(axis=0), RADIUS_M, MAX_POINTS)]
            if len(local) < 10:
                continue
            mu, sd = fit_predict(xy[local], y[local], xy[q], params, latent=False)
            preds["Gaussian Process"][q], gp_sd[q] = mu, sd
            preds["Inverse distance"][q] = idw(xy[local], y[local], xy[q])
            preds["Nearest neighbours"][q] = knn(xy[local], y[local], xy[q])
            preds["Local mean"][q] = y[local].mean()
            preds["Area mean"][q] = area_mean
    ok = ~np.isnan(preds["Gaussian Process"])
    res = {"points": int(len(y)), "evaluated_points": int(ok.sum()), "blocks_evaluated": len(keep)}
    for m in METHODS:
        e = preds[m][ok] - y[ok]
        res[m] = {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e))),
                  "strong_agreement": float(np.mean((preds[m][ok] >= threshold) == (y[ok] >= threshold)))}
    z = np.abs(preds["Gaussian Process"][ok] - y[ok]) / gp_sd[ok]
    res["gp_interval_coverage"] = {f"{int(lvl * 100)}%": float(np.mean(z <= norm.ppf(0.5 + lvl / 2))) for lvl in (0.5, 0.68, 0.8, 0.9, 0.95)}
    res["residuals"] = (preds["Gaussian Process"][ok] - y[ok]).tolist()

    # Random-point hold-out (easier: neighbours of every test point are in training) for reference.
    kf = KFold(n_splits=5, shuffle=True, random_state=seed)
    errs = []
    for tr, te in kf.split(xy):
        tr = rng.choice(tr, size=min(2000, len(tr)), replace=False)
        mu, _ = fit_predict(xy[tr], y[tr], xy[te], params, latent=False)
        errs.append(mu - y[te])
    e = np.concatenate(errs)
    res["random_holdout_gp"] = {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e)))}
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-copy", action="store_true", help="do not copy the result to models/")
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    seed_everything(args.seed)
    P.style()
    run_dir, log = new_run("gp_quick" if args.quick else "gp", Path(args.out_root) if args.out_root else EXPERIMENTS)
    t0 = time.time()
    df = pd.read_csv(PROCESSED / "lte_speed_clean.csv.gz", parse_dates=["ts"])
    n_areas, max_blocks = (1, 25) if args.quick else (3, 120)
    rng = np.random.default_rng(args.seed)

    results: dict = {}
    saved_targets: dict = {}
    surface_example = None
    for target, spec in TARGETS.items():
        points = target_points(df, target)
        areas = dense_areas(points, n_areas)
        log.info("[%s] %d cells of %.0f m, %d evaluation areas", target, len(points), CELL_M, len(areas))
        learned = []
        for name, area in areas:
            sub = area.sample(n=min(1200, len(area)), random_state=args.seed)
            xy = project(sub.lat, sub.lon, float(sub.lat.mean()), float(sub.lon.mean()))
            yv = sub.value.to_numpy()
            p = learn_params(xy, yv, GPParams.initial(yv), restarts=1 if args.quick else 2, seed=args.seed)
            learned.append({"area": name, "operator": name.split(" / ")[0], **p.to_dict()})
            log.info("[%s] %-32s short %.0f m (var %.2f), long %.0f m (var %.2f), noise %.2f",
                     target, name, p.ls_short, p.amp_short, p.ls_long, p.amp_long, p.noise)
        lp = pd.DataFrame(learned)
        keys = ["amp_short", "ls_short", "amp_long", "ls_long", "noise"]
        med = GPParams(**{k: float(lp[k].median()) for k in keys})
        by_op = {op: GPParams(**{k: float(g[k].median()) for k in keys}).to_dict() for op, g in lp.groupby("operator")}

        evals = {}
        for name, area in areas:
            evals[name] = evaluate_area(area, med, spec["strong_threshold"], args.seed, max_blocks)
            log.info("[%s] %-32s block-CV RMSE  GP %.3f | IDW %.3f | kNN %.3f | local mean %.3f | area mean %.3f  (95%% coverage %.2f)",
                     target, name, *(evals[name][m]["rmse"] for m in METHODS), evals[name]["gp_interval_coverage"]["95%"])
            if target == "rsrp" and surface_example is None:
                surface_example = (name, area, med)

        def pooled(method, key):
            w = np.array([e["evaluated_points"] for e in evals.values()], float)
            v = np.array([e[method][key] for e in evals.values()])
            return float(np.sqrt(np.sum(w * v ** 2) / w.sum())) if key == "rmse" else float(np.sum(w * v) / w.sum())

        summary = {m: {k: pooled(m, k) for k in ("rmse", "mae", "strong_agreement")} for m in METHODS}
        cov = {lvl: float(np.mean([e["gp_interval_coverage"][lvl] for e in evals.values()])) for lvl in ("50%", "68%", "80%", "90%", "95%")}
        results[target] = {"spec": spec, "learned_per_area": learned, "params": med.to_dict(), "params_by_operator": by_op,
                           "block_cv_summary": summary, "gp_interval_coverage": cov,
                           "random_holdout_gp_rmse": float(np.mean([e["random_holdout_gp"]["rmse"] for e in evals.values()])),
                           "areas": {k: {kk: vv for kk, vv in v.items() if kk != "residuals"} for k, v in evals.items()}}
        results[target]["_residuals"] = np.concatenate([np.asarray(e["residuals"]) for e in evals.values()])
        saved_targets[target] = {**spec, "params": med.to_dict(), "params_by_operator": by_op}
        log.info("[%s] pooled block-CV RMSE: %s", target, ", ".join(f"{m} {summary[m]['rmse']:.3f}" for m in METHODS))

    # ------------------------------------------------ plots
    fig, axes = P.plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, (target, res) in zip(axes, results.items()):
        vals = [res["block_cv_summary"][m]["rmse"] for m in METHODS]
        colors = [P.SERIES[0]] + [P.BASELINE_GREYS[0]] * (len(METHODS) - 1)
        bars = ax.bar(range(len(METHODS)), vals, color=colors, width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=P.TEXT_2)
        ax.set_xticks(range(len(METHODS)), [m.replace(" ", "\n") for m in METHODS], fontsize=8)
        ax.set_ylabel(f"RMSE ({res['spec']['unit']})")
        ax.set_title(res["spec"]["label"], fontsize=11)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Interpolation error on held-out 200 m blocks (lower is better)", fontsize=12, fontweight="bold", color=P.TEXT)
    fig.tight_layout()
    P.save(fig, run_dir / "rmse_comparison.png")

    fig, ax = P.plt.subplots(figsize=(5.4, 5))
    nominal = [0.5, 0.68, 0.8, 0.9, 0.95]
    ax.plot([0.45, 1], [0.45, 1], color=P.BASELINE_GREYS[1], linestyle="--", linewidth=1.2, label="Ideal")
    for k, (target, res) in enumerate(results.items()):
        ax.plot(nominal, [res["gp_interval_coverage"][f"{int(n * 100)}%"] for n in nominal], marker="o", markersize=5,
                color=P.SERIES[k], label=res["spec"]["label"])
    ax.set_xlabel("Nominal interval")
    ax.set_ylabel("Share of held-out readings inside")
    ax.set_title("Are the uncertainty bands honest?")
    ax.legend(loc="upper left")
    P.save(fig, run_dir / "interval_calibration.png")

    fig, axes = P.plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (target, res) in zip(axes, results.items()):
        r = res["_residuals"]
        lim = np.percentile(np.abs(r), 99)
        ax.hist(np.clip(r, -lim, lim), bins=50, color=P.SERIES[0], edgecolor=P.SURFACE, linewidth=0.5)
        ax.set_xlabel(f"Prediction - measured ({res['spec']['unit']})")
        ax.set_ylabel("Readings")
        ax.set_title(res["spec"]["label"], fontsize=11)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Gaussian Process residuals on held-out blocks", fontsize=12, fontweight="bold", color=P.TEXT)
    fig.tight_layout()
    P.save(fig, run_dir / "residuals.png")

    if surface_example:
        name, area, params = surface_example
        lat0, lon0 = float(area.lat.mean()), float(area.lon.mean())
        xy = project(area.lat, area.lon, lat0, lon0)
        sub = rng.choice(len(area), size=min(MAX_POINTS, len(area)), replace=False)
        gx = np.arange(xy[:, 0].min(), xy[:, 0].max() + 30, 30)
        gy = np.arange(xy[:, 1].min(), xy[:, 1].max() + 30, 30)
        GX, GY = np.meshgrid(gx, gy)
        mu, sd = fit_predict(xy[sub], area.value.to_numpy()[sub], np.column_stack([GX.ravel(), GY.ravel()]), params)
        near = np.min(np.hypot(GX.ravel()[:, None] - xy[sub, 0][None, :], GY.ravel()[:, None] - xy[sub, 1][None, :]), axis=1)
        mu = np.where(near <= 300, mu, np.nan).reshape(GX.shape)   # only draw where there is data nearby
        fig, ax = P.plt.subplots(figsize=(7.2, 6))
        vmin, vmax = np.nanpercentile(area.value, [2, 98])
        im = ax.pcolormesh(GX, GY, mu, cmap=P.BLUES, vmin=vmin, vmax=vmax, shading="auto")
        ax.contour(GX, GY, mu, levels=[TARGETS["rsrp"]["strong_threshold"]], colors=[P.TEXT], linewidths=1, linestyles="--")
        ax.scatter(xy[sub, 0], xy[sub, 1], c=area.value.to_numpy()[sub], cmap=P.BLUES, vmin=vmin, vmax=vmax, s=9,
                   edgecolors=P.SURFACE, linewidths=0.4)
        cb = fig.colorbar(im, ax=ax, shrink=0.8)
        cb.set_label("Predicted RSRP (dBm)")
        cb.outline.set_visible(False)
        ax.set_aspect("equal")
        ax.set_xlabel("East (m)")
        ax.set_ylabel("North (m)")
        ax.grid(False)
        ax.set_title(f"Predicted LTE signal - {name}\n(dashed line: -100 dBm Strong threshold; dots: measured cells)", fontsize=10)
        P.save(fig, run_dir / "surface_rsrp.png")

    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bundle = {"version": run_dir.name, "trained_at": created, "targets": saved_targets,
              "search": {"cell_m": CELL_M, "radius_m": RADIUS_M, "max_points": MAX_POINTS, "grid_step_m": 25.0, "prob_threshold": 0.8}}
    joblib.dump(bundle, run_dir / "model.joblib")
    for res in results.values():
        res.pop("_residuals")
    write_json(run_dir / "metrics.json", {
        "run": run_dir.name, "created_at": created, "quick": args.quick, "seed": args.seed,
        "task": "Spatial interpolation of signal level and download speed for better-signal suggestions",
        "dataset": {"name": "4G LTE Speed Dataset (Cork)", "cell_m": CELL_M, "block_m": BLOCK_M,
                    "evaluation": "5-fold spatial block cross-validation (200 m blocks), local GP within 1.5 km, <=1500 points"},
        "kernel": "C_short * Matern(nu=1.5, 10-300 m) + C_long * Matern(nu=1.5, 300-10000 m) + White",
        "targets": results, "timings_s": {"total": round(time.time() - t0, 1)}})
    if not args.quick and not args.no_copy:
        MODELS.mkdir(exist_ok=True)
        shutil.copy2(run_dir / "model.joblib", MODELS / "gp_signal.joblib")
        write_json(MODELS / "gp_signal.json", {"version": run_dir.name, "created_at": created, "experiment": f"experiments/{run_dir.name}",
                                                "targets": {t: {"params": r["params"], "block_cv_rmse": {m: r["block_cv_summary"][m]["rmse"] for m in METHODS},
                                                                "coverage_95": r["gp_interval_coverage"]["95%"]} for t, r in results.items()}})
        log.info("copied to models/gp_signal.joblib")
    log.info("done in %.1f s", time.time() - t0)


if __name__ == "__main__":
    main()
