"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for BotGraph."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB

_T = {m: F.MODELS[m]["train_seconds"] for m in F.ORDER}
_ONE_SEED_RETRAIN = sum(_T.values())          # four models, one seed each (derived from the measured per-run times)
_S1, _S8 = F.scal_row(1), F.scal_row(8)
_SAGE1, _SAGE8 = _S1["models"]["sage"], _S8["models"]["sage"]
_GAT1, _GAT8 = _S1["models"]["gat"], _S8["models"]["gat"]


def blocks():
    out = chapter3() + chapter4()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: drop the least essential sections and secondary tables so the full report stays within its page budget."""
    drop_h2 = ("3.6 Risk Assessment", "4.8 Usage Scenarios")
    drop_tabs = ("Cost items and how each", "Existing approaches and what", "Data sources")
    out, skipping = [], False
    for b in bl:
        if b[0] in ("h1", "h2"):
            skipping = b[0] == "h2" and b[1] in drop_h2
        if skipping:
            continue
        if b[0] == "tab" and b[1].startswith(drop_tabs):
            continue
        if b[0] == "p" and b[1].startswith("The minimum column states"):
            continue
        if b[0] == "p" and b[1].startswith("BotGraph was built entirely from open-source"):
            b = ("p", b[1].replace("The numbers below describe what the project needs; no monetary figure is given because none was measured.", "The stack is listed in Section 4.6, the data in Section 4.9 and the machine in Section 4.5; no monetary figure is given because none was measured."))
        out.append(b)
    return out


# =====================================================================================================================
def chapter3():
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built, run and maintained with the resources at hand. For BotGraph the question was answered partly by analysis "
          "and partly by building the system and measuring it on the development machine, so most entries below carry a measured value rather than an estimate. "
          "Where a question could not be settled with the data available to the team, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk lay in five places: whether three graph neural network layers could be written and trained without a specialised graph library; whether the models "
          "could be trained and served on an ordinary processor; whether public data with real social-graph structure and labelled fake-account attributes could be obtained "
          "and joined into one graph; whether botnet clusters could be recovered from the learned embeddings; and whether all of it could sit behind one API and one web "
          f"application. The development machine is a desktop with an {F.HARDWARE}. It was shared with other jobs during the measurements, so timings are upper bounds."),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can GCN, GAT and GraphSAGE be implemented without torch-geometric?",
             "Yes: `ml/gnn.py` is 188 lines of plain PyTorch sparse operations; all four models train on the same split and the same features", "Feasible"],
            ["Can the models be trained on a CPU?",
             f"Mean time per training run: baseline {_T['baseline']:.1f} s, GCN {_T['gcn']:.1f} s, GraphSAGE {_T['sage']:.1f} s, GAT {_T['gat']:.1f} s "
             f"(up to {F.M['meta']['config']['epochs']} epochs, early stopping)", "Feasible"],
            ["Can real graph data and labelled fake-account data be combined?",
             f"Yes: {F.REAL_NODES:,} real accounts and {F.REAL_EDGES:,} real ties come from ten Facebook ego networks; profile and posting rows come from two labelled public sets; "
             f"the committed raw data is under 10 MB", "Feasible, with a caveat"],
            ["Does the graph help detection?",
             f"F1 on the 908-account test split: baseline {F.mean('baseline', 'f1'):.3f}, GCN {F.mean('gcn', 'f1'):.3f}, GAT {F.mean('gat', 'f1'):.3f}, "
             f"GraphSAGE {F.mean('sage', 'f1'):.3f} (mean of three seeds)", "Feasible"],
            ["Can botnets be recovered from the embeddings?",
             f"{F.REC['recovered']} of {F.REC['botnets']} injected botnets recovered as single Louvain communities (mean recall {F.REC['mean_recall']:.3f}, mean precision {F.REC['mean_precision']:.3f})", "Feasible on injected botnets"],
            ["Does cost grow acceptably with graph size?",
             f"GraphSAGE epoch {_SAGE1['train_seconds_per_epoch']:.3f} s at {_S1['nodes']:,} accounts and {_SAGE8['train_seconds_per_epoch']:.3f} s at {_S8['nodes']:,} accounts "
             f"({_S8['edges']:,} ties)", "Feasible to the size measured"],
            ["Can everything run behind one local API?",
             f"FastAPI with 18 routes, SQLite for users, decisions and retraining runs; {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke-test checks pass; median API latency 3 to 16 ms", "Feasible"],
        ], widths=[1.9, 3.3, 1.1], size=10, align=["l", "l", "l"]),
        P("The weakest point is the data, not the technology. Eight botnets and 150 lone spammers were injected into the real topology by a seeded script, and the timing and "
          "interaction features are generated, because no public data set offers a real social graph with labelled coordinated botnets, posting-time features and profile "
          "attributes at the same time. The technical feasibility of cluster recovery was therefore established against a known answer, which shows that the method finds "
          "this kind of coordination but not how often real botnets look like it. Chapter 8 repeats this caveat next to every result."),
        P("A second, smaller risk is the dependency chain on Windows. On the system Python used for the documentation run, importing `fastapi` before `torch` made the "
          "PyTorch libraries fail to initialise (WinError 1114). The smoke test and the experiment scripts therefore import `torch` first. The risk is cheap to remove and "
          "the project builds its own virtual environment through `setup.bat`."),

        H2("3.2 Economic Feasibility"),
        P("BotGraph was built entirely from open-source software and public data, so the economic question reduces to hardware and effort. No licence, subscription, "
          "hosted service or paid data source is involved, and the application makes no call to an outside service while it runs. The numbers below describe what the project "
          "needs; no monetary figure is given because none was measured."),
        TAB("Cost items and how each was covered", ["Item", "What was used", "Cost position"], [
            ["Programming language and ML library", "Python 3.11 and PyTorch (CPU build); NumPy, pandas, scikit-learn and networkx for data, metrics and Louvain", "No licence cost"],
            ["Back end", "FastAPI, Uvicorn, SQLAlchemy 2 with SQLite, PyJWT, bcrypt", "No licence cost"],
            ["Front end", "React 18, Vite 5, Recharts, react-force-graph-2d, Framer Motion, GSAP, lucide icons", "No licence cost"],
            ["Data", "SNAP Facebook ego networks (public research data), Instagram fake-account set (CC BY 3.0), Twitter bot set (CC0)", "No licence cost; about 8 MB committed to the repository"],
            ["Compute", f"{F.HARDWARE}; no GPU used; full training of four models for three seeds fits in minutes", "Existing machine"],
            ["Operations", "One Windows computer, two processes (API on 8309, web on 5309), one SQLite file", "No hosting cost for the demonstration"],
            ["Effort", "Four students under a faculty guide; effort was not logged", "Academic, not costed"],
        ], widths=[1.4, 3.3, 1.6], size=10, align=["l", "l", "l"]),
        P("Two cost drivers would change at platform scale: memory and training time grow with the number of ties, and a production service would need a GPU or a sampled "
          f"mini-batch design. The sweep in Chapter 8 measured {_S8['edges']:,} ties on a CPU in under half a second per GraphSAGE epoch, which says nothing about a graph "
          "thousands of times larger. The economic case for the demonstration is therefore sound; the case for a platform deployment is untested."),

        H2("3.3 Operational Feasibility"),
        P("Operational feasibility asks whether the people who would use the system can do so without effort that outweighs the benefit. BotGraph has two kinds of users. "
          "An **analyst** watches the overview, studies accounts and clusters and reads model results; a **moderator** does the same and also records decisions and starts "
          "retraining. Both sign in with an e-mail address and a password, and the sign-in page offers the two demonstration accounts."),
        B("**Set-up.** `setup.bat` creates the virtual environment, installs the Python and Node packages and takes several minutes the first time because PyTorch is large; "
          "`run.bat` then starts the API and the web application in a few seconds. The trained models, scores and clusters are committed, so nothing needs training before the first start.",
          f"**Daily use.** Every screen answers one question: who is flagged, what does the neighbourhood of this account look like, which botnets exist, what is waiting for review, "
          f"and how good is the model. API calls return in a median of 3 to 16 ms, so the interface feels immediate.",
          f"**Maintenance.** Retraining is a button for moderators. It trains the four models with one seed on the logged decisions and takes about {_ONE_SEED_RETRAIN:.0f} s of training, "
          "the sum of the measured per-run times, plus clustering. The full three-seed evaluation is a command, `python -m ml.train`.",
          "**Skills.** A moderator needs no machine-learning knowledge: each account shows a probability, the traits that pushed it up or down and a picture of its neighbours. "
          "Changing models or data needs Python and PyTorch knowledge."),
        P("What operational feasibility does not cover is organisational: the demonstration has two seeded users, no password reset, no audit export and no integration with a "
          "platform's moderation tooling. Those belong to Chapter 10."),

        H2("3.4 Schedule Feasibility"),
        P("No dated project log was kept, so the schedule below is the **planned** schedule the work followed, expressed in weeks rather than dates, and it is offered as a "
          "feasibility check and not as a record. The order matters more than the durations: the data and graph builder come first because every later step reads them, and "
          "the interface comes last because it only displays what the models and the API already produce."),
        TAB("Planned schedule (weeks, indicative)", ["Phase", "Work", "Planned weeks"], [
            ["1", "Problem study, literature survey, base-paper reading, objectives", "2"],
            ["2", "Data collection, graph builder, 23 node features, injected botnets (`ml/data.py`)", "2"],
            ["3", "GCN, GAT, GraphSAGE and baseline, training loop, threshold selection (`ml/gnn.py`, `ml/train.py`)", "3"],
            ["4", "Botnet clustering, recovery measure, scalability sweep (`ml/clustering.py`, `ml/eval.py`)", "2"],
            ["5", "API, authentication, SQLite storage, moderator queue and retraining (`backend/app`)", "2"],
            ["6", "Web application: ten screens, charts, neighbourhood graph, light and dark themes (`frontend/src`)", "3"],
            ["7", "Smoke test, screenshots, measurements, documents and review preparation", "2"],
        ], widths=[0.6, 4.6, 1.1], size=10.5, align=["c", "l", "c"]),
        P("The plan sums to 16 weeks. Its main assumption, that the models and the interface could proceed in sequence on one machine, held; the main risk, that the graph "
          "would add nothing over the profile features, is addressed in the design: a share of bots is given genuine-looking profiles so that the profile alone cannot solve the task, and the final comparison shows a gain for all three graph models."),

        H2("3.5 Advantages and Constraints"),
        H3("3.5.1 Advantages"),
        B("The graph is used for what it is good at: an account that looks ordinary by itself is scored against who it follows and who follows it.",
          f"Three architectures are compared on the same split with a no-graph baseline, so the value of the graph is a measured number (GraphSAGE +{F.lift('sage'):.1f} F1 points), not an assumption.",
          "Botnets are reported as groups with size, tie density, shared peak hour and reach, which is how a moderator thinks about them.",
          "Decisions flow back as labels while the test split stays untouched, so improvement can be measured fairly.",
          "Nothing is hidden: each score has its traits and neighbourhood, and the interface states which data are real and which are generated."),
        H3("3.5.2 Constraints"),
        B("Botnets and part of the features are synthetic; results describe this benchmark and not a live platform.",
          "There are no text or linguistic features, although the project abstract mentions behavioural language cues.",
          f"The graph is a single static snapshot of {F.NODES:,} accounts; the scale test goes to {_S8['nodes']:,} accounts using disjoint copies of that graph.",
          "Three seeds and one split give a standard deviation but not a confidence interval; there is no cross-validation.",
          "Authentication is a demonstration: two seeded users, JWT tokens, no password reset, no rate limiting."),

        H2("3.6 Risk Assessment"),
        TAB("Principal risks and the measure taken", ["Risk", "Effect", "Measure taken"], [
            ["Profile attributes alone could solve the task, leaving the graph with nothing to add", "A misleading comparison", "40% of botnet accounts and 25% of lone spammers received genuine-looking profiles; 6% of genuine accounts received fake-looking ones"],
            ["Class imbalance (12.6% fake)", "High accuracy with poor recall", "Class-weighted loss, threshold tuned on validation F1, F1, precision, recall and PR-AUC reported instead of accuracy alone"],
            ["Run-to-run variation", "A lucky seed reported as the result", "Three seeds per model; mean and standard deviation reported; GAT variation noted"],
            ["Test-set leakage through moderator feedback", "Inflated before/after comparison", "Reviewed accounts move only into training; test-split accounts are never relabelled"],
            ["Library import failure on Windows", "API or scripts do not start", "`torch` imported first in scripts; environment built by `setup.bat`"],
            ["Scale beyond what was measured", "Unknown cost on a real platform", "The claim is limited to 36,264 accounts and 755,648 ties; mini-batch training listed as future work"],
        ], widths=[2.2, 1.6, 2.5], size=10, align=["l", "l", "l"]),
    ]


# =====================================================================================================================
def chapter4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter states what BotGraph replaces, what it must do and what it needs in order to run. Requirements are numbered so that Chapter 7 can test them and Chapter 8 "
          "can report whether each was met."),

        H2("4.1 Existing System and Its Limitations"),
        P("Platforms defend against fake accounts with three layers that are older than graph learning. **Manual moderation** reviews reports and flagged profiles one at a time. "
          "**Rule-based filters** match patterns such as a missing profile picture, a username made of digits or a burst of posts. **Per-account classifiers** learn those "
          "signals from labelled profiles and score each account on its own attributes. The feature-only baseline in this project is a faithful stand-in for the third layer: "
          "it reads the same 23 features as the graph models and ignores every tie."),
        TAB("Existing approaches and what each leaves open", ["Approach", "What it sees", "Limitation shown in this project"], [
            ["Manual review", "One reported account at a time", "Cannot keep pace with account creation; nothing links one report to a group"],
            ["Rules and signatures", "Fixed thresholds on single attributes", "Go stale as behaviour changes; camouflaged accounts pass every rule"],
            ["Per-account classifier (no-graph baseline)", "The account's own 23 features",
             f"Misses accounts whose profile looks genuine: F1 {F.mean('baseline', 'f1'):.3f}, recall {F.mean('baseline', 'recall'):.3f}; sees no group"],
            ["Influence-oriented graph work such as the base paper", "Graph structure for ranking or classifying nodes by role", "Targets influential users, not fake ones; no bot labels, clusters or moderator loop"],
        ], widths=[1.8, 1.9, 2.6], size=10, align=["l", "l", "l"]),
        P("The central limitation is that each layer judges an account in isolation. A coordinated network is dangerous precisely because every member can be made to look "
          "ordinary, while the members' ties to each other and their shared timing are what give them away. A defence also needs a human step: a flag is only useful if someone "
          "can inspect it and the decision can improve the next model."),

        H2("4.2 Proposed System and Its Advantages"),
        P("BotGraph treats the platform as a graph in which accounts are nodes and interactions are undirected ties. It builds 23 features for every account, trains GCN, GAT "
          "and GraphSAGE alongside a no-graph baseline, serves the best architecture, groups suspicious accounts into botnet clusters with Louvain community detection over "
          "their embeddings, and gives moderators a queue whose decisions feed the next training run."),
        B(f"**Relational context.** The best model reaches F1 {F.mean('sage', 'f1'):.3f} against {F.mean('baseline', 'f1'):.3f} for the no-graph baseline on the same {F.TEST_N} test accounts.",
          f"**Group view.** {F.REC['recovered']} of {F.REC['botnets']} injected botnets come back as one cluster each, with size, density, shared peak hour and reach shown.",
          "**Explanations.** Each account shows the traits that pushed its score up or down and the contribution of its neighbours (a first-order gradient-times-input estimate, labelled as such).",
          "**Human in the loop.** Confirm or dismiss an account or a whole cluster; decisions are logged, can be undone until used, and become training labels.",
          "**Measured scale.** Training and inference time are reported as the graph grows from 4,533 to 36,264 accounts."),

        H2("4.3 Functional Requirements"),
        P("The seven features of the product are the functional core; the remaining rows are the access and housekeeping functions around them."),
        TAB("Functional requirements", ["ID", "Requirement", "Where it is met"], [
            ["FR1 (F1)", "Build one graph from accounts and interactions with a documented schema (node, edge, split, origin)", "`ml/data.py`; `GET /api/graph/summary`; screen *Graph and features*"],
            ["FR2 (F2)", "Compute 23 node features in four groups: profile metadata 12, posting behaviour 4, temporal pattern 6, interaction frequency 1", "`ml/data.py`; same screen"],
            ["FR3 (F3)", "Train GCN, GAT, GraphSAGE and a feature-only baseline on one split with the same budget and three seeds", "`ml/gnn.py`, `ml/train.py`; screen *Models and scale*"],
            ["FR4 (F4)", "Give every account a fake probability, the traits behind it and its neighbourhood", "`GET /api/accounts`, `/{id}`, `/{id}/neighbourhood`; screens *Accounts*, *Account detail*"],
            ["FR5 (F5)", "Group suspicious accounts into botnet clusters and describe each", "`ml/clustering.py`; `GET /api/clusters`, `/{id}`; screens *Botnet clusters*, *Cluster detail*"],
            ["FR6 (F6)", "Let a moderator confirm or dismiss an account or a cluster, log it, undo it until used, and retrain on the decisions", "`POST /api/queue/decisions`, `DELETE`, `POST /api/models/retrain`; screen *Moderator queue*"],
            ["FR7 (F7)", "Report accuracy, precision, recall, F1, ROC-AUC and PR-AUC per model, confusion matrices, ROC curves and a scalability sweep", "`experiments/*.json`; `GET /api/models`, `/scalability`"],
            ["FR8", "Sign in with e-mail and password; two roles, analyst (read-only) and moderator", "`backend/app/auth.py`; `POST /api/auth/login`, `GET /api/auth/me`"],
            ["FR9", "Search, filter, sort and page through accounts (query, status, cluster, flagged only; five sort keys)", "`GET /api/accounts`"],
            ["FR10", "Show an overview: counts, score histogram, model comparison, top accounts and clusters, recent decisions", "`GET /api/overview`"],
            ["FR11", "Refuse decisions and retraining from analysts and unauthenticated callers", "`require_moderator`; 401 and 403 responses"],
            ["FR12", "Report health and key counts without signing in", "`GET /api/health`"],
        ], widths=[0.8, 3.4, 2.1], size=9.5, align=["c", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and their measured status", ["ID", "Requirement", "Status"], [
            ["NFR1 Accuracy", f"Beat the no-graph baseline on F1 with the served model", f"Met: {F.mean('sage', 'f1'):.3f} against {F.mean('baseline', 'f1'):.3f}; GCN gain only {F.lift('gcn'):.1f} points"],
            ["NFR2 Responsiveness", "Interactive latency for every read route", "Met: medians 3.0 to 16.0 ms, p95 at most 28.4 ms on 127.0.0.1 (20 requests per route)"],
            ["NFR3 Start-up", "API ready in seconds with no training step", f"Met: {F.STARTUP_S} s to the first healthy response"],
            ["NFR4 Scalability", "Cost grows about in proportion to ties", f"Met to {_S8['edges']:,} ties on CPU; larger graphs not tested"],
            ["NFR5 Security", "Passwords hashed; signed expiring tokens; role checks on the server; CORS limited to the web origin", "Met for the demonstration (bcrypt, HS256 JWT valid 12 hours); no rate limiting or password reset"],
            ["NFR6 Reproducibility", "Fixed seeds, committed data and models, one command to retrain", "Met; GAT can move by about 0.01 F1 between runs"],
            ["NFR7 Usability", "Loading, empty, error and success states; light and dark themes; keyboard use; widths from 360 to 1440 px", "Checked when the interface was built (`scripts/ui_checks.py`); not repeated in the documentation run"],
            ["NFR8 Portability", "Runs on one Windows computer without a GPU", f"Met on the measurement machine ({F.HARDWARE})"],
            ["NFR9 Honesty of data", "Say which data are real and which are generated", "Met: provenance table on the graph screen and in the documents"],
        ], widths=[1.3, 2.6, 2.4], size=9.5, align=["l", "l", "l"]),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum to run", "Used for the measurements"], [
            ["Processor", "Any 64-bit x86 processor with four or more threads", "Intel Core i5-12500, 6 cores, 12 threads"],
            ["Memory", "8 GB", "16 GB (16,073 MB)"],
            ["Disk", "About 3 GB free (the PyTorch environment is most of it)", "Local SSD"],
            ["Graphics processor", "Not required", "None used"],
            ["Network", "Needed only for the first installation of packages", "Not needed at run time"],
        ], widths=[1.4, 2.6, 2.3], size=10.5, align=["l", "l", "l"]),
        P("The minimum column states what the installation guide asks for, not a tested floor; only the third column was measured."),

        H2("4.6 Software Requirements"),
        TAB("Software", ["Layer", "Component", "Version or constraint"], [
            ["Operating system", "Windows 10 or 11", "Windows 11 Pro on the measurement machine"],
            ["Language", "Python", "3.11 or newer (3.11.9 used)"],
            ["Deep learning", "PyTorch (CPU)", "`torch>=2.2,<2.6` pinned in requirements; 2.14.1+cpu on the system interpreter used for the documentation runs"],
            ["Data and graph", "NumPy, pandas, scikit-learn, networkx", "NumPy below 2, pandas 2, scikit-learn 1.4 to 1.6, networkx 3.2 or newer (Louvain)"],
            ["API", "FastAPI, Uvicorn, SQLAlchemy, PyJWT, bcrypt, python-dotenv", "FastAPI 0.110 or newer, SQLAlchemy 2.0.x, bcrypt 4 or newer"],
            ["Storage", "SQLite", "One file, `data/app.db`, WAL mode, foreign keys on"],
            ["Front end", "React, Vite, React Router, Recharts, react-force-graph-2d", "React 18.3, Vite 5.4, React Router 6.30, Recharts 2.15"],
            ["Tooling", "Node.js LTS", "v24.19.0 used"],
            ["Browser", "Any current Chromium, Edge, Firefox or Safari", "Chromium (Playwright) for the screenshots"],
        ], widths=[1.3, 2.4, 2.6], size=10, align=["l", "l", "l"]),

        H2("4.7 User Roles and Constraints"),
        TAB("Roles and what each may do", ["Capability", "Analyst", "Moderator", "No sign-in"], [
            ["Read overview, accounts, clusters, models, scalability", "Yes", "Yes", "No (401)"],
            ["Search and filter accounts, open neighbourhoods and clusters", "Yes", "Yes", "No (401)"],
            ["Confirm or dismiss an account or cluster", "No (403)", "Yes", "No (401)"],
            ["Undo a decision not yet used in training", "No (403)", "Yes", "No (401)"],
            ["Start retraining", "No (403)", "Yes", "No (401)"],
            ["Read `/api/health` and sign in", "Yes", "Yes", "Yes"],
        ], widths=[3.4, 0.9, 1.0, 1.0], size=10, align=["l", "c", "c", "c"]),
        B("The test split is never relabelled by moderator feedback; before and after a retraining run are measured on the same test accounts.",
          "A cluster decision applies to every member; a decision on a single account applies to that account. The latest decision for an account wins.",
          "A decision used in a training run cannot be undone (409).",
          "The queue shows accounts at or above the served threshold and clusters nobody has decided; one retraining job runs at a time."),

        H2("4.8 Usage Scenarios"),
        N("**Review a botnet.** A moderator opens *Botnet clusters*, selects the largest coordinated cluster, reads its size, tie density and shared peak hour, opens the graph, and confirms it as fake; all members are logged with the decision.",
          "**Check one account.** An analyst searches a handle, reads its probability and the traits behind it, compares the baseline and graph scores, and looks at the neighbours that are flagged.",
          "**Improve the model.** After confirming or dismissing a handful of items, the moderator presses *Retrain with decisions*; the run records F1 before and after for every model.",
          "**Judge the method.** A researcher opens *Models and scale*, compares the four models, reads the confusion matrix and ROC curves, and opens the scalability tab."),

        H2("4.9 Data Requirements"),
        P(f"The graph holds {F.NODES:,} nodes and {F.EDGES:,} undirected ties. Every node has 23 numeric features, a label (1 fake, 0 genuine), a botnet identifier (-1 for none), an "
          "origin (real topology or injected) and a split. Every tie is stored once as a pair with the smaller id first and an edge kind (0 real, 1 injected). "
          f"The split is stratified 60/20/20, giving {F.SPLITS['train']:,} training, {F.SPLITS['val']} validation and {F.SPLITS['test']} test accounts, identical for every model."),
        TAB("Data sources", ["Source", "Licence", "Used for"], [
            ["SNAP Facebook social circles, ten ego networks", "Public research data", f"Real topology: {F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties"],
            ["Instagram fake, spammer and genuine accounts, 696 labelled rows", "CC BY 3.0", "Profile attributes (resampled and jittered)"],
            ["Twitter Bot Detection Dataset, 50,000 rows", "CC0", "Posting-behaviour rows; its bot label carries almost no signal, so these columns act as realistic noise"],
            ["Injected botnets (`ml/data.py`, seed 7)", "Generated", f"{len(F.BOTNET_SIZES)} botnets of {min(F.BOTNET_SIZES)} to {max(F.BOTNET_SIZES)} accounts, {F.LONE_SPAMMERS} lone spammers, {F.INJ_EDGES:,} injected ties, timing and interaction features, handles"],
        ], widths=[2.4, 1.0, 2.9], size=10, align=["l", "l", "l"]),
        P("Profile rows and posting rows are not about the same people; they are combined per account by resampling, which keeps realistic value ranges but not real correlations between them. "
          "The documents say so wherever results are discussed."),
    ]
