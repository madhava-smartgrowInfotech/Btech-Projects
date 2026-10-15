"""Chapter 8 content: results and output screens."""
from __future__ import annotations

from doc_common import BENCH, CHARTS, DEMO, EXP, METHODS, SCEN, SHOTS, TUNING, UNPRED

# file, caption, what it shows, shown in the main chapter (True) or only in Appendix C / the results document
SCREENS = [
    ("01_landing.png", "Public home page", "The public front page: a hero with an example seat grid, the *Get started* and *Find my seat* actions, and the headline results of the engine benchmark read from the stored run: 1,253 same-paper neighbours avoided in a 600-candidate sitting compared with roll order, 2.36 s to seat 600 candidates (2,000 take 4.8 s), a roll-to-seat correlation of 0.065, and 24 benchmark runs, every one meeting every hard rule.", True),
    ("02_login.png", "Sign-in page", "Email and password sign-in, with *Demo workspace* buttons for the exam controller and the invigilator, and links to request an account and to find a seat without signing in.", True),
    ("03_register.png", "Request an account", "Invigilators request an account with name, work e-mail and a password of at least eight characters; the account waits for administrator approval.", False),
    ("04_dashboard.png", "Administrator dashboard after three plans and one register", "The hero tile shows 3,379 same-paper neighbours avoided across three published sittings compared with roll-order seating (remaining: 0). The tiles show 1,359 candidates seated, 3 of 6 sittings published, an average solve time of 2.0 s (slowest 2.2 s), attendance at 95% (57 present, 3 absent, 1,299 still to mark), 100% of plans meeting every rule, and 14 halls, 7 of them used. The charts show attendance by sitting and solve time per plan.", True),
    ("05_import_empty.png", "Import page before upload", "The three steps of an import: what is being imported (everything, courses, halls, candidates or timetable), how it is applied (add and update, or replace), and the upload area, with the list of recent imports below.", False),
    ("06_import_validated.png", "Validation report for the sample workbook", "Validation passed: 1,020 of 1,020 rows are valid with 10 warnings. The sheet summaries show 49 courses, 14 halls (10 warnings), 908 candidates and 49 timetable rows. The problems table lists each warning with its sheet, row and column; here every warning says that no accessible seats were given and the front-row seats A1 and A2 were used. Nothing is saved until *Import* is pressed.", True),
    ("07_data.png", "Data page: candidates", "The candidate tab lists the 908 imported candidates with roll number, name, department and courses, a search box and a department filter; further tabs show courses, halls and the timetable.", False),
    ("08_sittings.png", "Sittings and plans", "The six sittings of the sample timetable with their candidates, papers and plan status: three are published, three show *Plan seating*.", True),
    ("09_plan.png", "Plan page with scorecard", "Version 1 of Mon 12 Oct 2026 (morning), published, with its seed. The scorecard shows 0 same-paper neighbours, 0 roll-gap violations, 1,099 conflicts avoided compared with roll order, accessible seating honoured for everyone who needs it, a solve time of 2.1 s, and 6 halls used with 92% of their seats filled. The halls table lists seats used, papers and the assigned invigilator of each hall.", True),
    ("09c_verify.png", "Verify: reproduced exactly", "Running the engine again with the stored seed on unchanged data gives an identical result: the stored engine result and the recomputed one have the same hash, so the plan was not hand-picked.", True),
    ("10_seatmap.png", "Seat map of a hall", "Hall MB-G01 (Main Hall A) with 105 of 118 seats used and 8 papers. Seats are tinted by paper, aisles are gaps, hatched seats are blocked and the wheelchair mark shows accessible seats. The side panel shows that every rule is met in this hall.", False),
    ("11_seatmap_targets.png", "Seat map with a candidate picked up", "After picking up the candidate on seat A1, every other seat is outlined green (the move keeps every rule) or red (it does not). The side panel names the candidate being moved and shows the verdict for the seat under the pointer.", True),
    ("11b_swap_refused.png", "An illegal move is refused with the reason", "Dropping the candidate on a red seat is refused. The message reads: *HCA25059 would sit next to HCA25037 (A2) - both write HCA-101.* The refusal is the live rule check working on the same code as the engine.", True),
    ("12_exports.png", "Exports page", "A plan and a hall (or all halls) are chosen, and five files can be downloaded: seating charts (PDF), hall-wise lists (Excel), invigilator sheets (PDF), seat slips with QR codes (PDF) and the attendance report (Excel).", True),
    ("13_analytics_plans.png", "Analytics: plan figures", "For the selected plan the page shows same-paper neighbours (0, with 1,105 avoided), solve time, seats filled, and neighbour pairs, a bar chart that compares SeatWise with roll-order seating for each rule, and seats filled per hall.", False),
    ("14_analytics_engine.png", "Analytics: engine performance", "The benchmark as seen by the administrator: 100% of plans satisfy every hard rule across 8 scenarios and 3 seeds, 2.4 s for 600 candidates, 1,253 conflicts avoided compared with roll order, and a roll-to-seat correlation of 0.06, with charts of solve time by session size and same-paper pairs by method.", True),
    ("15_audit.png", "Audit trail", "A filterable, append-only log: plan versions with their seeds and results, publications, downloads and verifications, each with the person, the time and a link to the plan.", True),
    ("16_team.png", "Team page", "Accounts of the administrator and the invigilators with role, status and last sign-in; new people can be added and requests approved.", False),
    ("17_settings.png", "Settings: default seating rules", "The default rules used to pre-fill new plans: 8 or 4 neighbours, the roll-number gap (5), department mix, compact or balanced hall usage, and the number of accessible seats per hall when a hall lists none (2).", False),
    ("18a_lookup.png", "Find my seat", "The public page where a candidate enters a candidate ID.", False),
    ("18_lookup_result.png", "Seat lookup result", "For candidate BMG24003 the page greets \"Julia M.\" (a shortened name), shows the sitting, the course, the hall, the seat A1 and a mini map of the hall with the seat marked, and offers the seat slip (PDF) and the QR code. No e-mail or date of birth is shown.", True),
    ("19_plan_dark.png", "Plan page in the dark theme", "The same plan page in the dark theme; light, dark and system themes are available everywhere.", False),
    ("20_attendance_halls.png", "My halls (invigilator)", "The invigilator sees the halls to supervise, grouped by sitting, with progress bars: EW-205 is in progress (57 present, 3 absent, 14 to mark) and the others have not started.", False),
    ("21_attendance_list.png", "Tablet attendance: list view", "Counters for present (57), absent (3) and to mark (14); a scan or type box; filters and search; a Present and an Absent button for every seat; and a bottom bar with *Mark remaining absent* and *Submit* (enabled only when everyone is marked).", True),
    ("22_attendance_map.png", "Tablet attendance: seat-map view", "The same register as a seat map: present candidates are green, absent red; tapping a seat cycles present, absent and cleared.", False),
    ("23_pdf_seating_chart.png", "Generated seating chart (PDF, hall EW-205)", "One landscape page per hall: the grid colour-coded by paper with roll numbers and course codes, the paper legend with counts, the invigilator, and a footer with the plan version, the seed and the seating fingerprint.", True),
    ("24_pdf_invigilator_sheet.png", "Generated invigilator sheet (PDF)", "Per hall: the papers and their candidate counts, instructions for the invigilator, and a seat-by-seat list with Present and Signature columns.", False),
    ("25_pdf_qr_slips.png", "Generated seat slips with QR codes (PDF)", "Six slips per page with name, roll number, course, time, hall, building, seat and a QR code that opens the candidate's lookup page.", False),
]


