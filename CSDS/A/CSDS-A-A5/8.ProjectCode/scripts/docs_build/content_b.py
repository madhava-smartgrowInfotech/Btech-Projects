"""Report text, part B: chapters 4-5 (requirements and analysis, system design)."""
from common import *

# ---------------------------------------------------------------- 4. REQUIREMENTS
REQ = {}

REQ["existing"] = [
    ("h2", "4.1 Existing System and Its Limitations"),
    ("p", "In the current practice described in the base paper and the batch's literature survey, tax authorities rely on manual audits and investigations after fraud is suspected, on rule-based checks that flag mismatches between returns and invoice data, on supervised models that classify fraud from labelled historical cases, and on forensic and network analysis applied case by case by investigators [1]-[5]."),
    ("tbl", "exist", "Existing approaches and their limitations", ["Existing approach", "How it works", "Limitation"], [
        ["Manual audit and investigation", "Officers examine a taxpayer after suspicion arises", "Slow; detects fraud after revenue is lost; effort goes where suspicion already exists"],
        ["Rule-based mismatch checks", "Fixed thresholds on returns, e.g. ITC claimed above ITC available", "Easily evaded by staying under thresholds; 236 flags with 168 false alarms in this project's baseline test"],
        ["Supervised ML on labelled cases", "Classifier trained on past confirmed fraud", "Labels are scarce, late and biased by past enforcement"],
        ["Per-entity or per-invoice checks", "Each return or invoice scored on its own", "Cannot see loops and shell networks, which exist only across taxpayers"],
        ["Score-only systems", "Return a number or a flag", "No explanation an officer can verify or defend"],
    ], [1.6, 2.4, 3.0]),
]

REQ["proposed"] = [
    ("h2", "4.2 Proposed System and Its Advantages"),
    ("p", "TaxSentinel replaces the single-view, label-dependent, unexplained approach with a pipeline of four cooperating parts: a JEPA behaviour encoder trained without labels, network analysis that finds circular-trading loops and shared-identity clusters, an invoice-level anomaly score, and a noisy-OR risk model that combines them. Flagged taxpayers receive an evidence list and, on request, a case note written by an LLM from that list alone."),
    ("bul", [
        "**No labels needed to learn normal behaviour.** The encoder is trained on all 6,977 taxpayer-months without labels; labels are used only to evaluate.",
        "**Several kinds of evidence.** A fraudster who hides one behaviour is still exposed by another layer; ablations show that the layers are complementary (Chapter 8).",
        "**Group-level detection.** Rings and clusters are scored and shown as an interactive graph, and become ranked invoice chains.",
        "**Explainable.** Every flag has a numbered evidence list; every claim in a note cites an item; notes are checked for invalid citations and ungrounded numbers.",
        "**Light and fast.** A 53,420-parameter model trains in about 12 s on a CPU.",
        "**Operationally complete.** Accounts, history, a performance page and an activity log make it usable and auditable.",
    ]),
]

REQ["func"] = [
    ("h2", "4.3 Functional Requirements"),
    ("tbl", "fr", "Functional requirements and where each is realised", ["ID", "Requirement", "Realised by"], [
        ["FR1", "A user can register, sign in and sign out; sessions expire", "routes/auth.py, JWT (720 min), Login page"],
        ["FR2", "Generate a seeded GST ecosystem (150-1500 taxpayers) with injected fraud and labels", "scripts/generate_gst_data.py, POST /api/pipeline/run"],
        ["FR3", "Build invoice, behaviour and network features per taxpayer-month", "ml/features.py"],
        ["FR4", "Train and apply a self-supervised JEPA behaviour encoder", "ml/jepa.py, ml/train.py"],
        ["FR5", "Detect circular-trading loops and shared-identity clusters", "ml/graph.py"],
        ["FR6", "Score each invoice and each taxpayer; flag at risk >= 0.5", "ml/pipeline.py"],
        ["FR7", "Rank taxpayers and invoice chains; filter and search", "routes/investigate.py, Taxpayers and Overview pages"],
        ["FR8", "Show a taxpayer profile with layer scores, monthly chart, evidence, partners and invoices", "TaxpayerProfile page"],
        ["FR9", "Draw the buyer-seller graph with loops and clusters; drill into a chain", "FraudGraph and ChainDetail pages"],
        ["FR10", "Write a cited case note on demand and check its grounding", "routes/explanations.py, services/explainer.py, CaseDetail page"],
        ["FR11", "Report precision@k, recall@k, F1, ROC-AUC, ablations and per-pattern recall against a rule baseline", "ml/eval.py, Performance page"],
        ["FR12", "Keep a history of generation runs and show the loaded ecosystem", "Runs page, pipeline_runs table"],
    ], [0.5, 3.6, 2.9]),
]

