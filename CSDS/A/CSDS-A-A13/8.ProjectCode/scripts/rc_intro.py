"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations."""
from __future__ import annotations

from doc_common import BASE_PAPER, PRODUCT


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "Examinations are the main way in which colleges and universities certify what students have learnt, and every examination cycle "
        "begins with an administrative task that is easy to underestimate: deciding who sits where. For each sitting the examination cell has "
        "to turn a list of candidates, a list of courses, the layouts of the available halls and a timetable into a seating plan that every "
        "invigilator can follow and every candidate can find. A sitting of five hundred candidates writing eight different papers in a dozen "
        "halls already contains more than two hundred seat decisions per hall, and the cell usually prepares several sittings per day.",
        "The domain of this project is therefore **examination management**, and more precisely the **seat-allocation problem**. Seat allocation "
        "sits between two well-studied areas of computer science. It resembles examination *timetabling* [12], where events must be assigned "
        "to slots without clashes, and it resembles *graph colouring* [11], because candidates who must not sit next to one another form the "
        "edges of a conflict graph. Unlike timetabling, however, the unit of decision is a physical seat in a grid, and the conflicts that "
        "matter are geometric: who is in front, behind, beside or diagonal to whom.",
        "In practice, most institutions still solve this problem by hand or with spreadsheets. Software that automates it exists, but, as the "
        "literature survey in Chapter 2 shows, it mostly applies a fixed sort or interleaving pattern. This project, **SeatWise**, treats seat "
        "allocation as a constraint-optimisation problem and solves it with a constraint-programming solver, which allows several rules to be "
        "guaranteed at the same time. The title of the project, *AI-Enabled Digital Examination Seating Management System*, should be read in "
        "that sense: the artificial-intelligence component is combinatorial optimisation with controlled randomness. No machine-learning model "
        "is trained in this project, and the report says so wherever evaluation is discussed.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Three observations motivated the project. First, preparing seating by hand is slow and error-prone. The base paper [1] describes "
        "examination committees collecting student lists from several departments, counting the capacity of each room and assigning roll "
        "numbers one by one, a process that it says takes days for thousands of students and that produces duplicated or missing seats. "
        "Any late change, such as a broken bench or an added candidate, forces much of the plan to be redone.",
        "Second, the usual shortcuts are predictable. Seating in roll-number order, which is what a spreadsheet sorted by roll number "
        "produces, puts friends and classmates next to one another and, in a sitting where several courses are examined together, puts "
        "candidates of the same paper side by side. Our own measurements (Chapter 8) show how large the effect is: in a synthetic sitting of "
        "600 candidates writing eight papers, roll-order seating leaves 1,253 pairs of neighbours who write the same paper. Interleaving "
        "subjects in a repeating cycle, the usual improved manual method, still leaves 281 such pairs, and it repeats the same neighbours every "
        "time it is run, so the pattern can be learnt.",
        "Third, an examination day involves more than a seating chart. Candidates need to find their seats, invigilators need a register, "
        "and the examination cell needs to know afterwards what was planned, what was changed by hand and who attended. These tasks are "
        "usually handled by separate notices, printed sheets and phone calls. A system that creates the plan can also provide these outputs "
        "from the same data, which removes a source of inconsistency.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Manual and spreadsheet-based seating is slow and prone to errors. Predictable seating patterns allow malpractice. Several constraints "
        "have to hold at once, namely hall capacity, the papers that share a sitting, roll-number spacing, department distribution and "
        "accessible seating, and they are difficult to satisfy by hand. Candidates and staff have no reliable digital way to find or track "
        "seat allocations.",
        "**Formal statement.** Given a set of candidates, each with a roll number, a department, a set of registered courses and an "
        "accessibility need; a timetable that groups courses into sittings and may declare that some courses share one question paper; and a "
        "set of halls, each a grid of seats with blocked seats, accessible seats and aisles, produce for every sitting an assignment of "
        "every candidate to exactly one seat such that (i) no seat holds two candidates, (ii) no two neighbouring seats hold candidates who "
        "write the same paper, (iii) neighbouring candidates of the same roll-number prefix differ by at least a configured gap, and "
        "(iv) every candidate who needs an accessible seat has one. Among all such assignments the system must choose one in a way that "
        "cannot be predicted, record how it was chosen so that it can be reproduced, and deliver the result, together with seat lookup, "
        "attendance and reports, through a secure web application.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.bullets([
        "**Correctness by guarantee, not by inspection.** A plan that merely looks mixed is not enough: the examination controller needs "
        "an assurance that no neighbour writes the same paper, and a way to check it.",
        "**Speed.** Generating a plan in seconds instead of days allows the cell to try several plans, change halls and respond to late changes.",
        "**Unpredictability with accountability.** Candidates must not be able to guess their neighbours, yet the controller must be able "
        "to show that the plan was not hand-picked. A recorded random seed gives both.",
        "**One source of truth.** The chart, the hall list, the invigilator sheet, the QR slip, the public lookup and the attendance "
        "register should all come from the same stored plan.",
        "**Low cost and offline operation.** The system should run on an ordinary office PC with free software and without an internet "
        "connection, because colleges cannot always rely on one on examination day.",
    ])