def screens_block(d, items):
    """Describe screens two at a time and show each pair side by side."""
    for i in range(0, len(items), 2):
        pair = items[i:i + 2]
        for fname, cap, desc, _ in pair:
            d.p(desc, size=11, line=1.15, keep_next=True, space_after=4)
        d.figure_pair([(SHOTS / fname, cap) for fname, cap, _, _ in pair])


def sec_screens(d, all_screens=False, width=None):
    d.h2("Output Screens")
    d.p("All screens below are real captures of the running application at 1440 x 900 with the sample dataset imported, three plans "
        "published and attendance marked for one hall. Nothing is mocked up. The same screens are described in the user guide.")
    screens_block(d, [s for s in SCREENS if s[3] or all_screens])


def sec_engine_results(d):
    d.h2("Engine Performance (Benchmark Results)")
    d.p("Because nothing is trained, the usual measures of a learned model (accuracy, precision, recall, F1, a confusion matrix) do "
        "not exist for SeatWise, and we do not report invented substitutes. The engine is evaluated by *benchmarking*: it is run on seeded "
        "synthetic sittings, every plan is validated independently, and the results are compared with the three ways in which seating "
        "is usually done. The run `engine-benchmark-20260921` took place on 21 September 2026 on a 12-thread Intel desktop with "
        "Windows 11, Python 3.11.9 and OR-Tools 9.15.6755. It covers 8 scenarios, 4 methods and 3 seeds (11, 12, 13), plus predictability "
        "over 6 seeds (21 to 26) and budget tuning on two scenarios.")
    d.table([
        ["Measure", "Meaning", "Target"],
        ["Same-paper neighbour pairs", "Neighbouring seats (8 around each seat) whose candidates write the same paper", "0"],
        ["Roll-gap violations", "Neighbours whose roll numbers (same prefix) are closer than the gap", "0"],
        ["Accessible seats missed", "Candidates needing an accessible seat who are not on one", "0"],
        ["Hard rules met", "Share of plans with all of the above at 0 and everyone seated", "100%"],
        ["Solve time", "Wall-clock seconds from request to a validated plan", "seconds"],
        ["Same-department pairs", "Neighbours from one department (a preference, minimised)", "low"],
        ["Roll-to-seat correlation", "Spearman correlation between roll order and seat order", "about 0"],
        ["Repeated neighbour pairs", "Share of neighbour pairs that recur when the plan is regenerated with another seed", "as low as random"],
        ["Front-row bias", "Largest gap between a department's share of front-row seats and its share of candidates", "small"],
    ], "Measures used in the benchmark", widths=[0.26, 0.58, 0.16], font=9.5)
    d.p("The three baselines are *sequential* (roll-number order, row by row, the classic spreadsheet plan), *round-robin* (papers interleaved in "
        "a repeating cycle, the usual improved manual plan) and *random shuffle* (a random permutation with no rules).")
    d.h3("Headline results")
    d.table([
        ["Result", "Value"],
        ["Plans meeting every hard rule (SeatWise)", "24 of 24 (100%); baselines: 0 of 72"],
        ["Same-paper neighbours, SeatWise", "0 in every run"],
        ["Same-paper neighbours, sequential seating (600 candidates)", "1,253"],
        ["Solve time, 600 candidates (mean)", "2.36 s"],
        ["Solve time, 2,000 candidates (mean)", "4.77 s"],
        ["Slowest SeatWise run in the benchmark", "6.14 s (4-neighbour mode)"],
        ["Roll-to-seat correlation", "0.065 (sequential 1.000)"],
        ["Neighbour pairs repeated with a new seed", "1.0% (sequential and round-robin 100%)"],
    ], "Headline benchmark results", widths=[0.58, 0.42], font=10)
    d.h3("SeatWise in every scenario")
    rows = [["Scenario", "Candidates", "Solve (s)", "Same-paper", "Roll-gap", "Accessible missed", "Same-dept pairs", "Halls", "Seats filled"]]
    for n, c, *_ in SCEN:
        s = BENCH[n]["SeatWise"]
        rows.append([n, f"{c:,}", f"{s[0]:.2f}", str(s[1]), str(s[2]), str(s[3]), str(s[4]), str(s[5]), f"{s[6]}%"])
    d.table(rows, "SeatWise results by scenario (mean of 3 seeds)", widths=[0.16, 0.11, 0.1, 0.11, 0.09, 0.13, 0.12, 0.07, 0.11], font=9,
            align=["l", "r", "r", "r", "r", "r", "r", "r", "r"])
    d.h3("Baselines in every scenario")
    rows = [["Scenario", "Same-paper: seq.", "round-robin", "random", "Roll-gap: seq.", "round-robin", "random", "Accessible missed (seq.)"]]
    for n, *_ in SCEN:
        b = BENCH[n]
        rows.append([n, f"{b['Sequential'][1]:,}", f"{b['Round-robin'][1]:,}", f"{b['Random shuffle'][1]:,}", f"{b['Sequential'][2]:,}", f"{b['Round-robin'][2]:,}",
                     f"{b['Random shuffle'][2]:,}", str(b["Sequential"][3])])
    d.table(rows, "Violations left by the baselines (mean of 3 seeds; every baseline run failed at least one hard rule)",
            widths=[0.16, 0.14, 0.12, 0.1, 0.14, 0.12, 0.1, 0.12], font=9, align=["l", "r", "r", "r", "r", "r", "r", "r"])
    d.p("The baselines fill halls in the order given, so they sometimes use one more hall than SeatWise's compact strategy. In the "
        "gap-0 scenario the baselines have no roll-gap violations because the rule is switched off, but they still leave same-paper "
        "neighbours and accessible-seat misses.")
    d.figure(EXP / "conflicts_by_method.png", "Same-paper neighbour pairs by method and sitting size", width=4.6)
    d.figure(CHARTS / "violation_matrix.png", "Violations left by each method at 600 candidates (the equivalent of a confusion matrix for an optimisation engine)", width=4.4)
    d.figure(EXP / "solve_time_by_size.png", "Solve time by sitting size", width=4.6)
    d.h3("Unpredictability and fairness")
    rows = [["Method", "Roll-to-seat correlation", "Repeated neighbour pairs", "Front-row bias (percentage points)"]]
    rows += [[m, f"{c:.3f}", r, f"{b:.1f}"] for m, c, r, b in UNPRED]
    d.table(rows, "Unpredictability of each method (600 candidates, 6 seeds)", widths=[0.28, 0.24, 0.24, 0.24], font=9.5, align=["l", "r", "r", "r"])
    d.p("SeatWise is as unpredictable as a pure random shuffle: neighbours almost never repeat, and roll order says nothing about the "
        "seat. Unlike the shuffle it keeps every rule. Its front-row bias is small but higher than a shuffle's, because a paper occupies "
        "one colour class per hall and only two of the four classes include the front row; which paper gets which class is itself "
        "random, so the bias shrinks as more plans are drawn.")
    d.figure(EXP / "roll_seat_correlation.png", "Roll-to-seat correlation by method", width=4.0)
    d.figure(EXP / "neighbour_overlap.png", "Neighbour pairs repeated across seeds", width=4.0)
    d.figure(EXP / "department_mix_by_method.png", "Department mix by method", width=4.0)
    d.figure(EXP / "hall_utilisation.png", "Hall utilisation by method", width=4.0)
    d.h3("Observations")
    d.bullets([
        "**Correctness is structural.** Stage A confines each paper to one colour class per hall, and seats of one class are never neighbours, "
        "so same-paper neighbours are impossible before Stage B starts. This is why no run has any.",
        "**Four-neighbour adjacency is slower** (6.0 s against 2.4 s for 600 candidates) because its two classes each cover half the hall, "
        "so Stage B has twice as many seat choices per candidate; it also gives far fewer same-department neighbours (12 against 109).",
        "**Scaling is close to linear** in the number of halls: halls are solved in parallel and most of the time goes to the deterministic per-hall budget.",
        "**Reproducibility.** Re-running with the stored seed reproduces the plan exactly; the Verify action and the test suite both check this.",
        "**Department mix** is a preference, not a rule: SeatWise leaves 109 same-department pairs at 600 candidates against 1,648 for sequential seating.",
    ])


