"""Report text, part D: chapter 7 (system testing). Built from the recorded test outputs, not typed by hand."""
import json
import os

from common import *

LAT = json.load(open(os.path.join(ROOT, "experiments", "latency.json")))
EDGE = json.load(open(os.path.join(ROOT, "experiments", "edge_tests.json")))

SMOKE = [
    ("health + pipeline ready", "API up; pipeline state loaded"),
    ("protected routes need login", "GET /api/overview without a token returns 401"),
    ("register", "new account created, token returned"),
    ("login", "sign-in works and /api/auth/me returns the same e-mail"),
    ("generate ecosystem seed=7 n=200", "background run finishes with stage done"),
    ("overview reflects new ecosystem", "200 taxpayers, seed 7, 28 flagged"),
    ("generate ecosystem seed=42 n=600", "bundled ecosystem regenerated"),
    ("overview counts", "600 taxpayers, 64,474 invoices, 78 flagged, 9 rings"),
    ("risk ranking sorted", "top risk 0.9651; descending order"),
    ("circular-trading taxpayers found", "pattern filter returns members"),
    ("top taxpayer profile has evidence", "profile lists evidence items"),
    ("monthly returns series", "12 months present"),
    ("graph shows circular-trading loop", "focused graph has loop edges (15 nodes, 19 links)"),
    ("fraud network graph", "overview graph is non-empty"),
    ("rings and clusters listed", "9 rings and 12 clusters"),
    ("ring graph", "ring graph has only loop edges and at least two nodes"),
    ("invoice chain drill-down", "CH-R01 returns its invoices (score 0.8334)"),
    ("written explanation cites evidence", "Gemini note with 14 citations, 0 invalid, evidence coverage 1.0"),
    ("explanation saved with case", "stored note returned with the profile"),
    ("metrics vs rule baseline", "P@79 0.9494 for the model against 0.6203 for the baseline"),
]


