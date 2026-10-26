"""Chapter 7 content: system testing (ForgetSafe). Every number is read from experiments/*/metrics.json; the tests described are the real ones
in tests/test_end_to_end.py and scripts/smoke_test.py, and the probes in scripts/run_experiments.py (experiments/api, experiments/audit_tamper)."""
from __future__ import annotations

from doc_common import CHARTS, metrics

_api = metrics("api")
_aud = metrics("audit_tamper")
_sc = metrics("scaling")
_base = metrics("baseline")
_seq = metrics("sequential")
_seeds = metrics("seeds")


def _lat(key):
    return _api["latency"][key]


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        "ForgetSafe has three layers that can fail independently: the numerical engine (`certified_unlearning/engine.py`, `model.py`), the hash-chained audit "
        "ledger (`audit.py`) and the HTTP surface (`web.py`) with the React interface on top of it. The testing strategy therefore follows the layers from the "
        "inside out. The engine and the ledger are covered by deterministic unit tests that run in under a second; the HTTP surface is covered by an "
        "in-process server test and by an end-to-end smoke script that talks to a real server over TCP; the measurement suite `scripts/run_experiments.py` "
        "adds the probes that a test suite normally would not contain (fresh-noise retraining, a noise sweep, tamper attacks, API edge cases and latency); and "
        "the user interface was exercised by a scripted browser session (Playwright with Chrome) that also produced the screenshots in Chapter 8.",
        "The strategy has one deliberate limit that is stated here so that it is not mistaken for something else later: the product is a demonstrator on a "
        "1,089-parameter bigram model, so the tests establish that the *workflow and the bookkeeping* are correct and reproducible. They do not, and cannot, "
        "establish that a real federated large language model has been forgotten.")
    d.table([["Layer", "What is checked", "Instrument", "Where reported"],
             ["Engine and model", "training, unlearning, certificate fields, guards", "5 `unittest` cases; 14 smoke checks", "Unit and integration testing"],
             ["Audit ledger", "hash chain, tamper detection, export", "unit test; 8 tamper experiments", "Unit and security testing"],
             ["HTTP API", "routes, status codes, JSON errors, edge cases", "smoke script; 20 probe cases", "Integration and validation"],
             ["User interface", "train, explore, unlearn, audit, dark mode, mobile", "scripted Playwright session", "User acceptance"],
             ["Performance", "latency per endpoint, cost of unlearning against retraining, ledger growth", "timing probes on 127.0.0.1", "Performance testing"]],
            "Test layers and instruments", widths=[0.17, 0.37, 0.28, 0.18], font=9.5)
    d.p("All tests and probes ran on the development machine described in Chapter 6 (Intel Core i5-12500, 15.7 GB RAM, Windows 11, Python 3.11.9, no GPU). "
        "Every timing is therefore a statement about that machine under a quiet single-user load, not a benchmark.")


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
    d.paras(
        "Two properties of these tests deserve comment. First, they use the default configuration and the fixed random seed 2026, so they are repeatable but "
        "exercise a single numerical case; the 50-seed study in Chapter 8 supplies the missing variation (250 unlearning requests, all CERTIFIED, largest reference "
        f"distance {_seeds['reference_l2']['max']:.2e}). Second, test 1 asserts the reference distance with the same tolerance (1e-10) that the engine itself uses to "
        "grant the CERTIFIED status. The assertion therefore confirms that the code is internally consistent; it is not an independent check of forgetting, because the "
        "reference model re-uses the stored noise and the stored updates (the results chapter discusses what an independent check looks like).")


