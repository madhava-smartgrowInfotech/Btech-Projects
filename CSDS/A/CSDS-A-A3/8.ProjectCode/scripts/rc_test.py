"""Chapter 7 sections (System Testing)."""
from __future__ import annotations

from doc_common import CHARTS, LAT, R, T, p


def _c(cat):
    return T["by_category"][cat]


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.p("Testing combines three sets of automated checks, all run on 15 October 2026 with no failures, and a manual walkthrough of the interface. "
        "The checks use a throw-away SQLite database and never retrain, so the shipped data and models are untouched.")
    d.table([["Suite", "Run with", "Size", "Result"],
             ["Original unit and web tests", "python tests.py", "3 test functions (features, threat intelligence, web app and API)", "All passed"],
             ["End-to-end API smoke test", "python scripts/smoke_test.py", "20 checks over the API used by the React interface", "All passed"],
             ["Extended suite (added for this report)", "python scripts/extra_tests.py", f"{T['total']} checks in six categories", f"{T['passed']} of {T['total']} passed"],
             ["Interface walkthrough", "Playwright with Chrome", "24 captured screens, batch, report, sync and retrain flows", "Completed; screens in Chapter 8"]],
            "Test suites", widths=[0.26, 0.24, 0.32, 0.18], font=9.5)
    d.p(f"In total {3 + 20 + T['total']} automated checks were executed. The extended suite is organised by category, shown below.")
    d.figure(CHARTS / "tests_by_category.png", "Extended test suite: checks passed by category", width=4.6)


def sec_unit(d):
    d.h2("Unit Testing")
    d.p(f"{_c('unit')['total']} unit checks cover the feature extractor and the consensus rule.")
    d.table([["Area", "Checks", "Examples"],
             ["Feature extraction", "18", "47 features in a fixed order; suspicious TLD; brand outside the domain; IP host (dotted and hexadecimal); '@' symbol; URL shortener; executable extension; popular domain; two-level suffix split (co.uk); entropy of 'aaaa' is 0 and of 'ab' is 1 bit; normalisation; red flags for a bad URL and none for a plain reputable one"],
             ["Consensus", "5", "First report stays pending; second confirms phishing; an opposing vote returns to pending; a trusted feed confirms at once; two safe votes confirm legitimate"]],
            "Unit tests", widths=[0.2, 0.1, 0.7], font=9.5)


def sec_integration(d):
    d.h2("Integration Testing")
    d.p(f"{_c('integration')['total']} integration checks exercise the Detector together with the threat-intelligence store and the model.")
    d.table([["Check", "Outcome"],
             ["Obvious phishing URL decided by the model", "phishing, p = 0.9989"],
             ["Reputable URL", "safe, p = 0.0207"],
             ["Two community reports on a URL the model rates safe", "verdict becomes phishing, decided by the community"],
             ["Two safe reports on a URL the model flags", "verdict becomes safe, decided by the community"],
             ["A confirmed host covers its other pages", "another page on the host is phishing, decided by the community"],
             ["One pending phishing report", "the score rises (0.9188 to 1.0 in the test)"],
             ["training_examples after confirmations", "contains the confirmed URLs with labels 0 or 1"],
             ["mark_trained", "clears the awaiting-training count"]],
            "Integration checks", widths=[0.55, 0.45], font=9.5)


