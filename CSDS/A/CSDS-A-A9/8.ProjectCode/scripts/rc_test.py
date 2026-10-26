"""Chapter 7 content: system testing (ForgetSafe). Every number is read from experiments/*/metrics.json; the tests described are the real ones
in tests/test_end_to_end.py and scripts/smoke_test.py, the probes in scripts/run_experiments.py (experiments/api, experiments/audit_tamper) and the
load, security and acceptance studies of scripts/run_testing_experiments.py (experiments/load_test, security_probe, acceptance)."""
from __future__ import annotations

from doc_common import CHARTS, metrics

_api = metrics("api")
_aud = metrics("audit_tamper")
_sc = metrics("scaling")
_base = metrics("baseline")
_seq = metrics("sequential")
_seeds = metrics("seeds")
_ld = metrics("load_test")
_sp = metrics("security_probe")
_ac = metrics("acceptance")


def _rep(d):
    return bool(getattr(d, "report", False))


def _lat(key):
    return _api["latency"][key]


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        "ForgetSafe has three layers that can fail independently: the numerical engine (`certified_unlearning/engine.py`, `model.py`), the hash-chained audit "
        "ledger (`audit.py`) and the HTTP surface (`web.py`) with the React interface on top of it. The testing follows the layers from the inside out. The engine and "
        "the ledger are covered by deterministic unit tests; the HTTP surface by an in-process server test and an end-to-end smoke script over TCP; the measurement suite "
        "`scripts/run_experiments.py` adds probes a test suite normally lacks (fresh-noise retraining, a noise sweep, tamper attacks, API edge cases, latency). Three further "
        "studies, all driven by synthetic inputs, test the properties that unit tests cannot: a load and concurrency test, 58 security probes, and 20 scripted synthetic-user "
        "acceptance journeys through the real interface (`scripts/run_testing_experiments.py`). The tests show that the *workflow and the bookkeeping* are correct and "
        "reproducible; what they say about forgetting in a larger model is the subject of the results chapter.")
    d.table([["Layer", "What is checked", "Instrument", "Where reported"],
             ["Engine and model", "training, unlearning, certificate fields, guards", "5 `unittest` cases; 14 smoke checks", "Unit and integration testing"],
             ["Audit ledger", "hash chain, tamper detection, export", "unit test; 8 tamper experiments", "Unit and security testing"],
             ["HTTP API", "routes, status codes, JSON errors, edge cases", "smoke script; 20 edge-case probes", "Integration and validation"],
             ["Security", "malformed requests, browser-facing hardening, ledger integrity", "58 probes against the live server", "Security testing"],
             ["Load and concurrency", "throughput and latency at 1 to 64 clients, races, 2,000-request soak", "threaded HTTP clients", "Performance testing"],
             ["User interface", "train, explore, unlearn, audit, dark mode, mobile", "20 scripted Playwright journeys", "User acceptance"],
             ["Performance", "latency per endpoint, unlearning against retraining, ledger growth", "timing probes on 127.0.0.1", "Performance testing"]],
            "Test layers and instruments", widths=[0.17, 0.37, 0.28, 0.18], font=9.5)
    d.p("All tests and probes ran on the development machine described in Chapter 6 (Intel Core i5-12500, 15.7 GB RAM, Windows 11, Python 3.11.9, no GPU), so every "
        "timing is a statement about that machine, not a benchmark.")


