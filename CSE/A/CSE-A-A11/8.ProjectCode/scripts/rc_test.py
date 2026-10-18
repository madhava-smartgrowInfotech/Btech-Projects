"""Chapter 7 content: system testing."""
from __future__ import annotations

from doc_common import API, CHARTS, DEMO, EV, LAT, REP, RET, SMOKE_CHECKS, TESTS_API, TESTS_ENGINE, UI_FLOWS, f3


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        f"AutoSecAI was checked at five levels: automated engine and API tests ({TESTS_ENGINE + TESTS_API} tests), a scripted smoke test of the running API "
        f"({SMOKE_CHECKS} checks), a scripted walk through the real interface in a browser ({UI_FLOWS} flows), the production build of the web application, and "
        "measured studies of the analysis itself: a comparison of the rule engine with the learned model, a retrieval check of the codebase assistant and "
        "timing measurements. The levels answer different questions. The unit and API tests ask whether the code behaves as designed, deterministically and "
        "without a network. The smoke test asks whether a running server answers correctly end to end. The browser flows ask whether a person can use every "
        "feature and whether every state, including errors, is shown. The studies ask how good the analysis is.",
        "No test calls an external service: the language-model layer was never enabled, and GitHub was contacted only to confirm that an invalid link "
        "gives a readable error. The API tests use a temporary account database. All checks were run on 18 October 2026 on one Windows 11 machine "
        "(Intel Core i5-12500, 15.7 GB of memory, Python 3.11.9).")
    d.table([["Level", "Tool", "Count", "Result on 18 October 2026"],
             ["Unit and engine tests", "pytest, tests/test_core.py", str(TESTS_ENGINE), "passed"],
             ["API tests", "pytest and FastAPI TestClient, tests/test_api.py", str(TESTS_API), "passed (17 tests in about 10 s)"],
             ["API smoke test", "scripts/smoke_test.py against the running server", str(SMOKE_CHECKS), "16 of 16 passed"],
             ["Browser flows", "scripts/ui_flows.py, Playwright and Chrome", str(UI_FLOWS), "22 of 22 passed, no console errors"],
             ["Production build", "npm run build (TypeScript strict check, Vite bundle)", "1", "passed"],
             ["Layout check", "all screens at 360 and 768 px, light and dark", "4 views per screen", "no horizontal overflow"]],
            "Test levels and results", widths=[0.2, 0.36, 0.14, 0.3], font=9.5)


def sec_unit(d):
    d.h2("Unit Testing")
    d.p(f"The file `tests/test_core.py` holds {TESTS_ENGINE} tests of the engine, one for each property that must never regress. They use no mocks: the "
        "analyser, the metric extractor, the diff parser and the trained model are the real ones.")
    d.table([["No.", "Test", "What it checks"],
             ["1", "test_sqli_detected_and_safe_not", "A string-built SQL call is reported as SQL injection; the parameterised form is not"],
             ["2", "test_taint_from_request", "A value read from a request and concatenated into a shell command is reported as command injection"],
             ["3", "test_sanitizer_stops_taint", "Converting the value with `int()` before use removes the command-injection finding"],
             ["4", "test_autofix_parametrises_and_reparses", "The generated fix parses as valid Python, contains a placeholder and the finding disappears when the fixed code is analysed again"],
             ["5", "test_metrics_cyclomatic", "A function with one `if` and one `for` has cyclomatic complexity 3 and nesting depth 2"],
             ["6", "test_diff_parsing_and_review", "The demo diff is parsed, the review verdict is BLOCK and at least one patch is verified"],
             ["7", "test_before_after_marks_preexisting", "In a before/after comparison, a newly added `eval` is marked as inside the change"],
             ["8", "test_ml_scores_vulnerable_higher", "The model gives a vulnerable-looking function a higher probability than a trivial one"],
             ["9", "test_smote_tomek_balances", "After SMOTE and Tomek links a 200 : 20 imbalance is reduced to a difference of fewer than 30 samples"],
             ["10", "test_codebase_finds_auth", "In the demo repository, 'where is authentication implemented?' ranks `app/auth.py` first, and the `/auth/login` route is found"]],
            "Engine tests", widths=[0.06, 0.34, 0.6], font=9.5)
    d.p("Test 3 is the important negative case: a rule engine that reported every dangerous call regardless of data flow would flood reviewers with "
        "false alarms. Test 4 enforces the promise that a suggested fix is valid Python and removes its finding.")


