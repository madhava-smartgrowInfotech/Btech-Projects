"""Service layer: wraps the existing smart_traffic engine for the HTTP API (no engine logic lives here)."""
from __future__ import annotations

import base64
import math
import threading
import time

import cv2
import numpy as np
import pandas as pd

from smart_traffic import vision as V
from smart_traffic.predictor import QueuePredictor
from smart_traffic.sim import APPROACHES, CONTROLLERS, LINK_TIME, PHASE_NAME, Sim, demand_profile

GAP = 12.0
DIR = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
GRIDS = {"2x2": (2, 2), "3x3": (3, 3)}
LOCK = threading.RLock()


class ApiError(Exception):
    def __init__(self, status: int, message: str, hint: str = ""):
        super().__init__(message)
        self.status, self.message, self.hint = status, message, hint


def num(x, nd=2):
    """JSON-safe float (no NaN / inf)."""
    try:
        x = float(x)
    except Exception:
        return None
    return round(x, nd) if math.isfinite(x) else None


# ------------------------------------------------------------------ predictor
class Predictor:
    def __init__(self):
        self.model: QueuePredictor | None = None
        self.error: str | None = None
        self.started = time.time()
        self.fit_seconds: float | None = None

    def train(self):
        try:
            t = time.time()
            self.model = QueuePredictor().fit()
            self.fit_seconds = time.time() - t
        except Exception as e:  # pragma: no cover - surfaced through /api/health
            self.error = f"{type(e).__name__}: {e}"

    @property
    def ready(self):
        return self.model is not None


PRED = Predictor()
HEADLINE: dict = {}


def start_background():
    def run():
        PRED.train()
        if PRED.ready:
            try:
                rs = {c: Sim(2, 2, c, 1.2, seed=40, predictor=PRED.model if c == "advanced" else None).run(900).summary()
                      for c in ("fixed", "advanced")}
                f, a = rs["fixed"]["Avg delay / vehicle (s)"], rs["advanced"]["Avg delay / vehicle (s)"]
                HEADLINE.update(fixed_delay=num(f, 1), advanced_delay=num(a, 1), cut_pct=num(100 * (1 - a / max(f, 1e-9)), 0),
                                emg_fixed=num(rs["fixed"]["Emergency delay (s)"], 1),
                                emg_advanced=num(rs["advanced"]["Emergency delay (s)"], 1))
            except Exception:
                pass

    threading.Thread(target=run, daemon=True, name="predictor-train").start()


def need_predictor():
    if PRED.error:
        raise ApiError(500, "The traffic-prediction model failed to train.", PRED.error)
    if not PRED.ready:
        raise ApiError(503, "The traffic-prediction model is still training (first start only, ~10 s).",
                       "Wait a few seconds and retry.")
    return PRED.model


# ------------------------------------------------------------------- live sim
def clock(sim) -> str:
    s = int(sim.start_hour * 3600 + sim.t) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def _center(sim, j):
    r, c = divmod(j, sim.cols)
    return c * GAP, -r * GAP


def map_geometry(sim) -> dict:
    """Same layout as the Streamlit `draw_map`, as plain data for the SVG renderer (y is up)."""
    R, C = sim.rows, sim.cols
    ext = 7
    bounds = dict(x0=-ext - 1, x1=(C - 1) * GAP + ext + 1, y0=-(R - 1) * GAP - ext - 1, y1=ext + 1)
    roads = [dict(x0=-ext, x1=(C - 1) * GAP + ext, y0=-r * GAP, y1=-r * GAP) for r in range(R)]
    roads += [dict(x0=c * GAP, x1=c * GAP, y0=-(R - 1) * GAP - ext, y1=ext) for c in range(C)]
    vehicles, signals, labels = [], [], []
    for j in range(sim.n):
        cx, cy = _center(sim, j)
        for a, name in enumerate(APPROACHES):
            dx, dy = DIR[name]
            px, py = -dy * 0.65, dx * 0.65
            green = sim.phase[j] == (0 if name in "NS" else 1)
            state = "green" if green and sim.clear[j] == 0 else "clearing" if green else "red"
            signals.append(dict(x=round(cx + dx * 1.9 + px, 2), y=round(cy + dy * 1.9 + py, 2), s=state, j=j, a=name))
            for i, v in enumerate(sim.q[j][a]):
                vehicles.append([round(cx + dx * (2.6 + i * 0.27) + px, 2), round(cy + dy * (2.6 + i * 0.27) + py, 2), v.vtype])
    for arrivals in sim.transit.values():
        for v, nj, na, dep, src in arrivals:
            f = 0.12 + 0.76 * min(1.0, (sim.t - dep) / LINK_TIME)
            ax, ay = _center(sim, src)
            bx, by = _center(sim, nj)
            ux, uy = bx - ax, by - ay
            n = max((ux ** 2 + uy ** 2) ** .5, 1e-6)
            vehicles.append([round(ax + ux * f - uy / n * 0.65, 2), round(ay + uy * f + ux / n * 0.65, 2), v.vtype])
    for j in range(sim.n):
        cx, cy = _center(sim, j)
        labels.append(dict(x=cx, y=cy, j=j + 1, preempt=bool(sim._preempt_active[j]),
                           phase="NS" if sim.phase[j] == 0 else "EW", timer=int(sim.timer[j])))
    return dict(bounds=bounds, roads=roads, vehicles=vehicles, signals=signals, labels=labels)


