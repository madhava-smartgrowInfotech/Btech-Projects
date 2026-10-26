"""Reproducible experiments for the FlowSense report.  Writes experiments/<name>/metrics.json.

Run from 8.ProjectCode with the system Python:   python scripts/run_experiments.py [name ...]
Every number in the documents comes from these files.  Nothing here changes the product code.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:  # on Windows torch must load before scikit-learn / OpenCV
    import torch  # noqa: F401
except Exception:
    pass

import cv2
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from smart_traffic import vision as V  # noqa: E402
from smart_traffic.predictor import HORIZON, QueuePredictor  # noqa: E402
from smart_traffic.sim import CONTROLLERS, Sim  # noqa: E402

OUT = ROOT / "experiments"
SEEDS = [40, 41, 42, 43, 44]
KEYS = ["Avg delay / vehicle (s)", "Avg queue (veh)", "Max approach queue", "Throughput (veh)",
        "Emergency delay (s)", "Emergency max (s)", "Emergency served", "Red-light violations",
        "Wrong-way violations", "Fuel wasted idling (L)", "CO2 (kg)"]


def save(name, data):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(data, indent=2, default=float), encoding="utf-8")
    print("wrote", d / "metrics.json")


def agg(runs):
    """mean / std / per-seed for each summary key."""
    out = {}
    for k in KEYS:
        v = np.array([r[k] for r in runs], float)
        out[k] = dict(mean=float(v.mean()), std=float(v.std(ddof=1)) if len(v) > 1 else 0.0, per_seed=[float(x) for x in v])
    return out


_PRED = {}


def predictor():
    if "p" not in _PRED:
        t = time.time()
        _PRED["p"] = QueuePredictor().fit()
        _PRED["fit_s"] = time.time() - t
    return _PRED["p"]


def run_sim(rows, cols, ctrl, demand, seed, secs, pred, **kw):
    return Sim(rows, cols, ctrl, demand, seed=seed, predictor=pred if ctrl == "advanced" else None, **kw).run(secs)


# ------------------------------------------------------------------ controllers
def controllers(grid, demand=1.2, secs=1800):
    rows, cols = grid
    p = predictor()
    res = {}
    for c in CONTROLLERS:
        t = time.time()
        sims = [run_sim(rows, cols, c, demand, s, secs, p) for s in SEEDS]
        res[c] = dict(label=CONTROLLERS[c], metrics=agg([s.summary() for s in sims]),
                      emergency_delays=[e["delay"] for s in sims for e in s.emg_log],
                      emergency_spawned=sum(s.spawned for s in sims), preemptions=sum(s.preemptions for s in sims),
                      wall_s_per_run=(time.time() - t) / len(SEEDS))
    adv, base, fix = (res[k]["metrics"] for k in ("advanced", "emergency", "fixed"))
    res["_derived"] = dict(
        delay_cut_advanced_vs_fixed_pct=100 * (1 - adv["Avg delay / vehicle (s)"]["mean"] / fix["Avg delay / vehicle (s)"]["mean"]),
        delay_cut_advanced_vs_adaptive_pct=100 * (1 - adv["Avg delay / vehicle (s)"]["mean"] / res["adaptive"]["metrics"]["Avg delay / vehicle (s)"]["mean"]),
        delay_cut_advanced_vs_basepaper_pct=100 * (1 - adv["Avg delay / vehicle (s)"]["mean"] / base["Avg delay / vehicle (s)"]["mean"]),
        emergency_cut_advanced_vs_fixed_pct=100 * (1 - adv["Emergency delay (s)"]["mean"] / fix["Emergency delay (s)"]["mean"]),
        emergency_cut_advanced_vs_basepaper_pct=100 * (1 - adv["Emergency delay (s)"]["mean"] / base["Emergency delay (s)"]["mean"]),
        delay_cut_basepaper_vs_adaptive_pct=100 * (1 - base["Avg delay / vehicle (s)"]["mean"] / res["adaptive"]["metrics"]["Avg delay / vehicle (s)"]["mean"]),
        fuel_saved_L_advanced_vs_fixed_per_run=fix["Fuel wasted idling (L)"]["mean"] - adv["Fuel wasted idling (L)"]["mean"])
    return dict(grid=f"{rows}x{cols}", demand=demand, seconds=secs, seeds=SEEDS, start_hour=8.0, results=res)


def exp_controllers_2x2():
    save("controllers_2x2", controllers((2, 2)))


def exp_controllers_3x3():
    save("controllers_3x3", controllers((3, 3)))


def exp_demand_sweep():
    p = predictor()
    levels = [0.6, 0.9, 1.2, 1.5, 1.8]
    out = {}
    for c in CONTROLLERS:
        out[c] = []
        for d in levels:
            runs = [run_sim(2, 2, c, d, s, 1200, p).summary() for s in SEEDS[:3]]
            v = np.array([r["Avg delay / vehicle (s)"] for r in runs])
            out[c].append(dict(demand=d, delay_mean=float(v.mean()), delay_std=float(v.std(ddof=1)),
                               throughput=float(np.mean([r["Throughput (veh)"] for r in runs])),
                               emergency_delay=float(np.mean([r["Emergency delay (s)"] for r in runs]))))
    save("demand_sweep", dict(grid="2x2", seconds=1200, seeds=SEEDS[:3], levels=levels, series=out))


def exp_emergency():
    """Emergency-heavy traffic: one ambulance per 60 s on average, 3600 s, 5 seeds."""
    p = predictor()
    out = {}
    for c in CONTROLLERS:
        sims = [run_sim(2, 2, c, 1.2, s, 3600, p, emg_rate=1 / 60) for s in SEEDS]
        d = np.array([e["delay"] for s in sims for e in s.emg_log], float)
        out[c] = dict(label=CONTROLLERS[c], n=int(len(d)), mean=float(d.mean()), median=float(np.median(d)),
                      p90=float(np.percentile(d, 90)), max=float(d.max()), zero_delay_share=float((d == 0).mean()),
                      mean_travel=float(np.mean([e["travel"] for s in sims for e in s.emg_log])),
                      network_delay=float(np.mean([s.summary()["Avg delay / vehicle (s)"] for s in sims])),
                      preemptions=int(sum(s.preemptions for s in sims)))
    save("emergency", dict(grid="2x2", seconds=3600, demand=1.2, emg_rate="1/60 per second", seeds=SEEDS, results=out))


# --------------------------------------------------------------------- ablation
class NoLookahead(Sim):
    def _scan_upstream(self, lookahead_pcu, lookahead_emg):
        super()._scan_upstream(0, lookahead_emg)


class NoPreempt(Sim):
    def _emergency_target(self, j):
        return None


class NoEmergencyGreenWave(Sim):
    def _scan_upstream(self, lookahead_pcu, lookahead_emg):
        super()._scan_upstream(lookahead_pcu, 0)


def exp_ablation():
    p = predictor()
    variants = {
        "advanced (full)": (Sim, p),
        "no ML forecast": (Sim, None),
        "no platoon look-ahead": (NoLookahead, p),
        "no emergency green wave": (NoEmergencyGreenWave, p),
        "no emergency pre-emption": (NoPreempt, p),
    }
    out = {}
    for name, (cls, pr) in variants.items():
        sims = [cls(2, 2, "advanced", 1.2, seed=s, predictor=pr).run(1800) for s in SEEDS]
        runs = [s.summary() for s in sims]
        out[name] = agg(runs)
    save("ablation", dict(grid="2x2", demand=1.2, seconds=1800, seeds=SEEDS, results=out))


# -------------------------------------------------------------------- predictor
def _group_dataset(seeds=(1, 2, 3, 4, 5, 6), seconds=1800, demands=(0.7, 1.0, 1.3, 1.6)):
    """Same generator as smart_traffic.predictor.build_dataset, but keeps the simulation id of every row."""
    X, y, g = [], [], []
    for k, s in enumerate(seeds):
        rows, cols = (2, 2) if k % 2 == 0 else (3, 3)
        sim = Sim(rows, cols, "adaptive", demands[k % 4], seed=100 + s, start_hour=[7.0, 8.0, 12.0, 17.0][k % 4],
                  emergencies=False, violations=False)
        snaps = []
        for t in range(seconds):
            sim.step()
            if t >= 40 and t % 10 == 0:
                snaps.append((t, sim.feature_matrix()))
        for t, F in snaps:
            if t + HORIZON < seconds:
                X.append(F)
                y.append(sim.qhist[t + HORIZON].reshape(-1))
                g.append(np.full(len(F), k))
    return np.vstack(X), np.concatenate(y), np.concatenate(g)


def _models():
    return {
        "Persistence": None,
        "Ridge regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=80, max_depth=10, random_state=0, n_jobs=-1),
        "Gradient Boosting (used)": GradientBoostingRegressor(n_estimators=160, max_depth=4, learning_rate=0.08,
                                                              subsample=0.9, random_state=0),
    }


def _score(model, Xtr, ytr, Xte, yte):
    pred = Xte[:, 0] if model is None else model.fit(Xtr, ytr).predict(Xte)
    return float(mean_absolute_error(yte, pred)), float(r2_score(yte, pred))


def exp_predictor():
    X, y, g = _group_dataset()
    res = {"n_samples": int(len(y)), "n_features": int(X.shape[1]), "horizon_s": HORIZON,
           "target_mean": float(y.mean()), "target_std": float(y.std()), "target_max": float(y.max())}
    # (a) random 75/25 split, as the shipped model does - rows from the same simulation leak across the split
    rand = {}
    for m_name in _models():
        maes, r2s = [], []
        for rs in range(5):
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=rs)
            mae, r2 = _score(_models()[m_name], Xtr, ytr, Xte, yte)
            maes.append(mae)
            r2s.append(r2)
        rand[m_name] = dict(mae_mean=float(np.mean(maes)), mae_std=float(np.std(maes, ddof=1)),
                            r2_mean=float(np.mean(r2s)), r2_std=float(np.std(r2s, ddof=1)))
    res["random_split_5x"] = rand
    # (b) leave-one-simulation-out: each of the six simulations is held out in turn
    loso = {m: dict(mae=[], r2=[]) for m in _models()}
    for held in range(6):
        tr, te = g != held, g == held
        for m_name in _models():
            mae, r2 = _score(_models()[m_name], X[tr], y[tr], X[te], y[te])
            loso[m_name]["mae"].append(mae)
            loso[m_name]["r2"].append(r2)
    res["leave_one_simulation_out"] = {m: dict(mae_mean=float(np.mean(v["mae"])), mae_std=float(np.std(v["mae"], ddof=1)),
                                               r2_mean=float(np.mean(v["r2"])), r2_std=float(np.std(v["r2"], ddof=1)),
                                               mae_per_fold=v["mae"]) for m, v in loso.items()}
    # shipped model, as the app trains it
    p = predictor()
    res["shipped_fit"] = dict(fit_seconds=_PRED["fit_s"], n_samples=int(p.n_samples),
                              metrics={k: dict(mae=float(v[0]), r2=float(v[1])) for k, v in p.metrics.items()},
                              importance={k: float(v) for k, v in p.importance.items()})
    # closed-loop effect of the forecast: advanced with and without it (see ablation as well)
    save("predictor", res)


# ----------------------------------------------------------------------- vision
def _iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _eval_scene(img, truth, thr=0.3):
    dets, bars = V.detect_classical(img)
    used, tp, cls_ok = set(), 0, 0
    for kind, tb in truth:
        best, bi = 0.0, -1
        for i, d in enumerate(dets):
            if i in used:
                continue
            o = _iou(tb, d["box"])
            if o > best:
                best, bi = o, i
        if best >= thr:
            used.add(bi)
            tp += 1
            cls_ok += dets[bi]["cls"] == kind
    amb_truth = any(k == "ambulance" for k, _ in truth)
    amb_pred = any(d["cls"] == "ambulance" for d in dets)
    return dict(n_truth=len(truth), n_det=len(dets), tp=tp, cls_ok=cls_ok, amb_truth=amb_truth, amb_pred=amb_pred,
                density=V.density_report(dets)["level"])


def _vision_batch(n=300, perturb=None):
    rng = np.random.default_rng(7)
    rows = []
    for i in range(n):
        nv = int(rng.integers(3, 15))
        amb = bool(rng.random() < 0.5)
        img, truth = V.render_scene(nv, amb, i % 2, seed=1000 + i)
        if perturb:
            img = perturb(img, np.random.default_rng(i))
        rows.append(_eval_scene(img, truth))
    tp, nt, nd = sum(r["tp"] for r in rows), sum(r["n_truth"] for r in rows), sum(r["n_det"] for r in rows)
    a_t = [r for r in rows if r["amb_truth"]]
    a_f = [r for r in rows if not r["amb_truth"]]
    tpa = sum(r["amb_pred"] for r in a_t)
    fpa = sum(r["amb_pred"] for r in a_f)
    return dict(scenes=n, objects=nt, detections=nd, recall=tp / nt, precision=tp / nd if nd else 0.0,
                class_accuracy_of_matched=sum(r["cls_ok"] for r in rows) / max(tp, 1),
                count_exact_share=float(np.mean([r["n_det"] == r["n_truth"] for r in rows])),
                count_mae=float(np.mean([abs(r["n_det"] - r["n_truth"]) for r in rows])),
                ambulance_scenes=len(a_t), ambulance_recall=tpa / len(a_t),
                no_ambulance_scenes=len(a_f), ambulance_false_alarm_rate=fpa / len(a_f),
                ambulance_precision=tpa / max(tpa + fpa, 1))


def exp_vision_synthetic():
    def noise(s):
        return lambda img, rng: np.clip(img.astype(np.float32) + rng.normal(0, s, img.shape), 0, 255).astype(np.uint8)

    def dark(f):
        return lambda img, rng: np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

    def blur(img, rng):
        return cv2.GaussianBlur(img, (7, 7), 0)

    out = {"clean": _vision_batch(), "gaussian_noise_sigma10": _vision_batch(perturb=noise(10)),
           "gaussian_noise_sigma25": _vision_batch(perturb=noise(25)), "brightness_x0.6": _vision_batch(perturb=dark(0.6)),
           "gaussian_blur_7x7": _vision_batch(perturb=blur)}
    save("vision_synthetic", dict(note="Scenes come from smart_traffic.vision.render_scene (same author as the detector); "
                                       "an optimistic, in-domain test. IoU>=0.3 matching.", results=out))


def exp_vision_yolo():
    if not V.yolo_available():
        save("vision_yolo", dict(available=False))
        return
    res = {"available": True, "model": "yolov8n.pt"}
    path = V.sample_image_path()
    img = cv2.imread(path)
    V.detect_yolo(img)  # warm-up (loads the model)
    ts = []
    for _ in range(20):
        t = time.perf_counter()
        dets, bars = V.detect_yolo(img)
        ts.append((time.perf_counter() - t) * 1000)
    res["sample_photo"] = dict(path=Path(path).name, size=list(img.shape[:2]), detections=[dict(cls=d["cls"], conf=round(d["conf"], 3)) for d in dets],
                               lightbar_clusters=len(bars), latency_ms_mean=float(np.mean(ts)), latency_ms_median=float(np.median(ts)),
                               latency_ms_p95=float(np.percentile(ts, 95)))
    syn, _ = V.render_scene(9, True, 0, 3)
    sd, _ = V.detect_yolo(syn)
    res["synthetic_scene_with_yolo"] = dict(detections=[d["cls"] for d in sd])
    # a real-image detection benchmark if the COCO128 subset is already on disk (see scripts/eval_coco128.py)
    f = OUT / "vision_coco128" / "metrics.json"
    res["coco128_available"] = f.exists()
    save("vision_yolo", res)


def exp_throughput():
    p = predictor()
    out = {}
    for name, (rows, cols) in {"2x2": (2, 2), "3x3": (3, 3)}.items():
        for c in ("fixed", "advanced"):
            t = time.perf_counter()
            run_sim(rows, cols, c, 1.2, 40, 1800, p)
            out[f"{name}/{c}"] = dict(sim_seconds=1800, wall_s=time.perf_counter() - t, speedup=1800 / (time.perf_counter() - t))
    t = time.perf_counter()
    X, _, _ = _group_dataset(seeds=(1,), seconds=600)
    n = len(X)
    m = predictor()
    t = time.perf_counter()
    for _ in range(100):
        m.predict(X[:16])
    out["predictor_batch16_ms"] = (time.perf_counter() - t) * 10
    save("throughput", out)


ALL = {"controllers_2x2": exp_controllers_2x2, "controllers_3x3": exp_controllers_3x3, "demand_sweep": exp_demand_sweep,
       "emergency": exp_emergency, "ablation": exp_ablation, "predictor": exp_predictor,
       "vision_synthetic": exp_vision_synthetic, "vision_yolo": exp_vision_yolo, "throughput": exp_throughput}

if __name__ == "__main__":
    names = sys.argv[1:] or list(ALL)
    for n in names:
        t = time.time()
        ALL[n]()
        print(f"{n}: {time.time() - t:.1f}s")