def sec_integration(d):
    d.h2("Integration Testing")
    d.p(f"The file `tests/test_api.py` holds {TESTS_API} tests that run the whole stack from the HTTP layer down to the engine and the database, using FastAPI's "
        "test client. A fresh temporary account database is created for each run.")
    d.table([["No.", "Test", "What it checks"],
             ["1", "test_protected_routes_need_a_token", "Listing reviews without a token and with an invalid token both answer 401"],
             ["2", "test_demo_account_signs_in_and_bad_password_does_not", "The seeded demo account can sign in; a wrong password answers 401"],
             ["3", "test_register_validates_and_rejects_duplicates", "A valid registration answers 201; the same e-mail again 409; a malformed e-mail 422; a short password 422"],
             ["4", "test_demo_review_blocks_and_is_saved", "A demo review runs as a job, finishes with the verdict BLOCK, contains seven trace entries and a SQL-injection finding, exports valid SARIF 2.1.0, and can be deleted (then 404)"],
             ["5", "test_review_input_is_validated", "An empty diff, text that is not a diff and a missing folder each answer 422"],
             ["6", "test_codebase_index_and_ask", "The demo repository is indexed, the graph is not empty and a question returns hits"],
             ["7", "test_lab_analyze", "Pasted code with a string-built query yields a SQL-injection finding; code that does not parse answers 422"]],
            "API tests", widths=[0.06, 0.34, 0.6], font=9.5)
    d.h3("Smoke test of the running server")
    d.p(f"The script `scripts/smoke_test.py` sends real HTTP requests to the running API and passed all {SMOKE_CHECKS} checks: health; public statistics; the landing "
        "example and rule list; authentication required; bad login rejected; demo login and `/me`; registration and duplicate; metadata and samples; the demo "
        "diff review as a job; the compare-versions review; review input validation; a GitHub link that cannot be fetched produces a readable error; history "
        "and the four exports; deleting a review; codebase indexing and a question; and the Model Lab report and analysis.")
    d.p("The web application is checked by `npm run build`, which runs the TypeScript compiler in strict mode over all sources and then the Vite production "
        "build with route-level code splitting. The build completed without type errors.")


FLOWS = [
    ["1", "Protected route redirects to sign-in", "Opening the history while signed out leads to the sign-in page"],
    ["2", "Wrong password", "A readable error alert is shown"],
    ["3", "Registration", "A new account is created and the app opens with the user's name"],
    ["4", "Sign out", "Returns to sign-in and the app is blocked again"],
    ["5", "Demo review, filters, search", "Findings are counted, the search narrows them, an empty search shows the empty state, reset restores them, a card expands to show 'How to fix'"],
    ["6", "Exports", "Markdown, SARIF, JSON and CSV downloads each start and contain data"],
    ["7", "Compare two versions", "The SQL injection is found and a fixed file is offered"],
    ["8", "Typed diff and diff file upload", "Both inputs produce a review"],
    ["9", "Bad diff and bad GitHub link", "Readable errors are shown instead of a failure"],
    ["10", "File and zip upload", "A full scan runs on uploaded sources"],
    ["11", "Local folder", "A folder path is scanned"],
    ["12", "ML, Files and Agent trace tabs", "All tabs render real data"],
    ["13", "History", "Open, search, delete with confirmation and cancel with Escape"],
    ["14", "Codebase: demo repository", "Index, suggested question, typed question, map and onboarding guide"],
    ["15", "Codebase: this project, zip, bad folder", "The project indexes itself, a zip is indexed, a missing folder gives a readable error"],
    ["16", "Model Lab", "Every tab renders; 'Try it' analyses pasted code; retraining asks for confirmation first"],
    ["17", "Settings persistence", "Choices survive a reload and change the review options"],
    ["18", "Theme", "The chosen theme survives a reload"],
    ["19", "Keyboard", "A skip link appears on the first Tab, the focus ring is visible, and the mobile drawer closes with Escape"],
    ["20", "Reduced motion", "The landing page and the app render, and the pinned animated section falls back to a plain list"],
    ["21", "API unreachable", "Each page says what failed and offers a retry"],
    ["22", "Unknown route", "A friendly not-found page is shown"],
]