def sec_objectives(d):
    d.h2("Project Objectives")
    d.numbered([
        "Automate seat allocation from uploaded student, course, hall and timetable data.",
        "Satisfy capacity, subject-combination and roll-number constraints using optimisation.",
        "Enforce anti-cheating spacing and randomise seating.",
        "Generate exportable seating charts and hall-wise reports.",
        "Provide real-time seat lookup and attendance tracking.",
        "Reduce the time and errors of manual seating preparation.",
    ])
    d.p("Two further engineering objectives were added during design: to make every plan reproducible and auditable, and to evaluate the "
        "engine against the manual methods it replaces with measurements rather than claims. How far each objective was met is "
        "reported in the results chapter, under objectives versus outcomes.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "Validated import of courses, halls, candidates and the timetable from Excel or CSV files, with row-level error reports.",
        "Constraint-optimised seating for each sitting: capacity, no same-paper neighbours (8-neighbour or 4-neighbour adjacency), a configurable "
        "roll-number gap, accessible seats, department mix, and compact or balanced use of halls.",
        "Seeded randomisation, reproducibility, fingerprints, a Verify action, and an append-only audit trail.",
        "A seat map with drag-and-drop swaps that checks every move against the same rules.",
        "Outputs: seating charts and invigilator sheets (PDF), hall lists and attendance report (Excel), seat slips with QR codes (PDF).",
        "Tablet-friendly attendance, a public seat-lookup page, analytics, team management with two roles, and editable default rules.",
        "An evaluation harness (benchmark) that compares the engine with sequential, round-robin and random seating.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Timetabling itself: the timetable is an input; SeatWise does not decide which papers share a sitting.",
        "Invigilator duty rostering beyond an even, automatic assignment of one invigilator per hall.",
        "Online or remote proctoring, face recognition, biometric attendance, and result processing.",
        "Cloud hosting, multi-institution tenancy, e-mail or SMS delivery, and payment or fee features.",
        "Training machine-learning models: the engine is a constraint model, and nothing is learnt from data.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "A candidate's neighbours are the seats directly in front, behind, beside and (in 8-neighbour mode) diagonal to the candidate's "
        "seat. Aisles break adjacency across them. Cheating beyond that distance is outside the model.",
        "A roll number is a text prefix followed by a number (for example ACF24017); the roll-gap rule compares numbers that share a prefix.",
        "Two courses that share a question paper are declared as one paper group in the timetable, are examined in the same sitting, "
        "and count as one paper for separation.",
        "The system runs on one machine for one institution; the administrator is trusted to import correct data.",
    ])