REQ["nonfunc"] = [
    ("h2", "4.4 Non-Functional Requirements"),
    ("tbl", "nfr", "Non-functional requirements and measured status", ["Quality", "Requirement", "Status"], [
        ["Performance", "Interactive responses; full analysis in under a minute", "API median 1.7-12.1 ms per read endpoint; full run 18.6-29.0 s typical (Chapter 7)"],
        ["Security", "Passwords hashed; protected API; tamper-proof sessions", "bcrypt, HS256 JWT, 401 on missing, garbage or altered token (tested)"],
        ["Reliability", "One generation at a time; graceful failure of external service", "409 on concurrent run; 502 with a clear message if Gemini fails; fallback models"],
        ["Usability", "Keyboard access, readable in light and dark, reduced motion respected", "Command palette, shortcuts, theme toggle, reduce-motion fallback"],
        ["Portability", "Runs on a standard Windows PC without GPU", "Tested on Windows 11, CPU only"],
        ["Maintainability", "Separated layers; configuration in .env", "ml/, backend/, frontend/ split; settings in backend/app/config.py"],
        ["Reproducibility", "Same seed gives same data and same results", "Seeded generator, torch and numpy seeds; seed 42 reproduces the reported figures"],
        ["Explainability", "Every flag backed by evidence", "Evidence lists E1..En; cited notes; grounding checks"],
    ], [1.2, 2.7, 3.1]),
]

REQ["hw_sw"] = [
    ("h2", "4.5 Hardware and Software Requirements"),
    ("tbl", "hw", "Hardware used for development and measurement", ["Item", "Specification"], [
        ["Processor", "Intel Core i5-12500 (6 cores, 12 threads)"],
        ["Memory", "15.7 GB RAM"],
        ["Graphics", "Intel UHD Graphics 770 (integrated); no GPU used"],
        ["Operating system", "Windows 11 Pro"],
        ["Note", "Smaller machines were not tested. Training takes 11.7 s on this machine, so a GPU is not needed; the API process held about 0.5 GB (503 MB working set measured) while serving the ecosystem."],
    ], [1.6, 5.4]),
    ("tbl", "sw", "Software stack", ["Layer", "Software (as installed in the project)"], [
        ["Language and runtime", "Python 3.11.9; Node.js v24.19.0"],
        ["Machine learning", "PyTorch 2.14.0 (CPU build); NumPy 2.4.6; NetworkX 3.4.2"],
        ["Backend", "FastAPI 0.115.6; SQLAlchemy 2.0.36 with SQLite; PyJWT and bcrypt; python-dotenv; google-genai"],
        ["Frontend", "React 18.3, Vite 6, Tailwind CSS 4, react-router 6, axios, recharts 3, react-force-graph-2d, framer-motion, three"],
        ["Data tools", "kagglehub (PaySim download); matplotlib, python-docx, python-pptx (documentation only)"],
        ["External service", "Google Gemini API through the google-genai client (key in .env)"],
        ["Ports", "API 8105, web 5105"],
    ], [1.6, 5.4]),
]

REQ["users"] = [
    ("h2", "4.6 User Roles and Constraints"),
    ("p", "There is a single role in the implemented system, the **analyst**: any registered user who can sign in, generate ecosystems, browse and investigate and request notes. A seeded demo account (demo@taxsentinel.app) is provided for demonstrations. Role separation (for example, a read-only reviewer or an administrator who manages users and thresholds) is not implemented and is listed under future scope. The constraints on the solution are: synthetic data only; a Windows-oriented set-up; reliance on the Gemini free tier for notes; one generation at a time; and the interpretation of every output as a risk indication, not a legal finding."),
]

# ---------------------------------------------------------------- 5. DESIGN
DES = {}

