"""Chapter 7: System testing. Counts come from experiments/lablens/test_run.json, metrics.json and api_latency.json."""

import os

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from . import facts as F

# tests/test_lablens.py grouped by what they check (the groups sum to the 36 collected tests)
UNIT_GROUPS = [
    ["Status rule", "`classify_result` at the boundaries (5 and 10 inside 5-10, 4.99, 10.01), one-sided limits, missing value or range; `summarize_statuses`", 11],
    ["Row parsing", "two-sided range, one-sided limits (`<100`, `>40`), header lines skipped, duplicate rows dropped, report date, patient-name label", 6],
    ["Name matching", "OCR-style noise (\"Haemogl0bin\") snapped to Hemoglobin; an unseen name kept in title case", 2],
    ["Upload validation and OCR entry", "text layer of a generated PDF read, unsupported extension, empty file, oversize file, corrupt PDF", 5],
    ["Explanations", "disclaimer present and wording non-diagnostic, generic text for an unseen test, fall-back when no API key is set", 3],
    ["Pipeline and database", "full pipeline stores LOW/NORMAL/HIGH correctly and an insight for every abnormal row; unreadable report marked Failed; cascade delete; dashboard totals and the critical heuristic", 4],
    ["HTTP API", "login required and wrong password refused; tampered token refused; upload, detail, trend, compare and insights end to end; bad upload and missing report; sample seeding only into an empty library", 5],
]


