"""Chapter 5 content and the diagram catalogue (shared with the block-diagram document)."""
from __future__ import annotations

from doc_common import DIAG, SHOTS

# key -> (file, caption, landscape, explanation paragraphs)
DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of SeatWise", False, [
        "The architecture has four layers. Users work in a browser on a PC, tablet or phone: the examination controller on the administrator "
        "console, the invigilator on a tablet, and the public on the home and lookup pages. The React front end (port 5113) provides "
        "the pages, the seat map and the charts, and it reaches the back end through a data layer that sends the JWT in the Authorization "
        "header. The Vite development server forwards `/api` to the back end, so tablets and phones only need one address.",
        "The FastAPI back end (port 8113) exposes a REST API with JWT authentication, role checks and a rate limit on public endpoints. "
        "Behind it sit eight services: the importer, the seating engine, an independent validator, the swap checker, the exports, the "
        "attendance service, analytics and the audit service. The back end owns every rule: the front end never decides whether a seat "
        "move is legal; it asks the API, so the seat map, the exports and the benchmark all apply identical checks. SQLite stores 16 "
        "tables, and a small profile file records the tuned solver budget and the latest benchmark results."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow from data import to analysis", False, [
        "The workflow has ten steps. The administrator imports the four data files, which are validated row by row before anything is "
        "saved, sets the seating rules, and asks the engine for a plan. An independent validator scores the plan and computes a "
        "roll-order baseline for comparison. The administrator reviews the seat map, optionally moves seats with live checks, and "
        "publishes the plan, which archives the previous version. Published plans feed the printed outputs, the public lookup and the "
        "tablet attendance, and analytics and Verify close the loop.",
        "An impossible request does not fail silently: the pre-check explains the cause (not enough seats, too few accessible seats or one paper "
        "larger than the halls can separate) and suggests a fix. Every step writes to the append-only audit trail."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context diagram)", False, [
        "The context diagram shows SeatWise as a single process with three external entities. The exam controller sends data files, "
        "rules, a seed and swap or publish commands, and receives validation reports, plans, scorecards, charts, lists, analytics and "
        "the audit trail. The invigilator sends attendance marks and scanned slips and receives hall lists, seat maps and register "
        "counts. The candidate sends a candidate ID and receives the hall, the seat, a hall map and a QR slip."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1", False, [
        "Level 1 opens the system into eight processes and five data stores. Process 1 authenticates users and reads the user and "
        "settings store D1. Process 2 imports and validates data and maintains the reference data D2 (courses, candidates, halls, "
        "timetable). Process 3 generates a plan from D2 and the rules and writes it to the plans store D3. Process 4 reviews, swaps and "
        "publishes plans in D3. Process 5 produces the outputs from published plans. Process 6 answers candidate lookups from published "
        "seats. Process 7 records attendance in D4, using the seat lists in D3. Process 8 presents analytics and the audit trail by reading "
        "D3, D4 and D5. Processes 2 to 7 append their events to the audit store D5."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: expansion of process 3 (generate seating plan)", False, [
        "Level 2 opens the plan-generation process into seven steps. Sitting data is loaded from the reference data (3.1) and pre-checked "
        "(3.2); an impossible request returns plain-language reasons to the controller. Stage A (3.3) allocates groups of candidates to "
        "halls and gives each paper a colour class; candidates are then split between halls with a seeded shuffle (3.4), laid out "
        "seat by seat in each hall in parallel (3.5), and validated and scored (3.6). The plan, its seats and an audit event are stored "
        "with the seed and three fingerprints (3.7). If a hall fails within its budget, the loop returns to Stage A to re-balance."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram of the SeatWise database (16 tables)", True, [
        "The database has 16 tables. Reference data comprises departments, courses, candidates, registrations (the many-to-many link "
        "between candidates and courses), halls and the timetable (exam sessions and session papers). A plan belongs to an exam session "
        "and owns its seat assignments, invigilator assignments, attendance marks and hall submissions. Users, audit events, import "
        "batches and settings support the application. Every foreign key is marked in its table; only the principal relationships are "
        "drawn so that the diagram stays readable."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram: domain entities and the seating engine", True, [
        "The class diagram has two groups. The domain model on the left shows the persistent entities and their associations: a "
        "department has courses and candidates, candidates register for courses, an exam session schedules papers (courses) and has "
        "plans, and a plan owns seat assignments that link a candidate to a hall seat and attendance marks. The group on the right shows "
        "the engine's plain data types (rules, candidates, halls, placements and results) and the modules and services that use them: "
        "the plan service maps entities to engine types, calls the seating engine, which runs Stage A and Stage B over the seat graph, "
        "and checks the result with the validator; the swap checker applies the same rules to manual moves."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram", False, [
        "The administrator can import and validate data, set rules, generate, verify, swap, publish and export plans, view analytics and "
        "the audit trail, and manage the team. The invigilator can request an account, view assigned halls, mark attendance, submit and "
        "lock the register, and print the chart or sheet of an assigned hall. The candidate needs no account and can look up a seat "
        "and download a QR slip. Everyone who is signed in must first sign in."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: generate a plan, publish it, and a candidate finds the seat", False, [
        "The sequence follows the main flow. The administrator chooses a sitting, rules and a seed in the web UI, which sends "
        "`POST /api/sessions/{id}/plans`. The plan service loads candidates, halls and the timetable, calls the engine, validates the "
        "result, saves the plan with its seed and fingerprints, and returns the plan and its scorecard. Publishing sets the status, archives the "
        "previous version and records an audit event. Later, a candidate enters a candidate ID on the public lookup page, which "
        "calls the rate-limited public endpoint and receives the published seat."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core seating algorithm", False, [
        "The flowchart is the control flow of the engine's `solve` function. After loading the sitting, the pre-checks reject impossible "
        "requests with reasons. Stage A runs in two passes, the first finding the best allocation and the second choosing among equally "
        "good allocations with seeded random weights. Candidates are split between halls with a seeded shuffle, and Stage B lays out "
        "every hall in parallel. A hall that finds nothing within its time budget is retried with four times the budget; if it still "
        "fails, its capacity is eased and Stage A is re-run, at most five times. A successful result is re-checked by the independent "
        "validator and stored with the seed, rules and three SHA-256 hashes."]),
}
ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]


