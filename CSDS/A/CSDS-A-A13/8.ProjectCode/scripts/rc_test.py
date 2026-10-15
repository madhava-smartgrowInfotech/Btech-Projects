"""Chapter 7 content: system testing."""
from __future__ import annotations

from doc_common import CHARTS, DEMO, LATENCY, TESTS


def sec_test_strategy(d):
    d.h2("Test Strategy")
    d.paras(
        "SeatWise is checked at four levels, from the smallest unit to the whole installation. The levels are complementary: the first "
        "proves that each rule behaves as specified, the second that the pieces work together through the real API, the third that a "
        "complete examination scenario succeeds on a running installation, and the fourth that the engine meets its targets at scale.")
    d.table([
        ["Level", "Tool", "What it checks", "Result"],
        ["1  Backend tests", "pytest with a throw-away SQLite database", "Engine rules, importer, plans, exports, attendance, public lookup, analytics, authentication", "58 passed, 0 failed"],
        ["2  Front end", "TypeScript strict type check and production build; walkthrough in Chrome", "No type errors; the application builds; every screen was captured with real data", "No errors; screens captured (Chapter 8)"],
        ["3  Scripted scenario", "`scripts/demo_scenario.py` against a running server", "Import, three plans, illegal swap, downloads, lookup, attendance", "Passed in 11.4 s"],
        ["4  Engine benchmark", "`python -m ml.benchmark`", "8 scenarios, 3 seeds, 3 baselines; predictability; tuning", "24 of 24 plans met every hard rule"],
    ], "Test levels", widths=[0.16, 0.26, 0.38, 0.2], font=9)
    d.p("The backend tests use a throw-away SQLite database (see `tests/conftest.py`), so developer data is never touched, and they "
        "import the committed sample workbook through the real API. The results quoted in this chapter were obtained on 15 October 2026 "
        "by re-running the tests and the scenario on the delivered code.")
    d.figure(CHARTS / "tests_by_module.png", "Backend tests by module", width=5.3)


def sec_unit(d):
    d.h2("Unit Tests")
    d.p("The engine tests (14) exercise the smallest units and the rules they implement, without a database.")
    d.table([
        ["Unit under test", "Checks"],
        ["Seat labels", "Labels round-trip, including multi-letter rows (A1 ... AA1)"],
        ["Seat graph", "Neighbours respect aisles and blocked seats; colour classes never touch, for 4 and 8 neighbours"],
        ["Roll numbers", "Parsing into prefix and number; the gap rule; a custom gap is honoured"],
        ["Engine", "Every hard rule is met; the same seed reproduces the plan; different seeds give different plans; 4-neighbour and balanced fill work; compact uses fewer halls"],
        ["Pre-checks", "Impossible inputs are explained: too few seats, a paper larger than the ceiling, too few accessible seats"],
        ["Validator", "Catches every kind of violation it is designed to catch"],
        ["Baselines", "Roll-order seating creates conflicts that the engine avoids"],
    ], "Unit-level checks (test_engine.py)", widths=[0.24, 0.76], font=9.5)


