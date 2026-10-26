"""Draw the BotGraph design diagrams (first half) into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: ml/ (data.py, gnn.py, train.py, clustering.py, eval.py), backend/app/ (main.py, auth.py, db.py,
routes/*, services/store.py) and frontend/src (App.jsx and pages/).
    python scripts/docs_build/make_diagrams.py        (also runs diagrams_dfd.py and diagrams_more.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def system_architecture():
    fig, ax = canvas(10, 9.0, 100, 90)
    panel(ax, 2, 70, 96, 19, "Presentation tier - React 18 + Vite 5 web app (port 5309, proxies /api to the API)", PALE_BLUE, BLUE)
    box(ax, 17, 77, 28, 10.5, "Pages (code-split)\nLanding - Login - Overview\nGraph & features - Accounts\nAccount detail - Clusters\nCluster detail - Queue - Models", BLUE, fs=7.0)
    box(ax, 47, 77, 26, 10.5, "src/lib\nauth (token, RequireAuth)\nfetch wrapper over /api\nrole-aware actions", BLUE, fs=7.2)
    box(ax, 75, 77, 26, 10.5, "V4 Soft Pastel Calm kit\ncards, tables, gauges,\nforce graph, charts,\nmotion, toasts, dark mode", BLUE, fs=7.2)

    panel(ax, 2, 48, 96, 20, "Application tier - FastAPI + Uvicorn (backend/app, 127.0.0.1:8309)", PALE_TEAL, TEAL)
    box(ax, 14, 55.5, 20, 11, "core.py\n/health, /auth/login,\n/auth/me, /graph/summary,\n/overview", TEAL, fs=6.8)
    box(ax, 36.5, 55.5, 21, 11, "accounts.py, clusters.py\n/accounts, /accounts/{id},\n/{id}/neighbourhood,\n/clusters, /clusters/{id}", TEAL, fs=6.8)
    box(ax, 59, 55.5, 21, 11, "queue.py, models.py\n/queue, /queue/decisions,\n/decisions, /models,\n/models/retrain", TEAL, fs=6.8)
    box(ax, 84, 55.5, 24, 11, "auth.py\nbcrypt hashes, JWT HS256\n(12 h), analyst /\nmoderator roles, CORS", TEAL, fs=6.8)

    panel(ax, 2, 24.5, 96, 21.5, "Core modules and in-memory state", PALE_ORANGE, ORANGE)
    box(ax, 21, 34.5, 34, 11.5, "services/store.py  (Store)\nloads graph, scores, clusters,\nmetrics once; gradient x input\nexplanations; neighbour index", ORANGE, fs=7.0)
    box(ax, 61, 34.5, 40, 11.5, "ml/  (plain PyTorch sparse ops, no torch-geometric)\ndata.py graph builder - gnn.py GCN / GAT / GraphSAGE\ntrain.py training - clustering.py Louvain - eval.py", ORANGE, fs=6.9)
    box(ax, 89, 34.5, 14, 11.5, "retrain job\nbackground\nthread, one\nrun at a time", NAVY, fs=6.8)

    panel(ax, 2, 1.5, 96, 20, "Data tier - SQLite database and files on disk", LIGHT, "#B7C3D3")
    store(ax, 14, 9.5, 21, 10.5, "data/app.db (SQLite)\nusers, reviews,\ntraining_runs", fs=6.9)
    store(ax, 37, 9.5, 21, 10.5, "data/processed/\ngraph.npz, accounts.csv,\ngraph_meta.json", fs=6.9)
    store(ax, 60, 9.5, 21, 10.5, "models/\nbaseline.pt, gcn.pt, gat.pt,\nsage.pt, scores.npz,\nclusters.json, meta.json", fs=6.6)
    store(ax, 83, 9.5, 24, 10.5, "experiments/ + data/raw/\nmetrics.json, scalability.json,\neval/, public datasets", fs=6.6)

    arrow(ax, (50, 70), (50, 68), "HTTP + JSON, Bearer token", lo=(20, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 48), (50, 46), "function calls", lo=(8, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 24.5), (50, 21.5), "load once / read-write", lo=(12, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


def high_level_workflow():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63, "From public data to a moderator-reviewed botnet list", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.text(3, 56.5, "Lane A - offline pipeline (python -m ml.data, ml.train, ml.eval)", fontsize=8.6, color=TEAL, fontweight="bold")
    a = [("Public data", "Facebook ego nets,\nInstagram + Twitter\nlabelled rows", BLUE), ("Build graph", "inject 8 botnets and\n150 lone spammers\n(seeded)", TEAL),
         ("23 features", "profile, posting,\ntemporal, interaction;\nstandardised", TEAL), ("Train 4 models", "MLP, GCN, GAT,\nGraphSAGE x 3 seeds\n60/20/20 split", PURPLE),
         ("Pick + cluster", "best on validation F1;\nLouvain over\nembeddings", PURPLE), ("Artefacts", "models/, scores,\nclusters.json,\nmetrics.json", NAVY)]
    xs = [9 + i * 16.4 for i in range(6)]
    for x, (t, d, c) in zip(xs, a):
        box(ax, x, 45.5, 14.4, 14, f"{t}\n{d}", c, fs=7.0)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 7.4, 45.5), (q - 7.4, 45.5), color=NAVY)
    ax.text(12, 30.5, "Lane B - the running application (FastAPI + React)", fontsize=8.6, color=ORANGE, fontweight="bold")
    b = [("Load once", "graph, scores,\nclusters, metrics\ninto memory", BLUE), ("Sign in", "analyst or moderator;\nJWT token", TEAL),
         ("Review", "ranked accounts,\nreasons, neighbourhood,\nbotnet clusters", TEAL), ("Decide", "moderator confirms or\ndismisses an account\nor a whole cluster", ORANGE),
         ("Retrain", "decisions become labels;\ntest split never\ntouched", PURPLE), ("Reload", "new scores and\nclusters; F1 before\nand after logged", NAVY)]
    for x, (t, d, c) in zip(xs, b):
        box(ax, x, 20.5, 14.4, 14, f"{t}\n{d}", c, fs=7.0)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 7.4, 20.5), (q - 7.4, 20.5), color=NAVY)
    ax.plot([xs[5], xs[5]], [38.4, 34.0], color=NAVY, lw=1.5, ls="--", zorder=4)
    ax.plot([xs[5], xs[0]], [34.0, 34.0], color=NAVY, lw=1.5, ls="--", zorder=4)
    arrow(ax, (xs[0], 34.0), (xs[0], 27.6), "", color=NAVY, ls="--")
    ax.text(50, 35.2, "artefacts are read once at start-up", fontsize=7.2, ha="center", color=GREY)
    ax.text(50, 4.5, "Retraining (box 5, Lane B) calls the same training code as Lane A (ml.train.fit_all), then the application reloads: decisions -> labels -> new scores.",
            ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


def dfd0():
    fig, ax = canvas(10, 5.8, 100, 58)
    box(ax, 50, 29, 26, 16, "BotGraph\n(0)\ngraph builder, GNN scoring,\nbotnet clusters,\nmoderator queue", NAVY, fs=8.6, bold=True, r=2)
    box(ax, 10, 45, 17, 9, "Analyst /\nresearcher", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    box(ax, 10, 13, 17, 9, "Moderator", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    box(ax, 90, 29, 17, 11, "Public datasets\n(Facebook, Instagram,\nTwitter files)", WHITE, tc=INK, ec=BLUE, fs=8.0, bold=True)
    arrow(ax, (18.5, 46), (37, 34.5), "sign-in, queries", lo=(-3, 4.5), fs=7.4, color=NAVY)
    arrow(ax, (37, 32), (18.5, 43), "scores, reasons, clusters,\ngraph summary, metrics", lo=(-1, -6.0), fs=7.2, color=TEAL)
    arrow(ax, (18.5, 14), (37, 25), "confirm / dismiss,\nretrain command", lo=(-2, 6.5), fs=7.2, color=NAVY)
    arrow(ax, (37, 23), (18.5, 11.5), "decision log, new scores,\nF1 before and after", lo=(2, -6.0), fs=7.2, color=TEAL)
    arrow(ax, (81.5, 29), (63, 29), "topology, labelled\nprofile and posting rows", lo=(0, 4.2), fs=7.4, color=NAVY)
    ax.text(50, 5, "Level 0 (context). Nothing leaves the machine at run time: the datasets are read from data/raw, no external service is called.",
            ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


def uml_class_diagram():
    fig, ax = canvas(10, 8.8, 100, 88)
    uml_class(ax, 1, 87, 29, "User", ["id: int (pk)", "email: str (unique)", "name: str", "role: analyst | moderator", "password_hash: str"], [], hdr=NAVY, stereotype="SQLAlchemy model", fs=6.5)
    uml_class(ax, 1, 62, 29, "Review", ["id: int (pk)", "target_type: account | cluster", "target_id: str", "decision: confirm | dismiss", "note: str, score: float", "members: list[int] (JSON)", "user_id -> User.id", "created_at, used_in_run: int?"],
              [], hdr=NAVY, stereotype="SQLAlchemy model", fs=6.5)
    uml_class(ax, 1, 31, 29, "TrainingRun", ["id: int (pk)", "started_at, finished_at", "status: running|done|error", "feedback_labels: int", "best: str, message: str", "f1_before, f1_after: JSON", "user_id -> User.id"],
              [], hdr=NAVY, stereotype="SQLAlchemy model", fs=6.5)
    uml_class(ax, 40, 87, 30, "Store  (services/store.py)", ["g: graph dict, n: int", "best: str, thr: float", "probs: dict[model -> scores]", "score, emb: ndarray", "clusters, cluster_by_id", "accounts: DataFrame", "metrics, scalability"],
              ["reload()", "neighbours(i), edge_set(nodes)", "node_brief(i)", "explain(i) : gradient x input", "decisions_map(reviews)"], hdr=ORANGE, stereotype="singleton, thread-safe", fs=6.4)
    uml_class(ax, 40, 44, 30, "FastAPI routers + auth", [],
              ["core: login, health, overview", "accounts, clusters: list, detail", "queue: decide(), undo()", "models: retrain(), scalability()", "current_user(), require_moderator()", "make_token(), verify_password()"], hdr=TEAL, fs=6.4)
    uml_class(ax, 75, 87, 24, "Graph  (ml/gnn.py)", ["n, src, dst, src_sl, dst_sl", "a_hat: sparse (GCN)", "a_mean: sparse (SAGE)"], ["Graph(n, edge_index)"], hdr=PURPLE, fs=6.2)
    uml_class(ax, 75, 69, 24, "Net  (ml/gnn.py)", ["arch: baseline|gcn|sage|gat", "l1, l2: layer", "head: Linear(64, 2)", "dropout = 0.3"], ["forward(x, g) : (logits, emb)"], hdr=PURPLE, stereotype="torch.nn.Module", fs=6.2)
    uml_class(ax, 75, 48, 24, "Layers", ["GCNLayer: Lin, a_hat", "SAGELayer: self_lin,", "   neigh_lin, a_mean", "GATLayer: lin, a_src,", "   a_dst, heads"], ["forward(x, g)"], hdr=PURPLE, stereotype="torch.nn.Module", fs=6.2)
    uml_class(ax, 75, 24, 24, "ml modules", [], ["data.build() / load()", "train.fit_all(g, seeds, fb)", "train.write_artifacts()", "clustering.detect()", "clustering.describe()", "clustering.recovery()", "eval.scalability()"], hdr=GREY, stereotype="functions", fs=6.0)

    def line(p1, p2, ls="-", c=NAVY, lw=1.5):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=lw, ls=ls, zorder=4)
    # User 1 - * Review
    line((15, 68.1), (15, 62)); ax.text(16.2, 66.0, "1", fontsize=7); ax.text(16.2, 62.6, "*", fontsize=7.6)
    ax.text(18, 64.4, "decides", fontsize=6.6, color=GREY)
    # Review .. TrainingRun (logical)
    line((15, 36.7), (15, 31), ls="--", c=GREY); ax.text(16.5, 33.6, "used_in_run -> run id (no FK)", fontsize=6.4, color=GREY)
    # routers read Store
    arrow(ax, (55, 44), (55, 55.4), "reads", lo=(3.5, 0), fs=6.8, color=NAVY)
    # routers -> DB rows
    arrow(ax, (40, 36), (30, 24.5), "", color=NAVY)
    arrow(ax, (40, 40), (30, 50), "", color=NAVY)
    ax.text(30.6, 41.2, "read / write\nrows", fontsize=6.4, color=GREY, ha="left")
    # Store loads the served net
    arrow(ax, (70, 75), (75, 72), "loads", lo=(0, 2.2), fs=6.4, color=NAVY)
    # Net -> Graph, Net -> Layers
    arrow(ax, (87, 69), (87, 72.7), "", color=NAVY, ls="--")
    ax.text(88.4, 70.9, "forward(x, g)", fontsize=6.0, color=GREY)
    arrow(ax, (87, 51.7), (87, 48), "", color=NAVY, style="-|>")
    ax.text(88.4, 49.8, "has 2", fontsize=6.4, color=GREY)
    # routers -> ml modules (retrain)
    arrow(ax, (70, 38), (75, 20.5), "retrain()", lo=(-2, 3.5), fs=6.4, color=NAVY)
    ax.text(55, 20.5, "retrain() starts train.fit_all in a background thread,\nthen calls reload_store() so the Store serves the new scores.", fontsize=6.6, ha="center", color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


def sequence():
    fig, ax = canvas(10, 9.6, 100, 96)
    names = ["Browser\n(React app)", "FastAPI\nroutes", "auth.py\n(JWT, roles)", "SQLite\ndata/app.db", "Store\n(in memory)", "ml.train\n(retrain thread)"]
    xs = [9, 26, 43, 60, 77, 92]
    for x, n in zip(xs, names):
        box(ax, x, 91.5, 13, 6.5, n, NAVY, fs=7.0, bold=True)
        ax.plot([x, x], [88, 1], color="#9AA7B8", lw=1, ls="--", zorder=1)

    def msg(i, j, text, y, color=NAVY, ls="-", dy=1.5, fs=6.8):
        arrow(ax, (xs[i], y), (xs[j], y), text, color=color, ls=ls, lo=(0, dy), fs=fs)

    y = 84.5
    ax.text(2, y + 1.3, "1  Sign in", fontsize=7.4, color=TEAL, fontweight="bold")
    msg(0, 1, "POST /api/auth/login {email, password}", y - 3)
    msg(1, 3, "select user by email", y - 6.6)
    msg(1, 2, "verify_password (bcrypt), make_token", y - 10.2)
    msg(1, 0, "200 {token (HS256, 12 h), user}", y - 13.8, ls="--")
    ax.text(2, y - 18, "2  Score and explain one account", fontsize=7.4, color=TEAL, fontweight="bold")
    msg(0, 1, "GET /api/accounts/{id}  Bearer token", y - 21.3)
    msg(1, 2, "current_user: decode JWT", y - 24.9)
    msg(2, 3, "load User, reviews", y - 28.5)
    msg(1, 4, "scores, neighbours, explain(id)", y - 32.1)
    ax.text(78.5, y - 35.4, "gradient x input through the served net", fontsize=6.4, ha="left", color=INK, style="italic")
    msg(1, 0, "200 {score, reasons, neighbourhood, history}", y - 38.0, ls="--")
    ax.text(2, y - 42, "3  Moderator decision", fontsize=7.4, color=TEAL, fontweight="bold")
    msg(0, 1, "POST /api/queue/decisions {account, confirm}", y - 45.3)
    msg(1, 2, "require_moderator (403 for analyst)", y - 48.9)
    msg(1, 3, "insert Review (members, score)", y - 52.5)
    msg(1, 0, "201 {id, affected_accounts}", y - 56.1, ls="--")
    ax.text(2, y - 60.5, "4  Retrain on the decisions", fontsize=7.4, color=ORANGE, fontweight="bold")
    msg(0, 1, "POST /api/models/retrain", y - 63.8)
    msg(1, 3, "labels from reviews; add TrainingRun(running)", y - 67.4)
    msg(1, 0, "202 {run_id, feedback_labels}", y - 71.0, ls="--")
    msg(1, 5, "thread: fit_all(graph, [0], feedback)", y - 74.6)
    msg(5, 4, "write_artifacts; reload_store()", y - 78.2)
    msg(5, 3, "run done: f1_after; reviews.used_in_run", y - 81.8, ls="--", dy=-1.9)
    save(fig, OUT / "07_sequence_flow.png")


def use_case():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.add_patch(Rectangle((24, 2), 54, 71, fc="#F7F9FC", ec=GREY, lw=1.3, zorder=0))
    ax.text(51, 70, "BotGraph", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    cases = [(63.5, "Sign in (demo analyst or moderator)"), (56.5, "View overview and graph & features"), (49.5, "Browse and search ranked accounts"),
             (42.5, "Inspect an account: reasons, neighbourhood"), (35.5, "Explore botnet clusters"), (28.5, "Compare models and scalability"),
             (21.5, "Confirm or dismiss an account or cluster"), (14.5, "Undo a decision not yet used"), (7.5, "Retrain on logged decisions")]
    for y, t in cases:
        ellipse(ax, 51, y, 42, 5.6, t, PALE_ORANGE if y < 24 else PALE_BLUE, ORANGE if y < 24 else BLUE, fs=7.8)
    box(ax, 10, 42.5, 15, 12, "Analyst\n(read-only)", WHITE, tc=INK, ec=NAVY, fs=8.2, bold=True)
    box(ax, 10, 14.5, 15, 12, "Moderator", WHITE, tc=INK, ec=NAVY, fs=8.4, bold=True)
    box(ax, 90, 42.5, 15, 12, "Researcher\n(uses the\nanalyst login)", WHITE, tc=INK, ec=NAVY, fs=7.6, bold=True)
    for y, _t in cases[:6]:
        arrow(ax, (17.5, 42.5), (30, y), color=GREY, lw=1.0, style="-")
    for y, _t in cases[6:]:
        arrow(ax, (17.5, 14.5), (30, y), color=ORANGE, lw=1.2, style="-")
    arrow(ax, (10, 20.5), (10, 36.5), "", color=NAVY, lw=1.4, style="-|>")
    ax.text(11.5, 28.5, "inherits all\nanalyst use cases", fontsize=6.6, ha="left", color=GREY, style="italic")
    for y in (56.5, 35.5, 28.5):
        arrow(ax, (82.5, 42.5), (72, y), color=GREY, lw=1.0, style="-")
    ax.text(50, 0.2, "Moderator-only routes return 403 for the analyst. Researcher is a way of using the app, not a separate login role.", ha="center", fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


if __name__ == "__main__":
    system_architecture(); high_level_workflow(); dfd0(); uml_class_diagram(); sequence(); use_case()
    import diagrams_dfd
    diagrams_dfd.main()
    import diagrams_more
    diagrams_more.main()
