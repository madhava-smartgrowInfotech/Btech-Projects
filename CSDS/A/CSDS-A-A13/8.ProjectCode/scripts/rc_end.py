"""Chapters 9 and 10, references, design decisions, and the appendices."""
from __future__ import annotations

from doc_common import ROOT, REFERENCES, SHOTS
from rc_method import APP, excerpt
from rc_results import SCREENS


def sec_decisions(d):
    d.h2("Implementation Decisions and their Reasoning")
    d.table([
        ["Decision", "Alternatives considered", "Reasoning"],
        ["Constraint programming (CP-SAT) for the engine", "Sorting, zipper interleave, greedy colouring, genetic search", "Exact on hard rules; can prove infeasibility; rules are added as constraints; seeded objective gives controlled randomness"],
        ["Two stages (allocation, then layout)", "One model over all seats of all halls", "Smaller models, parallel halls, and the colour-class construction that makes same-paper neighbours impossible"],
        ["Colour classes by (row parity, column parity)", "Search for a colouring per hall", "Explicit, provably proper colouring; no search; works with aisles and blocked seats because they only remove edges"],
        ["Deterministic time budget, one worker per hall", "Wall-clock limits, many workers", "A wall-clock limit would make results depend on machine load; determinism makes plans reproducible"],
        ["Sub-seeds derived by SHA-256", "Python's built-in hash or sequential seeds", "Stable across runs and machines (Python hash randomisation would break reproducibility)"],
        ["Independent validator", "Trust the solver", "A plan is never stored unless a solver-free check agrees; the same checks serve the swap map and the benchmark"],
        ["Backend owns the rules", "Check moves in the browser", "One set of rules for the map, the exports and the benchmark; no rule drift"],
        ["FastAPI with Pydantic and SQLAlchemy", "Flask (the base paper's choice), Django", "Typed request models, automatic OpenAPI documentation, simple tests with a test client"],
        ["SQLite", "PostgreSQL or MySQL", "No server to install for one office; created on first start; adequate for the measured load. A server database is future work"],
        ["JWT with bcrypt", "Server-side sessions", "Stateless API suitable for tablets and phones; short-lived tokens; passwords never stored in clear"],
        ["React with TanStack Query and dnd-kit", "Server-rendered pages (the base paper's Jinja2)", "Responsive seat map with drag, tap and keyboard operation and live checks"],
        ["Vite proxy for /api", "Direct calls to the API port", "One address for tablets and phones; no CORS configuration for users"],
        ["Synthetic seeded data", "Real student data", "No privacy risk; reproducible; exercises every rule (shared papers, clashes, accessibility)"],
        ["Benchmark with baselines instead of accuracy metrics", "Reporting accuracy-style numbers", "Nothing is trained; violations and speed are the honest measures"],
    ], "Implementation decisions", widths=[0.26, 0.26, 0.48], font=9)