def sec_product_results(d):
    d.h2("Product Measurements")
    d.p("The product was also measured through its own interface and API on 15 October 2026. Three sittings of the sample timetable were "
        "planned with random seeds, each solved in about two seconds, with no rule violated.")
    d.table([["Sitting", "Candidates", "Halls", "Same-paper pairs", "Conflicts avoided vs roll order", "Solve (s)"]] +
            [[n, str(c), str(h), "0", f"{a:,}", f"{t}"] for n, c, h, a, t in DEMO],
            "Plans generated in the demonstration scenario", widths=[0.3, 0.12, 0.08, 0.16, 0.22, 0.12], font=9.5, align=["l", "r", "r", "r", "r", "r"])
    d.p("For plan 1 the scorecard recorded 451 candidates in 6 halls with 92% of their seats filled, 0 same-paper neighbours, 0 roll-gap "
        "violations, no accessible seat missed and 1 same-department neighbour pair; the roll-order baseline for the same sitting had "
        "1,099 same-paper pairs, 342 roll-gap violations and 7 accessible-seat misses. Stage A took 1.15 s and Stage B 0.97 s of the 2.1 s. "
        "API response times are in Chapter 7.")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("**The comparison is qualitative, and the datasets differ.** The base paper [1] reports no accuracy, no timing and no dataset: its "
        "only quantitative statement is a requirement that a batch of 100 students be allocated in under 3 seconds. SeatWise has "
        "not been run on the base paper's data, and the base paper's system was not available to us to run on ours, so a numerical "
        "head-to-head is not possible. What we can do is compare the two on what they do, and compare SeatWise with the closest proxy "
        "for the base paper's method that we could measure, our round-robin baseline, which interleaves papers in a repeating cycle "
        "much as the zipper interleaves two subject lists. The round-robin baseline is not a re-implementation of the base paper.")
    d.table([
        ["Aspect", "Base paper [1]", "SeatWise"],
        ["Reported performance", "Target: 100 students in under 3 s; no measurement reported", "2.4 s at 600 candidates; 4.8 s at 2,000 (measured)"],
        ["Rules guaranteed", "Subject alternation in a line; optional branch rule; blocked seats", "No same-paper neighbours in 8 or 4 directions; roll gap; accessible seats; capacity"],
        ["Violations at 600 candidates (our benchmark)", "Not measured. Closest proxy, round-robin: 281 same-paper pairs, 198 roll-gap violations", "0 and 0 in every run"],
        ["Predictability", "Fixed pattern (the proxy repeats 100% of neighbour pairs)", "1.0% repeated pairs; correlation 0.065"],
        ["Reproducibility and audit", "Not described", "Seed, fingerprints, Verify, audit trail"],
        ["Live editing", "Future work (drag and drop)", "Implemented, with live rule checks"],
        ["Attendance", "Future work", "Implemented (tablet register, scan, lock)"],
        ["Tests", "Not described", "58 automated tests; benchmark"],
    ], "SeatWise compared with the base paper", widths=[0.24, 0.38, 0.38], font=9.5)
    d.p("In short: where the base paper stops at generating and displaying a seating pattern, SeatWise guarantees the rules, measures "
        "its own behaviour and covers the examination-day workflow. Whether those advantages matter to a real examination cell is "
        "something only a pilot can show.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.h3("Sample inputs")
    d.p("These are the first rows of the committed sample files.")
    d.table([["course_code", "course_name", "department_code", "department_name"],
             ["ACF-101", "Principles of Accounting", "ACF", "Accounting & Finance"],
             ["ACF-102", "Business Mathematics", "ACF", "Accounting & Finance"]], "courses.csv", widths=[0.2, 0.34, 0.2, 0.26], font=9)
    d.table([["roll_no", "full_name", "department_code", "course_codes", "needs_accessible_seat"],
             ["ACF24001", "Camila Kaur", "ACF", "ACF-201;ACF-202;ACF-203", "no"],
             ["ACF24002", "Gabriel Rao", "ACF", "ACF-201;ACF-202;ACF-204", "no"]], "candidates.csv (e-mail and date of birth columns omitted)", widths=[0.16, 0.2, 0.16, 0.32, 0.16], font=9)
    d.table([["hall_code", "hall_name", "building", "floor", "rows", "columns", "blocked_seats", "accessible_seats", "aisles"],
             ["MB-G01", "Main Hall A", "Main Building", "Ground", "10", "12", "E6;E7", "A1;A12", "4;8"],
             ["MB-101", "Room 101", "Main Building", "1", "8", "8", "", "", "4"]], "halls.csv", widths=[0.1, 0.14, 0.14, 0.07, 0.07, 0.09, 0.13, 0.15, 0.11], font=8.5)
    d.table([["session_date", "start_time", "end_time", "course_code", "paper_group"],
             ["2026-10-12", "09:30", "12:30", "ACF-101", ""], ["2026-10-12", "09:30", "12:30", "BMG-201", ""]], "timetable.csv", widths=[0.22, 0.18, 0.18, 0.22, 0.2], font=9)
    d.h3("Sample outputs")
    d.p("**Plan scorecard** (plan 1, seed 1192609794, engine 1.0.0, per-hall budget 0.15):")
    d.table([["Measure", "SeatWise plan", "Roll-order baseline for the same sitting"],
             ["Candidates seated", "451 in 6 halls (92% of their seats)", "451"],
             ["Same-paper neighbour pairs", "0", "1,099"],
             ["Roll-gap violations", "0", "342"],
             ["Accessible seats missed", "0", "7"],
             ["Same-department neighbour pairs", "1", "1,194"],
             ["Solve time", "2,118 ms (Stage A 1,151 ms, Stage B 965 ms, 1 attempt, 0 retries)", "-"]],
            "Scorecard of a generated plan", widths=[0.3, 0.4, 0.3], font=9.5)
    d.p("**Refused seat move.** *This move is not allowed: HCA25059 would sit next to HCA25037 (A2) - both write HCA-101.* (HTTP 409.)")
    d.p("**Public lookup response** (excerpt for BMG24003): the name is shortened to \"Julia M.\", and each published seat is returned with "
        "the sitting, the course (BMG-201, Marketing Management), the hall (MB-G01, Main Hall A, 10 rows by 12 columns, blocked seats E6 and E7, "
        "accessible seats A1 and A12, aisles after columns 4 and 8) and the seat (A1, row 0, column 0, accessible).")


def sec_success_failure(d):
    d.h2("Analysis of Successful and Failure Cases")
    d.h3("Successful cases")
    d.bullets([
        "Every one of 24 benchmark plans, in scenarios from 150 to 2,000 candidates, with 8 or 4 neighbours and roll gaps of 0, 5 and 10, met every hard rule.",
        "Three real sittings of the sample timetable were planned in 1.8 to 2.2 s each with no violation, and each plan reproduced exactly when verified.",
        "An illegal manual move was refused with a precise reason, and a legal move was applied, audited and re-fingerprinted.",
        "The end-to-end scenario (import, plan, export, lookup, attendance) passed in 11.4 s.",
    ])
    d.h3("Failure and boundary cases")
    d.table([
        ["Case", "What happened", "Assessment"],
        ["Two small halls for a 457-candidate sitting", "422: *457 candidates but only 72 usable seats in the selected halls. Select halls with at least 385 more seats.* The reply also named every paper larger than the halls' per-paper ceiling (for example 73 candidates but at most 18)", "Correct refusal with an actionable reason; no plan was stored"],
        ["Five large halls with too few seats", "422: *457 candidates but only 424 usable seats. Select halls with at least 33 more seats.*", "Correct; the pre-check catches it before any solving"],
        ["Import file with errors", "Status *failed* with four row-level errors (duplicate roll number, unknown department, unknown course, invalid yes or no)", "Correct; nothing was imported"],
        ["Front-row bias", "SeatWise places departments on the front row less evenly than a random shuffle (4.7 against 1.6 percentage points)", "A real weakness of the colour-class construction; documented"],
        ["Four-neighbour mode", "Solve time 6.0 s against 2.4 s for 600 candidates; the slowest benchmark run was 6.14 s", "Acceptable for interactive use, but the slowest mode"],
        ["Tight budget", "A per-hall budget of 0.1 was slower overall (3.72 s) than 0.15 (2.63 s) because some halls were re-solved", "Handled by the retry strategy; the tuned budget avoids it"],
    ], "Failure and boundary cases", widths=[0.24, 0.5, 0.26], font=9)


def sec_results_limits(d):
    d.h2("Discussion of Limitations")
    d.bullets([
        "**Synthetic data.** Every number in this chapter comes from seeded synthetic sittings; real institutions' data may differ in paper sizes, hall shapes and roll-number formats.",
        "**One machine, one run.** The benchmark ran once on one desktop with three seeds per scenario. We did not study variation between machines, and we did not measure memory or concurrent use.",
        "**No user study.** The usability of the seat map, the attendance screen and the lookup page was not tested with real users.",
        "**No accuracy-style metrics.** Because nothing is trained, accuracy, F1 and confusion matrices do not exist; the benchmark measures rule violations and speed instead.",
        "**Base-paper comparison is qualitative.** The base paper reports no measurements; the round-robin baseline is a proxy, not a re-implementation.",
        "**Front-row bias and 4-neighbour speed** are known weaknesses, described above.",
    ])


def sec_objectives(d):
    d.h2("Objectives versus Outcomes")
    d.table([
        ["Objective", "Outcome", "Evidence", "Status"],
        ["1  Automate seat allocation from uploaded data", "Four file kinds imported and validated; plans generated in seconds", "1,020 rows imported; 2.4 s at 600 candidates", "Met"],
        ["2  Satisfy capacity, subject and roll-number constraints with optimisation", "CP-SAT engine; every hard rule met", "24 of 24 benchmark plans; 3 of 3 demo plans", "Met on synthetic data"],
        ["3  Enforce anti-cheating spacing and randomise", "0 same-paper neighbours; seeded random choice", "Correlation 0.065; 1.0% repeated pairs", "Met, with a front-row bias of 4.7 points"],
        ["4  Exportable charts and hall-wise reports", "Five exports", "Charts, sheets, slips (PDF); hall lists, attendance (Excel); tests", "Met"],
        ["5  Real-time seat lookup and attendance", "Public lookup with QR slip; tablet register with lock", "Scenario and tests; screens captured", "Met in testing; no real-user trial"],
        ["6  Reduce time and errors of manual preparation", "Plan in seconds; rules guaranteed", "2.4 s; roll-order seating leaves 1,253 violations", "Met for generation time and rule errors; time saved in a real cell not measured"],
        ["Added: reproducible and auditable plans", "Seeds, three hashes, Verify, audit trail", "Verify reproduced exactly; tests", "Met"],
        ["Added: evaluate against manual methods", "Benchmark with three baselines", "8 scenarios x 3 seeds", "Met, with the limits above"],
    ], "Objectives against outcomes", widths=[0.26, 0.26, 0.28, 0.2], font=9)
