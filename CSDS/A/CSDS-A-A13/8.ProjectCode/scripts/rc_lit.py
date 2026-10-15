"""Chapter 2 content: literature survey."""
from __future__ import annotations

from doc_common import BASE_PAPER


def sec_lit_overview(d):
    d.h2("Overview of the Survey")
    d.paras(
        "The survey covers the base paper, the five works listed in the batch literature survey, and the systems that the base paper itself "
        "reviews. Where we could retrieve a source (the base paper, Adetona and Akintoye [4], Kashyap et al. [6]) we describe what it "
        "reports. Where we could not retrieve the source, we say so and do not describe its method or results. Three of the five works "
        "in the batch survey, [2], [3] and [5], could not be found by title in a web search made on 15 October 2026; they are listed for "
        "completeness and characterised by their titles only. The works that the base paper summarises, [7]-[10], are described as the base "
        "paper describes them and are marked as such.",
        "The works fall into four groups: web-based seating management systems, randomisation approaches, graph-colouring and "
        "metaheuristic approaches, and the older research on examination timetabling and constraint programming. Seating is a smaller "
        "problem than timetabling, but it shares its structure of hard rules, soft preferences and the need for a solution that can be "
        "explained to the people affected by it.")


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"The base paper is {BASE_PAPER} It was written by students and a guide at ATME College of Engineering, Mysuru, and describes a "
        "web application called ExamSeater.")
    d.h3("What the base paper does")
    d.bullets([
        "**Architecture.** A Flask application with Jinja2 templates in a Model-View-Controller arrangement, SQLite through SQLAlchemy, "
        "pandas for reading uploaded lists, PyPDF2 for PDF text, and ReportLab for output.",
        "**Algorithm.** The *zipper* method: two subject lists are sorted (alphabetically, or by branch when a branch constraint is on) "
        "and interleaved with `itertools.zip_longest`, so that seat 1 holds a student of subject A, seat 2 a student of subject B, and "
        "so on. Seats marked blocked are skipped.",
        "**Features.** Login for administrators and staff with PBKDF2-hashed passwords; management of rooms, exams and staff; a visual "
        "grid of the room; a PDF seating chart; a history of earlier arrangements; and a public page where students search for a seat "
        "by USN or name.",
        "**Evidence.** Screenshots of the working application. The paper states one performance requirement, that a batch of 100 "
        "students should be processed in under 3 seconds, but it reports no measurement, no dataset and no comparison.",
        "**Future work named by the authors.** A mobile application, e-mail and SMS notification, facial-recognition attendance, cloud "
        "deployment and a drag-and-drop seat map.",
    ])
    d.h3("Strengths")
    d.bullets([
        "A complete, understandable system that a college can run on a single PC with free software.",
        "A public lookup page, which removes crowding at notice boards.",
        "Blocked seats and multiple exam types are supported, and the output is printable.",
    ])
    d.h3("Limitations")
    d.bullets([
        "Interleaving covers two subjects at a time. With three or more papers in a sitting, or with diagonal neighbours, the pattern "
        "does not by itself prevent same-paper neighbours.",
        "The seating pattern is fixed and therefore predictable; no randomness is used.",
        "There are no roll-number spacing rules, no accessible-seat handling and no department balancing beyond a sort order.",
        "No measured results are reported, so the claims cannot be compared quantitatively.",
        "No attendance, no audit trail, no reproducibility mechanism and no live validation of manual changes.",
    ])
    d.h3("What SeatWise adopts and what it changes")
    d.table([
        ["Aspect", "Base paper [1]", "SeatWise"],
        ["Data input", "CSV or PDF student list, manual entry", "Excel or CSV templates for four data kinds, validated row by row"],
        ["Allocation", "Zipper interleave of two subjects", "Two-stage CP-SAT optimisation for any number of papers"],
        ["Neighbour rule", "Alternate subjects in a line", "No same-paper neighbour in 8 or 4 directions, aisles respected"],
        ["Other rules", "Optional branch rule, blocked seats", "Roll gap, accessible seats, department mix, capacity, shared papers"],
        ["Randomness", "None (fixed pattern)", "Seeded random choice among valid plans"],
        ["Reproducibility", "Not addressed", "Seed, three SHA-256 hashes, Verify, audit trail"],
        ["Manual edits", "Re-run the generator", "Drag-and-drop with live rule check and reasons"],
        ["Outputs", "On-screen grid, PDF chart", "Charts, invigilator sheets, hall lists, QR slips, attendance report"],
        ["Seat lookup", "Public search by USN or name", "Public lookup by candidate ID with hall map and QR slip"],
        ["Attendance", "Future work", "Tablet register with scan, lock and report"],
        ["Evaluation", "Screenshots; 3 s target", "Benchmark: 8 scenarios, 3 baselines, 24 of 24 plans valid"],
        ["Back end", "Flask, SQLite", "FastAPI, SQLite, React front end"],
    ], "Base paper compared with SeatWise", widths=[0.2, 0.36, 0.44], font=9.5)