def diagram(d, key, extra=None):
    """Write the explanation, then the figure (landscape page for the wide ones)."""
    fname, caption, landscape, paras = DIAGRAMS[key]
    for t in paras:
        d.p(t)
    if extra:
        for t in extra:
            d.p(t)
    d.figure(DIAG / fname, caption, landscape=landscape)


# ------------------------------------------------------------------ Chapter 5
def sec_arch(d):
    d.h2("Overall System Architecture")
    d.p("SeatWise is a single-machine web product: a FastAPI back end with an SQLite database and a React front end served by Vite. "
        "Everything runs offline once installed.")
    diagram(d, "architecture")
    d.table([
        ["Layer", "Technology", "Responsibility"],
        ["Browser", "Chrome or Edge on PC, tablet or phone", "Administrator console, invigilator register, public lookup"],
        ["Front end", "React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, dnd-kit, Recharts", "Pages, seat map, charts, role guards, API calls"],
        ["API", "FastAPI, Pydantic v2, JWT (PyJWT), bcrypt", "REST endpoints, authentication, authorisation, errors"],
        ["Services", "Importer, engine, validator, swap checker, exports, attendance, analytics, audit", "All business rules and outputs"],
        ["Solver", "Google OR-Tools CP-SAT 9.15", "Stage A and Stage B optimisation"],
        ["Storage", "SQLite through SQLAlchemy 2", "16 tables; created automatically on first start"],
    ], "Layers of the architecture", widths=[0.15, 0.45, 0.4], font=9.5)


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data Flow Diagrams")
    d.p("Data-flow diagrams describe how data moves between the users, the processes and the data stores at three levels of detail.")
    d.h3("Level 0")
    diagram(d, "dfd0")
    d.h3("Level 1")
    diagram(d, "dfd1")
    d.h3("Level 2")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.h3("Use-case diagram")
    diagram(d, "usecase")
    d.h3("Sequence diagram")
    diagram(d, "sequence")
    d.h3("Class diagram")
    diagram(d, "uml")