def sec_contrib(d):
    d.h2("Novelty and Key Contributions")
    d.paras(
        "The base paper [1] allocates seats with a zipper algorithm that interleaves two subject lists. SeatWise keeps the idea of a "
        "data-driven, rule-based allocation but changes how the rules are enforced. The points below are new **relative to the base paper "
        "and the systems reviewed in Chapter 2**; we do not claim that they are new to the field as a whole, since constraint programming "
        "and graph colouring are established techniques [11]-[14].")
    d.numbered([
        "**Rules guaranteed by construction.** A hall's seats are coloured so that seats of one colour class are never neighbours. "
        "Stage A confines each paper to one colour class per hall, which makes same-paper neighbours impossible before any seat is "
        "chosen. This works for any number of papers and for diagonals, where a two-subject zipper does not.",
        "**Two-stage constraint optimisation.** Stage A (hall and colour-class allocation) and Stage B (seat layout per hall) are both "
        "modelled and solved with OR-Tools CP-SAT [14], with halls laid out in parallel and a bounded retry strategy.",
        "**Controlled randomness.** Among all valid plans the engine returns one chosen by a seeded random objective. Measured "
        "unpredictability matches a pure random shuffle (roll-to-seat correlation 0.065; 1.0% repeated neighbour pairs), while every "
        "hard rule still holds.",
        "**Reproducibility and audit.** Every plan stores its seed, rules, engine version and three SHA-256 fingerprints. The Verify "
        "action re-runs the engine and proves that the plan was not hand-picked. Every move, publication and download is logged.",
        "**An independent validator.** A plain-Python checker, which shares no code with the solver model, scores every plan and "
        "backs the live swap checks, so the seat map, the exports and the benchmark agree.",
        "**Live, explained editing.** The seat map shows every possible target seat as green or red and gives the reason for each red "
        "seat, so manual changes cannot break a rule unnoticed.",
        "**A complete workflow.** Validated import, QR seat slips, a public lookup page, tablet attendance with a lock, analytics and "
        "team management are built around the engine, so one stored plan serves the whole examination day.",
        "**A measured, honest evaluation.** A seeded benchmark of 8 scenarios and three manual baselines gives 24 of 24 plans meeting "
        "every hard rule, 2.4 s for 600 candidates and 4.8 s for 2,000, and reports its own limits, such as a front-row bias of 4.7 "
        "percentage points.",
    ])


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.paras(
        "The limitations below are properties of the delivered system and of the evidence for it. They are repeated, with measurements, "
        "in Chapters 7 and 8.")
    d.bullets([
        "**Synthetic data only.** All data used for development, testing and evaluation was generated by a seeded script. No real "
        "examination data and no real users were involved, so real-world performance is not established.",
        "**No user-acceptance testing.** The interface was exercised by automated tests, scripted scenarios and manual walkthroughs, "
        "but not by real invigilators or examination staff.",
        "**Single machine, one benchmark run.** The benchmark was run once on a 12-thread Windows desktop. Other hardware, memory use "
        "and many simultaneous users were not measured. SQLite is suited to one office, not to many institutions.",
        "**Front-row bias.** Because each paper occupies one colour class per hall and only two of the four classes include the front "
        "row, departments are slightly unevenly spread over the front row (4.7 percentage points, against 1.6 for a random shuffle).",
        "**Four-neighbour mode is slower** (6.0 s against 2.4 s for 600 candidates) because each class covers half the hall.",
        "**Capacity limit per paper.** A single paper cannot occupy more than the largest colour class of each hall; the engine "
        "refuses larger requests with an explanation rather than breaking a rule.",
        "**No machine learning.** There is no accuracy, precision, recall or F1 to report, because nothing is trained.",
        "**Camera scanning** works only where the browser allows camera access (localhost or HTTPS); otherwise a hand-held scanner or "
        "typing is used.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([
        ["Chapter", "Content"],
        ["1  Introduction", "Domain, motivation, problem statement, need, objectives, scope, contributions, limitations."],
        ["2  Literature Survey", "Base paper analysis, related work by theme, algorithms used in the literature, research gap."],
        ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility."],
        ["4  System Requirements and Analysis", "Existing and proposed systems, functional and non-functional requirements, hardware, software, roles."],
        ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, database and module design, user interface."],
        ["6  Methodology and Software Implementation", "Method, dataset, algorithm and its formulation, application, API, security, installation."],
        ["7  System Testing", "Test strategy and the unit, integration, functional, security, performance and edge-case results."],
        ["8  Results and Output Screens", "Output screens, benchmark results, comparison with the base paper, analysis, objectives versus outcomes."],
        ["9  Conclusion", "Summary, achievements, findings, applications, limitations."],
        ["10  Future Scope", "Improvements, features, deployment and research directions."],
        ["References, Appendices", "IEEE references; important code; installation and user guide; additional screens."],
    ], "Organisation of the report", widths=[0.3, 0.7], font=10)
