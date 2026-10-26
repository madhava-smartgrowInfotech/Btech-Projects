"""Appendices A (important code), B (installation and user guide) and C (additional screens) for BotGraph."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


GNN = "ml/gnn.py"
CLU = "ml/clustering.py"
TRN = "ml/train.py"
QUE = "backend/app/routes/queue.py"
MOD = "backend/app/routes/models.py"
STO = "backend/app/services/store.py"
AUTH = "backend/app/auth.py"


def _code_report():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` in the state in which the results were measured (whole statements; the full files are in the repository)."),
        H2("A.1 The GCN and GraphSAGE layers (`ml/gnn.py`)"),
        CODE(src(GNN, 35, 52), 7.5),
        H2("A.2 The training loop"),
        CODE(src(GNN, 148, 182), 7.5),
        H2("A.3 Botnet clusters (`ml/clustering.py`)"),
        CODE(src(CLU, 17, 41), 7.5),
        H2("A.4 Moderator feedback and retraining"),
        CODE(src(TRN, 35, 44) + "\n\n" + src(MOD, 65, 71), 7.5),
        CODE(src(QUE, 80, 101), 7.5),
    ]


def code_blocks():
    if F.REPORT:
        return _code_report()
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Docstrings and comments are kept as they are; "
          "each range is a whole statement or method."),
        H2("A.1 Graph structure for the layers (`ml/gnn.py`)"),
        P("`Graph` is built once from the undirected tie list. It stores both directions of every tie plus self-loops, the symmetric normalisation weights used by GCN (`a_hat`) and the row-normalised mean operator used by GraphSAGE (`a_mean`)."),
        CODE(src(GNN, 16, 32), 8),
        H2("A.2 GCN and GraphSAGE layers"),
        P("A GCN layer multiplies the normalised adjacency by the transformed features. A GraphSAGE layer keeps a separate weight for the account itself and one for the mean of its neighbours, "
          "which is the difference that Chapter 8 identifies as the likely reason for its better recall."),
        CODE(src(GNN, 35, 52), 8),
        H2("A.3 Graph attention layer"),
        P("PyTorch has no edge softmax for sparse graphs, so it is computed with `scatter_reduce` (maximum for stability) and `index_add_` (denominator and weighted sum). "
          "The order in which `index_add_` sums is not deterministic, which is why GAT results can move by about 0.01 between runs."),
        CODE(src(GNN, 54, 79), 8),
        H2("A.4 The network and the training loop"),
        P("Two message-passing layers (two dense layers for the baseline) and a linear head. Training uses a class-weighted cross-entropy and keeps the epoch with the best validation F1, stopping after 40 epochs without improvement."),
        CODE(src(GNN, 82, 116), 8),
        CODE(src(GNN, 148, 182), 8),
        H2("A.5 Botnet clusters (`ml/clustering.py`)"),
        P("Accounts at or above 0.30 become candidates; each is linked to its five most similar candidates in embedding space and to every candidate it is really tied to; Louvain finds the communities and groups under five accounts are dropped."),
        CODE(src(CLU, 17, 41), 8),
        H2("A.6 Scoring a recovery against the injected botnets"),
        CODE(src(CLU, 78, 100), 8),
        H2("A.7 Moderator feedback in training (`ml/train.py`)"),
        P("Decisions arrive as a map from account id to label. Accounts in the test split are skipped, reviewed accounts join the training set and leave the validation set."),
        CODE(src(TRN, 27, 44), 8),
        H2("A.8 Explaining one score (`backend/app/services/store.py`)"),
        P("The reason shown for an account is the gradient of the fake-versus-genuine margin multiplied by the input, which is a first-order approximation; the sum over other accounts' features is reported as the network contribution."),
        CODE(src(STO, 132, 152), 8),
        H2("A.9 Recording and undoing a decision (`backend/app/routes/queue.py`)"),
        CODE(src(QUE, 80, 113), 8),
        H2("A.10 Retraining on decisions (`backend/app/routes/models.py`)"),
        P("Every logged decision becomes a label (confirm is fake, dismiss is genuine), a run record stores the F1 before, and the work happens in a background thread so that the API stays responsive."),
        CODE(src(MOD, 65, 71) + "\n\n" + src(MOD, 110, 124), 8),
        H2("A.11 Sign-in and role guard (`backend/app/auth.py`)"),
        CODE(src(AUTH, 25, 42) + "\n\n...\n\n" + src(AUTH, 53, 70), 8),
    ]


def guide_blocks():
    return _guide_report() if F.REPORT else _guide_full()


def _guide_report():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements and start"),
        B("Windows 10 or 11, **Python 3.11 or newer** (tick *Add python.exe to PATH*), **Node.js LTS**, about 3 GB of free disk space (PyTorch is the large part) and an internet connection for the first set-up only.",
          f"Double-click `run.bat` in `8.ProjectCode`. The first run calls `setup.bat`, which creates `.venv`, installs the Python and web packages and takes several minutes. Afterwards it starts the API on http://127.0.0.1:{F.API_PORT} "
          f"and the web app on http://localhost:{F.WEB_PORT} and opens the browser. Two minimised windows named *BotGraph API* and *BotGraph web app* keep it running; close them to stop."),
        TAB("Demo sign-ins (password `Demo@1234`)", ["Role", "Email", "Can do"],
            [["Moderator", "`moderator@botgraph.app`", "Everything, including confirm / dismiss and retraining"],
             ["Analyst", "`analyst@botgraph.app`", "Explore accounts, botnets and model results (read-only)"]], widths=[1.1, 2.4, 3.0], align=["l", "l", "l"], size=10),
        CODE("ml.data      rebuild the graph from the committed datasets\n"
             "ml.train     train all models -> models/, experiments/metrics.json (a few minutes on CPU)\n"
             "ml.eval      scalability sweep -> experiments/scalability.json, experiments/eval/metrics.json\n"
             "scripts/smoke_test.py            36 end-to-end checks on a scratch copy\n"
             "scripts/run_extra_experiments.py threshold sweep, error analysis, feature-group ablation\n"
             "scripts/capture_screens.py       re-capture the screenshots (app must be running)", 8.5),
        B("**Python was not found:** install Python 3.11+ with *Add to PATH*, open a new terminal and run `setup.bat` again.  **API offline:** close both windows and run `run.bat` again.  "
          "**Port in use:** change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`.  **Wrong password:** use `Demo@1234`, or delete `data/app.db` and restart to re-create the demo users."),
    ]


def _guide_full():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11, 64-bit. **Python 3.11 or newer** (tick *Add python.exe to PATH* in the installer) and **Node.js LTS**.",
          "About 3 GB of free disk space (PyTorch is the large part) and 16 GB of memory is comfortable; the measurements in this report used " + F.HARDWARE + ".",
          "Internet access for the first set-up only. The datasets, the trained models, the scores and the clusters are part of the repository, so nothing has to be trained before the first start."),
        H2("B.2 Quick start with run.bat"),
        N("Open the `8.ProjectCode` folder and double-click `run.bat`. If `.env` is missing it is copied from `.env.example`.",
          "On the first run the script calls `setup.bat`, which creates `.venv`, installs `backend/requirements.txt` (FastAPI, SQLAlchemy, PyJWT, bcrypt, PyTorch, NumPy, pandas, scikit-learn, networkx) and installs the web packages with npm. PyTorch is the slow part.",
          f"The API starts on http://127.0.0.1:{F.API_PORT} (interactive documentation at `/docs`) and the web app on http://localhost:{F.WEB_PORT}; the browser opens on the web app.",
          "Two minimised windows named *BotGraph API* and *BotGraph web app* keep the servers running. Close them to stop. Later starts take a few seconds."),
        H2("B.3 Demo sign-in"),
        TAB("Demo accounts (password `Demo@1234`)", ["Role", "Email", "Can do"],
            [["Moderator", "`moderator@botgraph.app`", "Everything, including confirm / dismiss and retraining"],
             ["Analyst", "`analyst@botgraph.app`", "Explore accounts, botnets and model results (read-only; decisions and retraining return 403)"]],
            widths=[1.1, 2.4, 3.0], align=["l", "l", "l"], size=10),
        P("The sign-in page has *Fill* buttons for both accounts and a one-click demo sign-in as the moderator."),
        H2("B.4 Using the web app"),
        TAB("Screens and what to do on each", ["Screen", "Route", "What to do"],
            [["Landing", "/", "Read the summary, switch theme, press *Try the demo*."],
             ["Overview", "/app", "Read the five counters, the score histogram and the model comparison; *Open the queue* for review."],
             ["Graph & features", "/app/graph", "Node and tie counts, which parts are real or injected, the graph schema, the 23 features by group."],
             ["Accounts", "/app/accounts", "Search by handle or name; filter by status and botnet; sort by probability, followers, ties, age or flagged neighbours."],
             ["Account detail", "/app/accounts/:id", "Read the probability from every model, the traits behind the score, the profile and the neighbourhood graph; confirm or dismiss."],
             ["Botnet clusters", "/app/clusters", "Compare size, tie density, shared peak hour and creation spread; open one."],
             ["Cluster detail", "/app/clusters/:id", "Inspect the cluster graph and members; confirm or dismiss all members at once."],
             ["Moderator queue", "/app/queue", "Work through accounts and clusters; read the decision log; press *Retrain with decisions*."],
             ["Models & scale", "/app/models", "Comparison table and charts, scalability curves, retraining runs with F1 before and after."]],
            widths=[1.3, 1.4, 3.8], align=["l", "l", "l"], size=9.5),
        H2("B.5 A five-minute tour"),
        N("**Graph & features:** node and edge counts, which parts are real data, the 23 features.",
          "**Models & scale:** the three architectures against the no-graph baseline; open *Scalability*.",
          "**Accounts:** open the top account: its probability, the traits behind it, its neighbourhood graph.",
          "**Botnet clusters:** open a coordinated cluster; the injected botnets come back as single communities.",
          "**Moderator queue:** dismiss one member and confirm another; see both in the *Decision log*, then press *Retrain with decisions*."),
        H2("B.6 Commands"),
        P("Run from the `8.ProjectCode` folder with the project environment (`.venv\\Scripts\\python`)."),
        CODE("python -m ml.data                        # rebuild the graph from data/raw\n"
             "python -m ml.train                       # train 4 models x 3 seeds; writes models/ and experiments/metrics.json\n"
             "python -m ml.eval                        # scalability sweep and experiments/eval/metrics.json\n"
             "python scripts/smoke_test.py             # 36 end-to-end checks (own API, scratch database)\n"
             "python scripts/run_extra_experiments.py  # threshold sweep, error analysis, feature-group ablation\n"
             "cd frontend && npm run build             # production build of the web app\n"
             "python scripts/capture_screens.py        # re-capture the screenshots (app must be running)", 8.5),
        H2("B.7 Settings (`.env`)"),
        TAB("Settings", ["Key", "Meaning"],
            [["`BACKEND_PORT`", f"API port, {F.API_PORT}"], ["`FRONTEND_PORT`", f"web app port, {F.WEB_PORT}"],
             ["`DATABASE_URL`", "SQLite file for users, decisions and retraining runs (`data/app.db`, created on first start)"],
             ["`JWT_SECRET`", "signs the login tokens; replace the placeholder with a long random string for anything beyond a local demo (otherwise a fixed development secret is used)"]],
            widths=[1.6, 4.9], align=["l", "l"], size=10),
        H2("B.8 Troubleshooting"),
        B("**`Python ... was not found`:** install Python 3.11+, tick *Add to PATH*, open a new terminal and run `setup.bat` again.",
          "**Set-up stops while installing PyTorch:** check the connection and run `setup.bat` again; it resumes.",
          "**The page says *API offline*:** the API window closed or its port is busy. Close both BotGraph windows and run `run.bat` again.",
          "**`Port 5309 is already in use`:** another copy is running; close the old windows or change the ports in `.env`.",
          "**Sign-in says the password is wrong:** use `Demo@1234`. If users were changed, delete `data/app.db` and restart to re-create the demo accounts.",
          "**To wipe moderator decisions:** stop the app, delete `data/app.db`, start again.",
          "**`WinError 1114` when importing torch with a system Python:** import `torch` before `fastapi`, numpy or pandas (the project `.venv` does not show it)."),
    ]


# screens shown in Chapter 8 are listed there; Appendix C holds the ones the report chapter leaves out
APPX_SCREENS = [
    ("03_login.png", "Sign-in page with the one-click demo accounts.",
     "The sign-in page, with the moderator and analyst demo accounts offered as buttons that fill the credentials."),
    ("05_graph_and_features.png", "Graph and features screen: counts, data provenance and the 23 features.",
     "Node and tie counts split into real and injected, the class balance, the split sizes and the feature table with genuine and fake means."),
    ("11_queue_clusters.png", "Moderator queue, botnet clusters tab.",
     "Clusters awaiting a decision with their type, size, average fake probability and tie density; a decision applies to every member."),
    ("16_overview_dark.png", "Overview screen in the dark theme.",
     "The Overview screen with the same counters and charts in the dark theme."),
    ("02_landing_dark.png", "Landing page, dark theme.",
     "The same landing page in the dark theme. The theme button at the top right switches between the two and the choice is remembered in the browser."),
    ("07b_account_reasons_and_neighbourhood.png", "Account detail, lower half: reasons and neighbourhood.",
     "The lower half of the account page for @quartzaurora00880118. *Why this score* lists the account's own traits that push towards fake (rose bars): account age, share of activity in the peak hour, posting burstiness, digits in the username. "
     "A note states that the accounts around it add +9.73 to the model margin and that the reasons are a gradient-times-input approximation. *Profile and behaviour* shows the raw values, and a note repeats that the dataset label is used only for evaluation."),
    ("09b_cluster_graph_and_members.png", "Cluster detail with the cluster graph in a second layout state.",
     "A second capture of the cluster page for BN-00112, taken while the force layout was still moving; the 65 members appear as a tight pink group with a few outlying real accounts."),
    ("12_decision_log.png", "Moderator queue, Decision log tab.",
     "The log lists each decision with its time, target, decision, number of accounts affected and the moderator. Here a cluster of 34 accounts and two single accounts appear, and the right-hand panel shows that 38 labelled accounts are ready for the next training run."),
    ("14_models_scalability.png", "Models & scale, Scalability tab.",
     "Training time per epoch and inference time against graph size, one line per model. GAT rises fastest, GCN and GraphSAGE stay close together and the baseline is almost flat."),
    ("15_models_retraining.png", "Models & scale, Retraining tab before any run.",
     "With no run recorded the tab shows an empty state that tells the moderator what to do. The retraining results themselves are reported in Chapter 8."),
]


def screens_blocks():
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens complete the set of real captures of the running application (1440 x 900, shipped GraphSAGE model and committed data). The screens used in Chapter 8 are not repeated here.")]
    if F.REPORT:
        for k in range(0, len(APPX_SCREENS), 2):
            a, b = APPX_SCREENS[k], APPX_SCREENS[k + 1]
            out.append(PAIR([(F.shot(a[0]), a[1]), (F.shot(b[0]), b[1])], 3.0))
        out.append(P("Left to right, top to bottom: the sign-in page; the graph and features screen; the clusters tab of the moderator queue; the Overview screen in the dark theme; the landing page in the dark theme; the reasons and neighbourhood of one account; "
                     "the cluster graph of BN-00112 in a second layout state; the decision log with a 34-account cluster decision; the scalability curves; and the Retraining tab before any run. Each is described in its caption."))
        return out
    for i, (fn, cap, text) in enumerate(APPX_SCREENS, 1):
        out.append(H2(f"C.{i} {cap.rstrip('.')}"))
        out.append(P(text))
        out.append(FIG(F.shot(fn), cap, F.shot_w(F.shot(fn), 5.2, 3.6)))
    return out