def sec_unit(d):
    d.h2("Unit Testing")
    d.p("The unit tests live in `tests/test_end_to_end.py` and are run with `python -m unittest discover -s tests -v`. All five pass in 0.79 s. Each test builds a "
        "fresh `FederatedUnlearningEngine` whose audit ledger is a temporary file, so the tests never touch the real `data/audit_log.jsonl`.")
    d.table([["No.", "Test", "What it asserts", "Result"],
             ["1", "`test_complete_training_and_unlearning_workflow`", "after `train()` there are 5 active clients, epsilon > 0 and perplexity > 0; after `unlearn(\"client_finance\")` "
              "the status is CERTIFIED, clients go 5 -> 4, `reference_retrain_l2` <= 1e-10, the model hash changes, an audit record hash is present and the ledger verifies", "pass"],
             ["2", "`test_unlearning_is_not_repeatable_for_same_client`", "a second `unlearn(\"client_health\")` after the first raises `ValueError`", "pass"],
             ["3", "`test_audit_detects_tampering`", "the epsilon field of the first ledger record is rewritten to 999; `AuditLedger.verify()` returns False and the message contains \"failed\"", "pass"],
             ["4", "`test_certificate_export_is_machine_readable`", "`export_certificate` writes JSON whose `certificate_id` equals the in-memory certificate and whose `audit_verification` says \"Verified\"", "pass"],
             ["5", "`test_localhost_health_and_state_endpoints`", "a `ThreadingHTTPServer` on an OS-chosen port answers `/api/health` with status ok and `/api/state` with `trained` false and 5 contributions", "pass"]],
            "The five unit tests", widths=[0.06, 0.30, 0.54, 0.10], font=9)
    d.p("The tests use the default configuration and seed 2026, so they are repeatable but exercise one numerical case; the 50-seed study in Chapter 8 supplies the variation "
        f"(250 unlearning requests, all CERTIFIED, largest reference distance {_seeds['reference_l2']['max']:.2e}). Test 1 asserts the reference distance with the tolerance "
        "(1e-10) that the engine itself uses to grant CERTIFIED, so it confirms internal consistency; because the reference re-uses the stored noise and updates, it is an "
        "identity and cannot fail. The independent check, a retraining with fresh noise, is part of the results chapter.")


def sec_integration(d):
    d.h2("Integration Testing")
    d.p("Integration testing joins the engine, the ledger and the HTTP handler. It was done with `scripts/smoke_test.py`, which starts `app.py` on a spare port "
        "from a throw-away working directory (so the real ledger is untouched) and drives the JSON API with `urllib`; with `--url` it tests an already running "
        "server. It prints PASS or FAIL for fourteen checks and stops at the first failure; all fourteen pass.")
    d.table([["No.", "Check", "Expectation"],
             ["1", "health endpoint", "HTTP 200, `status` = ok"],
             ["2", "fresh state", "`trained` false and 5 contributions"],
             ["3", "unlearn before training", "HTTP 400 with an `error` field"],
             ["4", "generate before training", "HTTP 400"],
             ["5", "training", "HTTP 200, 5 active clients, epsilon > 0"],
             ["6", "generate", "HTTP 200, text starts with the seed \"privacy\""],
             ["7", "unlearning", "HTTP 200, status CERTIFIED, `clients_after` 4"],
             ["8", "certificate verifies", "`reference_retrain_l2` <= 1e-10 and a 64-character audit record hash"],
             ["9", "repeat unlearning", "HTTP 400 for the same client"],
             ["10", "certificate download", "`/api/certificate/latest` returns the same id with `audit_valid` true"],
             ["11", "audit verification", "`/api/audit/verify` returns `valid` true"],
             ["12", "ledger order", "events are exactly FEDERATED_TRAINING then CLIENT_UNLEARNING"],
             ["13", "new session", "`/api/session` returns a different session id"],
             ["14", "history kept", "the new session is untrained and the ledger still holds 2 records"]],
            "The fourteen smoke checks", widths=[0.07, 0.30, 0.63], font=9.5)
    d.p("The checks cover the whole path an operator uses: train, sample, unlearn, download the certificate, verify the ledger and start a new session. Check 14 matters "
        "for the compliance claim: opening a new session does not discard earlier audit history.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("Functional testing compares each feature with its description. The user-interface rows come from the scripted browser sessions (screens are shown in Chapter 8); "
        "the engine rows come from the unit, smoke and experiment runs.")
    d.table([["Feature", "How it was exercised", "Observed outcome"],
             ["Federated training", "UI button and `POST /api/train`", f"5 clients aggregated; epsilon {_base['training']['epsilon']:.4f}; perplexity {_base['training']['perplexity']:.2f}; accuracy {100 * _base['training']['next_character_accuracy']:.2f} %"],
             ["Clipping", "per-client norms on the training screen", "all five raw norms (25.22 - 28.23) exceed C = 25 and are clipped to 25.000"],
             ["Certified unlearning", "UI: Client 01 then Client 02; API for all five clients", f"{_base['certified_count']}/5 certified on the default seed; 250/250 over 50 seeds"],
             ["Guards", "API probes", "untrained, repeat and last-client requests: HTTP 400 with a JSON message"],
             ["Sequential removal", "5 -> 4 -> 3 -> 2 clients", f"4/4 CERTIFIED; perplexity {_seq['steps'][0]['perplexity']:.1f} -> {_seq['steps'][-1]['perplexity']:.1f}; ledger verifies 5 records"],
             ["Model explorer", "seed \"privacy\" before and after a removal", "text produced both times; the two 44-character samples are identical (see the results chapter)"],
             ["Certificate download", "`GET /api/certificate/latest`", "JSON with `audit_valid` true; 404 when no certificate exists"],
             ["Audit verification", "UI button and API", "\"Verified 4 audit record(s)\" in the capture session"],
             ["New session", "UI confirm dialog and API", "engine reset, audit history preserved"],
             ["Dark mode and mobile layout", "UI at 1440 x 900 and 390 px", "both render in all 20 acceptance journeys; bottom navigation replaces the sidebar on the narrow screen"],
             ["Legacy interface", "`GET /` on the API port", "original four-tab page loads and shows the same session state"]],
            "Functional test results", widths=[0.2, 0.3, 0.5], font=9)
    d.p("No functional defect was found in the engine paths the product offers. The defects found by the security and load studies concern the HTTP layer and the ledger "
        "file, and are listed in the next sections.")