def _opt_fig(name, caption, width=5.4):
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def blocks():
    t = F.TESTS
    py, sm = t["pytest"], t["smoke_test"]
    ex = F.EXTRACTION
    ov = ex["overall"]
    fk = ex["failure_kinds"]
    lay = ex["per_layout"]
    lat = F.LATENCY
    api = F.API_LAT["endpoints"]
    cls = F.CLASSIF
    assert sum(g[2] for g in UNIT_GROUPS) == py["passed"], "test groups no longer add up"
    unit_err = fk.get("field error: unit", 0) + fk.get("field error: name,unit", 0) + fk.get("field error: name,unit,range", 0) + fk.get("field error: name,unit,range,status", 0)
    name_err = sum(v for k, v in fk.items() if k.startswith("field error") and "name" in k)
    scale = lat["field_extraction_scaling_by_rows"]
    return [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing strategy"),
        P("The pipeline is a chain of pure functions around one database, so the strategy is to test each stage on its own with small inputs, then the chain with the "
          "database, then the HTTP layer, and finally the running product in a browser. Every test that touches storage points SQLAlchemy at a temporary SQLite file, "
          "so the real library in `data/medical_lab.db` is never read or changed. Input documents are generated on the fly as PDFs with PyMuPDF, which keeps the tests "
          "free of any real patient data."),
        TAB("Test layers", ["Layer", "Tool", "Scope", "Result"], [
            ["Unit and integration", "pytest (`tests/test_lablens.py`)", "status rule, parser, name matcher, upload validation, explanations, pipeline with database", f"{py['passed'] - 5} passed"],
            ["HTTP API", "pytest with the FastAPI test client", "authentication, upload, detail, trend, compare, insights, sample seeding", "5 passed"],
            ["Randomised property check", "`scripts/run_experiments.py`", f"{cls['random_cases']:,} random value and range combinations against an independently written rule", f"{cls['disagreements_with_reference_rule']} disagreements"],
            ["End-to-end smoke test", "`scripts/smoke_test.py`", "temporary copy of the product served on a spare port; API flow, then a browser flow", f"{sm['api_checks_passed']} API and {sm['browser_checks_passed']} browser checks passed"],
            ["Corpus experiments", "`scripts/run_experiments.py`", "120 generated reports in 8 layouts, 1,680 labelled rows", "Chapter 8"],
            ["Interface checks", "`scripts/ui_check.py` (Playwright)", "three widths, two themes, drawer, keyboard, reduced motion, error states", "script provided; not re-run for this report"],
        ], widths=[1.4, 1.5, 2.3, 1.1], size=9),
        H2("7.2 Unit and integration tests"),
        P(f"`python -m pytest tests -q` collects {py['passed']} tests and all pass in about {py['seconds']:.0f} seconds. They are written against behaviour that the interface "
          "depends on, not against implementation details, and each group is listed below."),
        TAB("Groups of the 36 automated tests", ["Group", "What is checked", "Tests"], UNIT_GROUPS, widths=[1.5, 4.2, 0.6], size=9, align=["l", "l", "c"]),
        P("One test expectation was wrong and was corrected. The dashboard test first expected one critical result for a report with a creatinine of 2.4 mg/dL; the run "
          "reported two, because the LDL cholesterol of 152 mg/dL is also above 1.5 times its upper limit of 100. The expectation was changed to two and the reason written "
          "beside it. A second finding concerns the test data, not the product: an en dash written into a generated PDF with the built-in font came back from text "
          "extraction as a middle dot, so the `mixed_sep` layout uses a hyphen, the word `to` or no spaces. The parser's en-dash and em-dash patterns were therefore "
          "never exercised on a real file."),
        H2("7.3 API and smoke tests"),
        P(f"The smoke test copies the product modules into a temporary folder, starts its own server on port 8398 and never touches the real database. Its API part makes "
          f"{sm['api_checks_passed']} checks in the order below, and it prints \"{sm['result']}\" when all pass."),
        TAB("Smoke-test checks", ["Area", "Checks"], [
            ["Service and configuration", "health; configuration holds the disclaimer and formats"],
            ["Access control", "protected route refuses an anonymous call; wrong password refused; demo login; current user"],
            ["Empty library", "empty dashboard; trend and compare empty states"],
            ["Sample data", "five sample reports seeded through the real pipeline; seeding twice refused"],
            ["Reading", "dashboard totals; report list newest first; report detail with insights; unknown report gives 404"],
            ["Analysis", "trend ordered by upload and increasing; comparison change equals second minus first; comparing a report with itself refused; insights cover every abnormal result"],
            ["Upload and failure", "PDF upload processed; unsupported file, empty file give readable errors; a failed report keeps its error message"],
            ["Deletion", "delete; deleting twice gives 404"],
            ["Browser (7 checks)", "an anonymous visit is sent to the sign-in page; the trend chart renders from the API; the comparison chart renders; insight cards render; a wrong file type is rejected in the browser; Escape closes the delete dialog; no console errors"],
        ], widths=[1.6, 4.7], size=9.5),
        H2("7.4 Randomised check of the status rule"),
        P(f"The rule that decides LOW, NORMAL and HIGH is the core of the product, so it was checked beyond hand-picked cases. {cls['random_cases']:,} random combinations of a "
          "value and a range were generated, with each limit independently present or absent and values from -5 to 250, and the status from `classify_result` was compared "
          f"with an independently written rule. There were {cls['disagreements_with_reference_rule']} disagreements. The boundaries behave as documented: with a range of 5 to 10, "
          f"the values 5 and 10 are {cls['boundary_5_in_5to10']}, 4.99 is {cls['just_below']} and 10.01 is {cls['just_above']}. This shows that the code implements the stated rule; "
          "it does not show that the rule is clinically sufficient."),
        H2("7.5 Validation on the generated corpus"),
        P(f"Chapter 8 reports the full results. For testing purposes the corpus acts as a regression suite with known answers: of {ov['reports_rows']:,} labelled rows the parser "
          f"returns {ov['predicted_rows']:,} rows with a precision of {F.f3(ov['row_precision'])} and a recall of {F.f3(ov['row_recall'])}; of the rows it finds, the range is right in "
          f"{F.pct(ov['range_acc'])} and the status in {F.pct(ov['status_acc'])}. Only {F.pct(ov['exact_row_rate'])} of all labelled rows are completely right (name, unit, range and "
          "status together) because of the defects below."),
        H2("7.6 Edge cases and defects found"),
        P("The experiments exposed five defects in the product. They are reported here as test findings; the product code was **not** changed during the documentation work, "
          "so each one is still present and is listed as a limitation in Chapter 10."),
        TAB("Defects found by testing", ["No.", "Defect", "Evidence", "Effect"], [
            ["D1", "A collection date written `dd-mm-yyyy` on a line that starts with a word is parsed as a result row (\"Sample Collected\", value 12, range -4 to 2026)",
             f"read as a row in all 56 reports that carry a `dd-mm-yyyy` date (the `dd/mm/yyyy` form is dropped because it has no range or unit); the {ov['false_positive_rows']} false-positive rows are 55 date-line rows plus 2 others (in one report the date value 12 equalled a real RDW value of 12, so the date row was matched to RDW and the real RDW row counted as extra; the other is a mis-read name row)", "A meaningless row appears with status NORMAL and pollutes the test list"],
            ["D2", "A table whose cells are extracted one per line yields no row",
             f"`tabular` layout: precision {F.f3(lay['tabular']['row_precision'])}, recall {F.f3(lay['tabular']['row_recall'])}; {fk.get('missed row', 0)} missed rows in all, 210 of them from this layout", "The report is marked Failed (\"no recognizable lab test rows\")"],
            ["D3", "The unit list is incomplete and a flag letter between value and unit hides the unit",
             f"{unit_err} unit errors; unit accuracy {F.pct(lay['flag']['unit_acc'])} in the `flag` layout against {F.pct(lay['plain']['unit_acc'])} in `plain`; missed units include mg/L, umol/L, ng/dL, uIU/mL", "Unit shown empty; range and status are still right"],
            ["D4", "A name that contains a dictionary name is snapped to it",
             f"\"Sodium Bicarbonate\" becomes \"Sodium\"; {name_err} name errors; unseen-test name accuracy {F.pct(ov['name_acc_ood_tests'])} against {F.pct(ov['name_acc_dict_tests'])} for dictionary tests", "Wrong test name, so the row joins the wrong trend"],
            ["D5", "Heavy name noise defeats the matcher",
             f"`ocr_noise` layout: name accuracy {F.pct(lay['ocr_noise']['name_acc'])}; at 20 % character noise {F.pct(F.NAMES['noise']['0.2']['tfidf_0.55'])} against {F.pct(F.NAMES['noise']['0.2']['difflib_0.60'])} for an edit-distance baseline", "Corrupted names stay unmatched or snap to a wrong test"],
        ], widths=[0.4, 2.1, 2.4, 1.4], size=8.5),
        P("Other edge cases that were tested and handled correctly: a value of exactly a range limit (NORMAL), a result with only an upper or only a lower limit, a result "
          "with neither (UNKNOWN), duplicate lines, an empty or oversize file, an unsupported extension, a corrupt PDF (Failed with a message), a PDF without any lab row "
          "(Failed with a message), deleting a report that was already deleted (404) and comparing a report with itself (400)."),
        *_opt_fig("fig_failure_kinds.png", "Kinds of extraction error found on the generated corpus", 5.0),
        H2("7.7 Performance testing"),
        P(f"Timings were taken on the development machine ({F.TESTS['machine']['cpu']}, {F.TESTS['machine']['ram_gb']} GB RAM, Windows 11, no GPU) with a one-page, 14-row text PDF of "
          f"{lat['pdf_bytes']:,} bytes. Stage times are medians of 100 runs; the end-to-end pipeline, which includes the SQLite writes, is the median of {lat['end_to_end_pipeline_with_db']['n']} runs. "
          "HTTP timings use `127.0.0.1`, because a hostname lookup of `localhost` adds seconds on this machine."),
        TAB("Pipeline stage latency (14-row report)", ["Stage", "Median (ms)", "95th percentile (ms)", "Maximum (ms)"], [
            ["PDF text layer (PyMuPDF)", f"{lat['text_layer_extraction']['median_ms']:.2f}", f"{lat['text_layer_extraction']['p95_ms']:.2f}", f"{lat['text_layer_extraction']['max_ms']:.2f}"],
            ["Row parsing and name matching", f"{lat['field_extraction']['median_ms']:.2f}", f"{lat['field_extraction']['p95_ms']:.2f}", f"{lat['field_extraction']['max_ms']:.2f}"],
            ["Classification", f"{lat['classification']['median_ms']:.2f}", f"{lat['classification']['p95_ms']:.2f}", f"{lat['classification']['max_ms']:.2f}"],
            ["Explanations for all abnormal rows", f"{lat['insight_generation_all_abnormal']['median_ms']:.2f}", f"{lat['insight_generation_all_abnormal']['p95_ms']:.2f}", f"{lat['insight_generation_all_abnormal']['max_ms']:.2f}"],
            ["End to end with database writes", f"{lat['end_to_end_pipeline_with_db']['median_ms']:.1f}", f"{lat['end_to_end_pipeline_with_db']['p95_ms']:.1f}", f"{lat['end_to_end_pipeline_with_db']['max_ms']:.1f}"],
        ], widths=[2.6, 1.2, 1.5, 1.0], size=9.5, align=["l", "r", "r", "r"]),
        P(f"Parsing time grows linearly with the number of rows: {scale['14']['median_ms']:.1f} ms for 14 rows, {scale['50']['median_ms']:.1f} ms for 50, {scale['100']['median_ms']:.1f} ms for 100 and "
          f"{scale['200']['median_ms']:.1f} ms for 200, about 0.6 ms per row, mostly the TF-IDF transform of the name. The abstract asks for less than 10 seconds per report; for a digital "
          f"PDF the pipeline needs a median of {lat['end_to_end_pipeline_with_db']['median_ms']:.0f} ms, so the target is met by a wide margin. For scanned images the time depends on Tesseract and "
          "was **not measured**."),
        *_opt_fig("fig_latency_stages.png", "Median latency of each pipeline stage", 5.0),
        TAB("HTTP endpoint latency on 127.0.0.1", ["Endpoint", "Median (ms)", "95th percentile (ms)", "Runs"],
            [[k.replace("POST /api/reports (PDF upload)", "POST /api/reports (PDF upload)"), f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", str(v["n"])] for k, v in api.items()],
            widths=[2.8, 1.2, 1.5, 0.8], size=9.5, align=["l", "r", "r", "r"]),
        P(f"Reads take between {min(v['median_ms'] for k, v in api.items() if k.startswith('GET'))} and {max(v['median_ms'] for k, v in api.items() if k.startswith('GET'))} ms; the upload, which runs the pipeline, takes a median of "
          f"{api['POST /api/reports (PDF upload)']['median_ms']:.0f} ms. The insights route is the slowest read because it loads every abnormal result and its insight one query at a time. "
          f"Loading the five sample reports takes {F.API_LAT['seed_five_reports_s']:.2f} s. No test with many simultaneous users was run."),
        H2("7.8 Security tests"),
        TAB("Security checks", ["Check", "Expected", "Result"], [
            ["Call a protected route with no token", "401", "Passed (pytest and smoke test)"],
            ["Call a protected route with the last characters of a valid token changed", "401", "Passed (pytest)"],
            ["Sign in with a wrong password", "401 and a message", "Passed (pytest and smoke test)"],
            ["Upload a `.txt` file", "Failed report with the message \"Unsupported file format\"", "Passed"],
            ["Upload an empty file and a file above 15 MB", "Readable error, nothing stored as results", "Passed"],
            ["Upload a corrupt PDF", "Failed report, no crash", "Passed"],
            ["Read or delete a report that does not exist", "404 with a message", "Passed"],
        ], widths=[3.0, 2.0, 1.3], size=9.5),
        P("These tests cover the controls of Section 6.11. They are functional checks of the code paths, not a penetration test, and expiry of the token after 12 hours was "
          "not exercised by a test."),
        H2("7.9 Interface checks"),
        P("The browser part of the smoke test was run and passed (Section 7.3). The separate script `scripts/ui_check.py` drives the running product in Playwright and checks that "
          "no page overflows horizontally at 360, 768 and 1440 pixels in both themes; that the navigation drawer opens, closes with Escape and closes after a link is chosen; that "
          "the light theme survives a reload through `localStorage`; that the landing page shows a static hero and no WebGL canvas when reduced motion is requested; that the first "
          "tab stop is the skip link, a focused control has a visible ring and every input has a label; and that a stopped backend produces an error message with a Try again "
          "button that recovers. The script was written during the interface build; it was **not re-run** while preparing this report, so its results are not quoted."),
        H2("7.10 User acceptance"),
        P("No acceptance test with real users, patients or clinicians was carried out. The interface was exercised only by the developers. A usability study with people who "
          "do not know laboratory reports, and a review of the explanation texts by a clinician, are the most important missing evidence and are listed as future work."),
        H2("7.11 Limits of the testing"),
        B("**Synthetic data.** All reports are generated or invented; no real laboratory report, and no manually labelled set of real reports, was tested, so the extraction "
          "figures describe the parser on the layouts the generator can produce, not on reports in general.",
          "**OCR path untested.** Tesseract is not installed on the test machine, so scanned images and scanned PDFs, and the OpenCV preprocessing in front of them, were not run end to end.",
          "**Language-model path untested.** No API key was available, so the optional rewording of explanations was never exercised.",
          "**Ground truth shares the rule.** The expected status of a corpus row is computed with the same comparison as the code, so status accuracy shows propagation of parsing errors only.",
          "**One machine, one user.** Timings are from one computer with no other load; concurrent access and a large database were not tested.",
          "**No clinical validation.** The tests show that the software does what its rules say; they say nothing about whether the explanations are medically adequate."),
    ]