class Live:
    """One shared simulation, the equivalent of Streamlit's `st.session_state.sim`."""

    def __init__(self):
        self.grid, self.use_ml = "2x2", True
        self.sim = Sim(2, 2, "advanced", 1.0, seed=7, predictor=None)

    def _attach(self):
        self.sim.predictor = PRED.model if self.use_ml and PRED.ready else None

    def configure(self, grid=None, controller=None, demand=None, emergencies=None, use_ml=None):
        if grid is not None:
            if grid not in GRIDS:
                raise ApiError(422, f"Unknown road network '{grid}'.", "Use 2x2 or 3x3.")
            if grid != self.grid:
                r, c = GRIDS[grid]
                old = self.sim
                self.sim = Sim(r, c, old.controller, old.demand, seed=7, predictor=None, emergencies=old.emergencies)
                self.grid = grid
        if controller is not None:
            if controller not in CONTROLLERS:
                raise ApiError(422, f"Unknown controller '{controller}'.", "Pick one of: " + ", ".join(CONTROLLERS))
            self.sim.controller = controller
        if demand is not None:
            self.sim.demand = min(2.0, max(0.4, float(demand)))
        if emergencies is not None:
            self.sim.emergencies = bool(emergencies)
        if use_ml is not None:
            self.use_ml = bool(use_ml)
        self._attach()

    def reset(self):
        r, c = GRIDS[self.grid]
        old = self.sim
        self.sim = Sim(r, c, old.controller, old.demand, seed=7, predictor=None, emergencies=old.emergencies)
        self._attach()

    def step(self, seconds: int):
        self._attach()
        self.sim.run(int(seconds))

    def ambulance(self):
        sim = self.sim
        j, a = sim.entries[int(np.random.randint(len(sim.entries)))]
        v = sim._new_vehicle(emg=True)
        sim.q[j][a].append(v)
        sim.active_emg[v.id] = v
        sim.spawned += 1
        return dict(junction=j + 1, approach=APPROACHES[a])

    def snapshot(self) -> dict:
        sim = self.sim
        m = sim.summary()
        emg = list(sim.active_emg.values())
        banner = None
        if emg and sim.controller in ("emergency", "advanced"):
            banner = dict(kind="preempt", text="Emergency vehicle detected (light-bar) - signals pre-empting"
                          + (" along the route (green wave)" if sim.controller == "advanced" else ""))
        elif emg:
            banner = dict(kind="ignored", text="Emergency vehicle in network - this controller ignores it")
        q = [float(x) for x in sim.qtot[-400:]]
        x0 = max(0, sim.t - 400)
        junctions = []
        for j in range(sim.n):
            p = sim.pred[j]
            junctions.append(dict(
                junction=f"J{j + 1}", green=PHASE_NAME[sim.phase[j]] + (" (clearing)" if sim.clear[j] else ""),
                timer=int(sim.timer[j]), queue="/".join(str(len(x)) for x in sim.q[j]),
                forecast="/".join(str(int(round(x))) for x in p), preempt=bool(sim._preempt_active[j])))
        return dict(
            t=int(sim.t), clock=clock(sim), predictor_ready=PRED.ready,
            config=dict(grid=self.grid, controller=sim.controller, demand=sim.demand, emergencies=sim.emergencies, use_ml=self.use_ml),
            kpis=dict(demand_mult=num(sim.demand * demand_profile(sim.hour())), in_network=int(sim.in_network()),
                      queued=int(sim.qtot[-1]) if sim.qtot else 0, avg_delay=num(m["Avg delay / vehicle (s)"], 1),
                      emg_delay=num(m["Emergency delay (s)"], 1), emg_served=int(m["Emergency served"]), emg_active=len(emg),
                      violations=int(m["Red-light violations"] + m["Wrong-way violations"]),
                      red=int(m["Red-light violations"]), wrong=int(m["Wrong-way violations"]),
                      throughput=int(m["Throughput (veh)"]), preemptions=int(sim.preemptions)),
            banner=banner, map=map_geometry(sim),
            queue_series=[dict(t=x0 + i, q=v) for i, v in enumerate(q)], junctions=junctions)


