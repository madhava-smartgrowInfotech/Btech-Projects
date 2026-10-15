"""Chapter 7 sections: system testing."""
from __future__ import annotations

from doc_common import HW, LATENCY, M, OPT_LAT, P, SMOKE_CHECKS


def sec_strategy(d):
    d.h2("Testing Strategy")
    d.p("Testing had three layers: Python tests of the science and of the original web application (`tests.py`), an API smoke test of the FastAPI layer that the React "
        "application uses (`scripts/smoke_test.py`), and scripted browser walkthroughs of the finished application (Playwright driving Chrome) that also produced the screenshots. "
        "All of them were run on 15 October 2026 on the machine described below. The optimisation results themselves are the product of the experiments of Chapter 8, not of tests.")
    d.table([["Layer", "Tool", "What it checks", "Result"],
             ["Unit and module", "tests.py (4 functions)", "data schema and distances, forecast contract, optimisation constraints, Flask pages", "4 of 4 passed (32.7 s)"],
             ["API integration", "scripts/smoke_test.py (18 checks)", "every endpoint, validation, edge cases, exact versus matheuristic", "18 of 18 passed (20.9 s)"],
             ["Functional (browser)", "scripts/capture_screens.py", "7 routes, 3 planning runs through the form, comparison, scalability and rolling screens, dark mode, not-found page", "22 screens captured with real data"],
             ["Performance", "Python timer over HTTP", "latency of every read endpoint and the planning endpoint", "see Section 'Performance Testing'"],
             ["Acceptance", "-", "user acceptance by real planners", "not done"]],
            "Testing layers", widths=[0.18, 0.24, 0.38, 0.2], font=9.5)
    d.p(f"**Test machine.** {HW}.")


def sec_unit(d):
    d.h2("Unit and Module Tests")
    d.table([["Test function", "What it asserts"],
             ["test_data", "at least 30 regions and 24 months; required columns present; the distance matrix is square, has a zero diagonal and the first distance exceeds 100 km"],
             ["test_forecast", "a model exists (trained if missing); the next-month forecast covers every region and is positive; the forecast of October 2025 from earlier data is within 30% of the realised network total"],
             ["test_optimisation", "a 5-hub matheuristic plan opens at most 5 hubs and assigns every region to an open hub; planned fulfilment is at least 0.99 with no overloaded hub; the matheuristic objective is within 2% of the exact MIP; with a hard 30 h SLA every assignment is within 30 h"],
             ["test_webapp", "the five Flask pages return 200; POST /api/optimize returns a plan with at most 4 hubs on realised demand; /api/forecast returns a positive total"]],
            "Assertions of tests.py", widths=[0.2, 0.8], font=9.5)
    d.p("All four tests passed. Notably, the test of the matheuristic against the exact MIP requires agreement within 2%, which is consistent with the identical results "
        "found in the comparison experiment at 90 nodes.")


def sec_integration(d):
    d.h2("API Integration Tests")
    d.p("The smoke test runs against the FastAPI application in-process (it can also be pointed at running servers with `--url` and `--frontend`). It stops at the first failing check; "
        "all 18 passed.")
    d.table([["#", "Check", "Detail observed"]] + [[str(i), n, t] for i, (n, t) in enumerate(SMOKE_CHECKS, 1)],
            "The 18 smoke checks and what they observed", widths=[0.06, 0.4, 0.54], font=9)


def sec_functional(d):
    d.h2("Functional Testing")
    d.table([["Scenario", "Steps", "Expected", "Observed"],
             ["Browse every page", "Open /, /app, /app/forecast, /app/regions, /app/compare, /app/rolling and an unknown route", "Each loads with data from the API; unknown route shows the not-found page", "As expected (screens 1-7, 15-22)"],
             ["Plan a past month", "Plan hubs: Oct 2025, p = 6, matheuristic, defaults", "6 hubs, scored on realised demand", "Mumbai, Delhi, Kolkata, Hyderabad-W2, Bengaluru-SE, Ahmedabad-SE; INR 62.2 M; 92.3% fulfilment; 9.23 s"],
             ["Plan the next month", "Plan hubs: Jan 2026, p = 6", "Scored on the forecast, not realised demand", "As expected; label 'scored on the forecast'"],
             ["Compare with exact MIP", "Plan hubs: Oct 2025, p = 6, exact MIP", "Same cost if the matheuristic is optimal", "Same hubs and cost; status Optimal; 9.29 s"],
             ["View saved comparison", "Compare methods page", "Six methods with KPIs and charts", "As expected; values equal results/comparison.json"],
             ["View scalability", "Compare methods > Scalability", "Three instance sizes with times and status", "As expected; 270 nodes shows 'Not Solved' for the exact MIP"],
             ["View rolling horizon", "Re-optimise page", "Six months, adaptive vs static", "As expected; 98.3% vs 83.7%"],
             ["Dark theme", "Open the app with a dark operating-system preference", "Dark colours, readable charts", "As expected (screen 21)"]],
            "Functional scenarios", widths=[0.17, 0.3, 0.22, 0.31], font=9)
    d.p("Long jobs (re-running the comparison, the benchmark or the rolling horizon) were not re-run during the walkthrough to avoid overwriting the saved results; their "
        "start, polling and completion path is covered by the optional `--jobs` flag of the smoke test, which was not used in this run.")