# ------------------------------------------------------------------ Chapter 9 and 10
def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project set out to replace the slow, error-prone and predictable preparation of examination seating with an intelligent, "
        "constraint-satisfying system. The result is SeatWise, a web application whose core is a two-stage OR-Tools CP-SAT engine: "
        "Stage A shares candidates between halls and gives each paper one colour class of the hall's seat grid, and Stage B lays out the "
        "seats of each hall with roll-number spacing, accessible seats and department mixing, using seeded random objectives so that "
        "the returned plan is a random member of the valid plans. An independent validator checks every plan before it is stored, and "
        "every plan records its seed and three SHA-256 fingerprints so that it can be reproduced and verified. Around the engine are a "
        "validated import, a seat map with live, explained editing, PDF and Excel outputs, QR seat slips, a public seat lookup, a "
        "tablet attendance register, analytics and an audit trail.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved and Main Contributions")
    d.p("All six objectives of the project definition were achieved on the evidence available: seating is automated from uploaded "
        "data; capacity, subject and roll-number constraints are satisfied; spacing is enforced and seating is randomised; charts "
        "and hall-wise reports can be exported; seat lookup and attendance work in real time; and plan preparation takes seconds. Two "
        "added objectives, reproducibility and an honest evaluation, were also met. The qualifications are stated below. The main "
        "contributions are listed in the section on novelty and key contributions.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.bullets([
        "Confining each paper to one colour class of a hall's seat grid makes same-paper neighbours impossible by construction, for any number of papers and for diagonal neighbours.",
        "On the benchmark, all 24 SeatWise plans met every hard rule, while none of the 72 baseline runs did. At 600 candidates roll-order seating leaves 1,253 same-paper pairs, round-robin 281 and a random shuffle 265; SeatWise leaves none.",
        "A 600-candidate sitting is seated in 2.4 s and a 2,000-candidate sitting in 4.8 s on a 12-thread desktop.",
        "Seeded randomisation within the valid set is as unpredictable as a random shuffle (correlation 0.065; 1.0% repeated pairs).",
        "The price of the construction is a front-row bias of 4.7 percentage points, and four-neighbour mode is slower (6.0 s).",
        "A deterministic budget, one worker per hall and SHA-256 sub-seeds make plans reproducible, which lets Verify prove that a plan was not hand-picked.",
        "58 automated tests pass, and an end-to-end scenario of import, planning, export, lookup and attendance completes in 11.4 s.",
    ])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets([
        "Examination cells of colleges and universities preparing internal, semester and supplementary sittings.",
        "Schools and coaching institutes with multiple papers in one hall, where mixing papers is the usual anti-malpractice measure.",
        "Entrance and recruitment examinations that need fair, unpredictable and auditable seating, with a public seat lookup instead of notice boards.",
        "Any setting with grid seating and separation rules, such as lab slots or staggered sessions, by changing the rules rather than the engine.",
    ])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.paras(
        "The evidence is from synthetic data, from one machine and from automated and scripted testing; no real examination cell or "
        "invigilator has used the system, so user acceptance is unknown. The front-row bias and the slower four-neighbour mode are "
        "known weaknesses of the design. The base paper reports no measurements, so the comparison with it is qualitative. There is no "
        "trained model, so accuracy-style metrics do not apply. These limitations are described in Chapters 1, 7 and 8 and shape the future work below.")


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Pilot and user study.** Run the engine on a real, anonymised sitting, compare it with the cell's manual plan, and gather feedback from invigilators and the examination cell on the seat map, attendance screen and lookup page.",
        "**Reduce the front-row bias.** Rotate or randomise which colour classes include the front row, or add a fairness term to Stage A, and re-measure.",
        "**Speed up four-neighbour mode.** Tune the per-hall budget separately for each adjacency mode, or reduce the Stage B model by symmetry breaking.",
        "**Better benchmarks.** Repeat the benchmark on several machines, add larger and irregular halls, and publish the scenario generator as a reusable dataset.",
        "**Front-end tests.** Add component and end-to-end tests for the seat map and attendance screens.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "E-mail or SMS seat notifications and an installable mobile app, which the base paper also names as future work.",
        "Invigilator rostering that balances load and avoids conflicts of interest, beyond the current even assignment.",
        "Further objectives in the optimiser, such as seat visibility and distance between candidates, as in the genetic approach of Kashyap et al. [6].",
        "Support for combined seating of several examination types in one hall and for last-minute substitutions with minimal change to an existing plan.",
        "Attendance with face recognition, only after a privacy and consent review.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets([
        "Move from SQLite to a server database (PostgreSQL) and run the API behind HTTPS and a reverse proxy.",
        "Container images for repeatable installation and, optionally, cloud hosting for several institutions with separate workspaces.",
        "Run the engine as a background job with a queue so that very large sittings do not hold an HTTP request open.",
        "A security review: dependency audit, penetration test, and stricter password and session policies for a shared deployment.",
    ])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "Learn from real malpractice reports which neighbour patterns matter most, and weight the constraints accordingly.",
        "Study the trade-off between guaranteed separation and fairness of seat positions with exact or approximate fairness constraints.",
        "Compare CP-SAT with mixed-integer programming and local search on the same benchmark.",
        "Combine seating with timetabling so that the choice of papers per sitting is optimised for separability.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h_plain("REFERENCES").alignment = 1
    for i, ref in enumerate(REFERENCES, 1):
        para = d.p(f"[{i}]\t{ref}", align="left", line=1.15)
        para.paragraph_format.left_indent = __import__("docx").shared.Inches(0.5)
        para.paragraph_format.first_line_indent = __import__("docx").shared.Inches(-0.5)
        para.paragraph_format.tab_stops.add_tab_stop(__import__("docx").shared.Inches(0.5))
        para.paragraph_format.space_after = __import__("docx").shared.Pt(6)
    d.p("Note: sources [2], [3] and [5] are listed from the batch literature survey; their abstracts could not be retrieved, so they "
        "are not described in the text. Sources [7]-[10] are described as the base paper [1] describes them.", italic=True, size=10, line=1.15)


