"""Chapter 7: System Testing. Numbers come from facts.py (experiments/**/metrics.json) and from the recorded test runs (REPORT_FACTS section 6)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .ch3_4 import FR_IDS, NFR_IDS


def _cat_rows():
    names = {"plain": "Plain statements", "negation": "Negation", "abbreviation": "Abbreviations", "ocr": "OCR run-ons and split words",
             "labs": "Lab values", "history": "History", "paraphrase": "Paraphrases outside the lexicon", "mixed": "Mixed narrative"}
    rows = []
    for k, v in F.STRESS["by_category"].items():
        rows.append([names[k], str(v["cases"]), str(v["tp"] + v["fn"]), F.f2(v["precision"]), F.f2(v["recall"]), f"{v['exact']} of {v['cases']}"])
    return rows


def _lat_rows():
    names = [("health", "GET /api/health"), ("login", "POST /api/auth/login (bcrypt check)"), ("queue_list", "GET /api/patients (queue)"),
             ("extract_pdf", "POST /api/reports/extract, text PDF"), ("extract_scan_png", "POST /api/reports/extract, PNG scan (OCR)"),
             ("create_patient", "POST /api/patients (fuse, model, SHAP, store)"), ("summary_pdf", "GET /api/patients/{id}/summary.pdf"),
             ("metrics", "GET /api/metrics"), ("flow_pdf_then_triage", "Flow: read a PDF, then assign a priority"),
             ("flow_scan_then_triage", "Flow: read a PNG scan, then assign a priority")]
    return [[n, f"{F.LAT[k]['median_ms']:,.1f}", f"{F.LAT[k]['p95_ms']:,.1f}", str(F.LAT[k]["n"])] for k, n in names]


def _trace_rows():
    rows = [
        ["FR-1", "test_wrong_password_rejected; test_protected_routes_require_token; test_garbage_token_rejected; smoke checks 2 to 4", "Pass"],
        ["FR-2", "test_extract_rejects_empty_and_unsupported; test_unsupported_upload_rejected; test_all_sample_reports_read_exactly; smoke check 5", "Pass (15 MB cap not tested)"],
        ["FR-3", "test_negation_drops_flag; test_abbreviations; test_abnormal_labs_set_flag; test_items_keep_their_page; 40-fragment stress set (Section 7.6)", "Partly: known wording read, defects listed"],
        ["FR-4", "test_create_patient_validates_vitals; screen 06", "Pass"],
        ["FR-5", "test_fused_record_has_36_inputs_in_model_order; screen 07", "Pass"],
        ["FR-6", "test_probabilities_sum_to_one_and_priority_is_argmax; test_sick_patient_is_more_urgent_than_well_patient; smoke checks 7 and 8; Chapter 8", "Pass (synthetic data)"],
        ["FR-7", "test_shap_sorted_by_absolute_impact_and_labelled; smoke check 9; screen 08", "Pass (wording defect, Section 7.6)"],
        ["FR-8", "test_create_patient_and_override_flow; smoke checks 10 and 11; screens 09 and 10", "Pass"],
        ["FR-9", "test_sample_queue_seeded_and_ordered; smoke checks 12 and 13; screens 04 and 11", "Pass (filter and search by screen only)"],
        ["FR-10", "test_summary_pdf; smoke check 16", "Pass"],
        ["FR-11", "test_metrics_reports_live_counts; smoke checks 14 and 15; screen 12", "Pass"],
        ["FR-12", "test_sample_queue_seeded_and_ordered; test_sample_download_blocks_path_traversal; test_all_sample_reports_read_exactly; screens 04 and 06", "Pass"],
        ["NFR-1", f"Section 7.7: PDF flow median {F.lat('flow_pdf_then_triage'):.0f} ms; scan flow median {F.lat('flow_scan_then_triage') / 1000:.1f} s; end-to-end maximum {F.E2E['max']:.1f} s on the samples", "Pass on this machine"],
        ["NFR-2", f"Model {F.MODEL_SEC * 1000:.3f} ms per patient in batch; POST /patients median {F.lat('create_patient'):.1f} ms", "Pass"],
        ["NFR-3", f"Chapter 8: {F.pct(F.W1, 2)} within one level (synthetic hold-out)", "Pass on synthetic data only"],
        ["NFR-4", "test_create_patient_and_override_flow (explanation present); test_shap_sorted_by_absolute_impact_and_labelled", "Pass"],
        ["NFR-5", f"Chapter 8: ECE {F.f3(F.CAL['ece_isotonic'])}, 0.8 to 0.9 bin over-confident", "Partly"],
        ["NFR-6", "Section 7.5: token, bcrypt, pydantic ranges, upload checks, path-traversal test", "Pass for the controls tested; gaps listed"],
        ["NFR-7", "Tests for 400, 401, 404 and 422; 413 and 503 paths not exercised", "Partly"],
        ["NFR-8", "scripts/check_responsive.py at build time; not re-run in the documentation session", "Not re-verified"],
        ["NFR-9", "By design no network call at run time; not verified with the network disabled", "Not verified"],
        ["NFR-10", f"{F.PYTEST_TOTAL} pytest tests ({F.PYTEST_PASSED} pass, {F.PYTEST_XFAIL} expected failure) in about {F.PYTEST_SECONDS} s", "Pass"],
        ["NFR-11", "Screen 12 banner and landing text state the data are synthetic", "Pass"],
    ]
    assert [r[0] for r in rows] == FR_IDS + NFR_IDS
    return rows


def blocks():
    st = F.STRESS
    rep = F.REPORT
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("ATHENA's first delivery shipped with one end-to-end smoke script and a screenshot walk. The documentation run added an automated pytest suite, a stress test for the report reader and a latency script, and this chapter reports what they show. "
            "The strategy follows the structure of the product. The report reader is rule-based, deterministic code, so it is tested at unit level with small hand-written fragments (negation, abbreviations, laboratory values, page numbers) and then stressed with a larger set of fragments that includes wording it is known not to handle. "
            "The triage model is a statistical component, so its *software* behaviour (input order, probabilities that sum to one, risk-level mapping, ordering of the explanation) is unit-tested, while its *predictive quality* is measured by the experiments of Chapter 8. "
            "The API ties the pieces together and is tested through FastAPI's test client against a scratch database and through a smoke script against a running server. Every screen of the console was walked with real data."),
          P("One qualification governs the whole chapter: the model under test is trained on seeded synthetic data (Chapter 6), so the tests show that the software does what it was designed to do, not that its triage decisions are clinically right."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_extract.py (report reader) and tests/test_triage.py (fused record, model, explanation)", f"{20 + 11} tests", "30 passed, 1 expected failure"],
               ["API / component", "pytest with FastAPI TestClient: tests/test_api.py, scratch SQLite database", "16 tests", "All passed"],
               ["Integration", "scripts/smoke_test.py against the running backend (127.0.0.1:" + str(F.API_PORT) + ")", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Functional / screens", "Playwright walk of the React console (scripts/capture_screens.py)", "12 screens", "All rendered with data"],
               ["Reader stress", "scripts/extract_stress.py: 40 hand-written fragments", f"{st['expected_flags']} expected flags", f"precision {F.pct(st['precision'])}, recall {F.pct(st['recall'])}"],
               ["Performance", "scripts/measure_api.py (HTTP) and ml/eval.py (end to end)", "10 call types", "Reported in Section 7.7"],
               ["Model validation", "ml/train.py, scripts/run_experiments.py (8 models, 5 seeds, 5-fold CV)", "Sections 8.3 to 8.9", "Reported in Chapter 8"]],
              widths=[1.3, 3.2, 1.2, 1.1], align=["l", "l", "l", "l"], size=9.5),
          P(f"All tests were run on one machine: {F.MACHINE}. The pytest suite of {F.PYTEST_TOTAL} tests finished in about {F.PYTEST_SECONDS} s. Timings in Section 7.7 are medians of repeated runs and should be read as indicative for this machine.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite has **{F.PYTEST_TOTAL} tests in three files: {F.PYTEST_PASSED} passed, {F.PYTEST_XFAIL} is an expected failure and {F.PYTEST_FAILED} failed**. "
            "The expected failure is deliberate: it records a defect found while writing the tests (negation scope, Section 7.6) as a test marked `xfail(strict=True)`, so the suite will fail loudly if the defect is ever fixed without the test being updated. "
            "`tests/conftest.py` points the application at a scratch SQLite file before the app is imported, so no test touches the demo database."),
          H3("7.2.1 Report reader (tests/test_extract.py, 20 tests)"),
          TAB("Unit tests of the report reader.",
              ["Test", "What it asserts"],
              [["test_plain_symptom_and_finding", "\"chest pain\" and \"ST elevation\" give exactly the flags chest_pain and st_elevation"],
               ["test_negation_drops_flag (4 cases)", "\"Denies chest pain\", \"No fever, no vomiting\", \"Negative for fracture\" and \"Without bleeding\" give no flag"],
               ["test_negation_is_clause_local (expected failure)", "\"Denies syncope but reports chest tightness\" should still flag chest pain; it does not (Section 7.6)"],
               ["test_abbreviations", "SOB, HTN and DM2 map to dyspnea, hypertension and diabetes"],
               ["test_ocr_run_on_words", "\"shortnessofbreath\" and \"chestpain\" (spaces lost by OCR) are still found"],
               ["test_brain_bleed_is_finding_not_symptom", "\"subarachnoid haemorrhage\" sets ct_hemorrhage and not the symptom bleeding"],
               ["test_abnormal_labs_set_flag (7 cases)", "Troponin 0.52, lactate 4.1, WBC 15.2, glucose 310 and 42, creatinine 2.4 and haemoglobin 7.8 set their lab flags"],
               ["test_normal_labs_do_not_set_flags", "Troponin 0.01, glucose 95, WBC 7.4, creatinine 0.9 and lactate 1.1 set none"],
               ["test_items_keep_their_page", "A finding on the second page is reported with page 2"],
               ["test_unsupported_upload_rejected", "A plain-text upload raises ValueError (HTTP 422 through the API)"],
               ["test_all_sample_reports_read_exactly", "All 12 generated reports (8 PDFs, 4 PNG scans, through real OCR) give exactly the expected flag set"]],
              widths=[2.9, 3.9], align=["l", "l"], size=9.5),
          H3("7.2.2 Fused record and triage model (tests/test_triage.py, 11 tests)"),
          TAB("Unit tests of the fused record and the model.",
              ["Test", "What it asserts"],
              [["test_fused_record_has_36_inputs_in_model_order", "The fused record has 36 keys in the exact training column order; ambulance codes as 2"],
               ["test_unknown_arrival_mode_defaults_to_walk_in", "An unrecognised arrival mode is coded 0"],
               ["test_risk_level_mapping (5 cases)", "P1 and P2 are High, P3 Moderate, P4 and P5 Low"],
               ["test_probabilities_sum_to_one_and_priority_is_argmax", "Probabilities sum to 1 (tolerance 0.001); the priority and confidence are the arg-max and maximum"],
               ["test_sick_patient_is_more_urgent_than_well_patient", "A STEMI-like record gets a more urgent priority than a well 30-year-old, who gets risk level Low"],
               ["test_shap_sorted_by_absolute_impact_and_labelled", "Explanation items are sorted by absolute impact, carry a direction text and name real model features"],
               ["test_absent_flags_with_negligible_effect_are_hidden", "Absent flags with an impact below 0.15 are not listed"]],
              widths=[2.9, 3.9], align=["l", "l"], size=9.5)]
    api_tab = TAB("Component tests of the HTTP API (tests/test_api.py, 16 tests).",
                  ["Test", "What it asserts"],
                  [["test_health_and_public_stats_need_no_token", "Health reports the model present; public statistics are available without a token"],
                   ["test_wrong_password_rejected", "A wrong password gives 401"],
                   ["test_protected_routes_require_token (4 cases)", "Queue, metrics, samples and /auth/me give 401 without a token"],
                   ["test_garbage_token_rejected", "A malformed bearer token gives 401"],
                   ["test_sample_queue_seeded_and_ordered", "At least 12 sample cases are seeded and the queue is ordered by priority"],
                   ["test_extract_rejects_empty_and_unsupported", "An empty file gives 400, a text file 422"],
                   ["test_create_patient_validates_vitals", "SpO2 of 20 and an unknown arrival mode give 422"],
                   ["test_create_patient_and_override_flow", "Create, change without reason (422), accept, change with reason: priority updated, model suggestion kept, risk level recomputed"],
                   ["test_override_priority_out_of_range", "Priority 9 gives 422"],
                   ["test_missing_patient_is_404", "Unknown patient id gives 404 on read and on override"],
                   ["test_summary_pdf", "The triage summary starts with the PDF signature"],
                   ["test_sample_download_blocks_path_traversal", "An encoded `../` path gives 404; a real sample downloads"],
                   ["test_metrics_reports_live_counts", "Offline accuracy and live counts, with a priority distribution over keys 1 to 5"]],
                  widths=[2.9, 3.9], align=["l", "l"], size=9.5)
    if rep:
        b += [H3("7.2.3 API (tests/test_api.py, 16 tests)"),
              P("The sixteen API tests check, through FastAPI's test client: that health and public statistics need no token; that a wrong password, a garbage token and every protected route without a token give 401; "
                "that the seeded sample queue exists and is ordered by priority; that an empty upload gives 400 and an unsupported one 422; that implausible vitals and an unknown arrival mode give 422; "
                "the full create, refuse-change-without-reason, accept, change-with-reason sequence, including that the model's original suggestion is kept and the risk level recomputed; "
                "an out-of-range priority (422); unknown patients (404); the summary PDF; the path-traversal guard on the sample route; and the metrics endpoint.")]
    else:
        b += [H3("7.2.3 API (tests/test_api.py, 16 tests)"), api_tab]

    # ------------------------------------------------------------------ 7.3
    smoke = [["1", "GET /api/health returns ok and the model is present"], ["2", "A wrong password is rejected"], ["3", "Login succeeds for the demo clinician"],
             ["4", "The queue requires a token"], ["5", "All 12 sample reports are read; precision and recall of the flags are at least 0.9 (observed 1.00 and 1.00)"],
             ["6", "Extracted items carry page numbers"], ["7", "Creating a patient from report 01 and its vitals returns 200"],
             ["8", "The STEMI case gets a high priority (observed priority 1)"], ["9", "The explanation list is ordered by influence"],
             ["10", "Changing a priority without a reason is rejected"], ["11", "The override is stored"], ["12", "The queue is ordered by priority"],
             ["13", "The queue reflects the override"], ["14", "Metrics return accuracy and per-class recall"], ["15", "Metrics return override counts and seconds per patient"],
             ["16", "The summary PDF downloads"], ["17", "An unknown patient gives 404"]]
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/smoke_test.py` drives a running backend over HTTP exactly as the console does. It was re-run in the documentation session against a scratch database on port {F.API_PORT}, and **all {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed**. "
            "The checks cross module boundaries: the reader with the model (5 to 9), the model with the database and the override rules (7 to 13), the database with the metrics (14, 15) and the PDF writer (16). "
            "The twelve reads in check 5 include the four PNG scans, so the OCR engine is exercised, and the script prints the time each took (about 0.0 to 0.2 s for PDFs, 2.3 to 3.7 s for scans)."),
          ]
    if rep:
        b += [P("The seventeen checks are: health; wrong password rejected; login; queue needs a token; 12 sample reports read with precision and recall of at least 0.9; page numbers present; patient created; STEMI case at high priority; "
                "explanation ordered by influence; change without reason rejected; override stored; queue ordered; queue reflects the override; metrics with accuracy and recall; metrics with override counts and timing; summary PDF; unknown patient 404.")]
    else:
        b += [TAB("The seventeen smoke checks.", ["No.", "Check"], smoke, widths=[0.6, 6.2], align=["c", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.4
    screens = [["01, 02", "Landing page, light and dark", "Page loads with the headline model numbers read from the API"],
               ["03", "Sign-in", "Demo login buttons for clinician and admin"],
               ["04", "Triage queue (12 sample cases)", "Counts per priority 0 / 0 / 5 / 1 / 6, filter tabs, rows ordered by priority then arrival"],
               ["05, 06", "New patient, empty and filled", "Sample report 01 read in 0.234 s; symptoms, findings and history appear with page numbers; vitals filled"],
               ["07", "Result, top", "Priority 1 Critical, High risk, calibrated confidence, fused record, extracted items with pages"],
               ["08", "Result, why this priority", "SHAP bars: ST elevation +3.11, troponin +2.19, lactate +1.51, heart rate +1.49"],
               ["09", "Accept or change dialog", "Priority selector and a required reason field"],
               ["10", "Result after a change", "Priority 2 Emergent, banner \"A clinician changed this from the model's priority 1 to 2\", REVIEWED badge"],
               ["11", "Queue after the change", "Thirteen cases; the changed patient is marked CHANGED"],
               ["12", "Model performance", f"Accuracy {F.ACC * 100:.1f}, within one level {F.W1 * 100:.1f}, macro F1 {F.MF1:.3f}; blue banner stating the data are synthetic; confusion matrix"]]
    b += [H2("7.4 Functional testing"),
          P("Functional testing walked every route of the React console with real data, using Playwright with 1440 x 900 pixel windows (`scripts/capture_screens.py`). The walk clicked the real controls (demo login, choose a sample report, Assign priority, Accept or change, Refresh), "
            "waited for the server's answers and saved a screenshot; it also collected browser console errors and failed requests, of which there were none when the screens were captured (`docs/FRONTEND_PLAN.md`, Section 4). "
            "A separate script, `scripts/check_responsive.py`, checked for horizontal scrolling at 360, 768 and 1440 pixels in light and dark themes, theme persistence, reduced-motion handling, keyboard focus and closing the drawer and dialog with Escape; it passed when the frontend was built and was not re-run in the documentation session. "
            "Screens 04 to 12 show states that exist only if the corresponding API call succeeded, so the screenshots double as evidence of the functional test."),
          TAB("Functional checks by screen.", ["Screen", "Function", "Observed result"], screens, widths=[0.8, 2.3, 3.7], align=["c", "l", "l"], size=9.5)]
    if not rep:
        b += [FIG(F.shot("06_new_patient_filled.png"), "New-patient screen: sample report 01 was read in 0.234 s and its symptoms, findings and history are shown with their page numbers.", F.shot_w(F.shot("06_new_patient_filled.png"), 5.4, 3.9)),
              FIG(F.shot("09_override_modal.png"), "The accept-or-change dialog: a change needs a reason, which is stored with the case.", F.shot_w(F.shot("09_override_modal.png"), 5.4, 3.9))]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("The security checks are limited to the controls the product actually has. Each is covered by an automated test in Section 7.2: a bearer token is required on every route except health, public statistics and login (queue, metrics, samples and /auth/me were each tested without a token, and a garbage token was refused); "
            "a wrong password gives 401; passwords are stored as bcrypt hashes; request bodies are validated by pydantic ranges (for example SpO2 between 50 and 100, heart rate between 20 and 250), so implausible vitals are refused with 422; uploads are capped at 15 MB and an empty or unreadable file is refused; "
            "the sample-file route resolves the path and refuses anything outside the sample folder (a `../` path gave 404); and all database access goes through the SQLAlchemy ORM, so there is no string-built SQL."),
          TAB("Security checks and known gaps.", ["Area", "What was checked", "Known gap"],
              [["Authentication", "Queue, metrics, samples and /auth/me tested without a token; wrong password and garbage token refused", "Default JWT secret `dev-secret-change-me` when JWT_SECRET is unset; PyJWT warns that the 22-byte key is below the recommended 32; tokens last 12 h with no revocation"],
               ["Authorisation", "Two demo roles exist (clinician, admin)", "Roles are not enforced differently on any route: any signed-in user can read every patient and override any priority"],
               ["Input handling", "Pydantic ranges, 15 MB cap, empty-file check, unsupported-file check, path-traversal guard", "No fuzzing; no check that an uploaded PDF is free of malicious content beyond the parsers' own handling"],
               ["Transport", "None", "Plain HTTP on localhost; CORS fixed to the two localhost origins; no HTTPS"],
               ["Abuse", "None", "No rate limiting, no lock-out after failed logins"],
               ["Data protection", "Passwords hashed", "Patient data stored unencrypted in SQLite; no audit trail beyond the override log; demo passwords are seeded"]],
              widths=[1.2, 2.8, 2.8], align=["l", "l", "l"], size=9.2),
          P("The adversary model of these checks is a casual or faulty client. No penetration test, dependency audit or review against a health-data regulation was done, and the product holds no real patient data. It must not be exposed to a network or fed real records in this state.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          P(f"Validation asks whether the system behaves sensibly at the edges of its input space. The report reader was stressed with {st['cases']} short fragments written by the developers for this check (`scripts/extract_stress.py`), "
            f"covering eight kinds of wording, with {st['expected_flags']} flags that a clinician would tick. The fragments are not independent clinical text and were written knowing the reader, so the figures are a probe, not an accuracy estimate. "
            f"Overall precision was **{F.pct(st['precision'])}** and recall **{F.pct(st['recall'])}**; {st['cases_read_exactly']} of the {st['cases']} fragments were read exactly."),
          TAB("Report reader on the 40 stress fragments, by kind of wording.", ["Kind", "Fragments", "Expected flags", "Precision", "Recall", "Read exactly"], _cat_rows(),
              widths=[2.3, 0.9, 1.0, 0.8, 0.8, 1.0], align=["l", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("f09_reader_stress_by_category.png"), "Precision and recall of the report reader on the hand-written stress fragments, by kind of wording.", 5.4),
          P("Plain statements, abbreviations, laboratory values and history are read well. The weak spots are specific and were found by reading the misses and the spurious flags:"),
          B("**Negation is incomplete.** \"Afebrile\" matches the fever pattern; \"Chest pain: absent\" (negation after the term) still flags chest pain; and \"Denies syncope but reports chest tightness\" loses the chest pain because the 45-character negation window does not stop at \"but\".",
            "**A pattern is too broad.** \"Haematemesis\" also triggers vomiting, because the vomiting pattern contains \"emesis\".",
            "**OCR damage that splits a word** (\"vomit ing\", \"elevat ion\") defeats the lexicon, although run-ons without spaces are handled.",
            "**Wording outside the lexicon is missed.** Of seven expected flags in five paraphrased fragments (\"cannot catch his breath\", \"crushing pain in the centre of the chest\", \"not responding to voice\") only one was found: recall 0.14. \"Fall at home\" is not recognised as trauma.",
            "**Page handling is correct:** a finding on page 2 is reported with page 2."),
          P("The defects were reported, not repaired, in this release, so that the measured behaviour matches the shipped code. A separate observation concerns the explanation: the `direction` text (\"raises urgency\" or \"lowers urgency\") is derived from the sign of the attribution toward the *predicted* class. "
            "For a predicted priority of 1 that reading is right; for a prediction of priority 5 a positive attribution pushes toward *less* urgency, so the wording is inverted. The bars on the result screen are labelled as attributions toward the model's choice and are correct; the text field in the API is the part that misleads."),
          TAB("Edge cases and how they were checked.", ["Case", "Behaviour", "Checked by"],
              [["Negated finding (\"denies chest pain\")", "No flag", "test_negation_drops_flag"],
               ["Abbreviations (SOB, HTN, DM2, STEMI)", "Mapped to flags", "test_abbreviations; stress set"],
               ["OCR run-ons (\"shortnessofbreath\")", "Found", "test_ocr_run_on_words"],
               ["Normal laboratory values", "No flag", "test_normal_labs_do_not_set_flags"],
               ["Empty upload; unsupported file type", "400; 422", "test_extract_rejects_empty_and_unsupported"],
               ["Implausible vitals (SpO2 20); unknown arrival mode", "422", "test_create_patient_validates_vitals"],
               ["Change of priority without a reason; priority 9", "422", "test_create_patient_and_override_flow; test_override_priority_out_of_range"],
               ["Unknown patient id", "404", "test_missing_patient_is_404"],
               ["Patient with no report at all", "Model runs on vitals only (every report flag 0); accuracy falls to about " + F.pct(F.rob_row(1.0)["accuracy"], 0) + " in the synthetic experiment", "Section 8.8; the API accepts it by construction, no dedicated API test"],
               ["Scanned image, first use of OCR", "A few seconds while the engine loads", "Timing in Section 7.7"],
               ["Multi-page PDF with no text layer", "Falls back to OCR on the first embedded image", "**Not tested** (no such sample exists)"],
               ["Upload above 15 MB", "Specified as 413", "**Not tested** (limit is in the code only)"],
               ["Concurrent users; long sessions", "Not specified", "**Not tested**"]],
              widths=[2.6, 2.3, 1.9], align=["l", "l", "l"], size=9.2),
          P(f"Model validation, the other kind of validation, is done by repetition rather than by single runs: the shipped recipe was retrained on five other train/test splits and gave a mean accuracy of {F.pct(F.SEEDS['accuracy_mean'], 2)} (standard deviation {F.pct(F.SEEDS['accuracy_std'], 2)}), "
            f"and 5-fold cross-validation of the gradient-boosted model gave {F.pct(F.CV5['XGBoost (shipped config)']['mean'], 2)} (standard deviation {F.pct(F.CV5['XGBoost (shipped config)']['std'], 2)}); the shipped split ({F.pct(F.ACC, 2)}) is a below-average draw (Chapter 8). The test split is never used for fitting or calibration.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P("Latency was measured over HTTP against a running server on 127.0.0.1 (the name `localhost` adds about two seconds of IPv6 fall-back on this Windows machine and would have inflated every figure) with a scratch database. "
            "Each call was repeated 10 to 50 times after a warm-up, using one patient report (sample 01) and one scan (sample 09). The table gives the median and the 95th percentile."),
          TAB("API latency over HTTP on 127.0.0.1 (milliseconds).", ["Call", "Median", "95th percentile", "Repetitions"], _lat_rows(), widths=[3.7, 0.9, 1.3, 0.9], align=["l", "r", "r", "r"], size=9.5),
          FIG(F.fig("f10_latency.png"), "Median and 95th-percentile latency of the API calls; a scanned image costs about two orders of magnitude more than a text PDF because of OCR.", 6.0),
          P(f"Three observations follow. First, with a text PDF the whole path from upload to priority takes about {F.LAT['flow_pdf_then_triage']['median_ms']:.0f} ms (median), of which the model with SHAP is about {F.LAT['create_patient']['median_ms']:.0f} ms; the database write, the queue and the PDF writer are each around 10 to 20 ms or less. "
            f"Second, a PNG scan costs a median of {F.LAT['extract_scan_png']['median_ms'] / 1000:.1f} s because the OCR engine runs on the CPU; the complete scan-then-triage flow took {F.LAT['flow_scan_then_triage']['median_ms'] / 1000:.1f} s. "
            f"Third, the bcrypt check makes login the slowest cheap call ({F.LAT['login']['median_ms']:.0f} ms), which is intended."),
          P(f"The offline end-to-end timing of the 12 generated sample reports (`ml/eval.py`) gave a mean of {F.E2E['mean']:.3f} s per patient, a median of {F.E2E['median']:.3f} s and a maximum of {F.E2E['max']:.3f} s; the mean is dominated by the four scans. "
            f"The model alone took about {F.MODEL_SEC * 1000:.3f} ms per patient in a batch of {F.N_TEST:,} and {F.TRAIN_SEC:.2f} s to train. Two cold-start costs are real: in a fresh process the first SHAP call took 11.7 s (the explainer is built on first use) and the first scan took 7.6 s to read (the OCR engine loads on first use). "
            "The server warms both in its start-up code, and the measurements above are taken after that warm-up. "
            "The performance page of the console shows a live average per patient, 0.30 s in the captured session, which mixes PDF and scan cases and so is not comparable with the table."),
          P("What the measurements do not cover is throughput under concurrent load, memory use, a database larger than a few dozen rows, and any network between the browser and a remote server.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance testing"),
          P("No user acceptance test was held. There was no test group, no questionnaire and no acceptance criteria agreed with a clinician, and this chapter does not claim one; triage is a clinical task and no clinician took part. "
            "What was done instead is a scripted walk-through by the project team of the complete journey on the demo data: sign in, choose a sample report, read it, enter or confirm the vitals, assign a priority, read the explanation, change the priority with a reason, watch the queue reorder, download the summary and open the performance page. "
            "Every step produced the expected screen (Section 7.4)."),
          P("The walk-through also exposed usability points that a real acceptance test would be expected to find. The performance page shows 69.4 % beside a banner that says the data are synthetic; a reader who skips the banner will over-trust the figure. "
            "The confidence shown for the STEMI sample is 100 %, which invites trust that Chapter 8 does not support for the most urgent class (recall 43.9 % for priority 1). And a clinician cannot correct a misread report finding in the interface: the extracted items are read-only, so a wrong one can only be repaired by replacing the file or re-entering the case.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Defects and observations from testing"),
          TAB("Findings of the test and measurement runs.", ["No.", "Finding", "Consequence"],
              [["1", "Negation scope ignores \"but\"; \"afebrile\" and \"absent\" are not treated as negation; \"haematemesis\" triggers vomiting", "Documented; one expected-failure test added; code not changed in this release"],
               ["2", f"Reader recall is {F.pct(st['recall'])} on the stress fragments but 100 % on the generated samples", "The 100 % describes reports written with the lexicon in view; the lower figure is the more honest guide"],
               ["3", "The API `direction` wording is inverted when the predicted priority is 4 or 5", "Documented in Section 7.6; the on-screen bars are correct"],
               ["4", f"High-risk (P1 or P2) cases are found with recall {F.pct(F.SAFE['high_risk_recall'])}; P1 recall is {F.pct(F.REC[0])}", "A clinician must review every priority; a lower alarm threshold is listed as future work (Chapter 8)"],
               ["5", "Logistic regression scores higher than the shipped gradient-boosted model on the synthetic data", "Reported as a finding in Chapter 8; the design was not altered to hide it"],
               ["6", "First SHAP call and first OCR call are slow (seconds) after a cold start", "Both are warmed when the server starts"],
               ["7", "Default JWT secret, no HTTPS, no rate limiting, no role separation", "Documented as limits; the product is a demonstrator"],
               ["8", "`scripts/download_data.py` and the fresh-environment `setup.bat` path were never run", "Listed under what was not tested"]],
              widths=[0.5, 3.7, 2.6], align=["c", "l", "l"], size=9.2)]

    # ------------------------------------------------------------------ 7.10
    b += [H2("7.10 Limits of the testing done"),
          P("The results above support the claims of this report, but they have limits that the reader should know:"),
          B("**One machine, one operating system.** All timings come from a single Intel i5-12500 computer running Windows 11 with CPU-only inference; no other operating system, browser other than Chromium, or Python version was tested.",
            "**No real patient data and no real scans.** Every model test uses synthetic records, and the only images read are the four generated PNG scans. Real scans (skew, stamps, handwriting, poor contrast) were never tried.",
            "**The reader tests are developer-written.** The 12 generated reports and the 40 fragments were written with the reader in mind; no independent clinical text was used.",
            "**No load, soak or concurrency testing,** no memory measurement and no test with more than a few dozen stored patients.",
            "**No security audit.** The checks in Section 7.5 are functional; no penetration test, dependency audit or fuzzing was done.",
            "**No user study.** No clinician has used the system; usability, trust and workload effects are unknown.",
            "**Front-end components are not unit-tested.** The React console was verified by the screenshot walk and the responsive script only.",
            "**Not run in this session:** the fresh-virtual-environment `setup.bat` path, `scripts/download_data.py` (the route to a real dataset), `scripts/check_responsive.py` and `npm run build`."),
          TAB("What was and was not tested.", ["Area", "Tested", "Not tested"],
              [["Report reading", "Text PDFs, 4 generated scans, 40 stress fragments", "Real scans, handwriting, non-English text, image-only multi-page PDFs"],
               ["Triage model", "Synthetic hold-out, 5 splits, 5-fold CV, 8 model types, calibration, robustness", "Real patient data, any other population, prospective use"],
               ["Explanation", "Ordering, labelling, hiding rule; global importance against the known generating rule", "Whether clinicians find the explanation useful or correct"],
               ["API and database", "16 component tests, 17 smoke checks, latency", "Concurrency, large data volumes, backups"],
               ["Interface", "12 screens with data, responsive script (at build time)", "Screen readers, users with disabilities, other browsers"],
               ["Security", "Token, validation, upload and path checks", "Penetration test, HTTPS, rate limits, role separation, regulation"]],
              widths=[1.4, 2.8, 2.6], align=["l", "l", "l"], size=9.3)]
    # ------------------------------------------------------------------ 7.11
    b += [H2("7.11 Requirements traceability"),
          P("Chapter 4 numbers the functional requirements FR-1 to FR-12 and the non-functional requirements NFR-1 to NFR-11. The table shows which test or measurement covers each and what the outcome was. "
            "A requirement is marked *Pass* only where the evidence in this chapter supports it; the model-quality requirements hold on synthetic data only."),
          TAB("Requirements against the evidence in this chapter.", ["Requirement", "Evidence", "Outcome"], _trace_rows(), widths=[0.9, 4.1, 1.8], align=["c", "l", "l"], size=9.0)]
    return b
