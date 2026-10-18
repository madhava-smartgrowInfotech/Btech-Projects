"""ER, UML class, use-case and sequence diagrams for AutoSecAI (drawn from the real code and database)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas


def _entity(c, x, y, w, title, rows, fs=6.8, head=INDIGO_L, rowh=3.3):
    h = 4.2 + rowh * len(rows) + 1.2
    c.box(x, y - h, w, h, "", fc="white", r=1.2)
    c.box(x, y - 4.2, w, 4.2, title, fc=head, bold=True, fs=fs + 0.6, r=1.2)
    for i, r in enumerate(rows):
        c.text(x + 1.5, y - 4.2 - rowh * (i + 0.65), r, fs=fs, ha="left")
    return h


def er(out):
    c = Canvas(10.4, 6.6)
    c.text(52, 63.5, "Two SQLite databases, two tables - the review itself is stored as one JSON document", fs=9, bold=True)
    c.zone(2, 6, 36, 52, "data/app.db  (backend/auth.py)", fc="#eef4fe")
    _entity(c, 5, 50, 30, "users", ["PK  id  INTEGER AUTOINCREMENT", "     email  TEXT  UNIQUE NOT NULL", "     name  TEXT  NOT NULL",
                                  "     password_hash  BLOB  (bcrypt)", "     created  TEXT  (UTC ISO time)"], fs=6.8)
    c.text(20, 17, "Demo account demo@autosecai.dev is\nseeded at start-up. Passwords are\nhashed with bcrypt (10 rounds);\nlogin returns an HS256 JWT (12 h).", fs=6.6)
    c.zone(46, 6, 56, 52, "data/history.db  (autosecai/store.py)", fc="#eef8f2")
    _entity(c, 49, 50, 50, "reviews", ["PK  id  TEXT  (8 hex characters)", "     created  TEXT   title  TEXT   source  TEXT", "     score  INTEGER  (0-100)   verdict  TEXT",
                                      "     n_findings  INTEGER   n_security  INTEGER", "     payload  TEXT  (JSON of the full review)"], fs=6.8)
    c.box(49, 8, 50, 20, "", fc=GREY_L, ls="--", r=1.2)
    c.text(74, 25.5, "payload (JSON, logical structure - not separate tables)", fs=7, bold=True)
    for i, t in enumerate(["findings[]  rule_id, severity, cwe, owasp, file, line, snippet, evidence, explanation, impact, remediation,",
                           "                 patch, fix_verified, in_diff, ml {probability, type}",
                           "ml[]  per function: probability, vuln_type, drivers[], metrics{M1..M14}      functions[]  name, loc, cyclomatic",
                           "trace[]  agent, role, seconds, summary, details[]       files[]  path, status, added, removed, language",
                           "stats{by_severity, by_cwe, autofix, autofix_verified}      patched{}  summary"]):
        c.text(50.5, 21.5 - i * 2.9, t, fs=5.8, ha="left")
    c.text(42, 36, "no foreign key:\nreviews are not\nlinked to a user", fs=6.4, italic=True)
    c.save(out)


def _cls(c, x, y, w, name, attrs, meths, fs=6.0, rowh=2.55, head=INDIGO_L):
    n = len(attrs) + len(meths)
    h = 4.0 + rowh * n + 2.0
    c.box(x, y - h, w, h, "", fc="white", r=1.0, lw=1.0)
    c.box(x, y - 4.0, w, 4.0, name, fc=head, bold=True, fs=fs + 1.0, r=1.0, lw=1.0)
    yy = y - 4.0
    for a in attrs:
        yy -= rowh
        c.text(x + 1.2, yy + rowh * 0.1, a, fs=fs, ha="left")
    if attrs and meths:
        c.line((x, yy - 0.7), (x + w, yy - 0.7), lw=0.8, color="#44506b")
        yy -= 0.7
    for m in meths:
        yy -= rowh
        c.text(x + 1.2, yy + rowh * 0.1, m, fs=fs, ha="left")
    return {"x": x, "y": y - h, "w": w, "h": h}


def uml(out):
    c = Canvas(10.4, 8.8)
    c.text(52, 85.5, "Domain types, engine classes and the backend job table", fs=9, bold=True)
    a = _cls(c, 2, 81, 24, "ChangedFile", ["path: str", "status: str", "added: set[int]", "n_added, n_removed: int", "hunks: list", "new_source, old_source"], ["language -> str"])
    b = _cls(c, 29, 81, 28, "Finding", ["rule_id, file, line, end_line", "function, snippet, sink", "confidence, severity", "detector: str", "fix: dict | None", "extra: dict"], ["category -> str", "key -> str"])
    d = _cls(c, 60, 81, 20, "Trace", ["items: list[dict]"], ["run(agent, role, fn)"])
    e = _cls(c, 83, 81, 19, "Review (dict)", ["id, created, title", "score: int, verdict", "findings[], ml[]", "trace[], stats", "files[], patched"], [])
    f = _cls(c, 2, 50, 30, "PyAnalyzer (rules.py)", ["source, filename, offset", "findings: list[Finding]", "taint: dict[name, origin]"], ["visit(tree)", "_check_call(node)", "_sql_fix / _shell_fix", "analyze_source(src, file)"])
    g = _cls(c, 35, 50, 31, "mlmodel (module)", ["FEATURES[14], bundle.joblib", "SEED = 42"], ["train_all(n=6000)", "smote_tomek(X, y)", "feature_selection(X, y, top)", "predict_metrics(m) -> p, type"])
    h = _cls(c, 69, 50, 33, "RepoIndex (codeintel.py)", ["files, chunks, graph: DiGraph", "routes, entry_points, hotspots", "vec: TfidfVectorizer"], ["ask(question, k)", "overview()", "onboarding_guide()", "file_graph()"])
    i = _cls(c, 2, 19, 33, "review_changes() (agents.py)", [], ["ingest() / static() / ml_risk()", "reason() / remediate()", "quality() / judge()", "finding_to_dict(f)"])
    j = _cls(c, 38, 19, 30, "Backend (main.py, auth.py)", ["JOBS: dict, INDEXES: LRU(6)"], ["start_job(kind, work)", "authenticate(email, pw)", "make_token(user) / current_user"])
    k = _cls(c, 71, 19, 31, "store / report", ["history.db: reviews"], ["save / load / list / delete", "to_markdown / to_sarif", "to_json / to_csv"])
    c.arrow((57, 62), (83, 62), label="findings[]   1..*", fs=6.0, loff=(0, 2))
    c.arrow((80, 72), (83, 72), label="trace[]", fs=5.8, loff=(0, 2))
    c.arrow((8, 57.2), (8, 50.2), ls="--", label="analysed by", fs=5.8, loff=(6, 0))
    c.arrow((30, 50), (30, 54.6), ls="--", label="creates 1..*", fs=5.8, loff=(7, 0))
    c.arrow((12, 19), (12, 26.2), ls="--", label="calls", fs=5.8, loff=(3, 0))
    c.arrow((30, 19), (42, 28.7), ls="--", label="scores", fs=5.8, loff=(5, 0))
    c.arrow((38, 11), (35, 11), ls="--", label="calls", fs=5.8, loff=(1.5, 2))
    c.arrow((68, 11), (71, 11), ls="--", label="calls", fs=5.8, loff=(0, 2))
    c.arrow((62, 19), (80, 26.1), ls="--", label="ask()", fs=5.8, loff=(-1, 3))
    c.text(52, 1.5, "solid arrows: association with multiplicity;  dashed: dependency (uses, creates, calls)", fs=6.4, italic=True)
    c.save(out)


def usecase(out):
    c = Canvas(10.4, 7.6)
    c.zone(22, 2, 60, 72, "AutoSecAI", fc="#f6f7fd")
    cases = [(52, 66, "Sign in, register or use the demo account"), (52, 58, "Start a PR review (demo, diff, versions,\nGitHub PR, files / zip / folder)"),
             (52, 50, "Watch the 7 agents work (live progress)"), (52, 42, "Read findings, patches and ML evidence"),
             (52, 34, "Export Markdown / SARIF / JSON / CSV / patched"), (52, 26, "Review history, trend, delete a review"),
             (52, 18, "Index a repository and ask questions"), (52, 10, "Model Lab: charts, try a function, retrain")]
    for x, y, t in cases:
        c.ellipse(x, y, 46, 6.4, t, fc="white", ec=INDIGO, fs=6.8)
    c.ellipse(62, 72, 26, 3.6, "View landing statistics (public)", fc="white", ec=INDIGO, fs=6.4)
    c.box(3, 51, 16, 10, "Developer /\nreviewer\n(signed in)", fc=GREY_L, fs=7.2, bold=True, r=1)
    for _, y, _t in cases:
        c.line((19, 56), (29, y), color="#8a93a8", lw=0.8)
    c.box(3, 70, 16, 5, "Visitor", fc=GREY_L, fs=7.6, bold=True)
    c.line((19, 72.5), (49, 72), color="#8a93a8", lw=0.8)
    c.box(86, 56, 14, 8, "GitHub\n(external)", fc=GREY_L, fs=7.2, bold=True)
    c.box(86, 20, 14, 8, "Anthropic API\n(optional)", fc=GREY_L, fs=7.0, bold=True)
    c.arrow((86, 60), (75, 58), ls="--", head=False)
    c.arrow((86, 24), (75, 18), ls="--", head=False)
    c.arrow((86, 25), (75, 42), ls="--", head=False)
    c.text(11, 8, "All use cases except\nthe landing page need a\nvalid JWT.", fs=6.6, italic=True)
    c.save(out)


def sequence(out):
    c = Canvas(10.4, 8.0)
    names = [("Developer", 9), ("React app", 25), ("FastAPI", 40), ("Job thread", 56), ("review_changes", 72), ("history.db", 91)]
    for n, x in names:
        c.box(x - 8, 74, 16, 4.5, n, fc=INDIGO_L, bold=True, fs=7.2)
        c.line((x, 74), (x, 3), color="#9aa5ba", lw=0.9, ls="--")
    X = dict(names)
    steps = [("Developer", "React app", "choose 'Demo PR', press Run", 70), ("React app", "FastAPI", "POST /api/reviews {kind, options} + JWT (token and input checked)", 66),
             ("FastAPI", "Job thread", "start_job(work)", 59), ("FastAPI", "React app", "202 {job_id}", 55.5),
             ("Job thread", "review_changes", "parse diff, review_changes(changed, options)", 52), ("review_changes", "Job thread", "agent message per step (progress)", 48.5),
             ("React app", "FastAPI", "GET /api/jobs/{id} (every 350 ms)", 45), ("FastAPI", "React app", "{status: running, messages[]}", 41.5),
             ("review_changes", "Job thread", "review dict: score, verdict, findings", 38), ("Job thread", "history.db", "store.save(review)", 34.5),
             ("React app", "FastAPI", "GET /api/jobs/{id}", 31), ("FastAPI", "React app", "{status: done, review_id}", 27.5),
             ("React app", "FastAPI", "GET /api/reviews/{id}", 24), ("FastAPI", "history.db", "store.load(id)", 20.5), ("FastAPI", "React app", "full review JSON", 17),
             ("React app", "Developer", "verdict banner, gauge, findings, charts", 13), ("Developer", "React app", "export SARIF -> GET .../export/sarif", 9)]
    for a, b, t, y in steps:
        xa, xb = X[a], X[b]
        if a == b:
            c.path([(xa, y + 1.5), (xa + 7, y + 1.5), (xa + 7, y - 1.2), (xa, y - 1.2)], label=t, fs=6.3, seg=1, loff=(2, 0), lha="left")
        else:
            c.arrow((xa, y), (xb, y), label=t, fs=6.3, loff=(0, 1.9), ls="--" if "202" in t or "{status" in t or "full review" in t else "-")
    c.save(out)