# ------------------------------------------------------------------ appendices
def _whole(rel, start=None, end=None, skip_header=False, max_lines=400):
    text = (APP / rel).read_text(encoding="utf-8")
    lines = text.splitlines()
    if start:
        i = next(n for n, ln in enumerate(lines) if start in ln)
        j = next((n for n in range(i + 1, len(lines)) if end and end in lines[n]), len(lines))
        lines = lines[i:j]
    return "\n".join(lines[:max_lines])


def appendix_a(d):
    d.p("The listings are copied verbatim from the delivered source (`backend/app`); comments are those of the original code. "
        "The seat graph, Stage B, the engine loop, plan storage and the swap check are listed in Chapter 6.")
    d.h_plain("A.1  Roll numbers and the roll-gap rule", level=2)
    d.code(_whole("services/engine/rolls.py"), "rolls.py")
    d.h_plain("A.2  Pre-checks", level=2)
    d.code(_whole("services/engine/prechecks.py"), "prechecks.py")
    d.h_plain("A.3  Stage A: greedy packing and the two passes (excerpt)", level=2)
    d.code(_whole("services/engine/stage_a.py", "def greedy_pack", "def select_halls", 60), "stage_a.py: greedy_pack")
    d.code(_whole("services/engine/stage_a.py", "    # Pass 1: the best allocation.", None, 32), "stage_a.py: the two passes")
    d.h_plain("A.4  Independent validator (excerpt)", level=2)
    d.code(_whole("services/engine/validator.py", "    for hall in halls:", "    card.utilisation", 40), "validator.py: neighbour checks")
    d.h_plain("A.5  Password hashing and tokens", level=2)
    d.code(_whole("core/security.py"), "security.py")