def sec_integration(d):
    d.h2("Integration Tests")
    d.p("The remaining tests call the real API through FastAPI's test client with the sample workbook imported, so they cover routers, "
        "services, database and file generation together.")
    d.table([["Test file", "Tests", "What is covered"]] + [
        ["test_auth.py", "8", "Health; sign-in and /me; wrong password; protected routes need a token; registration waits for approval, duplicates are refused, an administrator approves; invigilators cannot manage the team; the last administrator cannot be disabled; default rules and rule validation"],
        ["test_imports.py", "9", "Templates and samples download; candidates without courses are refused; the sample workbook imports cleanly (908 candidates, 49 courses, 14 halls, 6 sittings); re-import updates instead of duplicating and a batch cannot be applied twice; row-level errors with row numbers; hall layout errors; timetable clash and split paper group; unreadable files; invigilators cannot import"],
        ["test_plans.py", "6", "A generated plan meets every rule and avoids more than 500 conflicts, with invigilators assigned; same seed gives the same result and Verify confirms it; publishing archives the previous version and published plans cannot be deleted; hall map, illegal swap refused with a reason, legal swap applied and audited, fingerprints updated; invigilators see only their halls; an impossible request explains why and is audited"],
        ["test_exports.py", "7", "Seating charts, invigilator sheets and QR slips are valid PDFs with one chart page per hall; single-hall chart; hall-lists workbook with one sheet per hall and a complete roll-ordered door list; attendance workbook; invigilators cannot export everything"],
        ["test_attendance.py", "5", "My halls; marking and scanning (URL and lower-case roll number, already present); scanning a candidate of another hall says where they sit; submit needs everyone marked, locks the register and only administrators reopen; unassigned halls are forbidden"],
        ["test_public.py", "5", "Lookup shows published seats only, a shortened name and no private fields; unknown ID and unpublished plan; slip PDF and QR PNG; home-page benchmark summary; rate limiting (429)"],
        ["test_analytics.py", "4", "Overview figures match the plan; plan analytics add up; the benchmark and its charts are served and path tricks are refused; invigilators cannot see analytics"],
    ], "Integration tests", widths=[0.17, 0.08, 0.75], font=9, align=["l", "c", "l"])
    d.p("In total the suite has 8 + 14 + 9 + 6 + 7 + 5 + 5 + 4 = 58 tests. On 15 October 2026 all 58 passed; the slowest test (the same seed "
        "giving the same plan, with Verify) takes 7.1 s.")