def sec_related(d):
    d.h2("Related Work")
    d.h3("Web-based seating management systems")
    d.paras(
        "Several systems automate the clerical side of seating. Jitha and Fathima [7] propose a central web portal in which administrators "
        "upload student lists as CSV files and students view a static table of seats before the examination to avoid crowding at notice "
        "boards; the base paper notes that this system does not interleave subjects, so students of one branch are often seated "
        "sequentially. An AI-powered hall-allocation system published in IJSART in 2025 [10] is described in the base paper as a Flask and "
        "MySQL application that allocates students to halls and assigns invigilation duties with a deterministic constraint-based "
        "algorithm, with a weakness in dividing students across several partly used rooms. Patel [8] is described as a smart system that "
        "integrates biometric attendance and QR-code seat lookup, at a hardware cost that the base paper considers too high for typical "
        "colleges and with a requirement for internet access on every student device.",
        "Three further works appear in the batch survey: an automated seating arrangement and hall allocation system (2026) [2], a "
        "machine-learning-based system for hall seating in universities (2026) [3], and an automated seating arrangement for conducting "
        "examinations (2025) [5]. We could not retrieve their abstracts, so we use them only as evidence that the problem is active; we "
        "make no claim about their methods.")
    d.h3("Randomisation")
    d.p("The base paper summarises a study that uses a linear congruential generator to shuffle seats completely at random to prevent "
        "cheating [9]. Complete randomisation removes predictability but, as the base paper notes, confuses invigilators who collect "
        "scripts, because roll numbers are no longer in any order. It also gives no guarantee about neighbours: a random shuffle "
        "of a 600-candidate sitting leaves 265 same-paper neighbour pairs in our own benchmark. SeatWise keeps randomness but "
        "restricts it to plans that satisfy the rules, and it records the seed so that the choice can be reproduced.")
    d.h3("Graph colouring and metaheuristics")
    d.paras(
        "Adetona and Akintoye [4] describe a web application, built with Laravel and Vue.js, that seats students so that those enrolled "
        "in the same course are not adjacent. It uses a greedy graph-colouring algorithm over a connection matrix, and it sends text "
        "messages through the Termii API five minutes before the examination with the venue and required materials. The abstract reports "
        "testing in a university with a selected group of students; we read only the abstract and cannot comment on the size of the test "
        "or on its figures. The work is the closest to ours in method, since both use a colouring idea; SeatWise differs in modelling "
        "the whole allocation, including roll-number spacing, accessibility and department mix, as a constrained optimisation, in "
        "returning a random valid solution, and in making the result reproducible.",
        "Kashyap et al. [6] use a genetic multi-objective algorithm to allocate examination seats so as to reduce the chance of "
        "cheating, taking into account subject similarity, physical distancing and seat visibility. Genetic algorithms handle soft "
        "objectives well but give no guarantee that every hard rule is satisfied, which is why SeatWise uses an exact solver for the "
        "hard rules and uses optimisation only for the preferences.",
        "The theoretical background is the classical graph-colouring bound of Welsh and Powell [11], originally applied to timetabling. "
        "SeatWise uses a much simpler, explicit colouring of the seat grid: with 8-neighbour adjacency the four classes defined by "
        "(row parity, column parity) form a proper colouring.")
    d.h3("Examination timetabling and constraint programming")
    d.p("Qu et al. [12] survey search methodologies and automated systems for examination timetabling, distinguishing hard "
        "constraints that must hold from soft constraints that should be minimised, which is the same division SeatWise uses. "
        "Constraint programming [13] provides general solvers for such problems, and Google's OR-Tools CP-SAT solver [14] is a free, "
        "high-performance implementation that supports Boolean and integer models, objectives, hints and a deterministic time "
        "limit. These properties made it the natural choice for a seating engine that must also be reproducible.")


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature")
    d.paras(
        "None of the seating papers we could read uses a public benchmark dataset. The base paper works with institutional student, hall "
        "and exam lists; Adetona and Akintoye [4] test on a group of university students. Seating research therefore lacks a "
        "common dataset, which is one reason this project built a seeded generator and published its own benchmark scenarios.")
    d.table([
        ["Algorithm", "Used in", "Idea", "Guarantee on neighbours"],
        ["Sorting by roll number", "Manual and spreadsheet practice", "Fill seats in order", "None"],
        ["Zipper interleave", "Base paper [1]", "Alternate two subject lists", "Two subjects in a line only"],
        ["Linear congruential shuffle", "[9] via [1]", "Pseudo-random permutation", "None"],
        ["Greedy graph colouring", "[4]; theory in [11]", "Colour conflict graph so adjacent nodes differ", "Same-course separation (as reported)"],
        ["Genetic multi-objective search", "[6]", "Evolve seat assignments against several objectives", "Not guaranteed"],
        ["Constraint programming (CP-SAT)", "SeatWise; background [13], [14]", "Declare hard rules, solve exactly, optimise preferences", "All hard rules, or a proof that none exists"],
    ], "Seating algorithms in the literature and in SeatWise", widths=[0.24, 0.2, 0.3, 0.26], font=9.5)


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Work")
    d.table([
        ["Work", "Strengths", "Limitations"],
        ["Base paper [1]", "Complete, simple, public lookup, PDF output", "Two-subject interleave; fixed pattern; no measured results"],
        ["Adetona and Akintoye [4]", "Colouring keeps same-course students apart; SMS reminders", "Single rule family reported; abstract only read"],
        ["Kashyap et al. [6]", "Several objectives, including seat visibility", "No guarantee for hard rules (metaheuristic)"],
        ["Jitha and Fathima [7]", "Central upload; online seat table", "No interleaving (per [1])"],
        ["Patel [8]", "QR lookup, biometric attendance", "High hardware cost; needs internet (per [1])"],
        ["LCG allocation [9]", "Unpredictable", "Confuses invigilators; no rule guarantee (per [1])"],
        ["IJSART system [10]", "Hall allocation and staff duty assignment", "Weak room-overflow handling (per [1])"],
        ["Batch survey [2], [3], [5]", "Evidence that the problem is current", "Not retrieved; not assessed"],
    ], "Strengths and limitations of the surveyed work", widths=[0.24, 0.38, 0.38], font=9.5)


def sec_gap(d):
    d.h2("Research Gap")
    d.paras(
        "Existing seating systems follow fixed sorting rules; few apply constraint optimisation to guarantee anti-cheating spacing across "
        "courses and adjacent roll numbers. Reading the surveyed work against the needs of an examination cell, we identify five gaps.")
    d.numbered([
        "**Rules.** No reviewed system guarantees that no neighbour, diagonals included, writes the same paper for any number of papers.",
        "**Spacing and access.** Roll-number spacing and accessible-seat needs are rarely enforced together with paper separation.",
        "**Controlled randomness.** Fixed patterns are predictable, and complete shuffling breaks the rules; randomness that respects the rules is missing.",
        "**Evidence.** The reviewed work reports no measured conflict counts, solve times or comparisons with manual methods.",
        "**Application.** No single tool combines validated import, optimisation, reproducibility, live checked editing, QR slips, "
        "attendance and an audit trail.",
    ])
    d.p("SeatWise is designed to close these gaps, and the benchmark in Chapter 8 supplies the missing measurements for the engine.")