def sec_database(d):
    d.h2("Entity-Relationship Diagram and Database Schema")
    diagram(d, "er")
    d.p("The tables are created by SQLAlchemy when the application starts, so no separate migration step is needed for a first install. "
        "Unique constraints protect the main invariants: one registration per candidate and course, one seat per candidate in a plan, "
        "one candidate per seat of a hall in a plan, one attendance mark per candidate and plan, and one version number per sitting.")
    d.table([
        ["Table", "Purpose", "Key columns"],
        ["users", "Administrators and invigilators", "email (unique), role, status (active, pending, disabled), password_hash"],
        ["departments, courses", "Course catalogue", "code (unique), name, department_id"],
        ["candidates", "Candidates", "roll_no (unique), department_id, needs_accessible_seat, email, date_of_birth"],
        ["registrations", "Courses a candidate sits", "candidate_id, course_id (unique pair)"],
        ["halls", "Hall layouts", "rows, cols, blocked_seats, accessible_seats, aisles_after_cols (JSON), is_active"],
        ["exam_sessions", "Sittings", "code, date, start_time, end_time, label"],
        ["session_papers", "Courses examined in a sitting", "session_id, course_id, paper_group (shared question paper)"],
        ["plans", "A version of a sitting's seating", "status, seed, rules, engine_version, data_fingerprint, solver_hash, assignment_hash, solve_ms, scorecard, baseline"],
        ["seat_assignments", "Candidate to seat", "plan_id, candidate_id, course_id, hall_id, row, col, seat_label"],
        ["invigilator_assignments", "Who supervises a hall in a plan", "plan_id, hall_id, user_id"],
        ["attendance", "Marks per candidate", "plan_id, candidate_id, hall_id, status, method, marked_by, marked_at"],
        ["hall_submissions", "Register lock", "plan_id, hall_id, submitted_by, submitted_at"],
        ["import_batches", "Every upload and its report", "kind, filename, status, rows_total, rows_valid, report, payload"],
        ["audit_events", "Append-only log", "at, actor_id, action, plan_id, summary, details (JSON)"],
        ["settings", "Default rules", "key, value (JSON)"],
    ], "Database tables", widths=[0.2, 0.26, 0.54], font=9)