def sec_functional(d):
    d.h2("Functional Testing: the Scripted Scenario")
    d.p("The scenario script performs the definition-of-done flow through the API of a running installation and stops at the first "
        "failure. It was run on 15 October 2026 against an empty database.")
    d.table([
        ["Step", "Action", "Result"],
        ["1", "Import the sample workbook", "Validation passed: 1,020 rows, 10 warnings; imported 908 candidates, 49 courses, 14 halls, 6 sittings"],
        ["2", "Generate and publish plans for three sittings"] + [
            "; ".join(f"{n}: {c} candidates in {h} halls, 0 same-paper neighbours, {a:,} avoided, {t} s" for n, c, h, a, t in DEMO)],
        ["3", "Try an illegal swap (A1 to A2)", "Blocked: the candidate would sit next to a neighbour who writes the same course (reason shown)"],
        ["3", "Download outputs", "seating-charts.pdf 135 KB; invigilator-sheets.pdf 147 KB; qr-slips.pdf 1,666 KB; hall-lists.xlsx 47 KB; attendance.xlsx 28 KB"],
        ["4", "Seat lookup and QR slip", "BMG24064 (Zoe A.) sits in EW-205 seat A2; slip PDF of 64 KB downloaded"],
        ["4", "Attendance as an invigilator", "Two candidates marked present in EW-205 (2 present, 72 to mark)"],
        ["", "Whole scenario", "Passed in 11.4 s"],
    ], "Scripted scenario results", widths=[0.07, 0.3, 0.63], font=9)


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Security behaviour is covered by the authentication, public and analytics tests and by the scenario.")
    d.table([
        ["Check", "Observed"],
        ["Wrong password", "401 with a readable message; no token"],
        ["Protected routes without a token", "401"],
        ["Pending account sign-in", "403 explaining that approval is awaited"],
        ["Duplicate registration", "Refused"],
        ["Invigilator calling administrator endpoints (import, team, analytics, full exports)", "403"],
        ["Invigilator opening an unassigned hall", "403"],
        ["Demoting or disabling the last administrator", "409, refused"],
        ["Public lookup response", "Published seats only; shortened name; no e-mail or date of birth"],
        ["Public lookup flood", "429 after 30 requests in a minute from one client (observed during measurement on 15 October 2026)"],
        ["Path tricks on served chart files", "Refused"],
    ], "Security checks", widths=[0.5, 0.5], font=9.5)
    d.p("Not performed: a penetration test, a dependency vulnerability audit and HTTPS configuration. These are deployment tasks and are "
        "listed under future scope.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p("Edge cases were tested by the suite and by deliberate requests to the running system. Two of the latter are recorded here "
        "verbatim, because they show what a user sees.")
    d.table([
        ["Case", "System behaviour"],
        ["Too few seats", "422: *A plan could not be generated: 457 candidates but only 424 usable seats in the selected halls. Select halls with at least 33 more seats.*"],
        ["A paper larger than the ceiling", "422 with, for each paper, the number of candidates and the most that the halls can seat without neighbours writing it (for example 73 candidates but at most 18 in two small halls), advising more halls or 4-neighbour adjacency"],
        ["Bad import file (3 rows)", "Status *failed*: roll number appears more than once; unknown department XXX; unknown course code ACF-999; needs_accessible_seat must be yes or no, not 'maybe' - each with its row and column"],
        ["Illegal seat move", "409 with reasons such as *would sit next to ... both write ACF-101*"],
        ["Timetable clash", "Error: two papers of one sitting taken by the same candidates are named with the number of candidates affected"],
        ["Split paper group", "Error: courses sharing a paper must be in the same sitting"],
        ["Submitting an incomplete register", "409 while anyone is unmarked"],
        ["Deleting a published plan", "Refused"],
        ["Re-applying an import batch", "Refused; the batch is applied once"],
        ["Roll gap 0, 4-neighbour mode", "Benchmark scenarios m-600-gap0 and m-600-adj4 were solved with every hard rule met"],
        ["Seat label arithmetic", "Round-trips through A1 ... AA1"],
    ], "Edge cases and validation", widths=[0.26, 0.74], font=9)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Solve time was measured by the engine benchmark (Chapter 8). API latencies were measured on 15 October 2026 against the "
        "development server on the benchmark machine with the sample data loaded: thirty calls per endpoint after one warm-up (five for "
        "the file downloads and Verify, twenty for the public lookup, which is rate-limited to thirty requests a minute).")
    rows = [["Endpoint", "Median (ms)", "95th percentile (ms)"]] + [[n, f"{m:,.1f}" if m < 100 else f"{m:,.0f}", f"{p:,.1f}" if p < 100 else f"{p:,.0f}"] for n, m, p in LATENCY]
    d.table(rows, "API response times", widths=[0.5, 0.22, 0.28], font=9.5, align=["l", "r", "r"])
    d.figure(CHARTS / "api_latency.png", "API response times on a logarithmic scale", width=5.6)
    d.p("Interactive endpoints answer in 2 to 11 ms. File generation is slower, as expected: the QR-slip PDF (76 pages for the first "
        "plan) takes 3.2 s, and Verify, which re-runs the engine, takes 2.2 s. Not measured: memory use, behaviour under many "
        "simultaneous users, and other hardware.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("**User-acceptance testing with real users was not carried out.** The interface was exercised by the team through the "
        "scripted scenario, automated tests and walkthroughs of the screens (recorded in the project's testing notes for desktop, tablet and "
        "phone widths and for the light and dark themes; for this report the screens were re-captured at 1440 x 900). This is a limitation: the team cannot yet say how examination staff or invigilators will find the product. "
        "Collecting that feedback, and piloting the system on a real anonymised sitting, is the first item of future work.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "All test data is synthetic; real examination data may contain cases that the generator does not.",
        "The front end has no automated component or end-to-end test suite; it is checked by a strict type check, a production build and manual walkthroughs.",
        "The benchmark was run once on one machine; variation between machines and between runs was not studied beyond three seeds.",
        "No load, memory, security-penetration or accessibility-audit tests were carried out.",
        "The 58 tests check behaviour that the team thought of; they cannot prove the absence of defects.",
    ])
