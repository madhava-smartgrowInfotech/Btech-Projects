"""AI-Based Smart Traffic Management - end-to-end Streamlit application (pure Python).

Run:  streamlit run app.py
"""
from __future__ import annotations

import time

import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from smart_traffic import vision as V
from smart_traffic.predictor import QueuePredictor
from smart_traffic.sim import (APPROACHES, CONTROLLERS, LINK_TIME, PHASE_NAME, Sim,
                               demand_profile)

st.set_page_config(page_title="Smart Traffic AI", page_icon="🚦", layout="wide",
                   initial_sidebar_state="expanded")

CTRL_COLOR = {"fixed": "#94a3b8", "adaptive": "#38bdf8", "emergency": "#fbbf24", "advanced": "#22c55e"}
VT_STYLE = {"car": ("#60a5fa", 7), "bike": ("#fb923c", 5), "bus": ("#34d399", 11),
            "truck": ("#c084fc", 9), "ambulance": ("#ef4444", 15)}
DIR = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
GAP = 12.0

st.markdown("""
<style>
.block-container{padding-top:1.4rem;max-width:1500px}
.hero{background:linear-gradient(120deg,#0f172a 0%,#1e3a8a 55%,#0e7490 100%);padding:22px 28px;
      border-radius:16px;color:#fff;margin-bottom:14px}
.hero h1{margin:0;font-size:1.9rem;font-weight:800;letter-spacing:-.5px;color:#fff}
.hero p{margin:6px 0 0;color:#cbd5e1;font-size:.95rem}
.chip{display:inline-block;background:rgba(255,255,255,.14);border-radius:99px;padding:2px 12px;
      font-size:.75rem;margin:8px 6px 0 0;color:#e2e8f0}
.kpi{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;
     box-shadow:0 1px 2px rgba(15,23,42,.05)}
.kpi .l{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;font-weight:600}
.kpi .v{font-size:1.65rem;font-weight:800;color:#0f172a;line-height:1.25}
.kpi .s{font-size:.75rem;color:#64748b}
.kpi.good{border-left:5px solid #22c55e}.kpi.warn{border-left:5px solid #f59e0b}
.kpi.bad{border-left:5px solid #ef4444}.kpi.info{border-left:5px solid #3b82f6}
.banner{padding:10px 16px;border-radius:12px;font-weight:600;margin:6px 0}
.banner.emg{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
.banner.ok{background:#dcfce7;color:#166534;border:1px solid #86efac}
.sig{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------- helpers
def kpi(label, value, sub="", tone="info"):
    return (f'<div class="kpi {tone}"><div class="l">{label}</div>'
            f'<div class="v">{value}</div><div class="s">{sub}&nbsp;</div></div>')


def show_kpis(items):
    for col, it in zip(st.columns(len(items)), items):
        col.markdown(kpi(*it), unsafe_allow_html=True)


def clock(sim):
    s = int(sim.start_hour * 3600 + sim.t) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


@st.cache_resource(show_spinner="Training the traffic-prediction model (first run only)...")
def get_predictor():
    return QueuePredictor().fit()


def dark_layout(fig, h=340, title=None):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
                      title=title, legend=dict(orientation="h", y=-0.18),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ---------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("## 🚦 Smart Traffic AI")
    st.caption("CSE-A · Batch 10")
    page = st.radio("Navigate", ["📡 Live Control Center", "📊 Controller Benchmark", "👁️ Vision (YOLOv8)",
                                 "🔮 Traffic Prediction", "🚨 Violation Detection", "📄 About & Paper"],
                    label_visibility="collapsed")
    st.divider()
    st.markdown("**Network settings**")
    grid = st.selectbox("Road network", ["2 × 2 junctions", "3 × 3 junctions"])
    rows = cols = 2 if grid.startswith("2") else 3
    use_ml = st.toggle("Use ML queue forecast", True, help="Advanced controller uses the trained model")
    predictor = get_predictor() if use_ml else None

st.markdown("""
<div class="hero"><h1>AI-Based Smart Traffic Management</h1>
<p>Detect · Predict · Adapt · Coordinate — one pipeline from camera to signal head.</p>
<span class="chip">YOLOv8</span><span class="chip">Machine Learning</span><span class="chip">Computer Vision</span>
<span class="chip">Emergency Priority</span><span class="chip">Inter-Junction Communication</span>
<span class="chip">Violation Detection</span></div>
""", unsafe_allow_html=True)


def get_live():
    key = (rows, cols)
    if st.session_state.get("live_key") != key or "sim" not in st.session_state:
        st.session_state.sim = Sim(rows, cols, "advanced", 1.0, seed=7, predictor=predictor)
        st.session_state.live_key = key
    sim = st.session_state.sim
    sim.predictor = predictor
    return sim


# ------------------------------------------------------------------- map render
def draw_map(sim):
    R, C = sim.rows, sim.cols
    fig = go.Figure()
    ext = 7
    x0, x1, y0, y1 = -ext, (C - 1) * GAP + ext, -(R - 1) * GAP - ext, ext
    for r in range(R):
        y = -r * GAP
        fig.add_shape(type="line", x0=x0, x1=x1, y0=y, y1=y, line=dict(width=24, color="#1e293b"), layer="below")
        fig.add_shape(type="line", x0=x0, x1=x1, y0=y, y1=y, line=dict(width=1, color="#64748b", dash="dot"), layer="below")
    for c in range(C):
        x = c * GAP
        fig.add_shape(type="line", x0=x, x1=x, y0=y0, y1=y1, line=dict(width=24, color="#1e293b"), layer="below")
        fig.add_shape(type="line", x0=x, x1=x, y0=y0, y1=y1, line=dict(width=1, color="#64748b", dash="dot"), layer="below")

    def center(j):
        r, c = divmod(j, C)
        return c * GAP, -r * GAP

    buckets = {k: ([], []) for k in VT_STYLE}
    sx, sy, sc = [], [], []
    for j in range(sim.n):
        cx, cy = center(j)
        for a, name in enumerate(APPROACHES):
            dx, dy = DIR[name]
            px, py = -dy * 0.65, dx * 0.65
            green = sim.phase[j] == (0 if name in "NS" else 1)
            if green and sim.clear[j] == 0:
                col = "#22c55e"
            elif green and sim.clear[j] > 0:
                col = "#facc15"
            else:
                col = "#ef4444"
            sx.append(cx + dx * 1.9 + px)
            sy.append(cy + dy * 1.9 + py)
            sc.append(col)
            for i, v in enumerate(sim.q[j][a]):
                bx, by = buckets[v.vtype]
                bx.append(cx + dx * (2.6 + i * 0.27) + px)
                by.append(cy + dy * (2.6 + i * 0.27) + py)
    for arrivals in sim.transit.values():
        for v, nj, na, dep, src in arrivals:
            f = 0.12 + 0.76 * min(1.0, (sim.t - dep) / LINK_TIME)
            ax, ay = center(src)
            bx_, by_ = center(nj)
            ux, uy = bx_ - ax, by_ - ay
            n = max((ux ** 2 + uy ** 2) ** .5, 1e-6)
            bx, by = buckets[v.vtype]
            bx.append(ax + ux * f - uy / n * 0.65)
            by.append(ay + uy * f + ux / n * 0.65)
    for k, (xs, ys) in buckets.items():
        if not xs:
            continue
        colr, size = VT_STYLE[k]
        if k == "ambulance":
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", showlegend=False, hoverinfo="skip",
                                     marker=dict(size=34, color="rgba(239,68,68,.25)")))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=k.title(),
                                 marker=dict(size=size, color=colr, symbol="star" if k == "ambulance" else "square",
                                             line=dict(width=1, color="#0b1220"))))
    fig.add_trace(go.Scatter(x=sx, y=sy, mode="markers", name="Signal", showlegend=False, hoverinfo="skip",
                             marker=dict(size=12, color=sc, line=dict(width=2, color="#fff"))))
    lab_x, lab_y, lab_t = [], [], []
    for j in range(sim.n):
        cx, cy = center(j)
        pre = " ⚡" if sim._preempt_active[j] else ""
        lab_x.append(cx)
        lab_y.append(cy)
        lab_t.append(f"<b>J{j + 1}</b>{pre}<br>{'NS' if sim.phase[j] == 0 else 'EW'} {sim.timer[j]}s")
    fig.add_trace(go.Scatter(x=lab_x, y=lab_y, mode="text", text=lab_t, showlegend=False, hoverinfo="skip",
                             textfont=dict(color="#e2e8f0", size=11)))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="#0b1220", plot_bgcolor="#0b1220",
                      xaxis=dict(visible=False, range=[x0 - 1, x1 + 1]),
                      yaxis=dict(visible=False, scaleanchor="x", range=[y0 - 1, y1 + 1]),
                      legend=dict(orientation="h", y=0.01, x=0.01, font=dict(color="#cbd5e1")))
    return fig


def live_panel(sim, slot_map, slot_kpi, slot_chart, slot_tbl, tag=""):
    m = sim.summary()
    emg = list(sim.active_emg.values())
    with slot_kpi.container():
        show_kpis([
            ("Sim clock", clock(sim), f"demand ×{sim.demand * demand_profile(sim.hour()):.2f}", "info"),
            ("Vehicles in network", sim.in_network(), f"{int(sim.qtot[-1]) if sim.qtot else 0} queued", "info"),
            ("Avg delay / veh", f"{m['Avg delay / vehicle (s)']:.0f} s", "completed trips", "good"),
            ("Emergency delay", f"{m['Emergency delay (s)']:.1f} s", f"{m['Emergency served']} served · {len(emg)} active",
             "bad" if emg else "good"),
            ("Violations caught", m["Red-light violations"] + m["Wrong-way violations"], "red-light + wrong-way", "warn"),
        ])
        if emg and sim.controller in ("emergency", "advanced"):
            st.markdown('<div class="banner emg">🚨 Emergency vehicle detected (light-bar) — signals pre-empting'
                        + (" along the route (green wave)" if sim.controller == "advanced" else "") + "</div>",
                        unsafe_allow_html=True)
        elif emg:
            st.markdown('<div class="banner emg">🚨 Emergency vehicle in network — this controller ignores it</div>',
                        unsafe_allow_html=True)
    slot_map.plotly_chart(draw_map(sim), width="stretch", key=f"map{tag}{sim.t}")
    q = np.array(sim.qtot[-400:])
    f = go.Figure(go.Scatter(x=np.arange(len(q)) + max(0, sim.t - 400), y=q, fill="tozeroy",
                             line=dict(color="#3b82f6"), name="Queued vehicles"))
    slot_chart.plotly_chart(dark_layout(f, 230, "Vehicles queued (network total)"), width="stretch", key=f"ch{tag}{sim.t}")
    rows_ = []
    for j in range(sim.n):
        p = sim.pred[j]
        rows_.append({"Junction": f"J{j + 1}", "Green": PHASE_NAME[sim.phase[j]] + (" (clearing)" if sim.clear[j] else ""),
                      "Timer": sim.timer[j], "Queue N/E/S/W": "/".join(str(len(x)) for x in sim.q[j]),
                      "Forecast +30s": "/".join(str(int(round(x))) for x in p),
                      "Pre-empt": "⚡" if sim._preempt_active[j] else ""})
    slot_tbl.dataframe(pd.DataFrame(rows_), hide_index=True, width="stretch")


# ================================================================ LIVE CONTROL CENTER
if page.startswith("📡"):
    sim = get_live()
    c1, c2, c3 = st.columns([2.2, 1.4, 1])
    ctrl = c1.selectbox("Signal controller", list(CONTROLLERS), index=list(CONTROLLERS).index(sim.controller),
                        format_func=lambda k: CONTROLLERS[k])
    demand = c2.slider("Traffic demand", 0.4, 2.0, float(sim.demand), 0.1)
    emg_on = c3.toggle("Emergency vehicles", sim.emergencies)
    sim.controller, sim.demand, sim.emergencies = ctrl, demand, emg_on
    b1, b2, b3, b4 = st.columns(4)
    go_live = b1.button("▶ Run live (60 s)", type="primary", width="stretch")
    skip = b2.button("⏭ Skip 5 min", width="stretch")
    spawn = b3.button("🚑 Send ambulance", width="stretch")
    reset = b4.button("↺ Reset", width="stretch")
    if reset:
        st.session_state.pop("sim")
        st.rerun()
    if spawn:
        j, a = sim.entries[int(np.random.randint(len(sim.entries)))]
        v = sim._new_vehicle(emg=True)
        sim.q[j][a].append(v)
        sim.active_emg[v.id] = v
        sim.spawned += 1
    if skip:
        with st.spinner("Simulating 5 minutes..."):
            sim.run(300)
    left, right = st.columns([1.55, 1])
    slot_map = left.empty()
    slot_kpi_place = st.container()
    with right:
        slot_chart = st.empty()
        st.markdown("**Junction status**")
        slot_tbl = st.empty()
    slot_kpi = slot_kpi_place.empty()
    if go_live:
        for i in range(30):
            sim.run(2)
            live_panel(sim, slot_map, slot_kpi, slot_chart, slot_tbl, tag="L")
            time.sleep(0.1)
    live_panel(sim, slot_map, slot_kpi, slot_chart, slot_tbl, tag="S")
    st.caption("Signals: 🟢 green · 🟡 clearing · 🔴 red. Squares are vehicles (blue car, orange bike, green bus, "
               "purple truck). ⭐ ambulance. ⚡ marks a junction pre-empted for an emergency vehicle. "
               "Switch the controller while running to see the difference on the same traffic.")


# ================================================================ BENCHMARK
elif page.startswith("📊"):
    st.subheader("Controller benchmark — identical traffic, four strategies")
    st.caption("Replaces the base paper's SUMO system-level validation with a built-in Python simulator. "
               "Each controller faces exactly the same vehicles, emergency events and violators.")
    c1, c2, c3, c4 = st.columns(4)
    secs = c1.select_slider("Duration", [600, 900, 1200, 1800, 2700, 3600], 1800, format_func=lambda s: f"{s // 60} min")
    dem = c2.slider("Demand", 0.5, 1.8, 1.2, 0.1)
    nseeds = c3.slider("Random seeds", 1, 5, 3)
    start_h = c4.slider("Start hour", 0.0, 23.0, 8.0, 1.0)

    @st.cache_data(show_spinner=False)
    def bench(rows, cols, secs, dem, nseeds, start_h, ml, _p):
        out = {}
        for c in CONTROLLERS:
            sums, q, emg, viol = [], [], [], []
            for s in range(nseeds):
                sm = Sim(rows, cols, c, dem, seed=40 + s, start_hour=start_h, predictor=_p if ml else None).run(secs)
                sums.append(sm.summary())
                q.append(sm.qtot)
                emg += sm.emg_log
                viol += sm.viol_log
            out[c] = dict(sums=pd.DataFrame(sums), q=np.mean(q, axis=0), emg=emg, viol=viol)
        return out

    if st.button("▶ Run benchmark", type="primary") or "bench_done" in st.session_state:
        st.session_state["bench_done"] = True
        with st.spinner("Simulating 4 controllers..."):
            res = bench(rows, cols, secs, dem, nseeds, start_h, use_ml, predictor)
        st.session_state["bench"] = res
        mean = pd.DataFrame({CONTROLLERS[c]: r["sums"].mean() for c, r in res.items()}).T
        base, paper, ours = mean.iloc[0], mean.iloc[2], mean.iloc[3]
        d_fixed = 100 * (1 - ours["Avg delay / vehicle (s)"] / max(base["Avg delay / vehicle (s)"], 1e-9))
        d_paper = 100 * (1 - ours["Avg delay / vehicle (s)"] / max(paper["Avg delay / vehicle (s)"], 1e-9))
        e_fixed = 100 * (1 - ours["Emergency delay (s)"] / max(base["Emergency delay (s)"], 1e-9))
        fuel = base["Fuel wasted idling (L)"] - ours["Fuel wasted idling (L)"]
        show_kpis([
            ("Delay vs fixed-time", f"−{d_fixed:.0f}%", "advanced vs traditional", "good"),
            ("Delay vs base paper", f"{'−' if d_paper >= 0 else '+'}{abs(d_paper):.0f}%", "advanced vs emergency-aware", "good" if d_paper >= 0 else "warn"),
            ("Emergency delay", f"−{e_fixed:.0f}%", f"{ours['Emergency delay (s)']:.1f}s vs {base['Emergency delay (s)']:.1f}s", "good"),
            ("Fuel saved", f"{fuel:.1f} L", f"{fuel * 2.31:.1f} kg CO₂ avoided", "info"),
        ])
        st.write("")
        g1, g2 = st.columns(2)
        for col, metric in [(g1, "Avg delay / vehicle (s)"), (g2, "Emergency delay (s)")]:
            f = go.Figure()
            for c, r in res.items():
                s = r["sums"][metric]
                f.add_trace(go.Bar(x=[CONTROLLERS[c].split(" (")[0]], y=[s.mean()], name=CONTROLLERS[c],
                                   marker_color=CTRL_COLOR[c], error_y=dict(type="data", array=[s.std() if len(s) > 1 else 0]),
                                   text=[f"{s.mean():.1f}"], textposition="outside"))
            f.update_layout(showlegend=False)
            col.plotly_chart(dark_layout(f, 330, metric), width="stretch")
        g3, g4 = st.columns(2)
        f = go.Figure()
        for c, r in res.items():
            q = r["q"]
            k = 10
            q = q[: len(q) // k * k].reshape(-1, k).mean(1)
            f.add_trace(go.Scatter(x=np.arange(len(q)) * k / 60, y=q, name=CONTROLLERS[c].split(" (")[0],
                                   line=dict(color=CTRL_COLOR[c], width=3 if c == "advanced" else 1.8)))
        f.update_xaxes(title="minutes")
        g3.plotly_chart(dark_layout(f, 330, "Queued vehicles over time"), width="stretch")
        f = go.Figure()
        for c, r in res.items():
            e = pd.DataFrame(r["emg"])
            if len(e):
                f.add_trace(go.Box(y=e["delay"], name=CONTROLLERS[c].split(" (")[0], marker_color=CTRL_COLOR[c], boxmean=True))
        g4.plotly_chart(dark_layout(f, 330, "Emergency-vehicle delay distribution (s)"), width="stretch")
        st.markdown("**Full results (mean over seeds)**")
        st.dataframe(mean.round(2), width="stretch")

        st.markdown("#### Demand sweep — how each controller degrades as traffic grows")
        if st.button("Run demand sweep (≈15 s)"):
            levels = [0.6, 0.9, 1.2, 1.5, 1.8]
            f = go.Figure()
            prog = st.progress(0.0)
            for i, c in enumerate(CONTROLLERS):
                ys = [Sim(rows, cols, c, d, seed=5, predictor=predictor if c == "advanced" else None).run(1200)
                      .summary()["Avg delay / vehicle (s)"] for d in levels]
                f.add_trace(go.Scatter(x=levels, y=ys, name=CONTROLLERS[c].split(" (")[0], mode="lines+markers",
                                       line=dict(color=CTRL_COLOR[c])))
                prog.progress((i + 1) / 4)
            f.update_xaxes(title="demand multiplier")
            f.update_yaxes(title="avg delay (s)")
            st.plotly_chart(dark_layout(f, 340), width="stretch")
    else:
        st.info("Choose the settings and press **Run benchmark**.")


# ================================================================ VISION
elif page.startswith("👁️"):
    st.subheader("Vehicle detection, density and emergency light-bar recognition")
    yolo_ok = V.yolo_available()
    mode = st.radio("Input", ["Synthetic overhead scene (no files needed)", "YOLOv8 · sample photo",
                              "YOLOv8 · upload your own image"], horizontal=True)
    img, dets, bars, truth = None, [], [], None
    if mode.startswith("Synthetic"):
        c1, c2, c3, c4 = st.columns(4)
        n = c1.slider("Vehicles", 2, 16, 9)
        emg = c2.toggle("Ambulance present", True)
        flash = c3.radio("Flash frame", ["A", "B"], horizontal=True)
        seed = c4.number_input("Scene seed", 0, 999, 3)
        img, truth = V.render_scene(n, emg, 0 if flash == "A" else 1, int(seed))
        dets, bars = V.detect_classical(img)
    else:
        conf = st.slider("Confidence threshold", 0.1, 0.9, 0.3, 0.05)
        if not yolo_ok:
            st.error("`ultralytics` is not installed — run `pip install ultralytics`.")
        elif mode.startswith("YOLOv8 · sample"):
            p = V.sample_image_path()
            img = cv2.imread(p) if p else None
        else:
            up = st.file_uploader("Traffic camera image", type=["jpg", "jpeg", "png"])
            if up:
                img = cv2.imdecode(np.frombuffer(up.read(), np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            with st.spinner("Running YOLOv8..."):
                dets, bars = V.detect_yolo(img, conf)
    if img is not None:
        rep = V.density_report(dets)
        a, b = st.columns(2)
        a.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Camera frame", width="stretch")
        b.image(cv2.cvtColor(V.annotate(img, dets, bars), cv2.COLOR_BGR2RGB),
                caption="Detections (magenta ring = light-bar cluster)", width="stretch")
        tone = {"LOW": "good", "MEDIUM": "info", "HIGH": "warn", "JAMMED": "bad"}[rep["level"]]
        show_kpis([("Vehicles detected", len(dets), ", ".join(f"{n} {k}" for k, n in rep["counts"].items() if n) or "none", "info"),
                   ("Density (PCU)", f"{rep['pcu']:.1f}", f"{rep['ratio'] * 100:.0f}% of road capacity", tone),
                   ("Congestion level", rep["level"], "from PCU-weighted count", tone),
                   ("Emergency vehicle", "YES" if rep["emergency"] else "no",
                    "red+blue light-bar found" if rep["emergency"] else "no light-bar", "bad" if rep["emergency"] else "good"),
                   ("Recommended green", f"{rep['green']} s", "pre-empt" if rep["emergency"] else "density-based", "good")])
        if truth is not None:
            st.caption(f"Ground truth: {len(truth)} vehicles · detected: {len(dets)}. "
                       "Try flash frame B — the light-bar colours swap, and detection stays stable.")
        with st.expander("How it works"):
            st.markdown("""
1. **YOLOv8n** (COCO-pretrained) finds cars, motorbikes, buses and trucks; for synthetic frames a contour detector stands in.
2. **Light-bar detector** thresholds saturated *red* and *blue* in HSV and looks for touching blobs — the
   flashing signature of an emergency vehicle (the base paper's key idea). A detection whose light-bar sits on the
   roof region of a vehicle box is relabelled **ambulance**.
3. **Density** = sum of passenger-car-equivalents (bike 0.5, car 1, truck 2, bus 3) ÷ road capacity.
4. The recommended green time feeds the signal controller (emergency ⇒ pre-empt).
""")
    elif mode != "Synthetic overhead scene (no files needed)":
        st.info("Upload an image to begin.")


# ================================================================ PREDICTION
elif page.startswith("🔮"):
    st.subheader("Machine-learning traffic prediction (30 s ahead)")
    pred = get_predictor()
    show_kpis([("Training samples", f"{pred.n_samples:,}", "from simulated junction data", "info"),
               ("MAE (GBM)", f"{pred.metrics['Gradient Boosting (used)'][0]:.2f} veh", "mean absolute error", "good"),
               ("R² (GBM)", f"{pred.metrics['Gradient Boosting (used)'][1]:.3f}", "variance explained", "good"),
               ("vs persistence", f"−{100 * (1 - pred.metrics['Gradient Boosting (used)'][0] / pred.metrics['Persistence baseline'][0]):.0f}% error",
                "beats 'queue stays the same'", "good")])
    st.write("")
    a, b = st.columns(2)
    yte, yp = pred.test
    idx = np.random.default_rng(0).choice(len(yte), min(1500, len(yte)), replace=False)
    f = go.Figure(go.Scatter(x=yte[idx], y=yp[idx], mode="markers", marker=dict(size=5, color="#3b82f6", opacity=.45)))
    f.add_shape(type="line", x0=0, y0=0, x1=yte.max(), y1=yte.max(), line=dict(color="#ef4444", dash="dash"))
    f.update_xaxes(title="actual queue in 30 s")
    f.update_yaxes(title="predicted")
    a.plotly_chart(dark_layout(f, 340, "Predicted vs actual (held-out test set)"), width="stretch")
    imp = pd.Series(pred.importance).sort_values()
    b.plotly_chart(dark_layout(go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h", marker_color="#22c55e")), 340,
                               "What the model relies on"), width="stretch")
    st.markdown("**Model comparison**")
    st.dataframe(pd.DataFrame(pred.metrics, index=["MAE (veh)", "R²"]).T.round(3), width="stretch")
    st.markdown("#### Live forecast for the running simulation")
    sim = get_live()
    if sim.t < 40:
        st.info("Run the live simulation for a minute on **Live Control Center** to see forecasts.")
        if st.button("Simulate 3 minutes now"):
            sim.run(180)
            st.rerun()
    else:
        F = sim.feature_matrix()
        P = pred.predict(F).reshape(sim.n, 4)
        Q = F[:, 0].reshape(sim.n, 4)
        f = go.Figure()
        labels = [f"J{j + 1}-{a_}" for j in range(sim.n) for a_ in APPROACHES]
        f.add_trace(go.Bar(x=labels, y=Q.reshape(-1), name="Queue now", marker_color="#94a3b8"))
        f.add_trace(go.Bar(x=labels, y=P.reshape(-1), name="Forecast +30 s", marker_color="#f97316"))
        f.update_layout(barmode="group")
        st.plotly_chart(dark_layout(f, 340, f"Queue per approach at {clock(sim)}"), width="stretch")
        worst = np.unravel_index(np.argmax(P - Q), P.shape)
        st.warning(f"Highest predicted build-up: **J{worst[0] + 1} · {APPROACHES[worst[1]]}** approach "
                   f"({Q[worst]:.0f} → {P[worst]:.0f} vehicles). The advanced controller gives it green proactively.")


# ================================================================ VIOLATIONS
elif page.startswith("🚨"):
    st.subheader("Traffic-violation detection")
    sim = get_live()
    c1, c2 = st.columns([1, 3])
    if c1.button("Simulate 10 more minutes", type="primary"):
        with st.spinner("Simulating..."):
            sim.run(600)
    log = pd.DataFrame(sim.viol_log)
    if log.empty:
        st.info("No violations logged yet. Simulate a few minutes (demand ≥ 1.0 works best).")
    else:
        log["time"] = log["t"].map(lambda t: f"{int(sim.start_hour * 3600 + t) // 3600 % 24:02d}:{int(sim.start_hour * 3600 + t) % 3600 // 60:02d}:{t % 60:02d}")
        log["junction"] = log["junction"].map(lambda j: f"J{j + 1}")
        red, wrong = (log.kind == "Red-light jumping").sum(), (log.kind == "Wrong-way driving").sum()
        show_kpis([("Total violations", len(log), f"in {sim.t // 60} simulated minutes", "warn"),
                   ("Red-light jumping", red, "vehicle crosses stop line on red", "bad"),
                   ("Wrong-way driving", wrong, "enters against traffic flow", "bad"),
                   ("Avg confidence", f"{log.confidence.mean():.2f}", "detector score", "info")])
        st.write("")
        a, b = st.columns(2)
        by = log.groupby(["junction", "kind"]).size().reset_index(name="n")
        f = go.Figure()
        for k, col in [("Red-light jumping", "#ef4444"), ("Wrong-way driving", "#f59e0b")]:
            d = by[by.kind == k]
            f.add_trace(go.Bar(x=d.junction, y=d.n, name=k, marker_color=col))
        f.update_layout(barmode="stack")
        a.plotly_chart(dark_layout(f, 300, "Violations by junction"), width="stretch")
        per = log.assign(m=log.t // 60).groupby("m").size()
        b.plotly_chart(dark_layout(go.Figure(go.Bar(x=per.index, y=per.values, marker_color="#3b82f6")), 300,
                                   "Violations per simulated minute"), width="stretch")
        st.markdown("**Evidence log**")
        st.dataframe(log[["time", "junction", "approach", "kind", "plate", "vehicle", "confidence"]].iloc[::-1],
                     hide_index=True, width="stretch")
    st.caption("Red-light jumping happens when a red-runner has waited ≥ 25 s — so controllers that cut waiting "
               "time also reduce violations (compare on the Benchmark page). Wrong-way drivers are flagged at entry roads.")
    bench_res = st.session_state.get("bench")
    if bench_res:
        st.markdown("**Violations by controller (last benchmark)**")
        st.dataframe(pd.DataFrame({CONTROLLERS[c]: r["sums"][["Red-light violations", "Wrong-way violations"]].mean()
                                   for c, r in bench_res.items()}).T.round(1), width="stretch")


# ================================================================ ABOUT
else:
    st.subheader("About the project and the base paper")
    st.markdown("""
**Base paper** — *Emergency-Aware Adaptive Traffic Signal Control Using YOLO-Based Light-Bar Detection and SUMO
System-Level Validation*, **IEEE Access, 2026** · DOI [10.1109/access.2026.3710015](https://doi.org/10.1109/access.2026.3710015)

The surveyed systems do adaptive signal control **or** vehicle detection separately. The gap this project closes is
**one pipeline** that detects, adapts timing, prioritises emergency vehicles and coordinates between junctions.
""")
    st.markdown("#### What is adopted vs. what is advanced")
    st.dataframe(pd.DataFrame([
        ["YOLO vehicle detection", "YOLO-based light-bar detection", "YOLOv8n + HSV light-bar detector + PCU density (Vision page)"],
        ["Emergency-aware adaptive control", "Pre-emption at one junction", "Route-wide green wave via 15 s upstream look-ahead"],
        ["SUMO system-level validation", "Sumo scenarios", "Built-in pure-Python network simulator, 4 controllers on identical traffic"],
        ["— (abstract extension)", "—", "ML queue forecasting (gradient boosting, 30 s ahead)"],
        ["— (abstract extension)", "—", "Inter-junction communication: platoon look-ahead + spill-back avoidance"],
        ["— (abstract extension)", "—", "Red-light and wrong-way violation detection with evidence log"],
        ["— (advanced)", "—", "PCU-weighted pressure, fairness term, fuel/CO₂ estimates, live control centre"],
    ], columns=["Capability", "Base paper", "This implementation"]), hide_index=True, width="stretch")
    st.markdown("#### System pipeline")
    st.graphviz_chart("""
digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#e0f2fe", fontname="Helvetica"];
 Cam[label="Camera frame"]; Y[label="YOLOv8\\nvehicle detection"]; L[label="Light-bar\\nemergency detector"];
 D[label="Density (PCU)"]; P[label="ML queue\\nforecast"]; C[label="Signal controller\\n(pressure + pre-emption)", fillcolor="#dcfce7"];
 N[label="Neighbour junctions\\n(green wave, spill-back)", fillcolor="#fef9c3"]; Vio[label="Violation\\ndetector", fillcolor="#fee2e2"];
 Cam->Y->D->C; Cam->L->C; D->P->C; C->N; N->C; Y->Vio; }
""")
    st.markdown("#### Controllers")
    for k, v in CONTROLLERS.items():
        st.markdown(f"- **{v}** (`{k}`)")
    st.markdown("""
#### Run it
```
pip install streamlit plotly pandas scikit-learn opencv-python ultralytics
streamlit run app.py
```
""")
    st.caption("Vehicle speeds and flows are modelled at queue level (mesoscopic), calibrated to typical saturation flow "
               "(1800 veh/h/lane), 12 s links, 3 s clearance and 2 s start-up lost time.")