def sec_security_test(d):
    sp = _sp
    cc = sp["classification_counts"]
    d.h2("Security Testing")
    d.p(f"The product has no authentication, no accounts and no encryption, so security testing concerns what an unauthenticated caller or a hostile web page can do to the "
        f"server and to the ledger. `scripts/run_testing_experiments.py` sent {sp['n_probes']} synthetic malicious or malformed inputs to a live server (invalid, negative and "
        "oversized Content-Length values, invalid UTF-8, deeply nested and duplicate-key JSON, hostile client ids, header injection, slow and idle connections, unusual HTTP "
        f"methods, cross-origin requests, ledger-file manipulation). Result: {cc['handled']} handled, {cc['noteworthy']} handled with noteworthy behaviour and "
        f"{cc['defect']} defects; the server was still alive after the last probe ({sp['server_alive_after_all']}). The eight defects are findings of this project, not hidden:")
    d.table([["Defect", "Evidence", "Fix (Chapter 10)"],
             ["Negative Content-Length", "`rfile.read(-1)` blocks until the client closes; no response within 4 s", "validate the header, reject values < 0"],
             ["Declared body longer than sent", "500 bytes declared, 30 sent, socket left open: the server waits indefinitely", "socket read timeout"],
             ["Cross-site POST executes a removal", "text/plain POST with `Origin: evil.example` to `/api/unlearn` returns 200 and removes the client (CSRF)", "require a JSON content type, check Origin, add a token"],
             ["Host header not validated", "`Host: evil.example` is served (DNS-rebinding precondition)", "allow-list of hosts"],
             ["Bursts of new connections", "64 simultaneous connections: 34 served, 30 refused; 128: 43 served, 85 refused; the stdlib listen backlog is 5", "production server with a larger accept queue"],
             ["Corrupt ledger line", "a garbage line appended to the file makes `/api/state` return 500; the UI stops loading", "quarantine bad lines, keep serving"],
             ["Empty ledger verifies", "file truncated to zero bytes: `verify` returns valid with 0 records", "anchor the record count and head hash outside the file"],
             ["No authentication", "every route works without credentials: read the full audit log, erase a client, retrain and discard certificates, reset the session", "authentication and roles"]],
            "Defects found by the security probes", widths=[0.22, 0.53, 0.25], font=8.5)
    d.p("The 15 noteworthy cases are mild: unsupported methods (OPTIONS, HEAD, TRACE, PUT, DELETE, PATCH) return the standard-library HTML 501 page instead of JSON, the "
        "security response headers (content-security-policy, x-frame-options, x-content-type-options) are absent, a 100 kB client id is echoed back in the error, "
        "duplicate JSON keys resolve to the last one, 200 idle connections each pin a server thread, and a request abandoned with a half-closed socket is still executed. "
        "Input validation proper was sound: malformed, array, missing and hostile client ids all produced a clean HTTP 400 or 404, and no probe crashed the server.")
    if not _rep(d):
        d.h3("Input handling in the API edge-case run")
        cases = {c["case"]: c for c in _api["edge_cases"]}
        rows = []
        for key, note in (("malformed JSON body", "rejected with the parser message, no crash"),
                          ("JSON array instead of object", "rejected: \"JSON body must be an object\""),
                          ("unlearn without client_id", "rejected: \"client_id is required\""),
                          ("unlearn with SQL-ish id", "treated as an unknown client; there is no SQL layer"),
                          ("path traversal on /", "404 \"Route not found\"; the server serves no files from disk"),
                          ("oversized body (2 MB)", "no clean 400: the connection is aborted (client saw WinError 10053)")):
            c = cases[key]
            rows.append([key, str(c["status"]) if c["status"] > 0 else "no response", note])
        d.table([["Probe", "HTTP status", "Observation"]] + rows, "Input-handling probes against the live API", widths=[0.32, 0.14, 0.54], font=9.5)
    d.h3("Audit-ledger tamper tests")
    rows = [[c["case"], "yes" if c["detected"] else "no", c["detail"]] for c in _aud["cases"]]
    d.table([["Manipulation of a three-record ledger", "Detected", "`verify()` message"]] + rows, "Tamper experiments on the hash-chained ledger", widths=[0.46, 0.12, 0.42], font=9)
    if not _rep(d):
        d.figure(CHARTS / "c10_audit_tamper.png", "Seven manipulations of the audit ledger: four are detected, three are not", width=4.9)
    d.p("Any edit to a field, any deletion from the middle and any swap of two records breaks a link and is reported with the position of the first bad record. Removing the "
        "newest records, rewriting a record and recomputing every later hash, and appending a forged record with a correct hash all pass verification, because the chain has "
        "no secret, no signature and no copy of the head hash outside the file. The ledger is tamper-evident against careless edits, not against whoever can write the file; "
        "together with the empty-ledger probe this fixes the engineering item of Chapter 10: sign every record and anchor the head hash and the count externally.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p("Validation asks whether the system behaves sensibly on unusual input. The probes below were sent to a live server in a fixed order, so state-dependent cases such "
        "as the repeat and last-client guards run after the cases that create the state.")
    rows = []
    for c in _api["edge_cases"]:
        if _rep(d) and c["status"] == 200:
            continue
        resp = str(c["response"]).replace("\n", " ")
        resp = resp if len(resp) < 62 else resp[:59] + "..."
        status = str(c["status"]) if c["status"] > 0 else "no response"
        rows.append([c["case"], status, resp])
    note = " (the five HTTP 200 cases are omitted here: empty, Unicode and 5,000-character seeds, the first removal and the legacy page)" if _rep(d) else ""
    d.table([["Case", "HTTP", "Response"]] + rows, "API edge-case probes (experiments/api)" + note, widths=[0.34, 0.1, 0.56], font=8.5)
    d.paras(
        "Eighteen of the twenty probes behave as intended: invalid or premature requests get a 400 or 404 with a JSON `error` message, valid requests succeed, and "
        "unusual but legal text (an empty seed, a Unicode seed with an emoji, a 5,000-character seed) is normalised into the 33-symbol alphabet. The two exceptions are the "
        "oversized body and the PUT method, both covered by the security probes.",
        "Model-level validation was done by experiments. The membership statistic is a rank statistic over five member and five non-member sentences, so its resolution is 0.04; "
        f"the 50-seed study therefore reports AUC as {_seeds['membership_auc_before']['mean']:.3f} +/- {_seeds['membership_auc_before']['sd']:.3f} before and "
        f"{_seeds['membership_auc_after']['mean']:.3f} +/- {_seeds['membership_auc_after']['sd']:.3f} after removal, and the synthetic-corpus study raises the resolution to "
        "5e-5 with 200 versus 200 sentences. Removing clients one by one down to a single client works, and the removal of the last is refused.")


