"""Chapters 3 and 4: feasibility study, requirements and analysis."""
from __future__ import annotations


# ------------------------------------------------------------------ Chapter 3
def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.paras(
        "Technical feasibility asks whether the required capability can be built with available technology. The central risk of this "
        "project was whether a constraint solver could produce a valid, randomised plan for hundreds or thousands of candidates "
        "fast enough for interactive use. The benchmark in Chapter 8 answers that: every one of 24 benchmark plans met every hard rule, a "
        "600-candidate sitting took 2.4 s on average and a 2,000-candidate sitting 4.8 s, on an ordinary 12-thread desktop.",
        "The remaining components use mature, widely documented open-source technology: FastAPI and SQLAlchemy for the service layer, "
        "SQLite for storage, React and Vite for the interface, and ReportLab, openpyxl and qrcode for the outputs. All of them run on "
        "Windows 10 and 11 with Python 3.11 and Node.js LTS. The team's skills (Python, SQL, JavaScript and optimisation basics) cover "
        "the stack, and each component can be tested separately. The project is therefore technically feasible, and it was built.")


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.paras(
        "SeatWise needs no licence fees and no cloud subscription. Every library and tool used is free and open source, and no API key "
        "is required because the system works offline once installed. The only hardware needed is an ordinary office PC that an "
        "examination cell already owns; tablets for attendance are optional, since a hand-held scanner or typing also works. The "
        "development effort was student time. We did not record or estimate a monetary cost of that effort, and we therefore give "
        "no rupee figure; the table lists what would otherwise have to be bought.")
    d.table([
        ["Resource", "Used for", "Licence (to our knowledge)", "Cost"],
        ["Python 3.11, Node.js LTS", "Back end and build tools", "PSF; MIT", "Free"],
        ["FastAPI, SQLAlchemy, Pydantic", "API, ORM, validation", "MIT", "Free"],
        ["OR-Tools (CP-SAT)", "Seating engine", "Apache 2.0", "Free"],
        ["SQLite", "Database", "Public domain", "Free"],
        ["React, Vite, Tailwind CSS", "Front end", "MIT", "Free"],
        ["ReportLab, openpyxl, qrcode", "PDF, Excel and QR outputs", "BSD / MIT", "Free"],
        ["pytest, Playwright", "Tests and screenshots", "MIT; Apache 2.0", "Free"],
        ["Office PC (existing)", "Server and administrator console", "-", "Already owned"],
        ["Tablet or hand-held scanner", "Attendance (optional)", "-", "Optional"],
    ], "Resources and cost", widths=[0.26, 0.28, 0.28, 0.18], font=9.5)
    d.p("Against these costs, the benefit is the staff time saved on each sitting, the reduction in duplicate or missing seats, and the "
        "removal of separate paper processes for notices, registers and lookups. We have not measured time saved in a real "
        "examination cell, so we state the benefit qualitatively.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.paras(
        "The system has two kinds of staff users and one public audience. The examination controller imports data, generates and publishes "
        "plans, and reviews analytics. The invigilator opens an assigned hall and takes attendance. Candidates use a public page without "
        "an account. The workflows follow the existing process (collect lists, make plan, print, supervise) so the change for staff is "
        "mainly that the plan-making step is done by the software.",
        "Usability measures built into the product include a first-run checklist on the dashboard, Excel templates with a how-to sheet, "
        "plain-language validation messages that name the sheet, row and column, and explanations for impossible requests. The interface "
        "works from a 360 px phone to a desktop, supports light and dark themes, and the seat map can be operated from the keyboard. "
        "We did not test usability with real staff; this is recorded as a limitation and as the first item of future work.")


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The work followed the three review phases of the project. The dated milestones that we can evidence are the engine benchmark "
        "run of 21 September 2026 and the documentation and screenshot capture of 15 October 2026; the other dates were not recorded, so "
        "the table lists phases and outputs only.")
    d.table([
        ["Phase", "Activities", "Outputs"],
        ["Review 1: problem and research", "Problem identification, base paper study, literature survey, research gap, objectives, proposed approach", "Abstract, literature survey, objectives and problem statement, Review 1 slides"],
        ["Review 2: design and progress", "Architecture, data model, engine design, importer, plans, seat map, exports, attendance, analytics, tests, benchmark", "Working product, 58 tests, benchmark run, Review 2 slides"],
        ["Final: evaluation and documentation", "Re-run tests and demo scenario, latency measurements, screenshots, diagrams, report", "Final report and documents, Final slides"],
    ], "Project schedule by review phase", widths=[0.24, 0.46, 0.3], font=9.5)


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.h3("Advantages")
    d.bullets([
        "Guaranteed rule compliance, checked by an independent validator.",
        "Seconds instead of days; any plan can be regenerated or compared.",
        "Reproducible and auditable plans; one stored plan serves charts, slips, lookup and attendance.",
        "Free software, offline operation, simple Windows setup (`setup.bat`, `run.bat`).",
    ])
    d.h3("Constraints")
    d.bullets([
        "One machine and one SQLite database: suitable for one institution, not for many.",
        "Solve time grows with the number of halls and is higher in 4-neighbour mode.",
        "A single paper larger than the colour-class capacity of the selected halls cannot be seated; more halls are needed.",
        "Evidence is from synthetic data; real-world validation is future work.",
    ])