LIVE = Live()


# ----------------------------------------------------------- public preview sim
class Preview:
    """A separate sim that runs in real time behind the landing page."""

    def __init__(self):
        self.sim = Sim(2, 2, "advanced", 1.2, seed=21, predictor=None)
        self.last = time.time()
        self.seq = 0

    def pulse(self) -> dict:
        sim = self.sim
        sim.predictor = PRED.model if PRED.ready else None
        now = time.time()
        steps = int(min(4, max(1, round(now - self.last)))) if self.seq else 8
        self.last = now
        lines = []
        for _ in range(steps):
            ph, sp, vl, pe = list(sim.phase), sim.spawned, len(sim.viol_log), sim.preemptions
            sim.step()
            stamp = clock(sim)
            for j in range(sim.n):
                if sim.phase[j] != ph[j]:
                    lines.append(dict(kind="sig", text=f"{stamp} J{j + 1} -> {PHASE_NAME[sim.phase[j]]} green"))
            if sim.spawned > sp:
                lines.append(dict(kind="emg", text=f"{stamp} ambulance entered network - looking ahead"))
            if sim.preemptions > pe:
                lines.append(dict(kind="emg", text=f"{stamp} signal pre-empted for emergency vehicle"))
            for v in sim.viol_log[vl:]:
                lines.append(dict(kind="vio", text=f"{stamp} J{v['junction'] + 1} {v['kind'].lower()} plate {v['plate']}"))
        self.seq += 1
        m = sim.summary()
        return dict(seq=self.seq, clock=clock(sim), lines=lines[-12:], map=map_geometry(sim),
                    kpis=dict(in_network=int(sim.in_network()), queued=int(sim.qtot[-1]) if sim.qtot else 0,
                              avg_delay=num(m["Avg delay / vehicle (s)"], 1), throughput=int(m["Throughput (veh)"]),
                              violations=int(m["Red-light violations"] + m["Wrong-way violations"]),
                              emg_served=int(m["Emergency served"])),
                    headline=HEADLINE or None, predictor_ready=PRED.ready)


PREVIEW = Preview()


# ------------------------------------------------------------------ benchmark
_BENCH_CACHE: dict = {}
LAST_BENCH: dict = {}
SHORT = {c: CONTROLLERS[c].split(" (")[0] for c in CONTROLLERS}