def sec_load_concurrency(d):
    d.h3("Load and concurrency")
    ld = _ld
    d.p(f"Threaded HTTP clients on `127.0.0.1` (up to {ld['per_level_cap_requests']} requests or {ld['per_level_cap_seconds']} s per level) exercised four request mixes at 1, 2, 4, 8, 16, 32 and 64 "
        "concurrent clients against one server. The table gives requests per second, 95th-percentile latency in milliseconds and the number of 5xx or connection errors.")
    levels = (1, 4, 16, 64)
    rows = []
    for k, v in ld["scenarios"].items():
        lv = {x["concurrency"]: x for x in v["levels"]}
        rows.append([k] + [f"{lv[c]['requests_per_s']:.0f} / {lv[c]['p95_ms']:.0f} / {lv[c]['errors_5xx_or_connection']}" for c in levels])
    d.table([["Request mix (req/s / p95 ms / errors)", "1 client", "4 clients", "16 clients", "64 clients"]] + rows,
            "Throughput, latency and errors under concurrency (127.0.0.1)", widths=[0.36, 0.16, 0.16, 0.16, 0.16], font=9, align=["l", "c", "c", "c", "c"])
    r = ld["races"]
    r1 = r["32 simultaneous unlearn requests for the same client"]
    r2 = r["16 simultaneous train requests"]
    r3 = r["8 writers (120 train requests) while one thread verifies the chain"]
    so = ld["soak"]
    d.p(f"Read-only endpoints scale until the thread-per-connection server saturates: `/api/health` peaks near 1,070 req/s at four clients, while `/api/state` stays near 80 req/s "
        f"because every call re-reads and re-verifies the ledger, and its p95 latency grows from 29 ms with one client to 1.6 s with 64, where 19 of its requests failed with connection errors. "
        "The mixed read/write scenario falls from 48 to 26 req/s as the single engine lock serialises the writes. Correctness under concurrency held in all three race tests: "
        f"32 simultaneous removals of the same client produced exactly one HTTP 200 and 31 HTTP 400 responses ({r1['unlearning_events']} unlearning event in the ledger); 16 simultaneous training requests "
        f"produced {r2['ledger_records']} ledger records, one per success, with contiguous sequence numbers and a valid chain; and 8 writers appending {r3['writes_ok']} records while a ninth thread "
        f"verified the chain saw {r3['verify_invalid']} invalid reads. A soak of {so['requests']} mixed requests produced {so['errors_5xx_or_connection']} errors, the ledger grew to {so['ledger_records_end']} records, "
        f"memory rose from {so['rss_mb_before']:.0f} to {so['rss_mb_after']:.0f} MB, and the median state read slowed from {so['state_ms_first50']['p50_ms']:.0f} ms to {so['state_ms_last50']['p50_ms']:.0f} ms, "
        "the visible cost of reading the whole ledger on every call.")
    if not _rep(d) and (CHARTS / "t01_load.png").exists():
        d.figure(CHARTS / "t01_load.png", "Throughput and latency against the number of concurrent clients (127.0.0.1)", width=5.4)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Single-client performance was measured on `127.0.0.1`. (Against `localhost` on this machine, Python clients pay about two seconds per call for an IPv6 "
        "fall-back, which would inflate every figure fourfold.) Each endpoint was called 30 to 100 times; the table gives the median and 95th percentile.")
    rows = []
    for k, v in _api["latency"].items():
        if "p95_ms" in v:
            rows.append([k, str(v["n"]), f"{v['p50_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    d.table([["Endpoint", "Calls", "Median (ms)", "p95 (ms)", "Max (ms)"]] + rows, "API response times on 127.0.0.1", widths=[0.4, 0.12, 0.16, 0.16, 0.16], font=9.5,
            align=["l", "c", "c", "c", "c"])
    if not _rep(d):
        d.figure(CHARTS / "c09_api_latency.png", "Median and 95th-percentile response time per endpoint", width=5.0)
    u = _lat("POST /api/unlearn")
    t = _lat("POST /api/train")
    d.p(f"Training answers in {t['p50_ms']:.0f} ms and a full unlearning request, including two membership-attack evaluations, the metric recomputation and the ledger write, in "
        f"{u['p50_ms']:.0f} ms (p95 {u['p95_ms']:.0f} ms).")
    sec_load_concurrency(d)
    d.h3("Unlearning against retraining")
    rows = [[str(r["clients"]), f"{r['total_records']:,}", f"{r['train_ms_median']:.1f}", f"{r['unlearn_ms_median']:.1f}", f"{r['full_retrain_ms_median']:.1f}",
             f"{r['speedup_retrain_over_unlearn']:.2f}x"] for r in _sc["rows"]]
    d.table([["Clients", "Records", "Train (ms)", "unlearn() (ms)", "Retrain on retained (ms)", "Retrain / unlearn"]] + rows,
            "Cost of `unlearn()` against re-running the proxy training (median of 5 runs, synthetic clients)", widths=[0.12, 0.14, 0.16, 0.18, 0.22, 0.18], font=9.5,
            align=["c", "c", "c", "c", "c", "c"])
    if not _rep(d):
        d.figure(CHARTS / "c08_scaling.png", "Median wall time of unlearning and of retraining the proxy against the number of clients", width=4.8)
    d.p("On the five-client demonstration `unlearn()` (45.3 ms) is about three times *slower* than re-running the proxy training on the four retained clients (13.4 ms), because it "
        "carries a fixed cost that retraining does not: two membership evaluations, two metric evaluations and a ledger write. The curves cross near 100 clients (1.38x in favour of "
        "unlearning); at 500 clients and 50,000 synthetic records unlearning is 6.8x faster, because it touches one stored vector while retraining grows with the records. For the "
        "neural adapters of Chapter 8 the same comparison is far larger: subtraction takes 24 microseconds and retraining the seven retained adapters 5.9 s.")
    d.h3("Growth of the audit ledger")
    la = _sc["ledger_append_ms_at_length"]
    if not _rep(d):
        d.figure(CHARTS / "c12_ledger_append.png", "Time to append one record against the number of records already in the ledger", width=4.2)
    d.p(f"`AuditLedger.append` reads the entire file to find the previous hash, so each append costs more as the ledger grows: {la['1']:.2f} ms at the first record, "
        f"{la['100']:.1f} ms at 100, {la['1000']:.1f} ms at 1,000 and {la['2000']:.1f} ms at 2,000 records; verifying 2,000 records took {_sc['ledger_verify_2000_ms']:.1f} ms. "
        "A service logging every deletion request would need an index or a tail read (Chapter 10).")


def sec_uat(d):
    ac = _ac
    d.h2("User Acceptance Testing")
    d.p(f"Acceptance was tested by *scripted synthetic-user acceptance*: a Playwright script drives Chrome through the real interface of a running server. It is not a study with human "
        f"participants. The script ran {ac['journeys']} independent, randomised journeys ({ac['desktop_journeys']} at 1440 x 900 and {ac['mobile_journeys']} at 390 x 844; {ac['dark_mode_journeys']} in dark mode; "
        f"{ac['cancelled_dialog_journeys']} that first cancel the confirmation dialog). Each journey starts a fresh session, picks one to three clients to remove in random order and a random seed text, and "
        "checks seven steps against values read back from `/api/state`: the training page loads, training completes, a sample is generated, each removal shows a certificate with status CERTIFIED and the "
        "right ledger count, the audit chain verifies, the theme toggle works, and the browser console stays free of errors.")
    steps = ac["pass_count_per_step"]
    d.table([["Step", "Passed", "Criterion"],
             ["load training page", f"{steps['load training page']}/{ac['journeys']}", f"page renders; load time p50 {ac['training_page_load_ms']['p50_ms']:.0f} ms, p95 {ac['training_page_load_ms']['p95_ms']:.0f} ms"],
             ["train", f"{steps['train']}/{ac['journeys']}", "toast \"Federated training complete\"; the page shows the reported epsilon; the API reports 5 active clients and one new ledger record"],
             ["generate sample", f"{steps['generate sample']}/{ac['journeys']}", "the generated sample on the page contains the (normalised) seed text"],
             ["unlearn (certificate)", f"{steps['unlearn (certificate)']}/{ac['journeys']}", f"status CERTIFIED, certificate id shown, active-client and ledger counts correct after every removal; a cancelled dialog leaves the model unchanged ({ac['total_certificates_checked']} certificates checked)"],
             ["audit verify", f"{steps['audit verify']}/{ac['journeys']}", "toast \"Hash chain verified\"; the API reports valid and the expected record count"],
             ["theme toggle", f"{steps['theme toggle']}/{ac['journeys']}", "dark-mode journeys switch the theme attribute to dark; the others start in light"],
             ["no console errors", f"{steps['no console errors']}/{ac['journeys']}", "no error-level console message"]],
            "Results of the scripted synthetic-user acceptance journeys", widths=[0.22, 0.12, 0.66], font=9.5)
    d.p(f"All {ac['journeys_passed_all_steps']} journeys passed every step, with a mean duration of {ac['mean_duration_s']:.1f} s and {ac['console_error_journeys']} journeys with console errors. "
        "The earlier hand-scripted walk-through of nine steps (train, sample, remove Client 01, sample again, remove Client 02, dashboard, audit, theme, narrow viewport) produced the screenshots of "
        "Chapter 8 and is the sequence that the randomised journeys generalise. The result shows that the flow an operator needs is discoverable, complete and stable across viewports and themes; "
        "usability for human users and accessibility (no screen-reader or keyboard audit) are outside what a script can establish.")


def sec_test_limits(d):
    d.h2("Scope Boundaries of the Testing")
    d.p("The tests are real and repeatable; four boundaries define what their results cover.")
    d.bullets([
        "**Scale.** The unit and smoke tests run the 1,089-parameter bigram product; the synthetic-corpus study (up to 4,000 synthetic clients) and the neural adapter study (a 137,151-parameter GRU, eight synthetic clients, one aggregation round) extend the checks, but nothing here is a billion-parameter language model.",
        "**Data.** All test data are synthetic (seeded generators) or the product's own 25 sentences; the tests use fixed seeds, and the seed studies vary them.",
        "**Acceptance.** The acceptance result is from scripted synthetic users, not human participants.",
        "**Machine.** Every timing is from one CPU workstation under a quiet load, reported as medians and percentiles."])
