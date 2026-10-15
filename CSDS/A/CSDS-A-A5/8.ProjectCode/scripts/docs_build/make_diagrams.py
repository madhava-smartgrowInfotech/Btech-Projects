"""Generate the report diagrams (PNG, 150 dpi) into docs/diagrams/ from the real design of TaxSentinel."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dg import *  # noqa: F401,F403

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)


def P(n):
    return os.path.join(OUT, n)


def architecture():
    fig, ax = canvas(12, 8.2, "System architecture of TaxSentinel")
    box(ax, 0.3, 6.3, 11.4, 1.35, fc=BLUE_L, ec=BLUE, lw=1.2)
    label(ax, 0.55, 7.5, "PRESENTATION  -  React 18 + Vite + Tailwind (port 5105)", fs=9.5, bold=True, color=BLUE, ha="left")
    for i, t in enumerate(["Landing /\nLogin", "Overview\n(generate)", "Taxpayers &\nprofile", "Fraud rings\n& chains", "Case note\n(E# links)", "Model\nperformance"]):
        box(ax, 0.55 + i * 1.88, 6.42, 1.7, 0.78, t, fc="white", ec=BLUE, fs=8.5)
    box(ax, 0.3, 4.3, 11.4, 1.7, fc=LIGHT, ec=GREEN, lw=1.2)
    label(ax, 0.55, 5.85, "APPLICATION  -  FastAPI (port 8105), JWT bearer guard, CORS", fs=9.5, bold=True, color=GREEN, ha="left")
    for i, t in enumerate(["routes/auth\nregister, login, me", "routes/pipeline\nrun, status, overview", "routes/investigate\ntaxpayers, chains, graph",
                           "routes/explanations\nPOST /{gstin}", "services/state\nStore (thread)", "services/explainer\nprompt + checks"]):
        box(ax, 0.55 + i * 1.88, 4.45, 1.7, 0.98, t, fc="white", ec=GREEN, fs=8.2)
    box(ax, 0.3, 2.2, 7.3, 1.85, fc=PUR_L, ec=PUR, lw=1.2)
    label(ax, 0.55, 3.9, "ANALYTICS  -  ml/ (NumPy, PyTorch CPU, NetworkX)", fs=9.5, bold=True, color=PUR, ha="left")
    for i, t in enumerate(["features.py\n3 layers x 19", "jepa.py\nencoder + EMA\n+ predictor", "graph.py\ncycles, clusters", "pipeline.py\nrisk, evidence,\nchains, eval"]):
        box(ax, 0.5 + i * 1.78, 2.35, 1.62, 1.1, t, fc="white", ec=PUR, fs=8.2)
    box(ax, 7.8, 2.2, 3.9, 1.85, fc=AMB_L, ec=AMB, lw=1.2)
    label(ax, 8.0, 3.9, "DATA & MODEL STORES", fs=9.5, bold=True, color=AMB, ha="left")
    box(ax, 8.0, 3.0, 1.75, 0.65, "SQLite app.db\nusers, runs, notes", fc="white", ec=AMB, fs=8)
    box(ax, 9.9, 3.0, 1.65, 0.65, "state.pkl\n(pipeline state)", fc="white", ec=AMB, fs=8)
    box(ax, 8.0, 2.35, 1.75, 0.55, "CSV ecosystem", fc="white", ec=AMB, fs=8)
    box(ax, 9.9, 2.35, 1.65, 0.55, "models/jepa.pt", fc="white", ec=AMB, fs=8)
    box(ax, 0.3, 0.35, 5.3, 1.35, fc=GREY_L, ec=GREY, lw=1.2)
    label(ax, 0.55, 1.55, "DATA SOURCES", fs=9.5, bold=True, color=GREY, ha="left")
    box(ax, 0.55, 0.5, 2.4, 0.85, "generate_gst_data.py\nseeded GST ecosystem\n+ injected fraud labels", fc="white", ec=GREY, fs=8)
    box(ax, 3.05, 0.5, 2.3, 0.85, "PaySim sample\n(100k rows, transfer\ncheck only)", fc="white", ec=GREY, fs=8)
    box(ax, 6.2, 0.35, 5.5, 1.35, fc=RED_L, ec=RED, lw=1.2)
    label(ax, 6.45, 1.55, "EXTERNAL SERVICE", fs=9.5, bold=True, color=RED, ha="left")
    box(ax, 6.45, 0.5, 5.05, 0.85, "Google Gemini (google-genai)  -  evidence-only prompt,\nautomatic grounding checks, model fallbacks", fc="white", ec=RED, fs=8.2)
    arrow(ax, (6, 6.3), (6, 6.0), "HTTPS JSON /api", color=BLUE, off=(1.0, 0))
    arrow(ax, (4, 4.3), (4, 4.05), color=GREEN)
    arrow(ax, (9.7, 4.3), (9.7, 4.05), color=GREEN)
    arrow(ax, (3, 1.7), (3, 2.2), color=GREY)
    arrow(ax, (8.9, 1.7), (8.9, 2.2), "", color=RED, ls="--")
    label(ax, 8.95, 1.95, "note request", fs=7.5, color=RED, ha="left")
    save(fig, P("01_system_architecture.png"))


def workflow():
    fig, ax = canvas(12, 6.2, "High-level workflow: from GST data to a cited case note")
    steps = [("1  Data", "Seeded GST ecosystem:\ntaxpayers, invoices,\nGSTR-1/2B/3B returns", GREY_L, GREY),
             ("2  Features", "19 features per\ntaxpayer-month in\ninvoice / behaviour /\nnetwork layers", BLUE_L, BLUE),
             ("3  JEPA", "Self-supervised\nencoder predicts\nembeddings; error =\ndeviation score", PUR_L, PUR),
             ("4  Network", "Circular-trading loops,\nshared-identity\nclusters, exposure", LIGHT, GREEN)]
    for i, (t, d, fc, ec) in enumerate(steps):
        x = 0.4 + i * 2.95
        box(ax, x, 3.6, 2.6, 1.9, fc=fc, ec=ec)
        label(ax, x + 1.3, 5.2, t, fs=11, bold=True, color=ec)
        label(ax, x + 1.3, 4.3, d, fs=8.8)
        if i < 3:
            arrow(ax, (x + 2.62, 4.55), (x + 2.93, 4.55), color=GREY, lw=2)
    steps2 = [("5  Invoice score", "Noisy-OR of 8 signals\nper invoice;\n>= 0.5 = anomalous", AMB_L, AMB),
              ("6  Risk", "Noisy-OR of JEPA,\nbehaviour, network,\ninvoice scores;\nflag at >= 0.5", RED_L, RED),
              ("7  Evidence + chains", "Evidence list E1..En\nper taxpayer;\ninvoice chains ranked", LIGHT, GREEN),
              ("8  Case note", "Gemini writes a cited\nnote; grounding\nchecks run; stored", BLUE_L, BLUE)]
    for i, (t, d, fc, ec) in enumerate(steps2):
        x = 0.4 + (3 - i) * 2.95
        box(ax, x, 1.0, 2.6, 1.9, fc=fc, ec=ec)
        label(ax, x + 1.3, 2.6, t, fs=11, bold=True, color=ec)
        label(ax, x + 1.3, 1.7, d, fs=8.8)
        if i < 3:
            arrow(ax, (x - 0.02, 1.95), (x - 0.33, 1.95), color=GREY, lw=2)
    arrow(ax, (10.3, 3.6), (10.3, 2.92), color=GREY, lw=2)
    box(ax, 0.4, 0.15, 11.5, 0.5, "Evaluation against injected labels and a rule baseline (precision@k, F1, ROC-AUC, per-pattern recall, ring recovery) runs on the same scores", fc=GREY_L, ec=GREY, fs=8.4)
    label(ax, 4.2, 3.2, "Analyst reviews ranked taxpayers, rings, chains and notes in the web application", fs=9, italic=True, color=GREY)
    save(fig, P("02_high_level_workflow.png"))


def dfd0():
    fig, ax = canvas(10, 5.6, "DFD level 0 (context diagram)")
    ell(ax, 5, 2.7, 3.2, 2.1, "0\nTaxSentinel\nFraud analytics\nsystem", fc=LIGHT, fs=11)
    box(ax, 0.3, 2.1, 1.9, 1.2, "Tax analyst /\ninvestigator", fc=BLUE_L, ec=BLUE, fs=10, bold=True)
    box(ax, 7.9, 4.0, 1.8, 1.0, "Google Gemini\nAPI", fc=RED_L, ec=RED, fs=10, bold=True)
    box(ax, 7.5, 0.4, 2.3, 1.0, "Data generator\n(seeded GST data)", fc=GREY_L, ec=GREY, fs=10, bold=True)
    arrow(ax, (2.2, 3.1), (3.45, 3.0), "credentials, seed,\ntaxpayer count, queries", color=BLUE, off=(0, 0.4))
    arrow(ax, (3.45, 2.4), (2.2, 2.3), "risk ranking, rings,\nchains, case notes,\nmetrics", color=GREEN, off=(0, -0.5))
    arrow(ax, (6.3, 3.5), (7.9, 4.3), "evidence prompt", color=RED, off=(-0.55, 0.3))
    arrow(ax, (8.4, 4.0), (6.7, 3.0), "cited note", color=RED, off=(0.95, 0.1), rad=0.2)
    arrow(ax, (7.5, 1.1), (6.3, 1.9), "taxpayers, invoices,\nreturns, labels", color=GREY, off=(-0.9, -0.1))
    save(fig, P("03_dfd_level0.png"))


def dfd1():
    fig, ax = canvas(12.5, 9.2, "DFD level 1")
    box(ax, 0.2, 3.9, 1.5, 1.1, "Analyst", fc=BLUE_L, ec=BLUE, bold=True)
    ys = [7.9, 6.2, 4.5, 2.8, 1.1]
    names = ["1.0\nAuthenticate", "2.0\nGenerate &\nanalyse", "3.0\nInvestigate\n(rank, profile,\ngraph, chains)", "4.0\nEvaluate\nmetrics", "5.0\nExplain case"]
    for y, t in zip(ys, names):
        ell(ax, 4.3, y, 2.5, 1.3, t, fs=9)
    store(ax, 8.6, 7.65, 3.4, 0.5, "D1  users", fs=9)
    store(ax, 8.6, 6.55, 3.4, 0.5, "D2  pipeline_runs", fs=9)
    store(ax, 8.6, 5.75, 3.4, 0.5, "D4  CSV ecosystem + jepa.pt", fs=9)
    store(ax, 8.6, 4.2, 3.4, 0.5, "D5  pipeline state (state.pkl)", fs=9)
    store(ax, 8.6, 2.55, 3.4, 0.5, "D6  experiments/*.json", fs=9)
    store(ax, 8.6, 0.85, 3.4, 0.5, "D3  explanations", fs=9)
    box(ax, 9.0, 1.7, 2.6, 0.65, "Gemini API", fc=RED_L, ec=RED, bold=True, fs=9)
    arrow(ax, (1.0, 5.0), (3.2, 7.5), "email, password", color=BLUE, off=(-0.6, 0.2))
    arrow(ax, (1.7, 4.7), (3.1, 6.1), "seed, taxpayers", color=BLUE, off=(-0.35, 0.25))
    arrow(ax, (1.7, 4.45), (3.05, 4.5), "filters, GSTIN", color=BLUE, off=(0, -0.25))
    arrow(ax, (1.5, 3.9), (3.2, 2.9), "metrics query", color=BLUE, off=(-0.35, -0.1))
    arrow(ax, (1.0, 3.9), (3.2, 1.4), "case request", color=BLUE, off=(-0.5, -0.2))
    arrow(ax, (5.55, 7.95), (8.6, 7.9), "verify / create user", color=GREY, off=(0, 0.2))
    arrow(ax, (5.5, 6.4), (8.6, 6.8), "run row, stats", color=GREY, off=(0, 0.2))
    arrow(ax, (8.6, 6.0), (5.5, 6.0), "dataset, model", color=GREY, off=(0, -0.2))
    arrow(ax, (5.3, 5.7), (8.6, 4.55), "pipeline state", color=GREY, off=(-0.1, 0.35))
    arrow(ax, (8.6, 4.4), (5.55, 4.5), "state", color=GREY, off=(0, 0.17))
    arrow(ax, (8.6, 4.2), (5.45, 3.2), "evaluation", color=GREY, off=(0.55, 0.3))
    arrow(ax, (8.6, 2.8), (5.55, 2.8), "training + eval reports", color=GREY, off=(0, 0.2))
    arrow(ax, (8.6, 4.2), (5.4, 1.55), "evidence", color=GREY, off=(-0.9, -0.5))
    arrow(ax, (5.55, 1.1), (8.6, 1.1), "note + quality", color=GREY, off=(0, -0.22))
    arrow(ax, (5.5, 1.35), (9.0, 1.95), "prompt  <->  cited note", color=RED, off=(0.1, 0.28), style="<|-|>")
    save(fig, P("04_dfd_level1.png"))


def dfd2():
    fig, ax = canvas(12, 8.2, "DFD level 2: process 2.0 Generate and analyse")
    top, bot = 5.4, 3.0
    items = [(1.7, top, "2.1\nGenerate\necosystem"), (4.4, top, "2.2\nBuild feature\nlayers"), (7.1, top, "2.3\nTrain / score\nJEPA"), (9.8, top, "2.4\nNetwork\nanalysis"),
             (9.8, bot, "2.5\nInvoice\nanomaly score"), (7.1, bot, "2.6\nCombine\nrisk"), (4.4, bot, "2.7\nEvidence &\nchains"), (1.7, bot, "2.8\nEvaluate vs\nlabels")]
    for x, y, t in items:
        ell(ax, x, y, 2.3, 1.45, t, fs=9)
    for a, b in [(0, 1), (1, 2), (2, 3)]:
        arrow(ax, (items[a][0] + 1.15, items[a][1]), (items[b][0] - 1.15, items[b][1]), color=GREY, lw=1.8)
    arrow(ax, (9.8, top - 0.73), (9.8, bot + 0.73), "loop edges,\nclusters", color=GREY, off=(0.85, 0))
    for a, b in [(4, 5), (5, 6), (6, 7)]:
        arrow(ax, (items[a][0] - 1.15, items[a][1]), (items[b][0] + 1.15, items[b][1]), color=GREY, lw=1.8)
    arrow(ax, (7.1, top - 0.73), (7.1, bot + 0.73), "J, B scores", color=GREY, off=(-0.75, 0))
    arrow(ax, (8.75, top - 0.55), (8.0, bot + 0.6), "network\nscore", color=GREY, off=(0.55, 0.15))
    store(ax, 0.4, 7.05, 2.6, 0.55, "D4  CSV ecosystem", fs=9)
    store(ax, 5.8, 7.05, 2.6, 0.55, "D4b  jepa.pt", fs=9)
    store(ax, 5.8, 0.75, 2.6, 0.55, "D5  state.pkl", fs=9)
    store(ax, 8.9, 0.75, 2.8, 0.55, "D2  pipeline_runs", fs=9)
    arrow(ax, (1.7, 7.05), (1.7, top + 0.73), "writes CSVs", color=AMB, off=(0.7, 0.0), ls="--")
    arrow(ax, (7.1, 7.05), (7.1, top + 0.73), "weights, scaler", color=AMB, off=(0.9, 0.0), ls="--", style="<|-|>")
    arrow(ax, (4.4, bot - 0.73), (6.2, 1.3), "pickle", color=AMB, off=(-0.55, -0.05), ls="--")
    arrow(ax, (9.8, bot - 0.73), (10.2, 1.3), "status, stats", color=AMB, off=(0.75, 0.0), ls="--")
    arrow(ax, (3.0, 7.3), (4.4, top + 0.73), "dataset", color=AMB, off=(-0.7, 0.0), ls="--")
    label(ax, 4.5, 1.9, "Every stage reports progress: generate, features, train, score, rings, invoices, risk, evidence", fs=8.6, italic=True, color=GREY)
    label(ax, 1.7, 1.6, "(2.8 compares the final scores with the\ninjected labels held in the dataset)", fs=8, italic=True, color=GREY)
    save(fig, P("05_dfd_level2.png"))


def uml_class():
    fig, ax = canvas(14.2, 10.2, "UML class diagram (persistence, service and model classes)")

    def cls(x, y, w, name, attrs, meths=(), ec=GREEN, fc=LIGHT, stereo=None):
        lh = 0.27
        h = 0.5 + lh * (len(attrs) + len(meths)) + (0.12 if meths else 0)
        ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc="white", ec=ec, lw=1.6))
        ax.add_patch(Rectangle((x, y - 0.5), w, 0.5, fc=fc, ec=ec, lw=1.6))
        ax.text(x + w / 2, y - 0.25, (f"<<{stereo}>> " if stereo else "") + name, ha="center", va="center", fontsize=9.3, fontweight="bold")
        yy = y - 0.5
        for a_ in attrs:
            yy -= lh
            ax.text(x + 0.1, yy + lh / 2, a_, ha="left", va="center", fontsize=7.6, family="monospace")
        if meths:
            ax.plot([x, x + w], [yy - 0.06, yy - 0.06], color=ec, lw=1)
            yy -= 0.12
            for m in meths:
                yy -= lh
                ax.text(x + 0.1, yy + lh / 2, m, ha="left", va="center", fontsize=7.6, family="monospace")
        return y - h

    X1, X2, X3 = 0.9, 5.4, 10.1
    cls(X1, 9.6, 3.4, "User", ["+id: int (PK)", "+email: str (unique)", "+name: str", "+password_hash: str", "+created_at: datetime"], stereo="ORM")
    cls(X1, 7.0, 3.4, "PipelineRun", ["+id: int (PK)", "+seed: int", "+n_taxpayers: int", "+status: str", "+message: str", "+stats: JSON", "+user_id: int (FK)", "+started_at, finished_at"], stereo="ORM")
    cls(X1, 3.9, 3.4, "Explanation", ["+id: int (PK)", "+run_key, gstin: str", "+model: str", "+text: str", "+evidence: JSON", "+quality: JSON", "+user_id: int (FK)"], stereo="ORM")
    cls(X2, 7.7, 3.9, "Store", ["+state: dict", "+lock: Lock", "+status: dict"], ["+load()", "+get() -> state", "+start_run(seed, n, user)", "-_run(run_id, seed, n)", "-_save(state)"], ec=BLUE, fc=BLUE_L, stereo="service")
    cls(X2, 4.6, 3.9, "Pipeline (ml/pipeline.py)", [], ["train_model(data_dir, path)", "run_pipeline(data_dir, ...)", "evaluate(y, risk, ...)", "(uses features, graph, baseline)"], ec=GREEN, stereo="module")
    cls(X2, 2.5, 3.9, "Explainer (service)", ["SYSTEM: str  (prompt)"], ["build_prompt(tp, evidence)", "generate(prompt) -> text", "check_quality(text, ev)"], ec=RED, fc=RED_L, stereo="service")
    cls(X3, 9.6, 3.9, "JEPA (nn.Module)", ["+d_in, window, emb: int", "+groups: list[list[int]]", "+encoder: Encoder", "+target: Encoder (EMA)", "+predictor: Sequential"], ["+predict(ctx, present, cur, v)", "+update_target(momentum)"], ec=PUR, fc=PUR_L)
    cls(X3, 6.3, 3.9, "Encoder (nn.Module)", ["+net: Linear-LayerNorm-GELU-", "    Linear-GELU-Linear", "    (19 -> 64 -> 32)"], ["+forward(x) -> embedding"], ec=PUR, fc=PUR_L)
    cls(X3, 3.5, 3.9, "RobustScaler", ["+median: ndarray", "+scale: ndarray"], ["+fit(X), transform(X)", "+to_dict(), from_dict(d)"], ec=GREY, fc=GREY_L)
    arrow(ax, (1.9, 7.0), (1.9, 7.75), "", color=GREY, style="-")
    label(ax, 2.6, 7.4, "creates  1 .. *", fs=8, color=GREY)
    ax.plot([0.9, 0.35, 0.35], [8.7, 8.7, 3.4], color=GREY, lw=1.4)
    arrow(ax, (0.35, 3.4), (0.9, 3.4), "", color=GREY, style="-")
    label(ax, 0.6, 6.0, "writes  1 .. *", fs=8, color=GREY, rot=90)
    arrow(ax, (X2, 6.2), (X1 + 3.4, 6.2), "persists", color=BLUE, off=(0, 0.2), ls="--")
    arrow(ax, (7.35, 5.0), (7.35, 4.6), "", color=GREEN)
    label(ax, 8.6, 4.85, "calls run_pipeline", fs=8, color=GREEN)
    arrow(ax, (X2, 2.0), (X1 + 3.4, 2.0), "stores notes (route layer)", color=RED, off=(0, 0.22), ls="--")
    arrow(ax, (X2 + 3.9, 4.0), (X3, 3.0), "fit / scale", color=GREY, off=(0, 0.2))
    arrow(ax, (X2 + 3.9, 4.4), (X3, 8.8), "trains / scores", color=PUR, off=(-0.05, 0.4), ls="--")
    arrow(ax, (11.2, 7.08), (11.2, 6.3), "", color=PUR)
    label(ax, 12.8, 6.7, "2 composition (online + EMA)", fs=7.4, color=PUR)
    save(fig, P("06_uml_class_diagram.png"))


def sequence():
    fig, ax = canvas(13, 8.4, "Sequence diagram: generate, investigate and explain")
    actors = [("Analyst", 0.9), ("React SPA", 3.0), ("FastAPI", 5.2), ("Store /\nPipeline", 7.4), ("SQLite", 9.4), ("Gemini", 11.6)]
    for n, x in actors:
        box(ax, x - 0.8, 7.35, 1.6, 0.65, n, fc=LIGHT, ec=GREEN, bold=True, fs=9)
        ax.plot([x, x], [0.2, 7.35], color="#94a3b8", lw=1, ls="--")
    X = dict(a=0.9, s=3.0, f=5.2, p=7.4, d=9.4, g=11.6)
    msgs = [("a", "s", 7.0, "1  sign in (demo account)"), ("s", "f", 6.7, "2  POST /api/auth/login"), ("f", "d", 6.4, "3  select user, bcrypt check"), ("f", "s", 6.1, "4  JWT"),
            ("a", "s", 5.75, "5  Generate & analyse"), ("s", "f", 5.45, "6  POST /api/pipeline/run"), ("f", "p", 5.15, "7  start_run() -> thread"), ("f", "d", 4.85, "8  insert PipelineRun"),
            ("s", "f", 4.5, "9  poll GET /pipeline/status"), ("p", "p", 4.2, "10  generate, features, JEPA, graph, risk, evidence"), ("p", "d", 3.85, "11  update run: done + stats"),
            ("a", "s", 3.5, "12  open top taxpayer"), ("s", "f", 3.2, "13  GET /taxpayers/{gstin}"), ("f", "p", 2.9, "14  read profile + evidence"), ("f", "s", 2.6, "15  profile JSON"),
            ("a", "s", 2.25, "16  Write explanation"), ("s", "f", 1.95, "17  POST /explanations/{gstin}"), ("f", "g", 1.65, "18  build_prompt -> generate()"), ("g", "f", 1.35, "19  case note with [E#]"),
            ("f", "d", 1.05, "20  check_quality, save"), ("f", "s", 0.75, "21  note + quality"), ("s", "a", 0.45, "22  render note, E# links")]
    returns = {"4  JWT", "15  profile JSON", "19  case note with [E#]", "21  note + quality", "22  render note, E# links"}
    for a, b, y, t in msgs:
        if a == b:
            ax.annotate("", xy=(X[a] + 0.02, y - 0.12), xytext=(X[a] + 0.02, y + 0.1), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.4, connectionstyle="arc3,rad=-1.2"))
            ax.text(X[a] + 0.4, y, t, fontsize=8.2, va="center", ha="left")
            continue
        ret = t in returns
        arrow(ax, (X[a], y), (X[b], y), "", color=GREEN if ret else BLUE, ls="--" if ret else "-", lw=1.3)
        ax.text((X[a] + X[b]) / 2, y + 0.1, t, ha="center", va="bottom", fontsize=8, color=INK)
    save(fig, P("07_sequence_diagram.png"))


def usecase():
    fig, ax = canvas(11.5, 8, "Use-case diagram")
    ax.add_patch(Rectangle((2.8, 0.45), 6.2, 6.85, fc="white", ec=GREY, lw=1.6))
    label(ax, 5.9, 7.05, "TaxSentinel", fs=11, bold=True, color=GREY)
    cases = ["Register / sign in", "Generate & analyse ecosystem", "View overview & activity log", "Browse risk ranking (search, filter)", "Inspect taxpayer profile & evidence",
             "Explore fraud graph (loops, clusters)", "Drill into invoice chain", "Write cited case note", "View model performance", "View run history"]
    ys = [6.5 - i * 0.6 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ell(ax, 5.9, y, 4.3, 0.5, t, fs=8.8)
    for (cx, cy, nm, col) in [(1.2, 3.8, "Tax analyst /\ninvestigator", BLUE), (10.3, 2.4, "Gemini API\n(secondary)", RED)]:
        ax.add_patch(Ellipse((cx, cy + 0.65), 0.4, 0.4, fc="white", ec=col, lw=1.6))
        ax.plot([cx, cx], [cy + 0.45, cy - 0.15], color=col, lw=1.6)
        ax.plot([cx - 0.35, cx + 0.35], [cy + 0.25, cy + 0.25], color=col, lw=1.6)
        ax.plot([cx, cx - 0.3], [cy - 0.15, cy - 0.7], color=col, lw=1.6)
        ax.plot([cx, cx + 0.3], [cy - 0.15, cy - 0.7], color=col, lw=1.6)
        label(ax, cx, cy - 1.1, nm, fs=9, bold=True, color=col)
    for y in ys:
        ax.plot([1.6, 3.75], [3.7, y], color=BLUE, lw=0.9, alpha=0.7)
    ax.plot([9.9, 8.0], [2.5, ys[7]], color=RED, lw=1.2)
    ax.text(5.9, 0.2, "Every use case except Register / sign in requires a valid JWT.  'Write cited case note' includes 'Inspect taxpayer profile' (evidence).", ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, P("08_use_case_diagram.png"))


def er():
    fig, ax = canvas(12.5, 7.6, "Entity-relationship diagram")

    def ent(x, y, w, name, rows, ec=GREEN, fc=LIGHT, dashed=False):
        h = 0.45 + 0.3 * len(rows)
        ls = "--" if dashed else "-"
        ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=ec, lw=1.6, ls=ls))
        ax.add_patch(Rectangle((x, y - 0.45), w, 0.45, fc=fc, ec=ec, lw=1.6, ls=ls))
        ax.text(x + w / 2, y - 0.22, name, ha="center", va="center", fontsize=10, fontweight="bold")
        for i, r in enumerate(rows):
            ax.text(x + 0.1, y - 0.45 - 0.3 * i - 0.15, r, fontsize=8.0, family="monospace", va="center")

    ent(0.3, 7.2, 3.4, "users", ["PK id            INTEGER", "   email UNIQUE   VARCHAR(200)", "   name           VARCHAR(120)", "   password_hash  VARCHAR(200)", "   created_at     DATETIME"])
    ent(4.5, 7.2, 3.7, "pipeline_runs", ["PK id           INTEGER", "   seed           INTEGER", "   n_taxpayers    INTEGER", "   status         VARCHAR(20)", "   message        TEXT", "   stats          JSON", "FK user_id        -> users.id", "   started_at     DATETIME", "   finished_at    DATETIME"])
    ent(9.0, 7.2, 3.4, "explanations", ["PK id            INTEGER", "   run_key (idx)  VARCHAR(60)", "   gstin   (idx)  VARCHAR(20)", "   model          VARCHAR(80)", "   text           TEXT", "   evidence       JSON", "   quality        JSON", "FK user_id        -> users.id", "   created_at     DATETIME"])
    arrow(ax, (3.7, 6.3), (4.5, 6.3), "", color=GREEN, style="-")
    label(ax, 4.1, 6.55, "1 : N", fs=9, color=GREEN, bold=True)
    ax.plot([1.9, 1.9, 10.7, 10.7], [5.25, 3.85, 3.85, 4.05], color=GREEN, lw=1.5)
    label(ax, 6.3, 3.68, "users 1 : N explanations  (user_id)", fs=9, color=GREEN, bold=True)
    label(ax, 6.3, 3.3, "File-based analytical entities (CSV, not SQL tables), linked by GSTIN", fs=9.5, bold=True, color=AMB)
    ent(0.3, 3.0, 3.7, "taxpayers.csv", ["gstin (key), legal_name", "constitution, state, sector", "registration_date", "address_id, contact_id", "is_fraud, fraud_roles (labels)"], ec=AMB, fc=AMB_L, dashed=True)
    ent(4.4, 3.0, 3.8, "invoices.csv", ["invoice_no, invoice_date, month", "seller_gstin, buyer_gstin (FK)", "taxable_value, gst_rate, tax_amount", "eway_bill, seller_reported", "is_fraud (label)"], ec=AMB, fc=AMB_L, dashed=True)
    ent(8.6, 3.0, 3.8, "returns.csv", ["gstin (FK), month", "outward_taxable, b2c_taxable", "output_tax, itc_available_2b", "itc_claimed_3b, tax_paid_cash", "filing_delay_days"], ec=AMB, fc=AMB_L, dashed=True)
    ax.text(6.3, 0.2, "explanations.gstin refers logically to taxpayers.csv.gstin and run_key to the loaded ecosystem (e.g. run-14); no SQL foreign key is declared for these.", ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, P("09_er_diagram.png"))


def flowchart():
    fig, ax = canvas(11, 11.4, "Flowchart of the core algorithm (risk scoring)")

    def b(y, t, fc=LIGHT, ec=GREEN, w=6.4, h=0.7, x=5.5):
        box(ax, x - w / 2, y - h / 2, w, h, t, fc=fc, ec=ec, fs=9)

    b(10.7, "Start: load taxpayers, invoices, returns (CSV)", GREY_L, GREY)
    b(9.75, "Build 19 features per taxpayer-month; robust-scale and clip", BLUE_L, BLUE)
    b(8.8, "JEPA: predict EMA-target embedding from 3 previous months\n+ the month with one block masked (4 variants)", PUR_L, PUR, h=0.85)
    b(7.8, "Error / monthly median -> geometric mean -> top-2 months\n-> robust z -> sigmoid = JEPA score J; behaviour variant = B", PUR_L, PUR, h=0.85)
    b(6.85, "Network: simple_cycles (len <= 5) on recurring edges -> rings;\nshared address / contact -> clusters; exposure -> N", LIGHT, GREEN, h=0.85)
    b(5.85, "Invoices: noisy-OR of 8 flags; score >= 0.5 -> anomalous;\ninvoice score I = peak monthly anomalous share", AMB_L, AMB, h=0.85)
    b(4.85, "Risk = 1 - (1 - 0.75 J)(1 - 0.6 B)(1 - 0.7 N)(1 - 0.6 I)", RED_L, RED)
    diamond(ax, 5.5, 3.75, 3.2, 1.2, "Risk >= 0.5 ?")
    b(2.45, "Flag taxpayer; name pattern(s);\nbuild evidence E1..En", RED_L, RED, w=4.2, x=3.4, h=0.8)
    b(2.45, "Not flagged", GREY_L, GREY, w=2.2, x=8.9, h=0.8)
    b(1.5, "Rank, build invoice chains, evaluate vs labels and rule baseline", LIGHT, GREEN, w=6.6)
    b(0.65, "Analyst opens case -> Gemini note with [E#] citations -> grounding checks", BLUE_L, BLUE, w=7.6)
    for y1, y2 in [(10.35, 10.1), (9.4, 9.22), (8.37, 8.22), (7.37, 7.27), (6.42, 6.27), (5.42, 5.2), (4.5, 4.35)]:
        arrow(ax, (5.5, y1), (5.5, y2), color=GREY, lw=1.6)
    arrow(ax, (4.1, 3.55), (3.4, 2.85), "yes", color=RED, off=(-0.25, 0.1))
    arrow(ax, (6.9, 3.55), (8.9, 2.85), "no", color=GREY, off=(0.25, 0.1))
    arrow(ax, (3.4, 2.05), (4.3, 1.87), color=GREY)
    arrow(ax, (8.9, 2.05), (7.2, 1.87), color=GREY)
    arrow(ax, (5.5, 1.15), (5.5, 1.0), color=GREY)
    save(fig, P("10_core_algorithm_flowchart.png"))


if __name__ == "__main__":
    for f in (architecture, workflow, dfd0, dfd1, dfd2, uml_class, sequence, usecase, er, flowchart):
        f()