def benchmark(grid, secs, dem, nseeds, start_h, use_ml) -> dict:
    if grid not in GRIDS:
        raise ApiError(422, f"Unknown road network '{grid}'.", "Use 2x2 or 3x3.")
    if not (300 <= secs <= 3600 and 0.5 <= dem <= 1.8 and 1 <= nseeds <= 5 and 0 <= start_h <= 23):
        raise ApiError(422, "Benchmark settings are out of range.", "Duration 5-60 min, demand 0.5-1.8, 1-5 seeds, start hour 0-23.")
    pred = need_predictor() if use_ml else None
    key = (grid, secs, round(dem, 2), nseeds, start_h, use_ml)
    if key in _BENCH_CACHE:
        res = _BENCH_CACHE[key]
    else:
        rows, cols = GRIDS[grid]
        res = {}
        for c in CONTROLLERS:
            sums, q, emg, viol = [], [], [], []
            for s in range(nseeds):
                sm = Sim(rows, cols, c, dem, seed=40 + s, start_hour=start_h, predictor=pred if use_ml else None).run(secs)
                sums.append(sm.summary())
                q.append(sm.qtot)
                emg += sm.emg_log
                viol += sm.viol_log
            res[c] = dict(sums=pd.DataFrame(sums), q=np.mean(q, axis=0), emg=emg, viol=viol)
        _BENCH_CACHE[key] = res
    mean = pd.DataFrame({c: r["sums"].mean() for c, r in res.items()}).T
    base, paper, ours = mean.iloc[0], mean.iloc[2], mean.iloc[3]
    d_fixed = 100 * (1 - ours["Avg delay / vehicle (s)"] / max(base["Avg delay / vehicle (s)"], 1e-9))
    d_paper = 100 * (1 - ours["Avg delay / vehicle (s)"] / max(paper["Avg delay / vehicle (s)"], 1e-9))
    e_fixed = 100 * (1 - ours["Emergency delay (s)"] / max(base["Emergency delay (s)"], 1e-9))
    fuel = base["Fuel wasted idling (L)"] - ours["Fuel wasted idling (L)"]
    LAST_BENCH.clear()
    LAST_BENCH.update({c: {k: num(v, 1) for k, v in r["sums"][["Red-light violations", "Wrong-way violations"]].mean().items()}
                       for c, r in res.items()})
    controllers = {}
    for c, r in res.items():
        qv = r["q"]
        k = 10
        qv = qv[: len(qv) // k * k].reshape(-1, k).mean(1)
        s1, s2 = r["sums"]["Avg delay / vehicle (s)"], r["sums"]["Emergency delay (s)"]
        controllers[c] = dict(
            label=CONTROLLERS[c], short=SHORT[c],
            delay_mean=num(s1.mean()), delay_std=num(s1.std() if len(s1) > 1 else 0),
            emg_mean=num(s2.mean()), emg_std=num(s2.std() if len(s2) > 1 else 0),
            queue=[num(v, 2) for v in qv], emergency_delays=[num(e["delay"], 1) for e in r["emg"]])
    table = [dict(controller=CONTROLLERS[c], **{k: num(v, 2) for k, v in mean.loc[c].items()}) for c in mean.index]
    return dict(
        settings=dict(grid=grid, seconds=secs, demand=dem, seeds=nseeds, start_hour=start_h, use_ml=use_ml),
        kpis=dict(d_fixed=num(d_fixed, 0), d_paper=num(d_paper, 0), e_fixed=num(e_fixed, 0),
                  emg_ours=num(ours["Emergency delay (s)"], 1), emg_base=num(base["Emergency delay (s)"], 1),
                  fuel=num(fuel, 1), co2=num(fuel * 2.31, 1)),
        controllers=controllers, table=table, columns=list(mean.columns))


def sweep(grid, use_ml) -> dict:
    if grid not in GRIDS:
        raise ApiError(422, f"Unknown road network '{grid}'.", "Use 2x2 or 3x3.")
    pred = need_predictor() if use_ml else None
    rows, cols = GRIDS[grid]
    levels = [0.6, 0.9, 1.2, 1.5, 1.8]
    series = {c: [num(Sim(rows, cols, c, d, seed=5, predictor=pred if c == "advanced" else None).run(1200)
                      .summary()["Avg delay / vehicle (s)"], 1) for d in levels] for c in CONTROLLERS}
    return dict(levels=levels, series=series, labels=SHORT)


# --------------------------------------------------------------------- vision
def _b64(img, max_w=1100) -> str:
    h, w = img.shape[:2]
    if w > max_w:
        img = cv2.resize(img, (max_w, int(h * max_w / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def vision_payload(img, dets, bars, source, truth=None) -> dict:
    rep = V.density_report(dets)
    h, w = img.shape[:2]
    return dict(
        source=source, width=w, height=h, frame=_b64(img), annotated=_b64(V.annotate(img, dets, bars)),
        detections=[dict(cls=d["cls"], conf=num(d["conf"], 2), box=[round(v) for v in d["box"]], lightbar=num(d["lightbar"], 2)) for d in dets],
        lightbars=len(bars), truth_count=None if truth is None else len(truth),
        report=dict(counts=rep["counts"], pcu=num(rep["pcu"], 1), ratio=num(rep["ratio"], 3), level=rep["level"],
                    emergency=bool(rep["emergency"]), green=int(rep["green"])))


def vision_synthetic(n, emg, flash, seed):
    n = int(min(16, max(2, n)))
    img, truth = V.render_scene(n, bool(emg), 0 if flash == "A" else 1, int(seed))
    dets, bars = V.detect_classical(img)
    return vision_payload(img, dets, bars, "synthetic", truth)


def _need_yolo():
    if not V.yolo_available():
        raise ApiError(503, "YOLOv8 is not available: the `ultralytics` package is not installed.",
                       "Run `pip install ultralytics` in the backend environment, then restart the API.")


def _yolo(img, conf, source):
    try:
        dets, bars = V.detect_yolo(img, float(conf))
    except Exception as e:
        raise ApiError(502, "YOLOv8 could not run on this image.",
                       f"{type(e).__name__}: {e}. The first run downloads yolov8n.pt, so it needs internet access.")
    return vision_payload(img, dets, bars, source)


def vision_sample(conf):
    _need_yolo()
    p = V.sample_image_path()
    img = cv2.imread(p) if p else None
    if img is None:
        raise ApiError(404, "The bundled sample photo was not found.", "Upload your own image instead.")
    return _yolo(img, conf, "sample")


def vision_upload(data: bytes, conf):
    _need_yolo()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ApiError(415, "That file is not a readable JPG or PNG image.", "Choose a .jpg, .jpeg or .png camera frame.")
    return _yolo(img, conf, "upload")


# ----------------------------------------------------------------- prediction
def prediction() -> dict:
    p = need_predictor()
    gb, pers = p.metrics["Gradient Boosting (used)"], p.metrics["Persistence baseline"]
    yte, yp = p.test
    idx = np.random.default_rng(0).choice(len(yte), min(1500, len(yte)), replace=False)
    imp = pd.Series(p.importance).sort_values()
    return dict(
        kpis=dict(samples=int(p.n_samples), mae=num(gb[0], 2), r2=num(gb[1], 3), vs_persistence=num(100 * (1 - gb[0] / pers[0]), 0),
                  fit_seconds=num(PRED.fit_seconds, 1)),
        scatter=[dict(actual=num(yte[i], 2), predicted=num(yp[i], 2)) for i in idx], ideal_max=num(yte.max(), 1),
        importance=[dict(feature=k, value=num(v, 4)) for k, v in imp.items()],
        metrics=[dict(model=k, mae=num(v[0], 3), r2=num(v[1], 3)) for k, v in p.metrics.items()])


def prediction_live() -> dict:
    p = need_predictor()
    sim = LIVE.sim
    if sim.t < 40:
        return dict(available=False, t=int(sim.t), clock=clock(sim))
    F = sim.feature_matrix()
    P = p.predict(F).reshape(sim.n, 4)
    Q = F[:, 0].reshape(sim.n, 4)
    worst = np.unravel_index(np.argmax(P - Q), P.shape)
    return dict(available=True, t=int(sim.t), clock=clock(sim),
                bars=[dict(label=f"J{j + 1}-{a}", now=num(Q[j, i], 0), forecast=num(P[j, i], 1))
                      for j in range(sim.n) for i, a in enumerate(APPROACHES)],
                worst=dict(junction=int(worst[0]) + 1, approach=APPROACHES[worst[1]], now=num(Q[worst], 0), forecast=num(P[worst], 0)))


# ------------------------------------------------------------------ violations
def violations() -> dict:
    sim = LIVE.sim
    log = pd.DataFrame(sim.viol_log)
    out = dict(t=int(sim.t), minutes=int(sim.t // 60), last_benchmark=[
        dict(controller=CONTROLLERS[c], red=v["Red-light violations"], wrong=v["Wrong-way violations"]) for c, v in LAST_BENCH.items()])
    if log.empty:
        return dict(out, empty=True, kpis=dict(total=0, red=0, wrong=0, confidence=None), by_junction=[], per_minute=[], log=[])
    base = sim.start_hour * 3600
    log["time"] = log["t"].map(lambda t: f"{int(base + t) // 3600 % 24:02d}:{int(base + t) % 3600 // 60:02d}:{int(t) % 60:02d}")
    log["jn"] = log["junction"].map(lambda j: f"J{j + 1}")
    red, wrong = int((log.kind == "Red-light jumping").sum()), int((log.kind == "Wrong-way driving").sum())
    by = log.groupby(["jn", "kind"]).size().unstack(fill_value=0)
    per = log.assign(m=log.t // 60).groupby("m").size()
    rows = log.iloc[::-1].head(300)
    return dict(
        out, empty=False, kpis=dict(total=int(len(log)), red=red, wrong=wrong, confidence=num(log.confidence.mean(), 2)),
        by_junction=[dict(junction=j, red=int(r.get("Red-light jumping", 0)), wrong=int(r.get("Wrong-way driving", 0))) for j, r in by.iterrows()],
        per_minute=[dict(minute=int(m), n=int(n)) for m, n in per.items()],
        log=[dict(time=r.time, junction=r.jn, approach=r.approach, kind=r.kind, plate=r.plate, vehicle=r.vehicle, confidence=float(r.confidence))
             for r in rows.itertuples()])