# ------------------------------------------------------------------ Chapter 4
def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.paras(
        "In the existing process the examination cell collects candidate lists from departments, sorts them by roll number in a "
        "spreadsheet, fills halls row by row and prints a chart for the notice board. Some institutions use software that alternates "
        "subjects or branches in a fixed pattern, as in the base paper [1].")
    d.bullets([
        "Manual allocation is time-consuming and error-prone; duplicates and omissions occur.",
        "Sequential and fixed patterns are predictable and allow malpractice: roll-order seating leaves 1,253 same-paper neighbour "
        "pairs in a 600-candidate benchmark sitting, and interleaving still leaves 281.",
        "Constraints such as subject clashes, spacing, accessible seats and department mix are hard to satisfy by hand.",
        "Any change requires redoing much of the plan, and manual changes are not checked or recorded.",
        "Candidates cannot look up seats digitally, and attendance is recorded on paper.",
    ])


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.paras(
        "SeatWise replaces the plan-making step with a constraint-optimisation engine and wraps it in a web application. The examination "
        "controller uploads four files, sets the rules and presses *Generate plan*. The engine seats every candidate so that no two "
        "neighbours write the same paper, roll numbers are spaced, accessible seats are honoured and departments are mixed, and it "
        "chooses one such plan at random from a recorded seed. The controller reviews the seat map, moves seats with live checks, "
        "publishes, and prints charts and slips. On the day, candidates look up their seat, invigilators take attendance on a tablet, "
        "and analytics and the audit trail summarise what happened.")
    d.table([
        ["Advantage", "How it is achieved", "Evidence"],
        ["Rule compliance", "Colour-class construction plus Stage B constraints; independent validator", "0 same-paper pairs in 24 of 24 benchmark plans"],
        ["Speed", "Parallel per-hall solving, tuned budget", "2.4 s at 600 candidates; 4.8 s at 2,000"],
        ["Unpredictability", "Seeded random objective", "Roll-to-seat correlation 0.065; 1.0% repeated neighbour pairs"],
        ["Reproducibility", "SHA-256 sub-seeds and fingerprints; Verify", "Same seed gives the same plan (tests)"],
        ["Safe editing", "Swap checker with reasons", "Illegal move refused with a reason (tests)"],
        ["Complete workflow", "Import, exports, QR slips, lookup, attendance, analytics, audit", "Demo scenario passes end to end"],
    ], "Advantages of the proposed system", widths=[0.2, 0.42, 0.38], font=9.5)


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([
        ["ID", "Requirement", "Role"],
        ["FR1", "Import courses, halls, candidates and the timetable from Excel or CSV, with downloadable templates and samples", "Admin"],
        ["FR2", "Validate every row and report errors and warnings with sheet, row and column; block the import while errors remain", "Admin"],
        ["FR3", "Generate a seating plan for a sitting from selected halls, rules and an optional seed", "Admin"],
        ["FR4", "Guarantee capacity, no same-paper neighbours, roll-number gap and accessible seats for every candidate", "System"],
        ["FR5", "Explain in plain language why a plan is impossible and suggest a change", "System"],
        ["FR6", "Keep plan versions; publish a plan (archiving the previous one); delete only drafts and archived versions", "Admin"],
        ["FR7", "Verify a plan by re-running the engine with the stored seed and comparing fingerprints", "Admin"],
        ["FR8", "Show a colour-coded seat map and let the administrator move or swap candidates with a live rule check and reasons", "Admin"],
        ["FR9", "Export seating charts and invigilator sheets (PDF), hall lists and attendance report (Excel), and QR seat slips (PDF)", "Admin"],
        ["FR10", "Take attendance per hall: tap, scan, mark remaining absent, submit and lock; administrators may reopen", "Invigilator"],
        ["FR11", "Provide a public seat lookup by candidate ID showing published seats only, a shortened name and a hall map", "Candidate"],
        ["FR12", "Provide dashboard and analytics, including the engine benchmark", "Admin"],
        ["FR13", "Record every plan, seed, move, publication, import, download and attendance action in an append-only audit trail", "System"],
        ["FR14", "Authenticate users; two roles; account requests approved by an administrator; never leave the system without an administrator", "All"],
        ["FR15", "Edit default rules; reset the workspace only after typed confirmation", "Admin"],
        ["FR16", "Assign invigilators automatically and evenly, one hall per invigilator per sitting", "System"],
    ], "Functional requirements", widths=[0.08, 0.76, 0.16], font=9.5)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([
        ["Attribute", "Requirement", "Status (see Chapters 7 and 8)"],
        ["Performance", "Generate a plan in seconds; interactive pages respond within about 100 ms", "2.4 s at 600 candidates; data endpoints 2-11 ms median"],
        ["Correctness", "Never store a plan that breaks a hard rule", "Validator runs before storage; 24 of 24 plans valid"],
        ["Reproducibility", "Same data, rules, seed and engine give the same plan", "Tested; Verify action"],
        ["Security", "Hashed passwords, signed tokens, role checks, rate-limited public endpoints, minimal public data", "bcrypt, JWT, 429 after 30 lookups a minute"],
        ["Reliability", "Validate inputs, explain failures, recover from a failing hall", "Retry at 4x budget, then re-balance (max 5)"],
        ["Usability", "Work from 360 px phones to desktops; light and dark themes; keyboard operation of the seat map", "Checked by walkthrough; no user study"],
        ["Portability", "Run on Windows 10 and 11 with one setup script", "setup.bat completed on a clean copy in 108 s"],
        ["Maintainability", "Modular code, automated tests, documented configuration", "58 tests; 11 guides in docs/"],
        ["Offline operation", "No internet or API key needed after installation", "Yes"],
    ], "Non-functional requirements", widths=[0.18, 0.46, 0.36], font=9.5)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.h3("Hardware")
    d.table([
        ["Item", "Requirement"],
        ["Computer", "A Windows 10 or 11 (64-bit) PC. The benchmark and the measurements in this report were taken on a 12-thread Intel desktop; a minimum specification was not measured"],
        ["Disk", "About 1.5 GB free for the Python environment, web packages and data"],
        ["Network", "Internet only for the first installation; a local network for tablets and phones, if used"],
        ["Optional", "Tablet for attendance; hand-held QR scanner; printer for charts and slips"],
    ], "Hardware requirements", widths=[0.2, 0.8], font=9.5)
    d.h3("Software")
    d.table([
        ["Component", "Version used", "Purpose"],
        ["Python", "3.11", "Back end and engine"],
        ["Node.js", "LTS (20 or newer)", "Front-end tools and development server"],
        ["FastAPI / Uvicorn", "0.141 / 0.53", "REST API server"],
        ["SQLAlchemy / SQLite", "2.0 / bundled", "Persistence"],
        ["OR-Tools", "9.15.6755", "CP-SAT solver"],
        ["NumPy, pandas, openpyxl", "2.4, 3.0, 3.1", "Numerics and Excel import and export"],
        ["ReportLab, qrcode", "5.0, 8.2", "PDF and QR generation"],
        ["React / Vite / TypeScript", "18.3 / 6.3 / 5.8", "Front end"],
        ["Tailwind CSS, Recharts", "3.4, 3", "Styling and charts (with shadcn/ui and dnd-kit)"],
        ["pytest, httpx", "9.1, 0.28", "Back-end tests"],
        ["Browser", "Current Chrome or Edge", "Client"],
    ], "Software requirements", widths=[0.36, 0.24, 0.4], font=9.5)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.table([
        ["Role", "Can do", "Cannot do"],
        ["Exam controller (administrator)", "Everything: import, rules, generate, verify, swap, publish, exports, attendance (all halls), analytics, audit, team, settings", "Disable or demote the last active administrator"],
        ["Invigilator", "See assigned halls in published plans; open hall maps read-only; mark attendance; submit the register; download their hall's chart or sheet", "Import, generate, swap, publish, see analytics or audit, manage accounts"],
        ["Candidate (public)", "Look up a published seat by candidate ID; download a QR slip", "See any other data; see unpublished plans"],
    ], "User roles and permissions", widths=[0.22, 0.48, 0.3], font=9.5)
    d.bullets([
        "**Data constraints.** Every course in the timetable appears once; no candidate may have two papers in one sitting; courses sharing a paper must be in the same sitting.",
        "**Seat constraints.** Hall layouts are rectangles of at most 26 rows and 30 columns, with blocked seats, accessible seats and aisles.",
        "**Operational constraints.** One administrator console at a time is expected; the lookup endpoints allow 30 requests a minute per client.",
    ])