def sec_modules(d):
    d.h2("Module Design")
    d.p("The code is organised so that rules live in one place and every layer can be tested separately. Package sizes are the "
        "actual line counts of the delivered code.")
    d.table([
        ["Package", "Files", "Lines", "Responsibility"],
        ["backend/app/api", "13", "899", "One router per area: auth, users, imports, data, plans, exports, attendance, analytics, audit, public, settings, health"],
        ["backend/app/core", "7", "292", "Settings from .env, database session, security, dependencies, error types, logging"],
        ["backend/app/models", "7", "308", "SQLAlchemy entities for the 16 tables"],
        ["backend/app/schemas", "5", "362", "Pydantic request and response models"],
        ["backend/app/services/engine", "10", "1,023", "Seat graph, pre-checks, roll numbers, Stage A, Stage B, engine loop, validator, baselines"],
        ["backend/app/services/importer", "6", "1,031", "Parse CSV or XLSX, validate each kind, cross-checks, commit, templates"],
        ["backend/app/services/exports", "7", "747", "Seating charts, invigilator sheets, QR slips (PDF); hall lists and attendance (Excel)"],
        ["backend/app/services (other)", "12", "1,006", "Plans, swap, attendance, analytics, audit, hall map, sessions, rate limit, seed data"],
        ["ml (benchmark)", "6", "726", "Scenario generator, baselines, benchmark runner, predictability and plots"],
        ["backend/tests", "11", "813", "58 pytest tests"],
        ["frontend/src/pages", "19", "4,872", "Public, authentication and 13 application pages"],
        ["frontend/src/components, lib", "52", "3,787", "Layout, seat map, charts, UI kit, API client, auth, theme"],
        ["scripts", "24", "3,662", "Setup checks, sample data, demo scenario, and the documentation tools of this report"],
    ], "Modules and their size", widths=[0.28, 0.08, 0.1, 0.54], font=9)
    d.h3("Engine modules")
    d.bullets([
        "`graph.py` builds each hall's seat graph and its colour classes (the key geometric idea).",
        "`prechecks.py` produces plain-language reasons for impossible requests.",
        "`stage_a.py` allocates candidate groups to halls and colour classes with CP-SAT in two passes.",
        "`stage_b.py` lays out the seats of one hall with CP-SAT.",
        "`engine.py` runs the loop: pre-check, Stage A, split, Stage B in parallel, retry.",
        "`validator.py` is the independent checker and scorecard; `rolls.py` parses roll numbers; `baselines.py` creates the manual baselines.",
    ])


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The interface was designed around the three audiences. Administrators get a sidebar with Prepare (import, data), Seating "
        "(sittings and plans, exports, attendance, analytics, audit trail) and Workspace (team, settings). Invigilators see only their "
        "halls and the attendance screen. Candidates see a public home page and a lookup page. Principles applied throughout: every list "
        "has a loading state, an empty state and a *Try again* action; every chart has a table view; colours carry a second cue "
        "(icons, labels) so that they are not the only signal; the layout works from 360 px to desktop; and a sun or moon button "
        "switches between light, dark and system themes.",
        "The seat map is the central screen. The front of the hall is at the top, rows are lettered from the front and seats are "
        "numbered from the left. Each seat shows its label, roll number and course, with a coloured top edge for the paper. Picking up a "
        "candidate turns every other seat green (the move keeps every rule) or red (with the reason on hover or focus).")
    d.p("Real captures of the seat map and the dashboard are shown in Chapter 8.")
    d.table([
        ["Screen", "Route", "Audience", "Purpose"],
        ["Home", "/", "Public", "Overview, headline benchmark figures, links to lookup and sign-in"],
        ["Sign in, Request account", "/login, /register", "Public", "Authentication; demo workspace buttons"],
        ["Dashboard", "/app", "All staff", "Getting-started steps, figures, charts, sittings, busiest halls"],
        ["Import data", "/app/import", "Admin", "Upload, validation report, preview, commit, templates"],
        ["Data", "/app/data", "Admin", "Candidates, courses, halls, timetable"],
        ["Sittings and plans", "/app/sessions, /app/sessions/:id", "Admin", "Generate, versions, scorecard, publish, verify, invigilators"],
        ["Seat map", "/app/plans/:plan/halls/:hall", "Admin; invigilator (read-only)", "View and edit seats with live checks"],
        ["Exports", "/app/exports", "Admin", "Charts, lists, sheets, QR slips, attendance report"],
        ["Attendance", "/app/attendance, /app/attendance/:plan/:hall", "Staff", "Take and submit attendance"],
        ["Analytics", "/app/analytics", "Admin", "Plan comparison charts; engine performance"],
        ["Audit trail", "/app/audit", "Admin", "Filterable event log"],
        ["Team, Settings", "/app/team, /app/settings", "Admin", "Accounts and default rules"],
        ["Find my seat", "/lookup, /lookup/:id", "Public", "Seat lookup and QR slip"],
    ], "Screens of the application", widths=[0.2, 0.28, 0.18, 0.34], font=9)