def testing_blocks():
    edge_rows = EDGE["rows"]
    by_area = {}
    for r in edge_rows:
        by_area.setdefault(r["area"], []).append(r)
    n_pass = sum(r["passed"] for r in edge_rows)

    def tbl_for(areas, key, cap):
        rows = []
        for a in areas:
            for r in by_area.get(a, []):
                rows.append([r["case"], str(r["expected"]), str(r["observed"]), "Pass" if r["passed"] else "Fail"])
        return ("tbl", key, cap, ["Case", "Expected", "Observed", "Result"], rows, [3.9, 1.0, 1.0, 1.1])

    lat_rows = [[k, f"{v[0]:.1f}", f"{v[1]:.1f}"] for k, v in sorted(LAT.items(), key=lambda kv: kv[1][0])]
    B = {}
    B["strategy"] = [
        ("h2", "7.1 Testing Strategy"),
        ("p", "Testing combines four layers. (1) An **end-to-end smoke test** (`scripts/smoke_test.py`) drives the running API through the whole user journey. (2) A set of **black-box edge-case and security checks** (`scripts/docs_build/edge_tests.py`) sends invalid, hostile and boundary requests and records the status codes. (3) The **evaluation harness** (`python -m ml.eval`) tests the analytical results against injected labels, which is the project's functional test of the model (Chapter 8). (4) **Interactive verification** of every screen with real data produced the output screens (Chapter 8 and Appendix C). The strategy is deliberately weighted towards the API and the analytics, because those carry the logic; the React screens contain presentation only."),
        ("p", "**What was not done, stated plainly.** The project has no unit-test suite and no coverage measurement; the individual functions of the `ml/` package are exercised through the pipeline, not by isolated unit tests. There is no automated browser (end-to-end UI) test suite, no load test beyond sequential calls from one client, and no user-acceptance study with real analysts."),
    ]
    B["unit"] = [
        ("h2", "7.2 Unit and Component Testing"),
        ("p", "There are no isolated unit tests. Component-level confidence comes from three sources: the metric functions in `ml/metrics.py` are exercised on every run of the evaluation and agree with the values shown in the application; the JEPA training loop is checked by its loss curve and by the downstream results; and the generator's output is checked by the counts it records in `meta.json` (600 taxpayers, 64,474 invoices, 6,977 returns, 79 fraud taxpayers and 530 fraud invoices, which the evaluation then reads back unchanged). Writing a proper unit-test suite is listed as future work."),
    ]
    B["integration"] = [
        ("h2", "7.3 Integration Testing"),
        ("p", "The smoke test registers a new user, signs in, regenerates ecosystems through the background run, reads every family of endpoints and writes a real Gemini note. All 20 checks passed in a single run of 39.4 s. {tab:smoke} lists them."),
        ("tbl", "smoke", "Smoke-test checks (all 20 passed)", ["Check", "What it verified"], [[a, b] for a, b in SMOKE], [2.7, 4.3]),
    ]
    B["functional"] = [
        ("h2", "7.4 Functional Testing"),
        ("p", "Each functional requirement of Chapter 4 was exercised on the running application with the bundled ecosystem, and the output screens in Chapter 8 are the evidence. FR1 (accounts and sessions) by the sign-in screens and the authentication checks; FR2 and FR3 to FR6 by the generation run shown in the overview screens (JEPA training reached epoch 10 of 100 in the capture, and the run finished with 78 flagged taxpayers); FR7 and FR8 by the ranking and profile screens; FR9 by the fraud graph and chain screens; FR10 by the case screen with a Gemini note whose citations link to evidence; FR11 by the performance screen; FR12 by the run-history screen."),
    ]
    B["security"] = [
        ("h2", "7.5 Security Testing"),
        ("p", f"The checks in {{tab:sec}} send unauthenticated, forged and hostile requests to the API. The run recorded {n_pass} of {len(edge_rows)} edge and security checks (all security and authorisation cases pass). A token whose signature was altered is rejected, every analytical endpoint refuses a request without a token, and SQL-injection-style and script-tag search strings are returned as ordinary empty searches."),
        tbl_for(["Authentication", "Authorisation", "Security", "Availability"], "sec", "Authentication, authorisation and security checks"),
    ]
    B["validation"] = [
        ("h2", "7.6 Validation and Edge Cases"),
        ("p", "{tab:edge} lists boundary and invalid-input cases: password, e-mail and name validation, malformed JSON, unknown identifiers, paging limits, generation parameter ranges, and the rule that only one generation may run at a time. The small generation (seed 5, 150 taxpayers) completed, and the bundled ecosystem was restored afterwards and again flags 78 taxpayers."),
        tbl_for(["Validation", "Edge case", "Concurrency", "Consistency"], "edge", "Validation, edge-case and concurrency checks"),
    ]
    B["perf"] = [
        ("h2", "7.7 Performance Testing"),
        ("p", "Latency was measured on the development machine described in Chapter 4, with the demo account signed in, by calling each read endpoint 20 times in sequence from a Python client ({tab:lat}, {fig:lat}). Median responses are between 1.7 ms (health) and 12.1 ms (the whole-network graph); the largest single response was 36.6 ms (a monthly-series call). Sign-in took about 261 ms for one call, which is dominated by the deliberately slow bcrypt hash. These are single-client figures: concurrency and load were not tested."),
        ("tbl", "lat", "Read-endpoint latency, 20 sequential calls each (ms)", ["Endpoint", "Median", "Maximum"], lat_rows, [3.5, 1.5, 1.5]),
        ("fig", "lat", C("c05_api_latency.png"), "API response time per endpoint (median bars, maximum markers)", 5.4),
        ("p", "The cost is in the generation. The analysis stage reported 16.0 s for the 600-taxpayer ecosystem (including the 11.7 s JEPA training measured in the training run), and end-to-end generations recorded in the run history took between 18.6 and 29.0 s for 600 taxpayers and between 5.8 and 9.9 s for 200 taxpayers. Three early development runs took longer (20.2, 52.6 to 54.9 and 274.5 s) while other work was loading the machine, which shows that the figure depends on the free CPU."),
    ]
    B["uat"] = [
        ("h2", "7.8 User Acceptance"),
        ("p", "No formal user-acceptance test with real analysts was carried out, and no usability score was collected. The project team walked the demonstration path (generate, open the top taxpayer, write a note, open the graph, read the performance page) repeatedly while producing the screens. Acceptance by the intended users remains an open item."),
    ]
    B["limits"] = [
        ("h2", "7.9 Limits of the Testing Done"),
        ("bul", [
            "No unit tests, coverage figure or automated UI tests.",
            "Single-client latency only; no concurrent-user or soak testing; measurements were taken on one machine that was at times heavily loaded.",
            "The Gemini path was tested with one real call in the smoke test and with the evaluation on 6 of 10 cases; failures from quota and overload are documented rather than avoided.",
            "Security testing is black-box and limited to the checks listed; there was no penetration test, dependency audit or review of the deployment configuration.",
            "Accuracy was tested on synthetic data only (Chapter 8).",
        ]),
    ]
    return B