def sec_security_tests(d):
    d.h2("Security Testing")
    d.p("Security testing was limited to input validation and configuration review. The API rejects out-of-range bodies with HTTP 422 and unknown months with HTTP 400, "
        "restricts CORS to the web port and stores no secrets. No authentication, authorisation, rate limiting or injection testing exists because the application has no "
        "users or database; no penetration test was performed. These are stated limitations, not passed tests.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.table([["Edge case", "Input", "Result"],
             ["Zero hubs", "n_hubs = 0", "HTTP 422: 'Input should be greater than or equal to 1' on field n_hubs"],
             ["Unknown month", "period = 1999-01", "HTTP 400: 'Unknown planning month 1999-01.'"],
             ["Hard SLA that cannot be met", "1 hub, SLA 5 h, hard, Dec 2025", "Answered cleanly with a valid JSON plan (reliability 0.1957), no crash"],
             ["Hard SLA 30 h", "8 hubs, SLA 30 h hard (tests.py)", "Every assignment within 30 h"],
             ["Exact MIP stopped by its time limit", "270-node scalability instance, time-limited exact MIP", "Status 'Not Solved' is reported (wall time 67.14 s including model construction); the incumbent objective INR 53.43 M is reported"],
             ["Capacity exceeded by realised demand", "Oct 2025 peak, forecast 13.2% low", "3 of 6 hubs overloaded; fulfilment 92.3%; reported rather than hidden"],
             ["Second background job", "POST /api/compare/run while one runs", "HTTP 409"],
             ["Missing model file", "models/rf_demand.joblib absent", "The API trains the model at start-up (same behaviour as the command line)"]],
            "Edge cases", widths=[0.28, 0.32, 0.4], font=9.5)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p(f"Timings were taken over HTTP on localhost with the servers running ({HW}); n is the number of calls, the median and range are in the table. The planning calls include "
        "forecasting, instance construction, the solve and the evaluation, so they are slower than the solver-only times stored in the result files (for example 4.89 s for the "
        "matheuristic in the saved comparison).")
    d.table([["Endpoint", "Median (ms)", "Range (ms)", "n"]] + [[a, str(b), c, str(n)] for a, b, c, n in LATENCY],
            "Latency of read endpoints", widths=[0.5, 0.17, 0.2, 0.13], font=10, align=["l", "r", "r", "r"])
    d.table([["Planning call", "Median", "Range", "n"]] + [list(map(str, r)) for r in OPT_LAT],
            "Latency of the planning endpoint", widths=[0.5, 0.17, 0.2, 0.13], font=10, align=["l", "r", "r", "r"])
    d.bullets([
        "Read endpoints answer in 2-30 ms; the forecast endpoint takes 0.26 s because it builds features for 90 regions.",
        "Planning takes about 3 s for four hubs and 11-12 s for six hubs. At 90 nodes the exact MIP (15.3 s) is slower than the matheuristic (12.2 s) end to end but not dramatically; in the UI runs the solver-only times were 9.23 s and 9.29 s.",
        "Run-to-run variation of several seconds comes from CBC and from sharing the processor with the browser; the saved comparison measured 4.89 s (matheuristic) and 7.99 s (exact) for the same instance.",
    ])


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("**User acceptance testing was not performed.** No real logistics planner has used the application. The walkthroughs above show that the screens work with real data; "
        "they do not show that the screens are understandable or useful to the intended users. A pilot with planners is the first item of future work.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "No automated tests of the React frontend; it was checked by walkthroughs and a production build only.",
        "No concurrent-user or load test, no memory profile and only one machine; timings will differ elsewhere.",
        "No cross-validation or repeated seeds for the forecaster, and no statistical tests; the 18 smoke checks and 4 unit tests verify behaviour, not accuracy.",
        "The experiments of Chapter 8 are single runs on one synthetic dataset; run-to-run solve times vary by several seconds.",
        "Security was reviewed, not attacked.",
        "No user acceptance study.",
    ])