def appendix_b(d):
    d.h_plain("B.1  Requirements", level=2)
    d.table([
        ["Item", "Version", "How to get it"],
        ["Windows", "10 or 11 (64-bit)", "-"],
        ["Python", "3.11", "python.org, Windows installer (64-bit); tick *Add python.exe to PATH*"],
        ["Node.js", "LTS (20 or newer)", "nodejs.org, LTS installer"],
        ["Git", "any", "Only needed to download or update the code"],
        ["Disk space", "about 1.5 GB", "-"],
        ["Internet", "first setup only", "Packages are downloaded once; SeatWise itself runs offline"],
    ], "Installation requirements", widths=[0.2, 0.25, 0.55], font=9.5)
    d.h_plain("B.2  Set up, start and stop", level=2)
    d.numbered([
        "Open the product folder (the one that contains `setup.bat` and `run.bat`).",
        "Double-click `setup.bat`. It checks Python and Node.js, creates the `venv` environment, installs the backend packages, creates `.env` with a random login secret, installs the web packages, creates the database `data\\app.db` with the demo accounts and prints a checklist; every line should say OK. It is safe to run again.",
        "Double-click `run.bat`. It starts the API on port 8113 and the web app on port 5113, waits until both answer and opens http://localhost:5113. The API documentation is at http://localhost:8113/docs.",
        "Sign in with a demo account (below). Keep the two server windows open while you use SeatWise.",
        "Double-click `stop.bat` (or close the two windows) to stop SeatWise.",
    ])
    d.table([
        ["Account", "Email", "Password"],
        ["Exam controller (administrator)", "admin@seatwise.local", "SeatWise@2026"],
        ["Invigilator", "invigilator@seatwise.local", "SeatWise@2026"],
        ["More invigilators", "inv01@seatwise.local ... inv09@seatwise.local", "SeatWise@2026"],
    ], "Demo accounts (change the demo password before sharing the PC)", widths=[0.34, 0.42, 0.24], font=9.5)
    d.h_plain("B.3  A five-minute tour", level=2)
    d.numbered([
        "Sign in as the exam controller and open **Import data**. Under *Templates & samples* download the sample workbook, drop it on the upload area, and click **Import 1,020 rows** once validation has passed.",
        "Open **Sittings & plans**, choose a sitting and click **Generate plan**. It is solved in a few seconds with 0 same-paper neighbours. Click **Publish**; repeat for two more sittings.",
        "Click **Seat maps**. Drag a candidate onto a red seat: the move is blocked and the reason shown; drop on a green seat to swap. Open **Exports** and download the seating charts (PDF) and hall lists (Excel).",
        "Sign out and open **Find my seat** on the home page, enter a candidate ID and download the QR slip. Sign in as the invigilator, open **Attendance**, type or scan that ID and mark attendance.",
    ])
    d.p("The same scenario can be checked automatically with `venv\\Scripts\\python scripts\\demo_scenario.py`.")
    d.h_plain("B.4  User guide by role", level=2)
    d.table([
        ["Role", "Main tasks and where to find them"],
        ["Exam controller", "**Import data**: choose what to import, add and update or replace, upload; read the report; import. **Sittings & plans**: choose rules, halls and a seed; Generate; Verify; Publish; assign invigilators. **Seat maps**: pick up a candidate, read green and red seats, drop. **Exports**: five downloads. **Analytics, Audit trail, Team, Settings**."],
        ["Invigilator", "**Attendance**: open a hall, scan a slip or type a roll number, tap Present or Absent, *Mark remaining absent*, **Submit** to lock the register. Open the hall map read-only; print the chart or sheet of the assigned hall."],
        ["Candidate", "**Find my seat**: enter the candidate ID (for example ACF24017), read the hall, seat and map, download the QR slip. No account is needed; only published plans appear."],
    ], "Tasks by role", widths=[0.2, 0.8], font=9.5)
    d.h_plain("B.5  Tablets, phones and useful commands", level=2)
    d.p("Invigilators can take attendance on a tablet and candidates can look up seats on phones over the same Wi-Fi: find the PC's IPv4 "
        "address with `ipconfig`, open `http://<address>:5113` on the device, allow Node.js on private networks when Windows asks, and set "
        "`PUBLIC_BASE_URL` in `.env` to the same address before printing slips so that the QR codes open it. Camera scanning works only "
        "on localhost or HTTPS; over a plain network address use a hand-held scanner or type the ID.")
    d.code("venv\\Scripts\\python scripts\\check_env.py --network      :: check the machine and .env\n"
           "cd backend && ..\\venv\\Scripts\\python -m pytest         :: backend tests\n"
           "cd frontend && npm run build                            :: type check and production build\n"
           "venv\\Scripts\\python -m ml.benchmark                    :: engine benchmark (about 7 minutes)\n"
           "venv\\Scripts\\python -m ml.benchmark --quick            :: smoke run\n"
           "venv\\Scripts\\python scripts\\init_db.py --reset         :: start with a fresh database", "useful commands")


def appendix_c(d):
    from rc_results import screens_block
    d.p("Screens that are described in Chapter 8 are not repeated. All are captures of the running application with real data.")
    screens_block(d, [s for s in SCREENS if not s[3]])
