"""Chapter 5: System Design for BotGraph.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
"""

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, TAB


def blocks():
    out = _full()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: smaller figures, the two simplest diagrams side by side, and the least essential sections dropped."""
    out, skipping = [], False
    for b in bl:
        if b[0] in ("h2", "h3"):
            skipping = b[0] == "h2" and b[1].startswith("5.10")
            if b[0] == "h3" and b[1].startswith("5.4.3"):
                skipping = True
            elif b[0] == "h3":
                skipping = False
        if skipping:
            continue
        if b[0] == "tab" and b[1].startswith("File artefacts"):
            continue
        if b[0] == "fig" and (b[1].endswith("07b_account_reasons_and_neighbourhood.png") or b[1].endswith("10_queue_accounts.png")):
            continue
        if b[0] == "p" and b[1].startswith("SQLite runs in write-ahead"):
            out.append(("p", "SQLite runs in write-ahead-logging mode with foreign keys on."))
            continue
        if b[0] == "p" and b[1].startswith("Every screen has a loading skeleton"):
            out.append(("p", b[1].replace("Four of the screens are shown below", "Two of the screens are shown below")))
            continue
        if b[0] == "fig":
            if b[1].endswith("03_dfd_level0.png"):
                out.append(("pair", [(b[1], "Data flow diagram, level 0 (context)."), (F.diag("08_use_case.png"), "Use-case diagram.")], 2.9))
                continue
            w = min(b[3], 4.6) if b[3] <= 5.2 else 4.8
            out.append(("fig", b[1], b[2], w))
            continue
        out.append(b)
    return out


def _full():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how BotGraph is built: the architecture and workflow, the data flow, the class and sequence design, the data design, the algorithms, the module and "
          "API design and the user interface. Every diagram was drawn from the code (`ml/`, `backend/app/` and `frontend/src/`) and is reproduced with an explanation; the full set "
          "is also collected in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **the graph must earn its place**: every graph model is compared with a model that reads the same features without any tie, on the same split. "
          "Second, **groups, not just accounts**: the output must include botnet clusters with the evidence that makes them coordinated. Third, **a human decides**: model output is a "
          "queue for a moderator, and moderator decisions become training labels without contaminating the test set. Fourth, **honest data**: the graph schema records which nodes and ties are real "
          "and which were injected. Fifth, **small and runnable**: one API, one web application, one SQLite file and no external service, on a laptop CPU."),
        FIG(F.diag("01_system_architecture.png"), "Architecture of BotGraph: data and ML pipeline, trained artefacts, FastAPI service with SQLite, and the React web application.", 5.2),
        P(f"The system has four parts that meet at files and at one HTTP interface. The **ML pipeline** (`ml/`) builds the graph from the raw data and trains the models; it writes the graph "
          "(`data/processed/`), the trained weights, scores and clusters (`models/`) and the metrics (`experiments/`). The **API** (`backend/app/`, FastAPI on port "
          f"{F.API_PORT}) loads those artefacts once when it starts and serves them under `/api`, and it keeps users, moderator decisions and retraining runs in SQLite. The **web application** "
          f"(`frontend/`, React 18 and Vite on port {F.WEB_PORT}) proxies `/api` to the API. Retraining closes the loop: the API calls the same training code in a background thread, rewrites "
          "the artefacts and reloads its in-memory store."),

        H2("5.2 High-Level Workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow from raw data to moderator decisions and back into training.", 5.4),
        P("The workflow runs in two directions. Forwards, raw datasets become a graph with 23 features per account; four models are trained on one stratified split; the best graph model on "
          "validation F1 is served; its embeddings feed Louvain clustering; and the API presents flagged accounts and clusters in a queue. Backwards, a moderator's confirm or dismiss decision "
          "is stored as a label, and the next retraining run adds those accounts to the training set, rewrites scores and clusters, and records F1 before and after."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0: BotGraph as one process between its users and the data sources.", 4.8),
        P("At level 0 the platform is one process. The analyst or researcher sends sign-in details and queries and receives scores, reasons, clusters, the graph summary and metrics; the moderator "
          "sends confirm or dismiss decisions and a retraining command and receives the decision log, new scores and F1 before and after. The three public data sets enter only when the graph is built "
          "or rebuilt; nothing leaves the machine at run time and no live platform feed exists."),
        H3("5.3.2 Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1: seven processes and four data stores.", 5.4),
        P("Level 1 has seven processes and four data stores. Processes 2.0 (build the graph and features), 3.0 (train and evaluate the models) and 4.0 (detect botnet clusters) run in the `ml` package; "
          "they read the raw files (D2) and write the processed graph (D3) and the model and metric artefacts (D4). Process 1.0 authenticates requests against the users table, 5.0 serves scores, accounts, clusters "
          "and metrics from D3 and D4 and from the decisions in D1, and 6.0 records moderator decisions in D1. Process 7.0 retrains on those decisions: it reuses the training and clustering code in a background "
          "thread and writes new artefacts to D4. The review process is the only one that writes labels, and retraining is the only one that reads them back."),
        H3("5.3.3 Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: expansion of the serving process 5.0 into six steps.", 5.4),
        P("Level 2 expands process 5.0, the serving process, into six steps. Step 5.1 checks the bearer token and the role. Step 5.2 ranks, filters and pages the accounts (score at or above the threshold, status, "
          "cluster, search) and 5.3 joins each account with the latest moderator decision, using the decision map built from the reviews. Step 5.4 explains one account by gradient times input through the "
          "served network, using the saved weights and scores; 5.5 builds the neighbourhood from the highest-scoring ties and the links between them; and 5.6 assembles the cluster view from `clusters.json` "
          "with members, shared behaviour and graph. Every output is JSON with a 200 or 404 status."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class Diagram"),
        FIG(F.diag("06_uml_class.png"), "UML class diagram of the model classes, the Store, the database entities and the FastAPI routers.", 5.6),
        P("The model side has a `Graph` class that precomputes the symmetric-normalised and the mean-aggregation adjacency, three layer classes (`GCNLayer`, `SAGELayer`, `GATLayer`) and `Net`, "
          "which stacks two layers and a linear head, or two dense layers for the baseline. On the service side, `Store` holds the graph, scores, clusters and metrics in memory and "
          "answers neighbourhood, explanation and decision queries; the three SQLAlchemy entities `User`, `Review` and `TrainingRun` persist state; and five routers expose the functions."),
        H3("5.4.2 Sequence Diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Sequence diagram of the main flow: sign in, score an account, record a decision, retrain.", 5.2),
        P("The main flow starts with `POST /api/auth/login`, which checks the bcrypt hash and returns a signed token. `GET /api/accounts/{id}` then asks the Store for the score, the "
          "per-model scores, the gradient-times-input explanation and the neighbourhood summary. A moderator's `POST /api/queue/decisions` writes a `Review` row with the model score at the "
          "time and the affected account ids. `POST /api/models/retrain` creates a `TrainingRun`, starts a background thread that trains with the decisions as labels, reloads the Store "
          "and stamps the used decisions with the run id."),
        H3("5.4.3 Use-Case Diagram"),
        FIG(F.diag("08_use_case.png"), "Use-case diagram for the analyst, the moderator and the researcher.", 5.0),
        P("Three actors use the system. The analyst reads; the moderator reads and decides; the researcher reads the evaluation and scalability results. In the implementation the researcher "
          "is an analyst or moderator session, because the application has only two roles."),

        H2("5.5 Data Design"),
        P("Two stores are used. Structured, small, mutable data (users, decisions, retraining runs) live in SQLite. Large, read-only data (graph, scores, clusters, metrics) live in files that the "
          "API loads once. The split follows the access pattern: the files change only when a training run completes, the database changes with every moderator click."),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship diagram: the three database tables and the file-based graph, account and cluster entities.", 5.2),
        TAB("Table `users`", ["Column", "Type", "Notes"], [
            ["id", "INTEGER, primary key", ""],
            ["email", "VARCHAR(160)", "unique, indexed; matched in lower case"],
            ["name", "VARCHAR(120)", "display name"],
            ["role", "VARCHAR(20)", "`analyst` or `moderator`"],
            ["password_hash", "VARCHAR(80)", "bcrypt hash; passwords longer than 72 bytes are truncated before hashing"],
        ], widths=[1.4, 1.8, 3.1], size=10, align=["l", "l", "l"]),
        TAB("Table `reviews` (one moderator decision)", ["Column", "Type", "Notes"], [
            ["id", "INTEGER, primary key", ""],
            ["target_type", "VARCHAR(10), indexed", "`account` or `cluster`"],
            ["target_id", "VARCHAR(32), indexed", "account id as text, or cluster id such as `BN-00112`"],
            ["decision", "VARCHAR(10)", "`confirm` (fake) or `dismiss` (genuine)"],
            ["note", "TEXT", "up to 500 characters from the API"],
            ["score", "FLOAT", "model score at decision time (cluster mean for clusters)"],
            ["members", "JSON", "ids of every account the decision applies to"],
            ["user_id", "INTEGER, foreign key to users.id", "the moderator"],
            ["created_at", "DATETIME (UTC)", "decision time"],
            ["used_in_run", "INTEGER, nullable", "id of the training run that used it; set means the decision can no longer be undone"],
        ], widths=[1.4, 2.0, 2.9], size=10, align=["l", "l", "l"]),
        TAB("Table `training_runs`", ["Column", "Type", "Notes"], [
            ["id", "INTEGER, primary key", ""],
            ["started_at, finished_at", "DATETIME (UTC), finished_at nullable", "run times"],
            ["status", "VARCHAR(12)", "`running`, `done` or `error`"],
            ["feedback_labels", "INTEGER", "number of moderator labels used"],
            ["best", "VARCHAR(12)", "architecture served after the run"],
            ["f1_before, f1_after", "JSON", "F1 per model before and after"],
            ["message", "TEXT", "result or error text"],
            ["user_id", "INTEGER, nullable, foreign key to users.id", "moderator who started the run"],
        ], widths=[1.6, 2.2, 2.5], size=10, align=["l", "l", "l"]),
        P("SQLite runs in write-ahead-logging mode with foreign keys on. The file-based artefacts are listed below."),
        TAB("File artefacts", ["File", "Content"], [
            ["`data/processed/graph.npz`", f"X (4,533 x 23 features), y (labels), edge_index ({F.EDGES:,} pairs), edge_kind, cluster (botnet truth), is_real, split, feature names"],
            ["`data/processed/accounts.csv`", "id, handle, display_name, label, origin, botnet_truth, split, followers, following, posts, bio_length, has_profile_pic, account_age_days, peak_hour, posts_per_day, interactions_per_week"],
            ["`data/processed/graph_meta.json`", "seed, real and injected counts, botnet sizes, lone spammers, camouflaged bots, suspicious genuine accounts"],
            ["`models/{baseline,gcn,gat,sage}.pt`", "state dictionaries of the seed-0 model of each architecture"],
            ["`models/scores.npz`", "feature mean and deviation, served embeddings, one probability vector per model"],
            ["`models/clusters.json`", "cluster id, kind, members and description fields"],
            ["`models/meta.json`", "training time, served architecture, threshold, split sizes, configuration"],
            ["`experiments/*.json`", "metrics per model and seed, ROC points, confusion matrices, cluster recovery, scalability"],
        ], widths=[2.3, 4.0], size=9.5, align=["l", "l"]),

        H2("5.6 Algorithm Design"),
        H3("5.6.1 Graph and features"),
        P(f"The graph builder takes the ten Facebook ego networks as the real topology ({F.REAL_NODES:,} accounts, {F.REAL_EDGES:,} ties), draws a profile row for every real account from the labelled "
          "Instagram set and a posting row from the Twitter set, and generates the timing and interaction features. It then injects eight botnets and 150 lone spammers with their ties. "
          "Inside a botnet every pair of accounts is tied with probability 0.28, plus a ring so that each botnet is connected; every bot also follows two to seven real accounts, chosen in proportion "
          "to the square root of their degree; some botnets tie to each other; each lone spammer ties to three to ten real accounts and to no other bot. Botnet members share a creation window and a peak "
          "posting hour, which makes those traits common to a cluster without making any single member stand out."),
        P(f"Camouflage keeps the task honest: {F.CAMO_BOTS} bots receive a genuine-looking profile and {F.SUSPICIOUS_GENUINE} genuine accounts a fake-looking one. Features are standardised with the "
          "mean and deviation of all nodes before training and the same values are stored for explanations."),
        H3("5.6.2 Message passing and the classifier"),
        FIG(F.diag("12_model_architecture.png"), "Model architecture: two message-passing layers, a linear head and the three layer types compared.", 5.4),
        P("Every graph model has two message-passing layers of 64 units with ELU activation, dropout 0.3, and a linear head with two outputs. For node v with features x, the layers compute:"),
        EQ("GCN:        h_v = sum over u in N(v) + {v} of  x_u W / sqrt(d_u d_v)          (d counts the self-loop)"),
        EQ("GraphSAGE:  h_v = W_self x_v + W_neigh * mean over u in N(v) of x_u"),
        EQ("GAT:        e_uv = LeakyReLU(a_src . W x_u + a_dst . W x_v),  alpha_uv = softmax over u of e_uv,  h_v = sum over u of alpha_uv W x_u  (4 heads of 16 units, then 1 head of 64)"),
        P("The baseline replaces each message-passing layer with a dense layer, so it reads only the account's own features. Training uses Adam (learning rate 0.01, weight decay 5e-4), a cross-entropy loss "
          "with class weights 1 for genuine and the square root of the imbalance for fake, up to 160 epochs, and keeps the epoch with the best validation F1 (patience 40). After training, the decision "
          "threshold is chosen on the validation set from 33 values between 0.1 and 0.9 to maximise F1. The architecture with the best validation F1 among the graph models is served."),
        FIG(F.diag("10_flowchart_pipeline.png"), "Flowchart of the training pipeline from graph to served model.", 4.6),
        H3("5.6.3 Botnet clustering"),
        FIG(F.diag("11_flowchart_clustering.png"), "Flowchart of botnet cluster detection with Louvain over embeddings and real ties.", 4.8),
        P("Clustering works on the accounts whose probability is at least 0.30. Each candidate is linked to its five most cosine-similar candidates in embedding space (weight equal to the similarity) and "
          "every real tie between two candidates adds weight 1.0. Louvain community detection (networkx, resolution 1.0, seed 0) groups the weighted graph and groups under five accounts are dropped. "
          "Each group is described by size, mean score, share flagged, internal ties, tie density (internal ties divided by n(n-1)/2), the busiest 3-hour window and the share of members in it, the spread of "
          "creation dates, and median posting rate, interactions and followers. A group is labelled *coordinated* when its density is at least 5% and *diffuse* otherwise."),
        H3("5.6.4 Explanations"),
        P("The reason shown for an account is the gradient of the model's fake-versus-genuine margin with respect to the input features, multiplied by the input values. For the account's own seven largest "
          "contributions the application draws a bar; one further number reports how much the other accounts' features contribute through message passing. This is a first-order approximation and the "
          "interface says so."),

        H2("5.7 Module Design"),
        TAB("Modules and responsibilities", ["File", "Responsibility", "Lines"], [
            ["`ml/config.py`", "paths, seed, model list, training and clustering constants", "39"],
            ["`ml/data.py`", "load the three sources, inject botnets, build 23 features, split, save and summarise the graph", "345"],
            ["`ml/gnn.py`", "sparse `Graph`, GCN, SAGE and GAT layers, `Net`, class weights, threshold search, metrics, training loop", "188"],
            ["`ml/train.py`", "train every model for every seed, summarise, write weights, scores, clusters and metrics; also used for retraining with feedback labels", "138"],
            ["`ml/clustering.py`", "candidate selection, similarity graph, Louvain, cluster description, recovery against truth", "100"],
            ["`ml/eval.py`", "scalability sweep over 1, 2, 4 and 8 disjoint copies of the graph; evaluation summary", "90"],
            ["`backend/app/main.py`, `settings.py`", "application, CORS, start-up (database, demo users, Store); environment settings", "31, 31"],
            ["`backend/app/auth.py`", "bcrypt, JWT creation and checking, `current_user`, `require_moderator`, demo users", "70"],
            ["`backend/app/db.py`", "SQLAlchemy engine, `User`, `Review`, `TrainingRun`, session dependency", "87"],
            ["`backend/app/services/store.py`", "in-memory graph, scores, clusters, adjacency, neighbour statistics, explanations, decision map", "181"],
            ["`backend/app/routes/core.py`", "health, login, current user, graph summary, overview", "87"],
            ["`backend/app/routes/accounts.py`", "ranked list with filters, account detail, neighbourhood", "122"],
            ["`backend/app/routes/clusters.py`", "cluster list and detail with members, graph, reach and headline", "73"],
            ["`backend/app/routes/queue.py`", "queue, decisions, undo, decision log", "125"],
            ["`backend/app/routes/models.py`", "model comparison, scalability, retraining job and its status", "124"],
            ["`frontend/src/pages/`", "Landing, Login, Overview, GraphData, Accounts, AccountDetail, Clusters, ClusterDetail, Queue, Models, NotFound", "11 files"],
            ["`frontend/src/components/`", "UI kit (`ui`), `motion`, `charts` (Recharts), `graph/ForceGraph`, `app` (decision panel, retrain card), `reactbits/Blobs`", "6 folders"],
            ["`scripts/`", "`smoke_test.py`, `capture_screens.py`, `ui_checks.py`, `download_data.py`, `run_extra_experiments.py`", "5 files"],
        ], widths=[2.2, 3.5, 0.7], size=9.5, align=["l", "l", "c"]),

        H2("5.8 API Design"),
        P("The API is a JSON interface under `/api`. Every route except `/api/health` and `/api/auth/login` requires `Authorization: Bearer <token>`; moderator routes also check the role."),
        TAB("Endpoints", ["Method and path", "Access", "Purpose"], [
            ["GET /api/health", "public", "status, account and tie counts, served model, flagged and botnet counts, best and baseline F1"],
            ["POST /api/auth/login", "public", "e-mail and password to token and user"],
            ["GET /api/auth/me", "signed in", "current user"],
            ["GET /api/graph/summary", "signed in", "counts (real and injected), class balance, split, 23 feature summaries, degree histogram, provenance"],
            ["GET /api/overview", "signed in", "KPIs, score histogram, model F1, top accounts and clusters, recent decisions"],
            ["GET /api/accounts", "signed in", "ranked page; query, status, flagged only, cluster, sort, order, page, page size (at most 100)"],
            ["GET /api/accounts/{id}", "signed in", "score, per-model scores, explanation, neighbourhood summary, profile, decision history"],
            ["GET /api/accounts/{id}/neighbourhood", "signed in", "nodes and links, highest-scoring neighbours first (5 to 120)"],
            ["GET /api/clusters", "signed in", "all clusters with status"],
            ["GET /api/clusters/{id}", "signed in", "members, graph, shared behaviour, reach, headline"],
            ["GET /api/queue", "signed in", "pending or decided accounts or clusters with summary counts"],
            ["POST /api/queue/decisions", "moderator", "record confirm or dismiss for an account or cluster (201)"],
            ["DELETE /api/queue/decisions/{id}", "moderator", "undo a decision not yet used in training"],
            ["GET /api/decisions", "signed in", "decision log"],
            ["GET /api/models", "signed in", "per-model metrics, ROC, confusion, cluster recovery, runs, retraining state"],
            ["GET /api/models/scalability", "signed in", "training and inference time against graph size"],
            ["POST /api/models/retrain", "moderator", "start a retraining run on the logged decisions (202)"],
            ["GET /api/models/retrain/status", "signed in", "state, progress, message"],
        ], widths=[2.3, 0.9, 3.1], size=9.5, align=["l", "c", "l"]),
        TAB("Error responses", ["Status", "When"], [
            ["401", "no token, an invalid or expired token, or a wrong e-mail and password"],
            ["403", "an analyst calls a moderator route"],
            ["404", "unknown account or cluster id (a cluster id can change after retraining), no evaluation file"],
            ["409", "undo of a used decision; retraining with no decisions or while a run is in progress"],
            ["422", "request validation failed (for example a non-numeric account id or a decision other than confirm or dismiss)"],
        ], widths=[0.8, 5.5], size=10, align=["c", "l"]),

        H2("5.9 User Interface Design"),
        P("The web application uses the V4 *Soft Pastel Calm* design kit: warm off-white surfaces, rounded cards, six pastel accent colours (lavender, mint, peach, sky, rose, butter) read from CSS variables, "
          "light and dark themes, and restrained motion. Charts take their colours from the same variables, so they follow the theme. Every route is code-split and loaded on demand."),
        TAB("Screen map", ["Route", "Screen", "What it answers"], [
            ["`/`", "Landing", "what BotGraph is; live counts from the health route"],
            ["`/login`", "Sign in", "demonstration accounts with one-click fill"],
            ["`/app`", "Overview", "how many accounts, flags, botnets, items waiting; does the graph help"],
            ["`/app/graph`", "Graph and features", "what is in the graph, which part is real, which features exist"],
            ["`/app/accounts`", "Accounts", "who is flagged; search, filters and paging"],
            ["`/app/accounts/:id`", "Account detail", "why this score; who the neighbours are; decide"],
            ["`/app/clusters`, `/app/clusters/:id`", "Botnet clusters", "which groups exist; their graph, members and shared behaviour"],
            ["`/app/queue`", "Moderator queue", "what is waiting; decision log; retrain"],
            ["`/app/models`", "Models and scale", "which model is best; how cost grows"],
        ], widths=[1.9, 1.5, 2.9], size=10, align=["l", "l", "l"]),
        P("Every screen has a loading skeleton, an empty state with an action, an error state with a retry and visible success feedback through toasts. Keyboard focus rings, dialogs that close with Escape, "
          "a persisted theme toggle and respect for reduced-motion settings are part of the kit; they were checked when the interface was built and recorded in `docs/FRONTEND_PLAN.md`, and were not repeated in the "
          "documentation run. Four of the screens are shown below; the others appear in Chapter 8 and Appendix C."),
        FIG(F.shot("04_overview.png"), "Overview screen: key counts, the score histogram and the model comparison.", F.shot_w(F.shot("04_overview.png"), 5.2, 3.2)),
        FIG(F.shot("07b_account_reasons_and_neighbourhood.png"), "Account detail: the traits behind the score, the profile values and the neighbourhood graph.", F.shot_w(F.shot("07b_account_reasons_and_neighbourhood.png"), 5.2, 3.2)),
        FIG(F.shot("09_cluster_detail.png"), "Cluster detail: size, tie density, shared peak hour, reach, and the moderator decision.", F.shot_w(F.shot("09_cluster_detail.png"), 5.2, 3.2)),
        FIG(F.shot("10_queue_accounts.png"), "Moderator queue: items waiting, confirmed and dismissed counts, and the retraining card.", F.shot_w(F.shot("10_queue_accounts.png"), 5.2, 3.2)),

        H2("5.10 Key Design Decisions"),
        N("**Plain PyTorch instead of a graph library.** The three layers are about 50 lines on sparse tensors; this removes a dependency that is a frequent build failure on Windows and keeps every operation visible.",
          "**One stratified split, three seeds.** All models see the same accounts, so differences are due to the model; three seeds expose the variance.",
          "**Threshold from validation.** The decision threshold is tuned on the validation split and never on the test split.",
          "**Class weight by the square root of the imbalance.** The square root softens the correction for the 12.6% fake share; a full inverse weight was not tried.",
          "**Louvain over embeddings and real ties.** Embedding similarity finds accounts that behave alike; real ties keep a cluster anchored in the graph.",
          "**Artefacts loaded once.** The Store holds everything in memory, which is why read routes answer in milliseconds.",
          "**SQLite for decisions only.** Mutable state is small; large read-only data stay in files.",
          "**Test split protected.** Feedback labels only move accounts into training."),

        H2("5.11 Security and Error-Handling Design"),
        B("Passwords are stored as bcrypt hashes. Tokens are HS256 JWTs that expire after 12 hours; a placeholder secret is replaced by a development secret and should be replaced for any real deployment.",
          "Role checks run on the server in the `require_moderator` dependency; hiding a button in the interface is not relied on.",
          "CORS allows only the web application's own origin (`localhost` and `127.0.0.1` on port 5309).",
          "Request bodies are validated by Pydantic (target type, decision, note length) and query parameters by bounds (page size, neighbour limit).",
          "Errors are returned as plain sentences the interface can show, such as *Please sign in to continue* or *That decision was already used to train a model run and cannot be undone*.",
          "A failing retraining run is recorded with status `error` and the first 400 characters of the message, and the served model is left unchanged."),
    ]
