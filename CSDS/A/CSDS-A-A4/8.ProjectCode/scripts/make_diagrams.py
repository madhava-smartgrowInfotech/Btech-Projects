"""Generate the HubOptima design diagrams (PNG, 150 dpi) into docs/diagrams/.

    python scripts/make_diagrams.py

Every diagram is drawn from the real design: the `hublocator` package (data, forecast, model, matheuristic,
baselines, rolling), the FastAPI layer in backend/main.py and the React pages in frontend/src. matplotlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import (AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, LINE, ROSE_L, Canvas, anchor)  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"


# ------------------------------------------------------------------------------------------------ 1 architecture
def architecture(out):
    c = Canvas(10.4, 8.6)
    c.zone(2, 73, 100, 11, "User and browser", fc="#f4f5fb")
    c.box(6, 74.4, 44, 6, "Logistics planner (web browser)\nlanding, dashboard, forecast, plan, compare, re-optimise, regions", fc="white", fs=7.2)
    c.box(54, 74.4, 44, 6, "Developer / analyst (command line)\npython run.py data | forecast | optimize | compare | rolling | benchmark", fc="white", fs=7.2)

    c.zone(2, 57, 100, 13, "Frontend: React 18 + Vite 5   (port 5104; proxies /api to 8104)", fc="#eef4fe")
    fe = ["Pages\nreact-router: Landing, Dashboard,\nForecast, Plan, Compare,\nRolling, Regions", "Visual components\nNetworkMap (SVG), Recharts,\ntables, stat tiles", "Motion and theme\nframer-motion, gsap, light /\ndark theme (remembered)", "Data layer\nlib/api.js, useApi / usePoll\n(polls background jobs)"]
    for i, t in enumerate(fe):
        c.box(5 + i * 24.2, 58.4, 22.8, 8.0, t, fc="white", fs=6.6)
    c.arrow((28, 73), (28, 70), both=True)

    c.zone(2, 38, 100, 15, "API layer: FastAPI 0.110 + uvicorn   (port 8104)   -   backend/main.py", fc="#eef8f2")
    c.box(5, 44.4, 94, 4.2, "14 endpoints: GET health, summary, regions, options, forecast, forecast/metrics, compare, scalability, rolling, jobs  -  POST train, optimize, compare/run, rolling/run", fc=INDIGO_L, ec=INDIGO, fs=6.6, bold=True)
    c.box(5, 39.4, 30, 4.2, "Validation: pydantic bodies\n(p 1-20, SLA > 0, limits)", fc="white", fs=6.6)
    c.box(37, 39.4, 30, 4.2, "Job manager: thread + lock\n(compare, rolling, train)", fc="white", fs=6.6)
    c.box(69, 39.4, 30, 4.2, "Serialiser: NaN/inf -> null\nCORS limited to :5104", fc="white", fs=6.6)
    c.arrow((52, 57), (52, 53), label="HTTP / JSON", both=True, loff=(8, 0))

    c.zone(2, 19, 100, 16, "Core package: hublocator (pure Python)", fc="#f3fbf6")
    mods = [("data.py", "generate, clean,\nhaversine x1.25"), ("forecast.py", "19 features,\nRandom Forest"), ("model.py", "Instance, exact MIP,\nKPI evaluation"),
            ("matheuristic.py", "construct, local\nsearch, kernel"), ("baselines.py", "greedy, k-means,\nlargest, compare"), ("rolling.py", "rolling horizon,\nscalability")]
    for i, (n, t) in enumerate(mods):
        x = 4.5 + i * 15.8
        c.box(x, 20.5, 14.6, 10.6, "", fc="white")
        c.text(x + 7.3, 28.6, n, fs=7.2, bold=True)
        c.text(x + 7.3, 23.9, t, fs=6.5)
    c.arrow((52, 38), (52, 35), both=True)
    c.path([(98, 77.4), (101.6, 77.4), (101.6, 26), (98.3, 26)], ls=":", lw=1.1)
    c.text(88, 71.5, "CLI: direct calls into the core package (dotted)", fs=6.4, italic=True)

    c.zone(2, 1, 100, 15, "Libraries, solver and storage", fc="#fff8e8")
    c.box(5, 2.4, 22, 8.0, "scikit-learn 1.4\nRandomForestRegressor (400 trees)\nKMeans baseline", fc="white", fs=6.5)
    c.box(29, 2.4, 22, 8.0, "PuLP 3.3 + CBC\nexact MIP and the\nassignment sub-MIPs", fc="white", fs=6.5)
    c.box(53, 2.4, 22, 8.0, "data/\nregions.csv (90 rows)\ndemand_history.csv (3,240)", fc="white", fs=6.5)
    c.box(77, 2.4, 22, 8.0, "models/ + results/\nrf_demand.joblib, metrics,\ncomparison, rolling, scalability", fc="white", fs=6.5)
    for x in (16, 40, 64, 88):
        c.arrow((x, 19), (x, 10.4), both=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 2 workflow
def workflow(out):
    c = Canvas(10.4, 5.6)
    steps = [("1  Load data", "regions.csv and\ndemand_history.csv", BLUE_L), ("2  Preprocess", "de-duplicate, interpolate\ngaps, 36 months x 90\nregions", BLUE_L),
             ("3  Build features", "lags 1-12, rolling mean\nand std, season, promo,\nregion attributes", INDIGO_L), ("4  Train forecaster", "Random Forest, 400 trees;\ntrain to 2025-06,\ntest 2025-07..12", INDIGO_L),
             ("5  Forecast demand", "next month per region\nfrom lag features only", INDIGO_L)]
    steps2 = [("6  Build hub model", "distance x1.25, time,\nunit cost, fixed cost\nby tier, capacity", GREEN_L), ("7  Solve", "matheuristic or exact\nMIP (CBC): hubs +\nallocation", GREEN_L),
              ("8  Evaluate", "KPIs scored on realised\ndemand: cost, delivery\ntime, fulfilment", AMBER_L), ("9  Compare + re-plan", "baselines, scalability,\nmonthly rolling horizon", AMBER_L),
              ("10  Present", "FastAPI JSON, React\nscreens, network map", ROSE_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 31, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps)]
    row2 = [c.box(x, 8, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps2)]
    for b, (h, t, _) in zip(row1 + row2, steps + steps2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.0, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.8)
    for r in (row1, row2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    c.path([anchor(row1[-1], "b"), (xs[-1] + bw / 2, 27), (xs[0] + bw / 2, 27), anchor(row2[0], "t")], seg=1, label="forecast demand", loff=(0, 1.8))
    c.path([anchor(row2[-1], "b"), (xs[-1] + bw / 2, 3.2), (xs[0] + bw / 2, 3.2), (xs[0] + bw / 2, 8)], label="new month of data: re-forecast, rebuild and re-optimise", seg=1, loff=(0, 1.8), ls="--")
    c.text(52, 52.5, "HubOptima: predict-then-optimise workflow", fs=11, bold=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 3 DFD0
def dfd0(out):
    c = Canvas(10.4, 4.4)
    c.ellipse(52, 22, 30, 22, "0\nHubOptima\npredict-then-optimise\nhub planning system", fc=INDIGO_L, fs=8.4)
    c.box(2, 16, 22, 14, "Logistics planner\n(web user)", fc=GREEN_L, bold=True, fs=8)
    c.box(2, 1.5, 22, 8, "Data files\n(CSV: regions and order history)", fc=AMBER_L, bold=True, fs=7)
    c.box(80, 16, 22, 14, "CBC solver\n(via PuLP)", fc=BLUE_L, bold=True, fs=8)
    c.arrow((24, 26.5), (38.0, 26.5), label="month, p, costs, SLA, method", loff=(0, 2.0), fs=6.4)
    c.arrow((37.8, 19), (24, 19), label="forecast, hub plan, KPIs, comparison, rolling", loff=(0, -2.2), fs=6.2, color=INDIGO)
    c.arrow((24, 5.5), (41, 13.3), label="demand history,\nregion master", loff=(-1, -2.5), fs=6.3)
    c.arrow((66.5, 26.5), (80, 26.5), label="MIP sub-problems", loff=(0, 2.0), fs=6.4)
    c.arrow((80, 19), (66.5, 19), label="optimal / feasible\nassignments", loff=(0, -3.2), fs=6.3)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 4 DFD1
def dfd1(out):
    c = Canvas(10.4, 7.8)
    c.text(52, 75, "DFD level 1: HubOptima", fs=11, bold=True)

    def proc(cx, cy, text):
        c.ellipse(cx, cy, 20, 10.5, text, fc=INDIGO_L, fs=6.8)

    def store(x, y, w, text, h=5.4):
        return c.box(x, y, w, h, text, fc=AMBER_L, fs=6.5, r=0.8)
    c.box(1, 33, 13, 10, "Planner", fc=GREEN_L, bold=True, fs=8)
    proc(30, 55, "1\nLoad and preprocess\ndata"); proc(58, 55, "2\nTrain forecaster\n(Random Forest)"); proc(86, 55, "3\nForecast next-\nmonth demand")
    proc(86, 35, "4\nBuild hub-location\ninstance"); proc(58, 35, "5\nSolve: matheuristic\nor exact MIP"); proc(30, 35, "6\nEvaluate KPIs on\nrealised demand")
    proc(30, 15, "9\nPresent results\n(API + UI)"); proc(58, 15, "7\nCompare methods,\nscalability"); proc(86, 15, "8\nRolling re-\noptimisation")
    store(13, 66, 16, "D1  regions.csv"); store(31, 66, 20, "D2  demand_history.csv"); store(56, 66, 28, "D3  rf_demand.joblib + metrics")
    store(40, 1, 46, "D4  results/*.json  (comparison, rolling, scalability)")
    c.arrow((21, 66), (27, 60.2), fs=6.2); c.arrow((41, 66), (34, 60.2), fs=6.2)
    c.arrow((40, 55), (48, 55), label="features", loff=(0, 2.0), fs=6.2)
    c.arrow((60, 60.2), (64, 66), fs=6.2)
    c.arrow((82, 66), (87, 60.2), fs=6.2, ls=":", label="model", loff=(5, 1.5))
    c.path([(30, 49.8), (30, 47), (80, 47), (80, 50.2)], label="history (lag features)", seg=1, loff=(-8, 1.6), fs=6.2)
    c.arrow((86, 49.8), (86, 40.3), label="forecast", loff=(4.5, 0), fs=6.2)
    c.arrow((76, 35), (68, 35), label="instance", loff=(0, 2.0), fs=6.2)
    c.arrow((48, 35), (40, 35), label="hubs + allocation", loff=(0, 2.0), fs=6.2)
    c.arrow((30, 29.8), (30, 20.2), label="KPIs", loff=(3, 0), fs=6.2)
    c.arrow((58, 20.2), (58, 29.8), ls="--", label="re-run 3-6\nper method", loff=(5.5, 0), fs=6.0)
    c.arrow((86, 20.2), (86, 29.8), ls="--", label="re-run 3-6\nper month", loff=(5.5, 0), fs=6.0)
    c.arrow((58, 9.8), (58, 6.4), fs=6.2); c.arrow((84, 9.8), (78, 6.4), fs=6.2)
    c.arrow((44, 4), (30, 9.8), fs=6.2, ls=":", label="read", loff=(-4.5, 0.5))
    c.path([(7.5, 43), (7.5, 44.5), (99, 44.5), (99, 35), (96, 35)], label="month, p, costs, SLA, method", seg=1, loff=(-12, 1.6), fs=6.3)
    c.path([(20, 15), (7.5, 15), (7.5, 33)], label="screens, tables, charts", seg=0, loff=(0, 1.8), fs=6.3)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 5 DFD2
def dfd2(out):
    c = Canvas(10.4, 7.6)
    c.text(52, 73, "DFD level 2: expansion of process 5, solve hub location (matheuristic)", fs=10.5, bold=True)

    def proc(cx, cy, text):
        c.ellipse(cx, cy, 22, 11, text, fc=INDIGO_L, fs=6.8)
    proc(18, 54, "5.1\nConstruct start set\n(greedy + medoids)"); proc(52, 54, "5.2\nGenerate swap / drop /\nadd moves"); proc(86, 54, "5.3\nScreen with cheap\ngreedy bound (6%)")
    proc(18, 30, "5.6\nKernel search: MIP\nover <= 24 candidates"); proc(52, 30, "5.5\nAccept first\nimproving move"); proc(86, 30, "5.4\nPrice move: exact\nassignment MIP")
    proc(18, 9, "5.7\nReturn hubs, allocation,\nlog, seconds")
    c.box(3, 65, 30, 4.6, "Instance (from process 4)", fc=AMBER_L, fs=6.8, r=0.8)
    c.box(40, 8, 26, 4.6, "Sub-problem cache", fc=AMBER_L, fs=6.8, r=0.8)
    c.box(72, 8, 28, 4.6, "CBC via PuLP", fc=BLUE_L, fs=6.8, r=0.8)
    c.arrow((18, 65), (18, 59.5), fs=6.2)
    c.arrow((29, 54), (41, 54), label="hub set", loff=(0, 2.0), fs=6.2)
    c.arrow((63, 54), (75, 54), label="move list", loff=(0, 2.0), fs=6.2)
    c.arrow((86, 48.5), (86, 35.5), label="promising moves", loff=(7.5, 0), fs=6.2)
    c.arrow((75, 30), (63, 30), label="cost, assignment", loff=(0, 2.0), fs=6.2)
    c.arrow((52, 35.5), (52, 48.5), ls="--", label="improved:\nrestart", loff=(-5.5, 0), fs=6.1)
    c.arrow((41, 30), (29, 30), label="no better move\nor 70% of time", loff=(0, 3.3), fs=6.0)
    c.arrow((18, 24.5), (18, 14.5), label="best plan", loff=(4.5, 0), fs=6.2)
    c.arrow((86, 24.5), (86, 12.6), both=True, label="sub-MIPs / optimal\nassignments", loff=(-9.5, -1), fs=6.0)
    c.arrow((81, 24.9), (60, 12.6), ls=":", label="store / reuse", loff=(5, 2.6), fs=6.0)
    c.text(52, 2.2, "Process 5.4 solves the allocation of all 90 regions to a FIXED hub set exactly; process 5.6 solves the full MIP restricted to promising candidate hubs.", fs=6.6, italic=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 6 ER (file data model)
def entity(c, x, y, w, title, fields, fc=BLUE_L, row=2.55):
    h = 3.4 + row * len(fields)
    c.box(x, y, w, h, "", fc="white", r=0.8)
    c.box(x, y + h - 3.4, w, 3.4, title, fc=fc, bold=True, fs=7.0, r=0.8)
    for i, f in enumerate(fields):
        c.text(x + 1.2, y + h - 3.4 - row * (i + 0.5), f, fs=6.2, ha="left")
    return {"x": x, "y": y, "w": w, "h": h}


def er(out):
    c = Canvas(10.4, 7.6)
    c.text(52, 74, "Entity-relationship diagram (file-based data model: CSV, joblib and JSON files; no RDBMS)", fs=8.6, bold=True)
    entity(c, 3, 40, 26, "REGION  (data/regions.csv)", ["PK region_id", "city", "state", "lat, lon", "population", "tier  (1, 2, 3)", "parent", "penetration"], BLUE_L)
    entity(c, 36, 44, 30, "DEMAND_HISTORY  (demand_history.csv)", ["PK,FK region_id", "PK period  (YYYY-MM)", "year, month", "orders", "promo", "avg_order_value", "avg_parcel_weight_kg", "return_rate"], BLUE_L)
    entity(c, 73, 52, 28, "FORECAST_MODEL  (models/)", ["rf_demand.joblib: model, features", "forecast_metrics.json:", "  trained_at, train/test rows", "  random_forest, baselines", "  feature_importance", "  last_period_detail"], GREEN_L)
    entity(c, 36, 18, 30, "FORECAST  (derived, not stored)", ["FK region_id", "period  (next month)", "forecast  (orders)"], GREEN_L)
    entity(c, 3, 6, 30, "METHOD_RESULT  (comparison.json)", ["PK method  (6 methods)", "label, status, seconds", "hubs[], hub_cities[]", "total_cost: fixed, transport, time", "avg_delivery_hours, fulfilment", "reliability_sla, overloaded_hubs", "utilisation{}"], AMBER_L)
    entity(c, 40, 3, 28, "ASSIGNMENT  (inside each result)", ["FK region_id  (served region)", "hub  (serving hub city)", "demand", "distance_km, hours"], AMBER_L)
    entity(c, 73, 28, 28, "ROLLING_MONTH  (rolling.json)", ["PK period", "forecast_total, realized_total", "hubs[], opened[], closed[]", "adaptive{ cost, fulfilment }", "static{ cost, fulfilment }"], AMBER_L)
    entity(c, 73, 6, 28, "SCALABILITY_RUN  (scalability.json)", ["PK nodes", "binary_vars", "matheuristic_seconds", "exact_seconds, exact_status", "matheuristic_gap_pct"], AMBER_L)
    c.arrow((29, 52), (36, 52), head=False)
    c.text(30.6, 53.7, "1", fs=7); c.text(34.6, 53.7, "N", fs=7)
    c.path([(16, 40), (16, 33), (34, 33), (34, 26), (36, 26)], head=False)
    c.text(17.6, 38.2, "1", fs=7); c.text(32.6, 27.7, "N", fs=7)
    c.arrow((66, 60), (73, 60), label="trains", loff=(0, 1.9), fs=6.4)
    c.path([(73, 56), (69, 56), (69, 27), (66, 27)], label="predicts", seg=1, loff=(-0.5, 1.5), fs=6.4)
    c.arrow((33, 12), (40, 12), head=False)
    c.text(34.6, 13.7, "1", fs=7); c.text(38.6, 13.7, "N", fs=7)
    c.text(52, 36.5, "result files are derived from FORECAST by the optimiser;\nthey hold no foreign keys other than region names", fs=6.4, italic=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 7 UML
def nlines(items):
    return sum(i.count("\n") + 1 for i in items)


def klass(c, x, ytop, w, title, attrs, ops, fc=BLUE_L, stereo=None, row=2.0):
    h = 3.6 + row * (nlines(attrs) + nlines(ops)) + (1.4 if attrs and ops else 1.0)
    y = ytop - h
    c.box(x, y, w, h, "", fc="white", r=0.6)
    c.box(x, ytop - 3.6, w, 3.6, ("<<" + stereo + ">>\n" if stereo else "") + title, fc=fc, bold=True, fs=6.6, r=0.6)
    yy = ytop - 3.6 - 0.4
    for a in attrs:
        n = a.count("\n") + 1
        c.text(x + 1, yy - row * n / 2, a, fs=5.8, ha="left"); yy -= row * n
    if attrs and ops:
        c.line((x, yy - 0.3), (x + w, yy - 0.3), lw=0.8)
        yy -= 0.6
    for o in ops:
        n = o.count("\n") + 1
        c.text(x + 1, yy - row * n / 2, o, fs=5.8, ha="left"); yy -= row * n
    return {"x": x, "y": y, "w": w, "h": h}


def uml(out):
    c = Canvas(10.4, 9.6)
    c.text(52, 94.5, "UML class diagram: core types and modules of HubOptima", fs=10, bold=True)
    X1, X2, X3, W = 2, 36, 70, 31
    rf = klass(c, X1, 91, W, "RandomForestRegressor", ["n_estimators = 400", "min_samples_leaf = 2", "max_features = 0.6"], ["fit(X, y)", "predict(X)"], GREY_L, "scikit-learn")
    fo = klass(c, X1, rf["y"] - 5, W, "forecast.py", ["FEATURES: 19 names"], ["build_features(regions, demand)", "train_forecaster(regions, demand,\n   test_months=6) -> metrics", "forecast_next_period(...)", "forecast_for_period(..., period)"], GREEN_L, "module")
    da = klass(c, X1, fo["y"] - 5, W, "data.py", ["CITIES: 30 tuples"], ["generate_dataset(n_months, seed)", "load_dataset() -> regions, demand", "distance_matrix(regions)", "dataset_summary(regions, demand)"], GREEN_L, "module")
    cf = klass(c, X2, 91, W - 1, "config.py", ["DEFAULTS: n_hubs=6, capacity=1.25,", "  transport 0.04, fixed 2.5 M,", "  penalty 1.5, speed 45, SLA 48", "RANDOM_STATE = 42"], [], AMBER_L, "module")
    ins = klass(c, X2, cf["y"] - 5, W - 1, "Instance  (model.py)", ["regions: DataFrame", "demand: ndarray", "dist: ndarray (n x n)", "params: dict", "time, unit_cost, fixed_cost", "capacity, p, n"],
                ["from_forecast(regions, forecast,\n   **params)", "objective(hubs, assign, demand)"], INDIGO_L, "dataclass")
    mo = klass(c, X2, ins["y"] - 5, W - 1, "model.py (functions)", [], ["solve_exact(inst, time_limit,\n   candidates)", "assign_exact(inst, hubs)", "assign_greedy(inst, hubs)", "evaluate_solution(inst, hubs,\n   assign, realized) -> KPI dict"], GREEN_L, "module")
    ro = klass(c, X2, mo["y"] - 5, W - 1, "rolling.py", [], ["rolling_reoptimisation(regions,\n   demand, n_months)", "scalability_benchmark(regions,\n   demand_vec, factors)", "inflate_network(regions, d, k)"], GREEN_L, "module")
    ap = klass(c, X3, 91, W, "FastAPI app  (backend/main.py)", ["jobs: compare, rolling, train", "bodies: OptimizeBody, CompareBody,", "  RollingBody (pydantic)"], ["api_optimize(body)", "compare_run(body)", "rolling_run(body)", "start_job(name, kind, fn)"], BLUE_L, "service")
    mh = klass(c, X3, ap["y"] - 8, W, "matheuristic.py", [], ["construct(inst) -> hubs", "solve_matheuristic(inst,\n   time_limit, kernel_size,\n   screen_tol) -> solution", "_bound / _price (cached)"], GREEN_L, "module")
    bl = klass(c, X3, mh["y"] - 8, W, "baselines.py", [], ["solve_greedy(inst)", "solve_kmeans(inst)", "solve_largest_markets(inst)", "run_comparison(regions, forecast,\n   realized, hist_avg) -> summary"], GREEN_L, "module")
    c.arrow((17.5, rf["y"]), (17.5, fo["y"] + fo["h"]), label="owns", loff=(3, 0), fs=6, head=True)
    c.arrow((17.5, da["y"] + da["h"]), (17.5, fo["y"]), label="reads", loff=(3, 0), fs=6, ls="--")
    c.arrow((X1 + W, fo["y"] + fo["h"] - 14), (X2, ins["y"] + ins["h"] - 14), ls="--")
    c.arrow((51, ro["y"] + ro["h"]), (51, mo["y"]), label="uses", loff=(3, 0), fs=6, ls="--")
    c.arrow((51, cf["y"]), (51, ins["y"] + ins["h"]), label="defaults", loff=(4, 0), fs=6, ls="--")
    c.arrow((51, ins["y"]), (51, mo["y"] + mo["h"]), label="solved / scored by", loff=(8, 0), fs=6)
    c.arrow((X3, mh["y"] + mh["h"] - 6), (X2 + W - 1, ins["y"] + 9), label="uses", loff=(0, 2), fs=6, ls="--")
    c.arrow((X3 + 15, bl["y"] + bl["h"]), (X3 + 15, mh["y"]), label="calls construct", loff=(8.5, 0), fs=6, ls="--")
    c.arrow((X3, bl["y"] + bl["h"] - 6), (X2 + W - 1, mo["y"] + mo["h"] - 8), label="uses", loff=(0, 2), fs=6, ls="--")
    c.arrow((X3 + 15, ap["y"]), (X3 + 15, mh["y"] + mh["h"]), label="calls", loff=(4, 0), fs=6, ls="--")
    c.text(X3 + 15.5, 8.5, "FastAPI also calls forecast.py,\nbaselines.py, rolling.py and data.py", fs=6, italic=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 8 use case
def usecase(out):
    c = Canvas(10.4, 7.6)
    c.rect(24, 2, 56, 71, fc="#fafbfe", ec="#8a94b0", ls="--")
    c.text(52, 70.6, "HubOptima", fs=10, bold=True)

    def actor(x, y, label):
        c.ax.plot([x], [y + 8.5], "o", ms=7, mfc="white", mec=INK, mew=1.3)
        c.line((x, y + 7.2), (x, y + 3)); c.line((x - 2.8, y + 5.6), (x + 2.8, y + 5.6))
        c.line((x, y + 3), (x - 2.4, y)); c.line((x, y + 3), (x + 2.4, y))
        c.text(x, y - 2.6, label, fs=7.3, bold=True)
    actor(11, 40, "Logistics\nplanner (web)")
    actor(11, 9, "Developer /\nanalyst (CLI)")
    actor(93, 38, "CBC solver\n(system)")
    ucs = [("dash", 65, "View dashboard"), ("reg", 58.2, "Browse the 90 demand regions"), ("fc", 51.4, "View the demand forecast"), ("train", 44.6, "Retrain the Random Forest"),
           ("plan", 37.8, "Plan hubs for a month\n(set parameters, choose method)"), ("cmp", 30.6, "Compare methods and run\nscalability benchmark"), ("roll", 23.4, "Re-optimise month by month\n(rolling horizon)"),
           ("gen", 16.2, "Regenerate data, run CLI commands"), ("theme", 9.6, "Switch light / dark theme"), ("api", 3.9, "Call the JSON API directly (/docs)")]
    pos = {}
    for k, y, t in ucs:
        c.ellipse(52, y, 34, 5.4, t, fc=INDIGO_L, fs=6.8)
        pos[k] = y
    for k in ("dash", "reg", "fc", "train", "plan", "cmp", "roll", "theme"):
        c.line((14, 46), (35, pos[k]), lw=0.8)
    for k in ("train", "plan", "cmp", "roll", "gen"):
        c.line((14, 15), (35, pos[k]), lw=0.8)
    c.line((14, 15), (35.5, pos["api"]), lw=0.8)
    for k in ("plan", "cmp", "roll"):
        c.line((90, 41), (69, pos[k]), lw=0.8, ls="--")
    c.text(86, 31, "<<uses>>", fs=6.5, italic=True)
    c.text(52, 0.4, "Single user role: there is no sign-in and no administrator account.", fs=6.8, italic=True)
    c.save(out)


# ------------------------------------------------------------------------------------------------ 9 sequence
def sequence(out):
    c = Canvas(10.4, 7.6)
    names = ["Planner", "React Plan\npage", "FastAPI\n/api/optimize", "forecast.py\n(Random Forest)", "Instance /\nmatheuristic", "CBC\n(PuLP)"]
    xs = [8, 25.5, 43, 60.5, 78, 96]
    top, bot = 71, 0.8
    for x, n in zip(xs, names):
        c.box(x - 7, top, 14, 4.8, n, fc=INDIGO_L if x != xs[0] else GREEN_L, bold=True, fs=6.8, r=1.2)
        c.line((x, top), (x, bot), color="#9aa5ba", lw=0.9, ls="--")

    def msg(i, j, y, text, ret=False):
        c.arrow((xs[i], y), (xs[j], y), label=text, ls="--" if ret else "-", fs=6.2, loff=(0, 1.7))
    y = 66.2
    for i, j, t, r in [(0, 1, "choose month, p, method; click Optimise", False), (1, 2, "POST /api/optimize {period, n_hubs, ...}", False)]:
        msg(i, j, y, t, r); y -= 4.7
    c.text(xs[2] + 1.5, y + 0.8, "validate body (pydantic)", fs=5.9, italic=True, ha="left"); y -= 3.6
    for i, j, t, r in [(2, 3, "forecast_for_period(period)", False), (3, 2, "forecast per region (90)", True), (2, 4, "Instance.from_forecast(...)", False),
                       (2, 4, "solve_matheuristic(inst)", False), (4, 5, "assign_exact(hubs): sub-MIPs", False), (5, 4, "optimal assignments", True)]:
        msg(i, j, y, t, r); y -= 4.7
    c.text(xs[4] + 2, y + 1.8, "local search, then kernel MIP", fs=5.9, italic=True, ha="left"); y -= 2.0
    for i, j, t, r in [(4, 2, "hubs, allocation, log", True), (2, 4, "evaluate_solution(realised demand)", False), (4, 2, "KPIs: cost, hours, fulfilment", True),
                       (2, 1, "JSON {sol, kpi, demand_used}", True), (1, 0, "KPI tiles, network map, utilisation, search log, table", True)]:
        msg(i, j, y, t, r); y -= 4.7
    c.save(out)


# ------------------------------------------------------------------------------------------------ 10 flowchart
def flowchart(out):
    c = Canvas(10.4, 10.0)
    cx = 50

    def step(y, t, fc=INDIGO_L, w=46, h=5.6):
        return c.box(cx - w / 2, y - h / 2, w, h, t, fc=fc, fs=6.9, r=1.2)
    c.terminal(cx, 96.5, 14, 4, "Start")
    step(89.5, "Build Instance: distances x1.25, time, unit cost,\nfixed cost by tier, capacity = factor x demand / p")
    step(82, "Construct: greedy weighted k-medoids (open the hub that\nmost cuts cost), then medoid refinement")
    step(74.5, "Price the start set: exact assignment MIP for the hub set")
    c.diamond(cx, 66, 26, 7.4, "feasible?", fs=7)
    c.box(78, 63.2, 22, 5.6, "open more hubs by\ndemand until feasible", fc=ROSE_L, fs=6.4, r=1)
    step(57, "Rank closed candidates by nearby demand;\nbuild swap / drop / add moves")
    step(49.5, "Screen all moves with the greedy bound; keep those\nwithin 6% of the current cost; sort ascending")
    step(42, "Take the next move: price it with the exact\nassignment MIP (cached sub-problems)")
    c.diamond(cx, 34, 26, 7.4, "cheaper than\ncurrent plan?", fs=6.6)
    c.box(78, 31.2, 22, 5.6, "accept it (first\nimprovement), log it", fc=GREEN_L, fs=6.4, r=1)
    c.diamond(cx, 24.5, 30, 7.4, "more promising moves\nand time < 70%?", fs=6.4)
    step(15.5, "Kernel search: restricted full MIP over <= 24 promising\nhubs; keep it if cheaper", fc=INDIGO_L)
    step(8.2, "Return hubs, allocation, log, seconds, sub-problems", fc=GREEN_L)
    c.terminal(cx, 2.4, 12, 3.6, "End")
    c.arrow((cx, 94.5), (cx, 92.4)); c.arrow((cx, 86.7), (cx, 84.9)); c.arrow((cx, 79.2), (cx, 77.4)); c.arrow((cx, 71.7), (cx, 69.7))
    c.arrow((cx + 13, 66), (78, 66), label="no", loff=(0, 1.6), fs=6.3)
    c.arrow((cx, 62.3), (cx, 59.8), label="yes", loff=(2.6, 0), fs=6.3)
    c.arrow((cx, 54.2), (cx, 52.3)); c.arrow((cx, 46.7), (cx, 44.8)); c.arrow((cx, 39.2), (cx, 37.7))
    c.arrow((cx + 13, 34), (78, 34), label="yes", loff=(0, 1.6), fs=6.3)
    c.arrow((cx, 30.3), (cx, 28.2), label="no", loff=(2.6, 0), fs=6.3)
    # accept box -> up to the restart point (re-rank), joined by the infeasible box on the same rail
    c.line((89, 36.8), (89, 57)); c.line((89, 63.2), (89, 57))
    c.arrow((89, 57), (73, 57))
    c.text(84.5, 46, "restart:\nre-rank from the\nnew hub set", fs=6.3, italic=True)
    # more moves? -> yes: back to price the next move
    c.path([(cx - 15, 24.5), (21, 24.5), (21, 42), (cx - 23, 42)], label="yes: next move", seg=1, loff=(0, 0), fs=6.2)
    c.arrow((cx, 20.8), (cx, 18.4), label="no", loff=(2.6, 0), fs=6.3)
    c.arrow((cx, 12.7), (cx, 10.9)); c.arrow((cx, 5.4), (cx, 4.3))
    c.save(out)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "01_system_architecture.png")
    workflow(OUT / "02_high_level_workflow.png")
    dfd0(OUT / "03_dfd_level0.png")
    dfd1(OUT / "04_dfd_level1.png")
    dfd2(OUT / "05_dfd_level2.png")
    er(OUT / "06_er_diagram.png")
    uml(OUT / "07_uml_class_diagram.png")
    usecase(OUT / "08_use_case_diagram.png")
    sequence(OUT / "09_sequence_diagram.png")
    flowchart(OUT / "10_algorithm_flowchart.png")
    from diagrams_extra import decision_logic, flowchart_wide
    flowchart_wide(OUT / "11_algorithm_flowchart_wide.png")
    decision_logic(OUT / "12_decision_logic.png")
    print("done")