def sec_functional(d):
    d.h2("Functional Testing")
    d.p(f"Functional testing was automated with Playwright: a script drives a real Chrome browser through the application with the real API behind it and asserts "
        f"what the user sees. The {UI_FLOWS} flows below cover every input mode, every export, every state of the history, the codebase assistant, the Model Lab, "
        "the settings and the failure paths. All flows passed on 18 October 2026, and the browser console stayed free of errors during the run.")
    d.table([["No.", "Flow", "What is asserted"]] + FLOWS, "Browser flows of scripts/ui_flows.py", widths=[0.06, 0.32, 0.62], font=9)
    d.p("The twenty-six screen captures at 1440 by 900 pixels were taken with real data while the capture script also collected console errors, failed "
        "requests and 4xx or 5xx responses; none occurred.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Because AutoSecAI is itself a security tool, its own access control was tested with the same care as its analysis. The following behaviours are "
        "covered by automated checks.")
    d.table([["Behaviour", "Check", "Result"],
             ["Routes need a token", "Listing reviews without a token, and with a forged token (API test 1, smoke test)", "401"],
             ["Wrong password", "API test 2, smoke test and browser flow 2", "401 with a readable message"],
             ["Duplicate account", "API test 3 and smoke test", "409"],
             ["Invalid registration data", "Malformed e-mail, short password (API test 3)", "422"],
             ["Protected pages in the browser", "Browser flows 1 and 4: unauthenticated visits redirect to sign-in, also after sign-out", "redirect"],
             ["Hostile input to the analyser", "Pasted text that is not Python, not a diff, or a missing folder (API tests 5 and 7, flow 9, 15)", "422, no crash"],
             ["Sanitised rendering", "Finding text and Markdown are rendered through a sanitiser (code review of the components; flows 5 and 12 render the data)", "reviewed, not attacked"]],
            "Security checks", widths=[0.28, 0.5, 0.22], font=9.5)
    d.p("No penetration test, fuzzing campaign or dependency-vulnerability audit was performed. The known weaknesses of the design (a shared history, an "
        "unauthenticated demo-credentials endpoint, a development secret in the shipped settings, tokens in local storage, no rate limiting) are listed in the "
        "chapter on methodology and were not fixed, because the product is intended as a local tool.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p("Validation asks whether the analysis is right, not only whether the code runs. Three studies were run on the project's own data.")
    d.h3("Rule engine against the learned model")
    d.p("On the 1,500 held-out functions (125 vulnerable), the AST and taint analyser (security findings of medium severity or higher), the stored "
        f"{EV['best_model']} model, and their combinations were scored against the corpus labels.")
    rows = [["Detector", "Precision", "Recall", "F1", "TP", "FP", "FN"]]
    for name, k in (("Rule engine", "rule_engine"), (f"ML model ({EV['best_model']})", "ml_model"), ("Either detector flags (OR)", "combined_or"), ("Both flag (AND)", "combined_and")):
        e = EV[k]
        rows.append([name, f3(e["precision"]), f3(e["recall"]), f3(e["f1"]), str(e["tp"]), str(e["fp"]), str(e["fn"])])
    d.table(rows, "Rule engine and ML model on the same 1,500 functions", widths=[0.32, 0.12, 0.12, 0.12, 0.1, 0.1, 0.12], font=9.5, align=["l"] + ["c"] * 6)
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure(CHARTS / "engine_vs_ml.png", "Precision, recall and F1 of the two detectors and their combinations", width=5.0, max_h=3.0)
    d.p(f"The detectors are complementary. The rules are precise ({f3(EV['rule_engine']['precision'])}) but miss {EV['rule_engine']['fn']} of 125 vulnerable "
        f"functions; the model finds more (recall {f3(EV['ml_model']['recall'])}); flagging when either fires raises recall to {f3(EV['combined_or']['recall'])} and F1 to "
        f"{f3(EV['combined_or']['f1'])} at the price of {EV['combined_or']['fp']} instead of {EV['ml_model']['fp']} false alarms. The corpus caveat applies: generator and "
        "rules were written by the same team and about 1 % of the labels are wrong, so these figures describe the corpus, not real code.")
    d.h3("Codebase assistant on the demo repository")
    d.p(f"Twelve hand-written questions on the ten-file demo repository each name the file that should rank first. It ranked first for "
        f"{RET['top1']} of {RET['questions']} questions and within the first three files for {RET['top3']} of {RET['questions']}; indexing took "
        f"{RET['index_build_ms']} ms and an answer a median of {RET['ask_median_ms']} ms. The misses were questions that mix topics (orders and database, "
        "route decorator, front end), and looking up a user by name did not return the database module. This is a small check, not a benchmark.")
    rows = [["Question", "Expected file", "Ranked files (first three)", "Rank"]]
    for r in RET["rows"]:
        rows.append([r["question"], r["expected"], ", ".join(r["got"]), str(r["rank"]) if r["rank"] else "not found"])
    d.table(rows, "Retrieval check on the demo repository", widths=[0.4, 0.18, 0.32, 0.1], font=8.5)
    d.h3("Edge cases")
    d.p("The browser flows and API tests cover the following edge cases: an empty diff, text that is not a diff, a diff without files, a before/after pair where "
        "the issue was already present (reported as outside the change), a file that is not valid Python (reported by the Model Lab as 422), a missing folder, an "
        "invalid zip, an unreachable API, an unknown route, a GitHub link that cannot be fetched, a duplicate account and a deleted review. A whole-file "
        "fix is offered only when a full file was supplied, and the export tab says so when it is not.")


def sec_performance(d):
    d.h2("Performance Testing")
    d.p(f"Timings were measured on an otherwise idle machine. The engine-only review of the built-in demo pull request (one file, 67 added lines, seven functions) was "
        f"repeated {LAT['runs']} times after a warm-up run: the median was **{LAT['median_s']} s**, the mean {LAT['mean_s']} s, the 95th percentile {LAT['p95_s']} s and the range "
        f"{LAT['min_s']} to {LAT['max_s']} s. The review found {DEMO['findings']} issues and scored {DEMO['score']} of 100, with the verdict {DEMO['verdict']}; all seven generated patches were verified.")
    rows = [["Agent", "Median time (ms)"]] + [[k, f"{v * 1000:.1f}"] for k, v in LAT["per_agent_median_s"].items()]
    d.table(rows, "Median time per agent on the demo pull request", widths=[0.6, 0.4], font=10)
    d.p("The ML Risk agent dominates, because it scores each function with the stored model; the remediation agent, which re-runs the analyser for each patch, is "
        "second; the static analysis itself takes about 8 ms for the whole file.")
    if not getattr(d, "report", False):  # repeated in another chapter of the full report
        d.figure(CHARTS / "latency_agents.png", "Median time per agent", width=4.8, max_h=2.8)
    d.p("The table below gives the latency of the HTTP endpoints against the running API on localhost with a single client.")
    rows = [["Endpoint", "Runs", "Median (ms)", "95th percentile (ms)"]]
    for k, v in API.items():
        rows.append([k, str(v.get("n", "")), str(v.get("median_ms", v.get("ms", ""))), str(v.get("p95_ms", "-"))])
    d.table(rows, "HTTP latency measured on localhost", widths=[0.5, 0.1, 0.2, 0.2], font=9)
    d.p("Login takes about 60 ms because bcrypt is deliberately slow. A complete review through the job interface took a median of 435.5 ms including "
        f"the 50 ms polling of the test. Training the nine models takes about {REP['seconds']} s and the retraining job about 27 s through the API. "
        "Memory use, concurrent users and large repositories were not measured.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user study was carried out: no outside developer used AutoSecAI, so there are no usability scores or task times, and none are claimed. "
        "Instead the four developers walked through every screen with real data, exercised each input mode, and repeated the flows a new user meets "
        "first (demo sign-in, the one-click review, reading a finding, exporting, asking the codebase assistant, the Model Lab) until they worked without "
        "explanation. The twenty-two scripted browser flows encode that walk-through.")
    d.p("The acceptance criteria came from the project objectives: a change can be supplied in several ways, changed files and lines are identified, "
        "each finding is explained and located, a verified fix is offered where one can be generated, a verdict and report are produced, and a "
        "repository can be questioned. Each was met on the demo data. Whether the output helps developers on their own pull requests remains open.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.p("The tests establish that the system works as designed on the data used. They do not establish how well it performs on real software, and the following limits "
        "should be kept in mind when reading the results.")
    d.bullets([
        "**Synthetic evaluation data.** The model scores and the comparison of the rule engine with the model come from a generated corpus. They are not evidence of "
        "performance on real vulnerable code.",
        "**No real pull-request benchmark.** Objective six of the project asked for precision against manually reviewed pull requests. No labelled set of real "
        "pull requests was available, so this was not measured; the only demonstration is the built-in vulnerable pull request, which was written for the purpose.",
        "**No comparison with other tools.** The analyser was not compared with existing scanners such as Bandit, Semgrep or CodeQL.",
        "**GitHub was not exercised with a real pull request.** Only the error path of an invalid link was tested, because the tests avoid the network.",
        "**The language-model layer was never run.** No key was available, so the optional explanation and answer rewriting is untested and unmeasured.",
        "**Small retrieval check.** Twelve questions on a ten-file repository, written by the developers.",
        "**No load, concurrency or soak test.** Timings are for one client on one machine; memory use was not measured.",
        "**No usability study and no security audit** beyond the checks listed above.",
        "**One machine, one browser.** Everything ran on Windows 11 with Chrome; other browsers and systems were not tested, and the Streamlit interface was not run.",
    ])