def sec_integration(d):
    d.h2("Integration Testing")
    d.p("Integration testing joins the engine, the ledger and the HTTP handler. It was done with `scripts/smoke_test.py`, which starts `app.py` on a spare port "
        "from a throw-away working directory (so the real ledger is untouched) and drives the JSON API with `urllib`. It can also be pointed at an already running "
        "server with `--url`. The script prints PASS or FAIL for fourteen checks and stops at the first failure; all fourteen pass.")
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
    d.p("The checks cover the whole path an operator uses in the interface: train, sample, unlearn, download the certificate, verify the ledger and start a new "
        "session. Check 14 matters for the compliance claim, because it shows that opening a new session does not discard earlier audit history.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("Functional testing compares each feature of the application with its description. The table records what was exercised, how, and the observed outcome. "
        "The user-interface rows come from the scripted browser session (screens are shown in Chapter 8); the engine rows come from the unit, smoke and experiment runs.")
    b = _base["unlearning_per_client"]
    d.table([["Feature", "How it was exercised", "Observed outcome"],
             ["Federated training", "UI button and `POST /api/train`", f"5 clients aggregated; epsilon {_base['training']['epsilon']:.4f}; perplexity {_base['training']['perplexity']:.2f}; accuracy {100 * _base['training']['next_character_accuracy']:.2f} %"],
             ["Clipping", "per-client norms on the training screen", "all five raw norms (25.22 - 28.23) exceed C = 25 and are clipped to 25.000"],
             ["Certified unlearning", "UI: Client 01 then Client 02; API for all five clients", f"{_base['certified_count']}/5 certified on the default seed; 250/250 over 50 seeds"],
             ["Guard: untrained model", "API probe", "HTTP 400 \"Train the federated model before requesting unlearning\""],
             ["Guard: repeat request", "API probe", "HTTP 400 \"client_finance has already been unlearned\""],
             ["Guard: last client", "sequential experiment and API probe", "5th removal refused: \"At least one client must remain in the model\""],
             ["Sequential removal", "5 -> 4 -> 3 -> 2 clients", f"4/4 CERTIFIED; perplexity {_seq['steps'][0]['perplexity']:.1f} -> {_seq['steps'][-1]['perplexity']:.1f}; ledger verifies 5 records"],
             ["Model explorer", "seed \"privacy\" before and after a removal", "text produced both times; the two 44-character samples are identical (see the results chapter)"],
             ["Certificate download", "`GET /api/certificate/latest`", "JSON with `audit_valid` true; 404 when no certificate exists"],
             ["Audit verification", "UI button and API", "\"Verified 4 audit record(s)\" in the capture session"],
             ["New session", "UI confirm dialog and API", "engine reset, audit history preserved"],
             ["Dark mode and mobile layout", "UI at 1440 x 900 and 390 px", "both render; bottom navigation replaces the sidebar on the narrow screen"],
             ["Legacy interface", "`GET /` on the API port", "original four-tab page loads and shows the same session state"]],
            "Functional test results", widths=[0.2, 0.3, 0.5], font=9)
    d.p("No functional defect was found in the engine paths that the product actually offers. The defects and weak points that were found are not functional "
        "failures but design limits, and are collected in the security, validation and limits sections of this chapter and in the results chapter.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Security testing in this project is narrow and is reported as such. The product has no authentication, no user accounts and no encryption, so the tests "
        "concern input handling and the integrity of the audit ledger, which are the two security-relevant features it does claim.")
    d.h3("Input handling")
    cases = {c["case"]: c for c in _api["edge_cases"]}
    rows = []
    for key, note in (("malformed JSON body", "rejected with the parser message, no crash"),
                      ("JSON array instead of object", "rejected: \"JSON body must be an object\""),
                      ("unlearn without client_id", "rejected: \"client_id is required\""),
                      ("unlearn unknown client id", "rejected, id echoed as data in the JSON error"),
                      ("unlearn with SQL-ish id", "treated as an unknown client; there is no SQL layer to inject into"),
                      ("path traversal on /", "404 \"Route not found\"; the server serves no files from disk"),
                      ("oversized body (2 MB)", "no clean 400: the connection is aborted (client saw WinError 10053)"),
                      ("unsupported method (PUT)", "stdlib HTML 501 page instead of a JSON error")):
        c = cases[key]
        rows.append([key, str(c["status"]) if c["status"] > 0 else "no response", note])
    d.table([["Probe", "HTTP status", "Observation"]] + rows, "Input-handling probes against the live API", widths=[0.32, 0.14, 0.54], font=9.5)
    d.p("The handler limits request bodies to 1,000,000 bytes and raises before reading anything larger. On the tested machine that produced a connection abort "
        "rather than a readable 400 response, which is safe for the server but poor behaviour for a client. The legacy single-page interface escapes server values "
        "through a small `esc` helper before inserting them into the page and the React interface relies on React's default escaping; this was read in the code and "
        "was not attacked with payloads, so it is recorded as code inspection and not as a test result.")
    d.h3("Audit-ledger tamper tests")
    rows = [[c["case"], "yes" if c["detected"] else "no", c["detail"]] for c in _aud["cases"]]
    d.table([["Manipulation of a three-record ledger", "Detected", "`verify()` message"]] + rows, "Tamper experiments on the hash-chained ledger", widths=[0.46, 0.12, 0.42], font=9)
    d.figure(CHARTS / "c10_audit_tamper.png", "Seven manipulations of the audit ledger: four are detected, three are not", width=4.9)
    d.p("The chain does what a simple hash chain can do: any edit to a field, any deletion from the middle and any swap of two records breaks a link and is reported "
        "with the position of the first bad record. Three manipulations pass verification: removing the newest records from the end of the file, rewriting a record "
        "and then recomputing every later hash, and appending a forged record with a correctly computed hash. All three follow from the same fact: the chain has no "
        "secret, no digital signature and no copy of the latest hash held outside the file, so whoever can write the file can also write a consistent chain. "
        "The ledger is therefore *tamper-evident against careless edits*, not tamper-proof against a motivated insider. This is stated in the project report "
        "(`PROJECT_REPORT.md`) as a production extension and is repeated in the limitations below.")
    d.h3("Not tested")
    d.bullets(["authentication and authorisation (none exists: every endpoint is open and one engine is shared by all callers);",
               "transport security, cross-origin policy and denial-of-service resistance;",
               "a penetration test or any automated vulnerability scan;",
               "confidentiality of the stored clipped updates, which the design requires to be protected because they are what makes subtraction possible."])


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p("Validation asks whether the system behaves sensibly on unusual input. The probes below were sent to a live server by `scripts/run_experiments.py` "
        "(experiment `api`) in a fixed order, so state-dependent cases such as the repeat and last-client guards run after the cases that create the state.")
    rows = []
    for c in _api["edge_cases"]:
        resp = str(c["response"]).replace("\n", " ")
        resp = resp if len(resp) < 62 else resp[:59] + "..."
        status = str(c["status"]) if c["status"] > 0 else "no response"
        rows.append([c["case"], status, resp])
    d.table([["Case", "HTTP", "Response"]] + rows, "API edge-case probes (experiments/api)", widths=[0.34, 0.1, 0.56], font=8.5)
    d.paras(
        "Of the twenty probes, eighteen behave as intended: invalid or premature requests get a 400 or 404 with a JSON `error` message, valid requests succeed, and "
        "unusual but legal text (an empty seed, a Unicode seed with an emoji, and a 5,000-character seed) is normalised by `normalize_text` into the 33-symbol "
        "alphabet and handled without error. The two exceptions are the rough edges described above, the oversized body and the PUT method.",
        "Model-level validation was done by the experiments rather than by single cases. The membership statistic is a rank statistic over five member and five "
        "non-member sentences, so its resolution is 0.04 and individual values such as 0.04 or 0.48 in the baseline table are noisy; this is why the 50-seed study "
        f"reports AUC as {_seeds['membership_auc_before']['mean']:.3f} +/- {_seeds['membership_auc_before']['sd']:.3f} before and "
        f"{_seeds['membership_auc_after']['mean']:.3f} +/- {_seeds['membership_auc_after']['sd']:.3f} after removal. The `unlearn` guards were also validated "
        "in sequence: removing clients one by one down to a single client works, and the removal of the fifth is refused.")


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Performance was measured on `127.0.0.1` with a single client. (Measured against `localhost` on this machine, Python clients pay about two seconds per "
        "call for an IPv6 fall-back, which would have inflated every figure fourfold, so the loop-back address was used.) Each endpoint was called 30 to 100 times; "
        "the table gives the median and 95th percentile.")
    rows = []
    for k, v in _api["latency"].items():
        if "p95_ms" in v:
            rows.append([k, str(v["n"]), f"{v['p50_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    d.table([["Endpoint", "Calls", "Median (ms)", "p95 (ms)", "Max (ms)"]] + rows, "API response times on 127.0.0.1", widths=[0.4, 0.12, 0.16, 0.16, 0.16], font=9.5,
            align=["l", "c", "c", "c", "c"])
    d.figure(CHARTS / "c09_api_latency.png", "Median and 95th-percentile response time per endpoint", width=5.0)
    u = _lat("POST /api/unlearn")
    t = _lat("POST /api/train")
    d.p(f"Training answers in {t['p50_ms']:.0f} ms and a full unlearning request, including the two membership-attack evaluations, the metric recomputation and the "
        f"ledger write, in {u['p50_ms']:.0f} ms (p95 {u['p95_ms']:.0f} ms). The `/api/state` call is the slowest read because it re-reads and re-verifies the whole "
        "ledger on every request; it takes about 21 ms with a trained model against 5 ms untrained.")
    d.h3("Unlearning against retraining")
    rows = [[str(r["clients"]), f"{r['total_records']:,}", f"{r['train_ms_median']:.1f}", f"{r['unlearn_ms_median']:.1f}", f"{r['full_retrain_ms_median']:.1f}",
             f"{r['speedup_retrain_over_unlearn']:.2f}x"] for r in _sc["rows"]]
    d.table([["Clients", "Records", "Train (ms)", "unlearn() (ms)", "Retrain on retained (ms)", "Retrain / unlearn"]] + rows,
            "Cost of `unlearn()` against re-running the proxy training (median of 5 runs, synthetic clients)", widths=[0.12, 0.14, 0.16, 0.18, 0.22, 0.18], font=9.5,
            align=["c", "c", "c", "c", "c", "c"])
    d.figure(CHARTS / "c08_scaling.png", "Median wall time of unlearning and of retraining the proxy against the number of clients", width=4.8)
    d.p("The result is not the one the narrative of unlearning usually promises. On the five-client demonstration `unlearn()` (45.3 ms) is about three times *slower* "
        "than simply re-running the proxy training on the four retained clients (13.4 ms), because it carries a fixed cost that retraining does not: two membership "
        "evaluations, two metric evaluations and a ledger write. The two curves cross near 100 clients (1.38x in favour of unlearning); at 500 clients and 50,000 "
        "synthetic records unlearning is 6.8x faster. Unlearning is nearly flat in the number of clients because it touches one stored vector of 1,089 values, while "
        "retraining grows with the number of records. The comparison says nothing about a real large language model, where retraining costs hours rather than "
        "milliseconds; it only shows that the engine's own overhead is small and does not grow with the data.")
    d.h3("Growth of the audit ledger")
    la = _sc["ledger_append_ms_at_length"]
    d.figure(CHARTS / "c12_ledger_append.png", "Time to append one record against the number of records already in the ledger", width=4.2)
    d.p(f"`AuditLedger.append` reads the entire file to find the previous hash, so each append costs more as the ledger grows: {la['1']:.2f} ms at the first record, "
        f"{la['100']:.1f} ms at 100, {la['1000']:.1f} ms at 1,000 and {la['2000']:.1f} ms at 2,000 records. Writing 2,000 records took {_sc['ledger_2000_appends_total_s']:.1f} s "
        f"and verifying them {_sc['ledger_verify_2000_ms']:.1f} ms. For an interactive demonstrator this is irrelevant; for a service that logs every deletion request "
        "it would call for an index or a tail read.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user study was carried out. No external user, compliance officer or teacher used the application, and no questionnaire or acceptance sign-off exists. "
        "What this section reports is an acceptance *walk-through* performed by the project team with a scripted browser session (`scripts/capture_screens.py`, "
        "Playwright with Chrome at 1440 x 900), which doubles as the source of every screenshot in Chapter 8.")
    d.numbered(["Open the landing page and wait for the count-up animations to finish; open the lab.",
                "Train the federated model through the interface (the toast reads \"5 clients aggregated, epsilon 1.6149\").",
                "Generate a sample from the seed \"privacy\" on the explorer screen.",
                "Request removal of Client 01 (Finance), confirm the dialog, and read the certificate (status Certified, utility retained 93.65 %, membership AUC 0.200 to 0.160).",
                "Generate a second sample; compare it with the first.",
                "Remove Client 02 (Healthcare) and read the second certificate (utility retained 98.30 %).",
                "Open the dashboard and the training screen and confirm that three clients remain active.",
                "Open the audit screen, press Verify hash chain and read \"Verified 4 audit record(s)\".",
                "Switch to dark mode, return to light mode, and repeat the unlearning page in a 390-pixel-wide viewport."])
    d.p("All nine steps completed without a browser-console error. The walk-through shows that the flow an operator needs is discoverable and coherent; it is not "
        "evidence of usability for real users, of accessibility compliance (no screen-reader or keyboard audit was run) or of fitness for a regulator's purposes.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.p("The testing reported in this chapter is real, repeatable and honest about its scope, and the following limits apply to every conclusion drawn from it.")
    d.bullets([
        "**The system under test is a proxy.** Passing tests show that clipping, noisy aggregation, subtraction, the reference recomputation, the attack, the "
        "certificate and the ledger work as coded on 1,089 bigram parameters. They say nothing about LoRA adapters, a transformer or a real client population.",
        "**Fixed seeds and one corpus.** Unit and smoke tests use seed 2026 and the five built-in clients (25 sentences). The 50-seed and sweep studies vary the noise "
        "seed but not the data; no other corpus was tried.",
        "**The certification check cannot fail.** Because the reference re-uses the stored noise and updates, `reference_retrain_l2` is zero up to floating-point error "
        f"(largest value over 250 requests {_seeds['reference_l2']['max']:.2e}); a test that cannot fail does not test forgetting. The retraining comparison with fresh noise "
        "is an experiment added by this project, not part of the shipped test suite.",
        "**Weak statistical power of the attack.** Five member and five non-member sentences give an AUC resolution of 0.04; at the default noise the attack is at chance "
        "even before unlearning, so it cannot show that anything was removed.",
        "**No load, concurrency or soak testing.** One client at a time was used; the server shares one engine behind a lock, and concurrent operators were not tested.",
        "**No penetration test, no authentication test** (there is no authentication), and no accessibility audit.",
        "**No real user testing**, as stated under user acceptance testing.",
        "**No code-coverage measurement** was made; the five unit tests exercise the engine, ledger and two endpoints, and the remaining routes are covered by the smoke script."])