DES["arch"] = [
    ("h2", "5.1 System Architecture"),
    ("p", "TaxSentinel is a four-tier system ({fig:arch}). A React single-page application presents the screens. A FastAPI service exposes a JSON API behind a JWT bearer guard. An analytics layer in the `ml/` package turns a dataset into scores, rings, chains and evidence. Persistent state is kept in SQLite (users, runs, notes), in the pickled pipeline state, in the CSV ecosystem and in the saved model weights. Gemini is the only external service."),
    ("fig", "arch", ARCH, "System architecture of TaxSentinel", 6.4),
    ("p", "Two design decisions shape the architecture. First, the analytical result is computed once per ecosystem and held in memory (and pickled to `data/workspace/state.pkl`), so every read endpoint is a lookup rather than a computation; this is why the read endpoints respond in milliseconds. Second, long computations never run in a request: a generation is started on a background thread and the interface polls a status endpoint, which also feeds the stage stepper and the activity log."),
]

DES["flow"] = [
    ("h2", "5.2 High-Level Workflow"),
    ("p", "The workflow in {fig:flow} has eight steps. Data are generated or loaded (1); nineteen features per taxpayer-month are computed in three layers (2); the JEPA encoder scores the deviation of each month (3); the trade graph is analysed for loops and clusters (4); every invoice is scored (5); the four layer scores are combined into a risk (6); evidence and invoice chains are built for the flagged taxpayers (7); and on request a case note is written and checked (8). Evaluation against injected labels and the rule baseline runs on the same scores."),
    ("fig", "flow", FLOW, "High-level workflow from GST data to a cited case note", 6.4),
]

DES["dfd"] = [
    ("h2", "5.3 Data Flow Diagrams"),
    ("p", "The context diagram ({fig:dfd0}) shows one system, three external entities (the analyst, the Gemini API and the data generator) and the data crossing the boundary: credentials, seeds and queries in; rankings, rings, chains, notes and metrics out; evidence prompts to Gemini and cited notes back; and the generated ecosystem in."),
    ("fig", "dfd0", DFD0, "Data flow diagram, level 0 (context diagram)", 5.6),
    ("p", "Level 1 ({fig:dfd1}) divides the system into five processes: authentication (1.0) against the users store; generation and analysis (2.0), which reads the CSV ecosystem and model, writes the run row and produces the pipeline state; investigation (3.0), which reads the state to serve rankings, profiles, graphs and chains; evaluation (4.0), which reads the evaluation held in the state and the training and evaluation reports; and case explanation (5.0), which reads evidence from the state, exchanges a prompt and a cited note with Gemini and stores the note and its quality checks."),
    ("fig", "dfd1", DFD1, "Data flow diagram, level 1", 6.2),
    ("p", "Level 2 ({fig:dfd2}) expands process 2.0 into its eight internal steps. Each step reads the output of the one before it, and the network score and the JEPA and behaviour scores meet in the risk combination (2.6). The ecosystem and the model weights are read from and written to their stores, and the finished state is pickled."),
    ("fig", "dfd2", DFD2, "Data flow diagram, level 2: Generate and analyse", 6.2),
]

DES["uml"] = [
    ("h2", "5.4 UML Diagrams"),
    ("p", "The class diagram ({fig:uml}) shows three persistent classes (User, PipelineRun and Explanation), the `Store` service that holds the pipeline state and starts background runs, the pipeline and explainer modules, and the model classes `JEPA`, `Encoder` and `RobustScaler`. A JEPA instance owns two encoders, the online one and the exponential-moving-average target."),
    ("fig", "uml", UML, "UML class diagram", 6.4),
    ("p", "The sequence diagram ({fig:seq}) follows the main flow: sign-in, generating an ecosystem (the interface polls while a background thread runs the pipeline and updates the run row), opening the top taxpayer, and writing an explanation (the API builds the prompt from the evidence, calls Gemini, checks the grounding of the answer and saves it)."),
    ("fig", "seq", SEQ, "Sequence diagram of the main flow", 6.4),
    ("p", "The use-case diagram ({fig:uc}) has the analyst as the primary actor and Gemini as a secondary actor of the case-note use case."),
    ("fig", "uc", UC, "Use-case diagram", 5.6),
]