def sec_functional(d):
    d.h2("Functional Testing")
    d.p(f"{_c('functional')['total']} functional checks run the HTTP API and the original pages through Flask's test client.")
    d.table([["Function", "Check"],
             ["GET /api/health", "reports a ready model"],
             ["GET /api/check", "returns verdict, probability, decided_by, reason, red_flags, features (47 entries) and model"],
             ["POST /api/report", "returns the vote counts and status"],
             ["GET /api/stats, /api/config, /api/checks", "return the documented structures"],
             ["GET /api/intel?status=, /api/intel/lookup", "filter by status; return the report history of a URL (2 reports)"],
             ["Pages /, /report, /community, /models", "all render with HTTP 200"],
             ["Form POST on /", "shows a verdict"]],
            "Functional checks", widths=[0.4, 0.6], font=9.5)
    d.p("The interface was walked through by script: single check, batch check of 10 URLs, report form, threat-intelligence board and detail drawer, "
        "feed sync, retraining and the Models and Activity pages. Each flow worked and produced the screens shown in Chapter 8.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.p(f"{_c('security')['total']} security checks passed.")
    d.table([["Threat", "Test", "Result"],
             ["SQL injection", "URL `http://x.com/'; DROP TABLE reports; --` and a reporter name containing a DROP statement", "stored as data; tables intact"],
             ["Cross-site scripting", "A reported URL with a script tag; a reporter name with markup; a checked URL with a script tag", "escaped on /community and /; no raw tag in the page"],
             ["Cross-origin access", "Access-Control-Allow-Origin on API responses", "present as `*` (documented weakness)"],
             ["Session state", "Set-Cookie header", "none set"],
             ["Resource abuse", "A 100,000-character note in a report", "no crash"]],
            "Security checks", widths=[0.2, 0.52, 0.28], font=9.5)
    d.p("These are targeted checks, not a penetration test. Authentication, authorisation, rate limiting and abuse of the report channel were not "
        "tested because they do not exist in the application.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p(f"{_c('validation')['total']} validation checks passed. Invalid input is rejected with HTTP 400 and a JSON error; unusual but well-formed input is handled without error.")
    d.table([["Input", "Expected behaviour", "Result"],
             ["Empty, missing or whitespace-only URL", "HTTP 400", "Pass"],
             ["Unknown verdict in a report; empty URL in a report", "HTTP 400", "Pass"],
             ["Unknown status filter; lookup without a URL", "HTTP 400", "Pass"],
             ["Non-numeric limit", "default limit used", "Pass"],
             ["Bare domain; no scheme with path and query", "normalised and classified", "Pass (HTTP 200)"],
             ["Malformed port; unmatched bracket", "no exception", "Pass (HTTP 200)"],
             ["5,000-character URL; unicode host; percent-encoded traversal", "classified", "Pass (HTTP 200)"],
             ["javascript: and data: URLs", "classified as text, never executed", "Pass (HTTP 200)"]],
            "Validation and edge cases", widths=[0.4, 0.34, 0.26], font=9.5)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Timings were measured on the development machine (Intel Core i5-12500, 12 threads, 15.7 GB) with the Flask test client, so they exclude network "
        "latency and the browser.")
    d.table([["Measurement", "Result"],
             ["Feature extraction, one URL (2,000 URLs)", f"{LAT['feature_extraction_ms_per_url']:.3f} ms"],
             ["Feature extraction + model, one URL (500 URLs)", f"{LAT['single_url_score_ms']:.3f} ms"],
             ["Model scoring of 8,000 feature rows", f"{LAT['batch_scoring_ms_per_url']:.4f} ms per URL"],
             ["Featurising the 40,000-URL dataset", f"{R['dataset']['featurize_seconds_40k']} s"],
             [f"GET /api/check ({LAT['api_requests_timed']} requests, includes a log write)", f"mean {LAT['api_check_ms_mean']:.2f} ms, median {LAT['api_check_ms_median']:.2f} ms, p95 {LAT['api_check_ms_p95']:.2f} ms, max {LAT['api_check_ms_max']:.2f} ms"],
             ["Training all three models (32,000 rows)", "RF 12.2 s, XGBoost 2.7 s, LR 0.2 s"]],
            "Measured response times", widths=[0.5, 0.5], font=9.5)
    d.figure(CHARTS / "latency.png", "Measured response times", width=4.6)
    d.p(f"The base paper reports about 0.20 ms per URL for its model; the single-URL figure here ({LAT['single_url_score_ms']:.2f} ms) includes feature extraction and a Python call "
        "per URL, so the two numbers measure different things and are not compared as a result.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user-acceptance test was carried out. The interface was exercised by the developers only, and no feedback from real analysts or reporters "
        "was collected. This is the most important missing piece of evidence for the claim that the system is easy to use, and it is listed as future work.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets(["All tests run on one Windows machine with one browser (Chrome); other systems and browsers were not tested.",
               "There are no unit tests for the React frontend; it is checked by a production build and by scripted walkthroughs.",
               "There is no load or concurrency test; the behaviour under many simultaneous users, or during a retrain, is not measured.",
               "Model quality was measured on a held-out part of the same dataset and by cross-validation, not on live URLs collected after training.",
               "The security tests are targeted checks; there was no independent security review.",
               "The retraining experiment used random in-distribution URLs; it cannot show how well the loop adapts to a new campaign."])
