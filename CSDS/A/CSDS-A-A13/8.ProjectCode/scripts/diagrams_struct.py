"""ER diagram and UML class diagram, drawn from backend/app/models and the engine/service modules."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas

PITCH = 2.35


# ------------------------------------------------------------------ ER diagram
def _table(c, x, y_top, w, name, fields, fc="white", head=INDIGO_L):
    """Draw a table; returns its box dict (y is the bottom). Fields starting with '*' are primary keys."""
    h = 4.6 + PITCH * len(fields) + 0.8
    y = y_top - h
    c.box(x, y, w, h, "", fc=fc, r=1.0, lw=1.1)
    c.box(x, y_top - 4.3, w, 4.3, name, fc=head, ec=INK, bold=True, fs=7.6, r=1.0, lw=1.1)
    for i, f in enumerate(fields):
        pk = f.startswith("*")
        txt = f[1:] if pk else f
        c.text(x + 1.2, y_top - 4.6 - PITCH * (i + 0.55), txt, fs=6.3, ha="left", bold=pk)
    return {"x": x, "y": y, "w": w, "h": h}


def _conn(c, a, b, mode, ca="1", cb="N", fa=0.5, fb=0.5):
    """Connect two table boxes with an elbow line and cardinality labels."""
    cx_a, cx_b = a["x"] + a["w"] / 2, b["x"] + b["w"] / 2
    if mode == "v":  # a above b (same column)
        p, q = (cx_a, a["y"]), (cx_b, b["y"] + b["h"])
        c.line(p, q, lw=1.1)
        c.text(p[0] + 1.6, p[1] - 1.5, ca, fs=7, bold=True)
        c.text(q[0] + 1.6, q[1] + 1.5, cb, fs=7, bold=True)
        return
    left, right = (a, b) if a["x"] < b["x"] else (b, a)
    la, lb = (ca, cb) if a is left else (cb, ca)
    ya = a["y"] + a["h"] * fa
    yb = b["y"] + b["h"] * fb
    xa = a["x"] + a["w"] if a is left else a["x"]
    xb = b["x"] if b is right else b["x"] + b["w"]
    mx = (xa + xb) / 2
    c.line((xa, ya), (mx, ya), lw=1.1)
    c.line((mx, ya), (mx, yb), lw=1.1)
    c.line((mx, yb), (xb, yb), lw=1.1)
    sa = 1 if a is left else -1
    c.text(xa + sa * 1.4, ya + 1.5, ca, fs=7, bold=True)
    c.text(xb - sa * 1.4, yb + 1.5, cb, fs=7, bold=True)


def er(out):
    c = Canvas(12.2, 9.7)
    W = 21.0
    xs = [2, 27, 52, 77, 100]
    top = 94
    gap = 4.5
    d = {}
    # column 1
    y = top
    d["departments"] = _table(c, xs[0], y, W, "departments", ["*id", "code (unique)", "name"])
    y = d["departments"]["y"] - gap
    d["courses"] = _table(c, xs[0], y, W, "courses", ["*id", "code (unique)", "name", "department_id  FK"])
    y = d["courses"]["y"] - gap
    d["session_papers"] = _table(c, xs[0], y, W, "session_papers", ["*id", "session_id  FK", "course_id  FK", "paper_group"])
    y = d["session_papers"]["y"] - gap
    d["exam_sessions"] = _table(c, xs[0], y, W, "exam_sessions", ["*id", "code (unique)", "date", "start_time", "end_time", "label"])
    # column 2
    y = top
    d["candidates"] = _table(c, xs[1], y, W, "candidates", ["*id", "roll_no (unique)", "full_name", "department_id  FK", "needs_accessible_seat", "email", "date_of_birth"])
    y = d["candidates"]["y"] - gap
    d["registrations"] = _table(c, xs[1], y, W, "registrations", ["*id", "candidate_id  FK", "course_id  FK"])
    y = d["registrations"]["y"] - gap
    d["halls"] = _table(c, xs[1], y, W, "halls", ["*id", "code (unique)", "name, building, floor", "rows, cols", "blocked_seats (JSON)", "accessible_seats (JSON)", "aisles_after_cols (JSON)", "is_active"])
    # column 3
    y = top
    d["seat_assignments"] = _table(c, xs[2], y, W, "seat_assignments", ["*id", "plan_id  FK", "candidate_id  FK", "course_id  FK", "hall_id  FK", "row, col", "seat_label"])
    y = d["seat_assignments"]["y"] - gap
    d["plans"] = _table(c, xs[2], y, W, "plans", ["*id", "session_id  FK", "version, status", "seed", "rules (JSON)", "engine_version", "data_fingerprint", "solver_hash", "assignment_hash",
                                                  "solve_ms, swaps", "stats, scorecard,", "baseline (JSON)", "created_by  FK"])
    # column 4
    y = top
    d["invigilator_assignments"] = _table(c, xs[3], y, W, "invigilator_assignments", ["*id", "plan_id  FK", "hall_id  FK", "user_id  FK"])
    y = d["invigilator_assignments"]["y"] - gap
    d["attendance"] = _table(c, xs[3], y, W, "attendance", ["*id", "plan_id  FK", "candidate_id  FK", "hall_id  FK", "status", "method", "marked_by  FK", "marked_at"])
    y = d["attendance"]["y"] - gap
    d["hall_submissions"] = _table(c, xs[3], y, W, "hall_submissions", ["*id", "plan_id  FK", "hall_id  FK", "submitted_by  FK", "submitted_at"])
    # column 5
    y = top
    d["users"] = _table(c, xs[4], y, 19.5, "users", ["*id", "email (unique)", "full_name", "role", "status", "password_hash", "created_at", "last_login_at"])
    y = d["users"]["y"] - gap
    d["audit_events"] = _table(c, xs[4], y, 19.5, "audit_events", ["*id", "at", "actor_id  FK", "action", "plan_id  FK", "summary", "details (JSON)"])
    y = d["audit_events"]["y"] - gap
    d["import_batches"] = _table(c, xs[4], y, 19.5, "import_batches", ["*id", "kind, filename", "status", "rows_total,", "rows_valid", "report (JSON)", "created_by  FK"])
    y = d["import_batches"]["y"] - gap
    d["settings"] = _table(c, xs[4], y, 19.5, "settings", ["*key", "value (JSON)"])
    # relationships
    _conn(c, d["departments"], d["courses"], "v")
    _conn(c, d["departments"], d["candidates"], "h")
    _conn(c, d["candidates"], d["registrations"], "v")
    _conn(c, d["courses"], d["registrations"], "h")
    _conn(c, d["courses"], d["session_papers"], "v")
    _conn(c, d["session_papers"], d["exam_sessions"], "v", "N", "1")
    _conn(c, d["seat_assignments"], d["plans"], "v", "N", "1")
    _conn(c, d["candidates"], d["seat_assignments"], "h", "1", "N", 0.7, 0.8)
    _conn(c, d["halls"], d["seat_assignments"], "h", "1", "N", 0.45, 0.35)
    _conn(c, d["plans"], d["invigilator_assignments"], "h", "1", "N", 0.9, 0.5)
    _conn(c, d["plans"], d["attendance"], "h", "1", "N", 0.6, 0.5)
    _conn(c, d["plans"], d["hall_submissions"], "h", "1", "N", 0.3, 0.5)
    _conn(c, d["invigilator_assignments"], d["users"], "h", "N", "1", 0.5, 0.9)
    _conn(c, d["users"], d["audit_events"], "v")
    # exam_sessions -> plans (routed under everything)
    es, pl = d["exam_sessions"], d["plans"]
    ych = 2.6
    c.line((es["x"] + es["w"] / 2, es["y"]), (es["x"] + es["w"] / 2, ych), lw=1.1)
    c.line((es["x"] + es["w"] / 2, ych), (pl["x"] + pl["w"] / 2, ych), lw=1.1)
    c.line((pl["x"] + pl["w"] / 2, ych), (pl["x"] + pl["w"] / 2, pl["y"]), lw=1.1)
    c.text(es["x"] + es["w"] / 2 + 1.6, es["y"] - 1.5, "1", fs=7, bold=True)
    c.text(pl["x"] + pl["w"] / 2 + 1.6, pl["y"] - 1.5, "N", fs=7, bold=True)
    c.text(52, 0.9, "16 tables. Bold = primary key; FK = foreign key. Only the principal relationships are drawn - every FK column is marked in its table. 1 = one, N = many.",
           fs=6.8, italic=True)
    c.save(out)


# ------------------------------------------------------------------ UML class diagram
def _cls(c, x, y_top, w, name, attrs, methods=(), stereo=None, fc="white"):
    hh = 3.4 if not stereo else 5.4
    h = hh + 0.9 + (PITCH * len(attrs) if attrs else 0) + (PITCH * len(methods) + 0.9 if methods else 0) + 0.4
    y = y_top - h
    c.box(x, y, w, h, "", fc=fc, r=0.8, lw=1.1)
    c.box(x, y_top - hh, w, hh, "", fc=INDIGO_L, r=0.8, lw=1.1)
    if stereo:
        c.text(x + w / 2, y_top - 1.5, stereo, fs=5.8, italic=True)
        c.text(x + w / 2, y_top - 3.9, name, fs=7.2, bold=True)
    else:
        c.text(x + w / 2, y_top - 1.8, name, fs=7.2, bold=True)
    yy = y_top - hh - 0.9
    for i, a in enumerate(attrs):
        c.text(x + 1.0, yy - PITCH * (i + 0.55), a, fs=6.0, ha="left")
    if methods:
        ym = yy - PITCH * len(attrs) - (0.4 if attrs else 0.2)
        if attrs:
            c.line((x, ym), (x + w, ym), lw=0.8)
        for i, m in enumerate(methods):
            c.text(x + 1.0, ym - PITCH * (i + 0.6), m, fs=6.0, ha="left")
    return {"x": x, "y": y, "w": w, "h": h}


def _clip(b, p, q):
    """Point where the segment p->q leaves box b (p inside b)."""
    x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    dx, dy = q[0] - p[0], q[1] - p[1]
    ts = []
    if dx:
        ts += [(x0 - p[0]) / dx, (x1 - p[0]) / dx]
    if dy:
        ts += [(y0 - p[1]) / dy, (y1 - p[1]) / dy]
    t = min(t for t in ts if t > 0)
    return p[0] + dx * t, p[1] + dy * t


def _assoc(c, a, b, ma="", mb="", label="", dashed=False, arrow=False, lo=(0, 0), diamond=False):
    pa = (a["x"] + a["w"] / 2, a["y"] + a["h"] / 2)
    pb = (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
    p, q = _clip(a, pa, pb), _clip(b, pb, pa)
    if arrow or dashed:
        c.arrow(p, q, ls="--" if dashed else "-", lw=1.0, head=True)
    else:
        c.line(p, q, lw=1.1)
    ux, uy = q[0] - p[0], q[1] - p[1]
    n = max((ux ** 2 + uy ** 2) ** 0.5, 1e-6)
    ux, uy = ux / n, uy / n
    if ma:
        c.text(p[0] + ux * 2.6 - uy * 1.6, p[1] + uy * 2.6 + ux * 1.6, ma, fs=6.4, bold=True)
    if mb:
        c.text(q[0] - ux * 2.6 - uy * 1.6, q[1] - uy * 2.6 + ux * 1.6, mb, fs=6.4, bold=True)
    if label:
        c.text((p[0] + q[0]) / 2 + lo[0], (p[1] + q[1]) / 2 + lo[1], label, fs=6.0, italic=True)


def uml(out):
    c = Canvas(12.0, 8.8)
    c.zone(1, 1, 59, 86, "Domain model (SQLAlchemy entities)", fc="#f5f7ff")
    c.zone(62, 1, 57, 86, "Seating engine and services", fc="#f3faf6")
    w = 17.5
    top = 79
    X = [3, 22.5, 42]
    cl = {}
    cl["Department"] = _cls(c, X[0], top, w, "Department", ["code", "name"])
    cl["Course"] = _cls(c, X[1], top, w, "Course", ["code", "name"])
    cl["SessionPaper"] = _cls(c, X[2], top, w, "SessionPaper", ["paper_group"])
    r2 = 58
    cl["Candidate"] = _cls(c, X[0], r2, w, "Candidate", ["roll_no", "full_name", "needs_accessible_seat"])
    cl["ExamSession"] = _cls(c, X[2], r2, w, "ExamSession", ["code", "date", "start_time", "end_time"])
    r3 = 36
    cl["Hall"] = _cls(c, X[0], r3, w, "Hall", ["code, rows, cols", "blocked_seats", "accessible_seats", "aisles_after_cols"], ["capacity()"])
    cl["SeatAssignment"] = _cls(c, X[1], r3, w, "SeatAssignment", ["row, col", "seat_label"])
    cl["Plan"] = _cls(c, X[2], r3, w, "Plan", ["version, status", "seed, rules", "data_fingerprint", "solver_hash", "assignment_hash", "scorecard, baseline"])
    r4 = 14
    cl["User"] = _cls(c, X[0], r4, w, "User", ["email, full_name", "role, status"], ["is_admin()"])
    cl["Attendance"] = _cls(c, X[2], r4, w, "AttendanceMark", ["status", "method", "marked_at"])
    _assoc(c, cl["Department"], cl["Course"], "1", "*")
    _assoc(c, cl["Course"], cl["SessionPaper"], "1", "*")
    _assoc(c, cl["ExamSession"], cl["SessionPaper"], "1", "*")
    _assoc(c, cl["Department"], cl["Candidate"], "1", "*")
    _assoc(c, cl["Candidate"], cl["Course"], "*", "*", "registers for", lo=(-3, 2.2))
    _assoc(c, cl["ExamSession"], cl["Plan"], "1", "*")
    _assoc(c, cl["Plan"], cl["SeatAssignment"], "1", "*")
    _assoc(c, cl["SeatAssignment"], cl["Hall"], "*", "1")
    _assoc(c, cl["SeatAssignment"], cl["Candidate"], "*", "1")
    _assoc(c, cl["Plan"], cl["Attendance"], "1", "*")
    _assoc(c, cl["User"], cl["Plan"], "1", "*", "created_by", lo=(0, 2.0))
    # engine side
    w2 = 17.2
    EX = [64, 83.5, 103]
    ec = {}
    ec["Rules"] = _cls(c, EX[0], top, w2, "Rules", ["adjacency", "roll_gap", "department_mix", "fill_strategy"], stereo="<<dataclass>>")
    ec["EngineCandidate"] = _cls(c, EX[1], top, w2, "EngineCandidate", ["key, roll_no", "paper, course", "department", "needs_accessible"], stereo="<<dataclass>>")
    ec["EngineHall"] = _cls(c, EX[2], top, w2 - 1.2, "EngineHall", ["rows, cols", "blocked", "accessible", "aisles_after"], ["seats()", "capacity()"], stereo="<<dataclass>>")
    ec["PlanService"] = _cls(c, EX[0], 53.5, w2, "PlanService", [], ["generate()", "publish()", "verify()"], stereo="<<service>>")
    ec["Engine"] = _cls(c, EX[1], 53.5, w2, "SeatingEngine", [], ["solve()", "precheck()", "derive_seed()"], stereo="<<module>>")
    ec["EngineResult"] = _cls(c, EX[2], 53.5, w2 - 1.2, "EngineResult", ["ok", "placements", "reasons", "seed, solve_ms", "stats"], stereo="<<dataclass>>")
    ec["Validator"] = _cls(c, EX[0], 34, w2, "Validator", [], ["validate() -> Scorecard"], stereo="<<module>>")
    ec["StageA"] = _cls(c, EX[1], 34, w2, "StageA", [], ["allocate()", "select_halls()", "greedy_pack()"], stereo="<<module>>")
    ec["Placement"] = _cls(c, EX[2], 32.5, w2 - 1.2, "Placement", ["candidate", "hall", "row, col"], stereo="<<dataclass>>")
    ec["Swap"] = _cls(c, EX[0], 17.5, w2, "SwapChecker", [], ["swap_options()", "apply_swap()"], stereo="<<service>>")
    ec["StageB"] = _cls(c, EX[1], 17.5, w2, "StageB", [], ["solve_hall()"], stereo="<<module>>")
    ec["Graph"] = _cls(c, EX[2], 17.5, w2 - 1.2, "SeatGraph", [], ["seat_neighbours()", "seat_class()", "paper_ceiling()"], stereo="<<module>>")
    _assoc(c, ec["PlanService"], ec["Engine"], "", "", "calls", dashed=True, lo=(0, 1.8))
    _assoc(c, ec["Engine"], ec["EngineResult"], "", "", "returns", arrow=True, lo=(0, 1.8))
    _assoc(c, ec["EngineResult"], ec["Placement"], "1", "*")
    _assoc(c, ec["PlanService"], ec["Validator"], "", "", "checks the plan", dashed=True, lo=(-7.5, 0))
    _assoc(c, ec["Engine"], ec["StageA"], "", "", "", dashed=True)
    _assoc(c, ec["StageA"], ec["StageB"], "", "", "colour class per paper", dashed=True, lo=(-8.5, 0))
    _assoc(c, ec["StageB"], ec["Graph"], "", "", "uses", dashed=True, lo=(0, 1.8))
    _assoc(c, ec["Swap"], ec["Validator"], "", "", "same rules", dashed=True, lo=(-6.5, 0))
    c.text(91, 82.2, "Rules, EngineCandidate and EngineHall are the inputs of solve(). PlanService maps the domain entities to them.", fs=6.0, italic=True)
    _assoc(c, cl["Plan"], ec["PlanService"], "", "", "maps entities to engine types", dashed=True, lo=(-10, 1.0))
    c.save(out)