DES["db"] = [
    ("h2", "5.5 Database Design"),
    ("p", "Application data that changes at run time is stored in SQLite through SQLAlchemy; the analytical dataset is not, because it is read as a whole, is regenerated from a seed and is naturally columnar. {fig:er} shows the three SQL tables and the three CSV entities that they refer to logically."),
    ("fig", "er", ER, "Entity-relationship diagram", 6.2),
    ("tbl", "db", "SQL tables", ["Table", "Columns", "Keys and notes"], [
        ["users", "id, email, name, password_hash, created_at", "PK id; email unique and indexed; password stored only as a bcrypt hash"],
        ["pipeline_runs", "id, seed, n_taxpayers, status, message, stats (JSON), user_id, started_at, finished_at", "PK id; FK user_id to users; status is running, done or failed; stats holds the summary counts"],
        ["explanations", "id, run_key, gstin, model, text, evidence (JSON), quality (JSON), user_id, created_at", "PK id; FK user_id to users; run_key and gstin indexed so a note is found for the loaded ecosystem; evidence is stored with the note so the citations stay valid"],
    ], [1.2, 3.1, 2.7]),
    ("p", "The CSV entities are `taxpayers.csv` (GSTIN, legal name, constitution, state, sector, registration date, address and contact identifiers, and the injected labels), `invoices.csv` (invoice number and date, seller and buyer GSTIN, taxable value, rate, tax, e-way bill flag, whether the seller reported it in GSTR-1, and the label) and `returns.csv` (monthly outward supplies, output tax, ITC available in GSTR-2B, ITC claimed in GSTR-3B, tax paid in cash and filing delay). The labels are carried in the files so that evaluation can run, but the model never reads them."),
]

DES["modules"] = [
    ("h2", "5.6 Module Design"),
    ("tbl", "mods", "Modules and responsibilities", ["Module", "File(s)", "Responsibility"], [
        ["Data generator", "scripts/generate_gst_data.py (483 lines)", "Seeded ecosystem with GSTIN-format ids, tiered supply network, returns, injected fraud and hard negatives"],
        ["Feature builder", "ml/features.py (169)", "Loads the dataset; builds 19 features per taxpayer-month; robust scaler"],
        ["JEPA", "ml/jepa.py (149), ml/train.py (37)", "Encoder, EMA target, predictor, sample construction, training, scoring, save and load"],
        ["Network analysis", "ml/graph.py (110)", "Trade graph, bounded cycle search and scoring, ring merging, identity clusters, communities"],
        ["Rule baseline", "ml/baseline.py (45)", "Rules R1-R5 used as the comparison"],
        ["Metrics", "ml/metrics.py (60)", "Precision@k, recall@k, P/R/F1, ROC-AUC, average precision"],
        ["Pipeline", "ml/pipeline.py (530)", "Deviation scoring, invoice scoring, risk, patterns, evidence, chains, evaluation"],
        ["Evaluation", "ml/eval.py (133)", "Writes experiments/eval/metrics.json including the PaySim transfer and explanation checks"],
        ["API", "backend/app/ (main, auth, config, db, routes, services; 787 lines)", "Endpoints, JWT guard, persistence, background runs, explainer"],
        ["Web application", "frontend/src/ (10 pages plus components, 1,415 lines in the pages; 3,774 lines in 36 source files overall)", "Screens, charts, graph, navigation, themes"],
    ], [1.3, 2.3, 3.4]),
]

DES["ui"] = [
    ("h2", "5.7 User Interface Design"),
    ("p", "The interface is a \"control room\" for an analyst. Its main design rules are: show the answer before the mechanism (the overview leads with counts, flagged taxpayers and the comparison with the baseline); let every number lead to its evidence (a taxpayer opens a profile, a citation chip jumps to its evidence item, a chain opens its invoices); keep the system status visible (a health card, a stage stepper, an activity log); and respect the user's environment (light and dark themes following the operating-system setting, reduced-motion support, keyboard navigation with a command palette and `g` shortcuts). The screens are presented in Chapter 8 and Appendix C."),
    ("tbl", "ui", "Screens and their purpose", ["Screen", "Route", "Purpose"], [
        ["Landing", "/", "What the product does; live health card"],
        ["Sign in / register", "/login", "JWT sign-in, demo account"],
        ["Overview", "/app", "Generate and analyse; counts; flagged taxpayers; patterns; top chains; activity log"],
        ["Taxpayers", "/app/taxpayers", "Ranked list with search and filters"],
        ["Taxpayer profile", "/app/taxpayers/:gstin", "Signals, evidence, network, invoices"],
        ["Case", "/app/cases/:gstin", "Evidence list and the cited case note"],
        ["Fraud rings", "/app/graph", "Interactive network; loops and clusters"],
        ["Invoice chain", "/app/chains/:id", "Chain graph, parties and invoices"],
        ["Model performance", "/app/performance", "Metrics, ablations, per-pattern recall"],
        ["Run history", "/app/runs", "Last ten generations and the loaded ecosystem"],
    ], [1.5, 1.9, 3.6]),
]
