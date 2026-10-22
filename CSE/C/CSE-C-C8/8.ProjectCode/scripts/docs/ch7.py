"""Chapter 7: System Testing."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

TBF = "[to be filled]"
SECTIONS9 = ["summary", "introduction", "related_work", "methodology", "experiments", "results", "discussion", "conclusion", "references"]


def lat(*keys, fmt="{:.0f}", default=TBF):
    cur = F.LATENCY
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    try:
        return fmt.format(cur)
    except (ValueError, TypeError):
        return default


def _val(x, fmt="{}"):
    return TBF if x is None else fmt.format(x)


def pytest_result():
    return "Pass" if F.PYTEST_PASSED is not None and F.PYTEST_PASSED == F.PYTEST_TOTAL else TBF


def smoke_result():
    return "Pass" if F.SMOKE_TOTAL is not None and F.SMOKE_PASSED == F.SMOKE_TOTAL else TBF


def stage_rows():
    rows = []
    for key, label in (("PDF extraction", "PDF extraction"), ("Feature extraction", "Feature extraction"), ("Decision signal", "Decision signal (classifier)"),
                       ("Local AI review (3 steps)", "Local AI review (3 steps)"), ("Literature (OpenAlex)", "Literature (OpenAlex, network)"), ("Reviewer matching", "Reviewer matching (6 reviewers)")):
        d = lat("pipeline_stages", "demo", key, fmt="{:,.0f}")
        s = lat("pipeline_stages", "survey_30_pages", key, fmt="{:,.0f}")
        rows.append([label, d, s])
    rows.append(["**Total**", lat("pipeline_stages", "demo", "_total_ms", fmt="{:,.0f}"), lat("pipeline_stages", "survey_30_pages", "_total_ms", fmt="{:,.0f}")])
    return rows


def http_rows():
    rows = []
    for key, label in (("health", "GET `/api/health`"), ("reviewers_list", "GET `/api/reviewers`"), ("model_metrics", "GET `/api/model/metrics`"), ("analyses_list", "GET `/api/analyses`")):
        rows.append([label, lat("http_api", key, "n"), lat("http_api", key, "median_ms", fmt="{:.1f}"), lat("http_api", key, "p95_ms", fmt="{:.1f}")])
    for key, label in (("analyze_demo_3_pages", "POST `/api/analyze`, 3-page demo paper (AI review off)"), ("analyze_survey_30_pages", "POST `/api/analyze`, 30-page survey (AI review off)")):
        rows.append([label, lat("http_api", key, "n"), lat("http_api", key, "median_ms", fmt="{:,.0f}"), f"max {lat('http_api', key, 'max_ms', fmt='{:,.0f}')}"])
    return rows


def real_rows():
    names = ["Demo paper (fixture)", "Survey of AI peer review", "Graph-reasoning review paper", "IEEE Access base paper"]
    rows = []
    for nm, r in zip(names, F.REAL):
        missing = [s for s in SECTIONS9 if s not in r["sections_detected"]]
        rows.append([nm, str(r["pages"]), f"{r['words']:,}", str(len(r["sections_detected"])) + " / 9", ", ".join(missing) or "none", str(r["references_detected"]),
                     f"{r['structural_score']:.1f}", f"{r['ml_label']} ({r['ml_confidence']:.2f})"])
    return rows


def _full_blocks():
    L = F.LOC
    M = F.MINILM
    T = F.TFIDF
    S = F.SHIPPED
    sc = M["scaling_ms"]
    cf = M["conflict"]
    kinds = cf["detected_by_kind"]
    literal = sum(v["detected"] for k, v in kinds.items() if not k.startswith("paraphrased") and k != "first name only")
    literal_n = sum(v["n"] for k, v in kinds.items() if not k.startswith("paraphrased") and k != "first name only")
    miss = sum(v["n"] - v["detected"] for v in kinds.values())
    miss_n = sum(v["n"] for k, v in kinds.items() if k.startswith("paraphrased") or k == "first name only")
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    b += [H2("7.1 Testing strategy"),
          P(f"Testing covers five layers. Single functions (extraction, features, matching, conflict detection, the classifier service) are tested in isolation; the API is tested in-process against the real application "
            f"object; the whole stack is exercised by a smoke test that drives a running server over HTTP; the trained and rule-based components are *measured* on held-out data and probe sets "
            f"(Chapter 8 reports those measurements); and the web interface is walked in a real browser while the screenshots are captured. The automated tests are in the repository (`tests/`, "
            f"{L['tests']} lines, and `scripts/smoke_test.py`) and run with one command each. They test behaviour, not the scientific quality of the assessments: that quality can only be judged by "
            f"people, and no such judgement was collected (Section 7.10)."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"],
              [["Unit", "PDF extraction, feature extraction, matching and conflict logic, decision-signal service", "pytest, in-process", f"{F.PYTEST_TOTAL} tests in the suite; {pytest_result()}"],
               ["Integration", "Health route, reviewer create / update / delete, full analysis of the demo PDF through `/api/analyze`", "pytest + FastAPI `TestClient`", pytest_result()],
               ["Functional", "Reviewer CRUD and CSV, bad uploads, analysis, history, export, CORS, web app served", "`scripts/smoke_test.py` against the running servers", f"{_val(F.SMOKE_PASSED)} of {_val(F.SMOKE_TOTAL)} checks pass"],
               ["Security and input validation", "Upload rules, field limits, error messages", "Smoke test plus probes run for this report (Section 7.5)", "See Section 7.5"],
               ["Measured experiments", "Decision model, baselines, five splits, matching probe set, conflict injection, scaling, four real PDFs", "`scripts/measure_metrics.py`", "Numbers in Chapter 8"],
               ["Browser walk", "Every screen in dark and light theme, a real analysis, console, page and request errors", "Playwright with the installed Chrome (`scripts/capture_screens.py`)", "Screenshots in Chapter 8; the script lists any console, page or request error it sees"]],
              widths=[1.2, 2.5, 1.6, 1.0], align=["l", "l", "l", "c"], size=9.5),
          P("Before the documentation work the project already contained seven pytest tests and a smoke script; no tests were added to the product code for this report, and the numbers below are those of the existing "
            "suite re-run on the final code. The evaluation experiments were written for this report and live in `scripts/measure_metrics.py` and `scripts/eval_data.py`.")]

    b += [H2("7.2 Unit testing"),
          P("Each of the seven pytest functions is a real check of behaviour; none is a placeholder. They are listed with what they actually assert."),
          TAB("Automated pytest cases", ["ID", "Test function", "Input", "Assertions", "Result"],
              [["T1", "`test_pdf_extraction`", "The demo PDF is regenerated by `make_demo_pdf` and parsed", "File exists; at least one page and more than 200 words; a methodology or experiments section is detected", pytest_result()],
               ["T2", "`test_features`", "A synthetic document with introduction, methodology and 8 references", "`has_methodology` is true; structural score within 0-100; keywords or words present", pytest_result()],
               ["T3", "`test_matching_and_conflict`", "A language-processing paper against an NLP reviewer and a security reviewer; then a reviewer whose conflict term occurs in the text", "NLP reviewer ranked first with a higher score; `breakdown` and `explanation` present; conflict flag true", pytest_result()],
               ["T4", "`test_ml_predict_service`", "A short title and summary", "Label is accept, borderline, reject or `unavailable`", pytest_result()],
               ["T5", "`test_api_health`", "GET `/api/health`", "Status 200 and product `PeerScope`", pytest_result()],
               ["T6", "`test_reviewer_crud`", "POST, PUT, DELETE of a temporary reviewer", "201, 200, 200", pytest_result()],
               ["T7", "`test_pipeline_with_demo`", "The demo PDF posted to `/api/analyze`", "200; more than 100 words extracted; at least one ranked reviewer; strengths listed", pytest_result()]],
              widths=[0.4, 1.5, 1.9, 2.2, 0.6], align=["c", "l", "l", "l", "c"], size=9),
          P(f"The suite ran in {_val(F.PYTEST_SECONDS, '{:.0f}')} seconds. T7 is the slowest because it runs the whole pipeline; when the local language model can be loaded, the three generation steps run on the CPU and the test "
            "takes minutes rather than seconds. One earlier attempt with the model enabled was stopped by the tester after about 40 minutes because the machine had almost no free memory left; the recorded result is "
            "the final run kept in `docs/metrics/tests.json`. Two of the tests (T2 and T4) are loose by design: they verify that the code runs and "
            "returns values in range, not that the values are right, which is why the accuracy of the classifier and of the matcher is measured separately."),
          P("The deterministic logic that most affects the output, namely the structural score, the review rules and the conflict test, is covered by the experiments in Section 7.8 rather than by many small unit tests. "
            "That is a gap in the test suite and is listed among the limits in Section 7.10.")]

    b += [H2("7.3 Integration testing"),
          P("Integration is exercised in three ways. T7 sends a real PDF through the full request path (upload validation, extraction, features, classifier, review, literature, matching, storage, response) and checks the "
            "result. T5 and T6 call the routes through the same application object. The smoke test (next section) repeats the paths over a real HTTP connection, where cross-origin handling and file uploads behave as they do "
            "for the browser. The one integration that no automated test covers is the browser itself: the React application was exercised only by the capture script, which clicks through every page and reports "
            "console errors, page errors, failed requests and HTTP responses of 400 or above (other than the deliberate 404 probe).")]

    b += [H2("7.4 Functional testing"),
          P("`scripts/smoke_test.py` needs the API (and, for the last two checks, the web server) to be running. It creates its own reviewers, removes them afterwards and checks the result of every step."),
          TAB("Functional checks of the smoke test", ["ID", "Check", "Expected", "Result"],
              [["S1", "Health route", "200 and product `PeerScope`", smoke_result()],
               ["S2", "Model metrics route", "`accuracy` present", smoke_result()],
               ["S3", "Metrics consistency", "Confusion matrix as large as the label list", smoke_result()],
               ["S4", "Reviewer list", "Non-empty list", smoke_result()],
               ["S5", "Reviewer with empty name", "422", smoke_result()],
               ["S6", "Reviewer create", "201", smoke_result()],
               ["S7", "Reviewer deactivate", "200 and `is_active` false", smoke_result()],
               ["S8", "Reviewer CSV export", "200, header and the new reviewer present", smoke_result()],
               ["S9", "Reviewer CSV import", "200 and `imported` = 1", smoke_result()],
               ["S10", "Clean-up", "Reviewer count back to its initial value", smoke_result()],
               ["S11", "Delete unknown reviewer", "404", smoke_result()],
               ["S12", "Text file posted as a paper", "400 and a message mentioning PDF", smoke_result()],
               ["S13", "File named `.pdf` that is not a PDF", "400", smoke_result()],
               ["S14", "Analyse the demo PDF", "200", smoke_result()],
               ["S15", "Result structure", "`review`, `reviewers`, `literature`, `features` present", smoke_result()],
               ["S16", "Audit data", "Top reviewer has a `breakdown`", smoke_result()],
               ["S17", "Responsible-use text", "Disclaimer mentions a human decision-maker", smoke_result()],
               ["S18", "History", "New analysis in `/api/analyses`", smoke_result()],
               ["S19", "Fetch by id", "200", smoke_result()],
               ["S20", "JSON export", "200 and an attachment header", smoke_result()],
               ["S21", "PDF export", "200 and the bytes start with `%PDF`", smoke_result()],
               ["S22", "Unknown analysis", "404", smoke_result()],
               ["S23", "Web application", "`index.html` with the root element is served", smoke_result()],
               ["S24", "CORS", "The web origin is allowed", smoke_result()]],
              widths=[0.5, 2.3, 2.7, 0.8], align=["c", "l", "l", "c"], size=9.5),
          P(f"The script counts {_val(F.SMOKE_TOTAL)} checks in the recorded run (S23 and S24 are skipped, not failed, if the web server is down), of which {_val(F.SMOKE_PASSED)} passed.")]

    b += [H2("7.5 Security testing"),
          P("The upload path is the only place where untrusted data enter the system, so it received the most attention. The first two rows below are in the smoke test; the others are probes run for this report with the "
            "FastAPI test client on a scratch database and with the AI review switched off. They are not part of the automated suite."),
          TAB("Upload and input validation probes", ["ID", "Input", "Expected", "Observed"],
              [["V1", "Plain-text file named `a.txt`", "400, only PDF accepted", "400 \"Only PDF files are accepted (.pdf).\""],
               ["V2", "Text posted with a `.pdf` name and a PDF content type", "400, header check", "400 \"File does not look like a valid PDF (missing PDF header).\""],
               ["V3", "Zero-byte file `a.pdf`", "400", "400 \"Uploaded file is empty.\""],
               ["V4", "`.pdf` name with content type `image/png`", "400", "400 \"Unexpected file type: image/png. Please upload a PDF.\""],
               ["V5", "21 MB body starting with `%PDF`", "413", "413 \"File too large (21.0 MB). Limit is 20 MB.\""],
               ["V6", "Reviewer with `current_load` 101, `maximum_load` 0 or a 201-character name", "422", "422 with the field and the limit in the message (all three)"],
               ["V7", "CSV with a non-numeric load, and a binary file posted as CSV", "400, nothing stored", "400 \"Malformed reviewer CSV: ...\" (both)"],
               ["V8", "Non-integer analysis id (`/api/analyses/abc`)", "422", "422 integer-parsing message"],
               ["V9", "A stack-trace check: force an unexpected error", "Generic 500 text", "Handler returns `Internal server error.`; analysis failures return \"Paper analysis failed. Try another PDF.\" (by code reading; not forced in a test)"]],
              widths=[0.4, 2.3, 1.3, 2.4], align=["c", "l", "l", "l"], size=9),
          P("These probes show that the validation is consistent and that error messages are short and safe to display. They also show what the validation does *not* do: a file that starts with `%PDF` but is "
            "otherwise corrupt is accepted and returns status 200 with almost no extracted text (the 'very little extractable text' warning applies), and a CSV whose rows have no name is accepted with zero rows imported. "
            "Neither is dangerous, but both would be better as explicit errors. The API has no authentication and allows all origins; no test could pass or fail on that because it is a design decision for a single-user "
            "local tool, and it is stated as a limitation (Chapter 10). No penetration test, fuzzing of the PDF parser or prompt-injection test against the language model was carried out; the risk of hidden instructions "
            "in a PDF is known from the literature [2], [27] and is addressed by design (the language model never changes a score), not by a measured defence.")]

    b += [H2("7.6 Validation and edge cases"),
          TAB("Edge cases", ["ID", "Situation", "Expected behaviour", "Observed"],
              [["E1", "Empty reviewer directory", "Analysis refused with a clear message", "400 \"Reviewer directory is empty. Add reviewers first.\""],
               ["E2", "PDF with a single short sentence of text", "Analysis still returns, with a warning", "200 with the warning \"Very little extractable text was found in this PDF; results are limited.\"; AI review `unavailable`; literature `ok`"],
               ["E3", "Local language model not installed or not downloadable", "Deterministic review shown with the reason", "Observed in the first screenshot session: `llm_status: unavailable` and the note \"Showing deterministic structural review only.\" in the Overview tab"],
               ["E4", "OpenAlex unreachable", "`literature_retrieval_status: unavailable`, no crash", "By code: every exception is caught; not exercised offline in a test. With the network on, three queries returned six works each"],
               ["E5", "Sentence-embedding model not loadable", "TF-IDF fallback, lower accuracy", f"Measured: top-1 {F.f2(T['full_hybrid_shipped_weights']['top1'])} with the fallback against {F.f2(M['full_hybrid_shipped_weights']['top1'])} with MiniLM (Chapter 8)"],
               ["E6", "Classifier artifacts missing", "`model_unavailable`, no guess", "By code reading; the dashboard shows the model state"],
               ["E7", "Classifier trained by a different scikit-learn release", "Fails to load or warns", "Warning of a version mismatch observed when 1.9.0 artifacts were read by 1.9.1; an older release (1.5) could not produce probabilities, so `run.bat` retrains"],
               ["E8", "Reviewer at full load", "Availability 0 and lower score", "Handled by the formula (availability = 0); visible in the audit table"],
               ["E9", "Inactive reviewer (Epsilon)", "Excluded when `active_only` is on", "Excluded from the list by the filter; included in the matching experiments by design"],
               ["E10", "Conflict term in the paper text", "Reviewer penalised and explained", f"All {literal} of {literal_n} literal links injected in the experiment were flagged and the reviewer fell to the bottom of the ranking"]],
              widths=[0.4, 1.7, 1.7, 2.6], align=["c", "l", "l", "l"], size=9)]

    b += [H2("7.7 Performance testing"),
          P(f"Timings were taken on the development machine ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, no GPU). The in-process measurement calls each stage separately on a 3-page demo paper and on a 30-page survey; "
            f"the HTTP measurement calls a running server on `127.0.0.1` (using `localhost` adds about two seconds per call on this machine because of an IPv6 fallback). Loading the embedding model took "
            f"{lat('embedding_model_load_s', fmt='{:.1f}')} s and loading the Qwen model {lat('llm_load_s', fmt='{:.1f}')} s once per server start."),
          TAB("Stage timings of one analysis (milliseconds, in-process)", ["Stage", "Demo paper (3 pages)", "Survey (30 pages)"], stage_rows(),
              widths=[2.8, 1.8, 1.8], align=["l", "r", "r"], size=10),
          P(f"The language-model review dominates: its three generations make up almost the whole time of an analysis, which is by far the largest row of the table (total for the demo paper: {lat('pipeline_stages', 'demo', '_total_ms', fmt='{:,.0f}')} ms). A single generation of 48 tokens took about 15 seconds in a separate probe (roughly 3 tokens per second), so the AI review takes minutes, not seconds; this is the "
            "price of running a 1.5-billion-parameter model in 32-bit precision on a CPU, and it is why the review is labelled as optional and the deterministic review is always shown first."),
          TAB("HTTP latency with the AI review off (milliseconds)", ["Request", "Calls", "Median", "95th percentile / max"], http_rows(),
              widths=[3.2, 0.7, 1.0, 1.5], align=["l", "c", "r", "r"], size=10),
          P(f"Matching time grows linearly with the number of reviewers because every reviewer profile is embedded on every request: with MiniLM the median ranking time is {sc[0]['median_ms']:.0f} ms for {sc[0]['pool']} reviewers, "
            f"{sc[1]['median_ms']:.0f} ms for {sc[1]['pool']}, {sc[2]['median_ms'] / 1000:.1f} s for {sc[2]['pool']} and {sc[3]['median_ms'] / 1000:.1f} s for {sc[3]['pool']}. The TF-IDF fallback needs "
            f"{F.TFIDF['scaling_ms'][3]['median_ms']:.0f} ms for {F.TFIDF['scaling_ms'][3]['pool']} reviewers. A directory of a few dozen reviewers is comfortable; a conference-sized pool would need cached reviewer embeddings, "
            "which the application does not have."),
          FIG(F.fig("f09_matching_scaling.png"), "Median reviewer-ranking time against the size of the reviewer directory.", 4.6)]

    b += [H2("7.8 Experiments used as tests"),
          P("Some behaviours can only be checked by running the component on data and comparing with an expectation. They are listed here as test cases; their numbers are discussed in Chapter 8."),
          TAB("Measured test cases", ["ID", "Case", "Expected", "Observed"],
              [["X1", "Re-score the shipped classifier on its split", "Reproduces `models/metrics.json`", f"{'Reproduced exactly' if F.DM['matches_saved_metrics_json'] else 'Differs'}: accuracy {F.f3(S['accuracy'])}, macro F1 {F.f3(S['f1_macro'])}"],
               ["X2", "Classifier against the majority baseline", "Better than predicting the biggest class", f"Accuracy {F.f3(S['accuracy'])} against {F.f3(F.BASELINES['majority_class']['accuracy'])}; macro F1 {F.f3(S['f1_macro'])} against {F.f3(F.BASELINES['majority_class']['f1_macro'])}"],
               ["X3", "Stability over five splits", "Small spread", f"Accuracy {F.f3(F.SEEDS['accuracy']['mean'])} ± {F.f3(F.SEEDS['accuracy']['sd'])} (range {F.f3(F.SEEDS['accuracy']['min'])}-{F.f3(F.SEEDS['accuracy']['max'])})"],
               ["X4", "Accept versus reject only", "Clear separation", f"{F.pct(F.DM['decisive_only']['accuracy'])} of the {F.DM['decisive_only']['n']} accept and reject test papers correct"],
               ["X5", "Borderline class", "Cannot be recovered from the text by construction", f"Recall {F.f2(F.PER_CLASS['borderline']['recall'])} (a known limit of the synthetic labels)"],
               ["X6", "Matcher top-1 on 40 probe papers (MiniLM, shipped weights)", "Far above chance", f"{F.f2(M['full_hybrid_shipped_weights']['top1'])} against {F.f2(M['random_expectation_top1'])} for a random ranking"],
               ["X7", "Matcher top-3 / MRR", "High", f"{F.f2(M['full_hybrid_shipped_weights']['top3'])} / {F.f3(M['full_hybrid_shipped_weights']['mrr'])}"],
               ["X8", "Lexical overlap alone", "Weaker than embeddings", f"Top-1 {F.f2(M['lexical_only_keyword_and_method']['top1'])}"],
               ["X9", "Offline embedder", "Lower but usable", f"Top-1 {F.f2(T['full_hybrid_shipped_weights']['top1'])}, top-3 {F.f2(T['full_hybrid_shipped_weights']['top3'])}"],
               ["X10", "Literal conflict links injected", "All flagged", f"{literal} of {literal_n} flagged"],
               ["X11", "Reworded affiliation, first name only", "Expected to be missed by string matching", f"{miss} of {miss_n} missed (flagged: {miss_n - miss})"],
               ["X12", "False conflict flags on clean pairs", "None", f"{cf['false_flags_on_clean_papers']} of {cf['clean_pairs_checked']} paper-reviewer pairs flagged"]],
              widths=[0.5, 2.2, 1.7, 2.2], align=["c", "l", "l", "l"], size=9)]

    b += [H2("7.9 Regression and known failures on real PDFs"),
          P("Four real PDFs were run through extraction, features and the classifier. They are not labelled, so the table shows behaviour, not accuracy."),
          TAB("Real PDFs through the pipeline", ["Document", "Pages", "Words", "Sections found", "Not detected", "Refs", "Structural score", "Decision signal"], real_rows(),
              widths=[1.5, 0.45, 0.6, 0.6, 1.5, 0.4, 0.6, 0.9], align=["l", "c", "r", "c", "l", "c", "c", "l"], size=8.5),
          P("Three findings come out of this run. First, **section detection is brittle**: the IEEE paper uses roman-numeral headings (for example `I. INTRODUCTION`) that the regular expressions do not match, so its introduction "
            f"is not found and its structure completeness drops to {F.REAL[3]['structure_completeness']:.1f}; the same paper's first line is a digital object identifier, so the title heuristic returns "
            f"\"{F.REAL[3]['title_extracted'][:45]}...\" instead of the title. Second, **the decision signal is not informative on real papers**: all four papers receive *borderline* with a confidence of "
            f"{min(r['ml_confidence'] for r in F.REAL):.2f} to {max(r['ml_confidence'] for r in F.REAL):.2f}, which is what a classifier trained on template sentences would be expected to do with genuine prose. Third, the "
            f"structural scores ({min(r['structural_score'] for r in F.REAL):.0f} to {max(r['structural_score'] for r in F.REAL):.0f}) are plausible for finished papers but nothing in the project shows that they track quality. None of these failures stops the application; all are recorded as limitations and "
            "as the first targets for improvement (Chapter 10).")]

    b += [H2("7.10 User acceptance testing and the limits of the testing done"),
          P("**No user-acceptance test was run.** No editor, reviewer or programme chair used the application, so there is no measure of usability, trust or time saved. What exists instead is a scripted walkthrough "
            "(upload the demo or a real PDF, read the five result tabs, open the audit table of a reviewer, add a reviewer, export the analysis) that the capture script performs and records as screenshots (Chapter 8)."),
          P("The main limits of the testing are:"),
          B(f"**Few automated tests.** Seven pytest tests and a smoke script of {_val(F.SMOKE_TOTAL)} checks cover the routes and the happy path; the scoring rules, the section detector and the review rules have no unit tests of their own.",
            "**Probe data written by the team.** The matcher was scored on 40 abstracts and 15 conflict cases written by the same people who wrote the matcher, with labels from the same people. The results show that the "
            "mechanism works as designed; they do not show that it will rank real reviewers as an editor would.",
            "**Synthetic training data.** The classifier was tested only on held-out synthetic rows and observed on four real papers; no test could show real predictive power.",
            "**No quality judgement of the language model's text.** Its output was read by the team for the screenshots but was not rated, fact-checked or compared with human reviews.",
            "**One machine.** All timings come from one CPU-only computer; other hardware, a GPU or a concurrent load were not tested, and concurrent users were not tested at all.",
            "**No security assessment** beyond the validation probes in Section 7.5.",
            "**Browser coverage.** The interface was walked in one browser at one window size (1440 x 900), not on phones or other browsers."),
          P("These limits mean that the system is demonstrated, not validated. The testing supports the claim that the pipeline runs end to end, rejects bad input politely, degrades visibly when a component is missing and "
            "produces an auditable ranking; it does not support any claim about the correctness of its assessments on real submissions.")]
    return b


def _report_blocks():
    """Compact variant for the full report (F.REPORT True): same sections and numbers, shorter prose, merged tables."""
    M, T, S = F.MINILM, F.TFIDF, F.SHIPPED
    cf = M["conflict"]
    kinds = cf["detected_by_kind"]
    literal = sum(v["detected"] for k, v in kinds.items() if not k.startswith("paraphrased") and k != "first name only")
    literal_n = sum(v["n"] for k, v in kinds.items() if not k.startswith("paraphrased") and k != "first name only")
    miss_n = sum(v["n"] for k, v in kinds.items() if k.startswith("paraphrased") or k == "first name only")
    miss = sum(v["n"] - v["detected"] for v in kinds.values())
    sc = M["scaling_ms"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]
    b += [H2("7.1 Testing strategy"),
          P("Testing has five layers: unit tests of single functions, in-process API tests, a smoke test that drives a running server over HTTP, measured experiments on held-out data and probe sets (Chapter 8), "
            f"and a browser walk that produces the screenshots. The tests (`tests/`, {F.LOC['tests']} lines, and `scripts/smoke_test.py`) check behaviour, not the scientific quality of the assessments, which only people can judge "
            "and which no one was asked to judge (Section 7.8)."),
          TAB("Test layers and results", ["Layer", "What it covers", "Result"],
              [["Unit and integration (pytest)", "Extraction, features, matching and conflict logic, classifier service, health, reviewer CRUD, full analysis of the demo PDF", f"{F.PYTEST_TOTAL} tests; {pytest_result()}"],
               ["Functional (smoke test)", "Reviewer CRUD and CSV, bad uploads, analysis, history, export, CORS, web app", f"{_val(F.SMOKE_PASSED)} of {_val(F.SMOKE_TOTAL)} checks pass"],
               ["Validation probes", "Upload rules, field limits, edge cases (Section 7.4)", "Observed as listed"],
               ["Measured experiments", "Decision model, baselines, five splits, matching probe set, conflict injection, four real PDFs", "Numbers in Chapter 8"]],
              widths=[1.6, 3.4, 1.4], align=["l", "l", "c"], size=9.5)]
    b += [H2("7.2 Unit testing"),
          TAB("Automated pytest cases", ["ID", "Test", "Assertions", "Result"],
              [["T1", "`test_pdf_extraction`", "Demo PDF parsed: at least one page, more than 200 words, methodology or experiments detected", pytest_result()],
               ["T2", "`test_features`", "Synthetic document: `has_methodology` true; structural score within 0-100", pytest_result()],
               ["T3", "`test_matching_and_conflict`", "NLP reviewer ranked first; `breakdown` and `explanation` present; conflict flag true for a conflict term", pytest_result()],
               ["T4", "`test_ml_predict_service`", "Label is accept, borderline, reject or `unavailable`", pytest_result()],
               ["T5", "`test_api_health`", "200 and product `PeerScope`", pytest_result()],
               ["T6", "`test_reviewer_crud`", "POST 201, PUT 200, DELETE 200", pytest_result()],
               ["T7", "`test_pipeline_with_demo`", "Demo PDF through `/api/analyze`: 200, more than 100 words, at least one ranked reviewer, strengths listed", pytest_result()]],
              widths=[0.4, 1.9, 3.4, 0.7], align=["c", "l", "l", "c"], size=9.5),
          P(f"The suite ran in {_val(F.PYTEST_SECONDS, '{:.0f}')} seconds; T7 is the slowest because it runs the whole pipeline, and with the local language model enabled it takes minutes on a CPU. "
            "T2 and T4 are deliberately loose (code runs, values in range); the accuracy of the classifier and of the matcher is measured separately. The scoring rules, the section detector and the review rules have "
            "no unit tests of their own, which is a gap (Section 7.8).")]
    b += [H2("7.3 Integration testing"),
          P("T7 sends a real PDF through the full request path (validation, extraction, features, classifier, review, literature, matching, storage, response); T5 and T6 call the routes through the same application object; "
            "the smoke test repeats the paths over a real HTTP connection, where uploads and cross-origin handling behave as they do for the browser. The browser itself was exercised only by the capture script, "
            "which reports console errors, page errors and failed requests.")]
    b += [H2("7.4 Functional testing, validation and edge cases"),
          P("`scripts/smoke_test.py` creates its own reviewers, removes them afterwards and checks every step. The validation rows were probed for this report with the FastAPI test client on a scratch database "
            "with the AI review off; they are not part of the automated suite."),
          TAB("Functional, validation and edge-case checks", ["ID", "Check", "Expected / observed", "Result"],
              [["S1-S3", "Health route; model metrics; confusion matrix as large as the label list", "200, product `PeerScope`, `accuracy` present", smoke_result()],
               ["S4", "Reviewer list", "Non-empty list", smoke_result()],
               ["S5", "Reviewer with an empty name", "422", smoke_result()],
               ["S6-S7", "Reviewer create; deactivate", "201; 200 and `is_active` false", smoke_result()],
               ["S8-S9", "Reviewer CSV export; CSV import", "200 with header and new reviewer; `imported` = 1", smoke_result()],
               ["S10-S11", "Clean-up; delete an unknown reviewer", "Count restored; 404", smoke_result()],
               ["S12", "Text file posted as a paper", "400 \"Only PDF files are accepted\"", smoke_result()],
               ["S13", "File named `.pdf` that is not a PDF", "400 missing PDF header", smoke_result()],
               ["S14-S15", "Analyse the demo PDF; result has `review`, `reviewers`, `literature`, `features`", "200; fields present", smoke_result()],
               ["S16-S17", "Top reviewer has a `breakdown`; disclaimer mentions a human decision-maker", "Present", smoke_result()],
               ["S18-S19", "New analysis in history; fetch by id", "Listed; 200", smoke_result()],
               ["S20-S21", "JSON export; PDF export", "200 with attachment header; bytes start with `%PDF`", smoke_result()],
               ["S22", "Unknown analysis id", "404", smoke_result()],
               ["S23-S24", "Web application served; CORS allows the web origin", "`index.html` served; origin allowed", smoke_result()],
               ["V1", "Zero-byte `a.pdf`; `.pdf` with content type `image/png`", "400 \"Uploaded file is empty.\" / 400 \"Unexpected file type\"", "Observed"],
               ["V2", "21 MB body starting with `%PDF`", "413 \"File too large (21.0 MB). Limit is 20 MB.\"", "Observed"],
               ["V3", "Reviewer with load 101, maximum load 0 or a 201-character name; non-integer analysis id", "422 with the field and the limit", "Observed"],
               ["V4", "CSV with a non-numeric load; binary file posted as CSV", "400 \"Malformed reviewer CSV\", nothing stored", "Observed"],
               ["V5", "Corrupt body after a `%PDF` header; CSV rows without a name", "Accepted: 200 with almost no text; 0 rows imported (better as explicit errors)", "Observed"],
               ["E1", "Empty reviewer directory", "400 \"Reviewer directory is empty. Add reviewers first.\"", "Observed"],
               ["E2", "PDF with one short sentence", "200 with the warning \"Very little extractable text was found\"", "Observed"],
               ["E3", "Local model not installed", "`llm_status: unavailable`, deterministic review shown with the reason", "Observed (first screenshot session)"],
               ["E4", "OpenAlex unreachable", "`unavailable`, no crash (by code; three online queries returned six works each)", "By code"],
               ["E5", "Embedding model not loadable", f"TF-IDF fallback: top-1 {F.f2(T['full_hybrid_shipped_weights']['top1'])} against {F.f2(M['full_hybrid_shipped_weights']['top1'])} with MiniLM", "Measured"],
               ["E6", "Classifier artifacts missing or from another scikit-learn release", "`model_unavailable`; version warning seen for 1.9.0 artifacts under 1.9.1; `run.bat` retrains", "By code / observed"],
               ["E7", "Reviewer at full load; inactive reviewer", "Availability 0 lowers the score; inactive reviewers are filtered when `active_only` is on", "By formula / filter"],
               ["E8", "Conflict term, name or affiliation in the paper text", f"{literal} of {literal_n} literal links flagged and the reviewer fell to the bottom", "Measured"]],
              widths=[0.6, 2.4, 2.8, 0.9], align=["c", "l", "l", "c"], size=9),
          P("The probes show consistent validation and short, safe error messages. They also show what validation does not do: a file that starts with `%PDF` but is otherwise corrupt is accepted and returns 200 with almost no "
            "extracted text, and a CSV whose rows have no name is accepted with zero rows imported; neither is dangerous, but both would be better as explicit errors. Uploaded bytes go to a temporary file that is deleted "
            "in a `finally` block, database access uses bound parameters through the ORM, and the PDF export escapes `&`, `<` and `>`."),
          P("The API has no authentication and allows all origins (a design decision for a single-user local tool, listed in Chapter 10). No penetration test, PDF-parser fuzzing or prompt-injection test was carried out; "
            "hidden instructions in a PDF are a known risk [2], [27] addressed by design (the language model never changes a score), not by a measured defence.")]
    b += [H2("7.5 Performance testing"),
          P(f"Timings come from one CPU-only machine ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM). Loading the embedding model took {lat('embedding_model_load_s', fmt='{:.1f}')} s and the Qwen model "
            f"{lat('llm_load_s', fmt='{:.1f}')} s, once per server start. A 48-token generation took about 15 s in a separate probe (roughly 3 tokens per second), so the AI review takes minutes while every other stage "
            "is far faster; it is therefore optional and the deterministic review is shown first."),
          TAB("Stage timings of one analysis (milliseconds, in-process)", ["Stage", "Demo paper (3 pages)", "Survey (30 pages)"], stage_rows(), widths=[2.8, 1.8, 1.8], align=["l", "r", "r"], size=9.5),
          TAB("HTTP latency with the AI review off (milliseconds, `127.0.0.1`)", ["Request", "Calls", "Median", "95th percentile / max"], http_rows(), widths=[3.2, 0.7, 1.0, 1.5], align=["l", "c", "r", "r"], size=9.5),
          P("The language-model review dominates the total: its three generations of up to 512, 512 and 700 tokens run in 32-bit precision on the CPU, which is why the review is labelled optional, the deterministic review is "
            "always shown first, and the API timings above were taken with the model switched off so that they describe the deterministic path."),
          P(f"Ranking time grows linearly with the reviewer pool because every profile is embedded on every request: with MiniLM {sc[0]['median_ms']:.0f} ms for {sc[0]['pool']} reviewers, "
            f"{sc[1]['median_ms']:.0f} ms for {sc[1]['pool']}, {sc[2]['median_ms'] / 1000:.1f} s for {sc[2]['pool']} and {sc[3]['median_ms'] / 1000:.1f} s for {sc[3]['pool']}; the TF-IDF fallback needs "
            f"{T['scaling_ms'][3]['median_ms']:.0f} ms for {T['scaling_ms'][3]['pool']}. A conference-sized pool would need cached reviewer embeddings."),
          FIG(F.fig("f09_matching_scaling.png"), "Median reviewer-ranking time against the size of the reviewer directory.", 4.4)]
    b += [H2("7.6 Experiments used as tests"),
          TAB("Measured test cases", ["ID", "Case", "Observed"],
              [["X1", "Shipped classifier re-scored on its split", f"{'Reproduces' if F.DM['matches_saved_metrics_json'] else 'Differs from'} `models/metrics.json`: accuracy {F.f3(S['accuracy'])}, macro F1 {F.f3(S['f1_macro'])}"],
               ["X2", "Against the majority baseline", f"Accuracy {F.f3(S['accuracy'])} against {F.f3(F.BASELINES['majority_class']['accuracy'])}; macro F1 {F.f3(S['f1_macro'])} against {F.f3(F.BASELINES['majority_class']['f1_macro'])}"],
               ["X3", "Stability over five splits", f"Accuracy {F.f3(F.SEEDS['accuracy']['mean'])} ± {F.f3(F.SEEDS['accuracy']['sd'])} (range {F.f3(F.SEEDS['accuracy']['min'])}-{F.f3(F.SEEDS['accuracy']['max'])})"],
               ["X4", "Accept versus reject only", f"{F.pct(F.DM['decisive_only']['accuracy'])} of the {F.DM['decisive_only']['n']} accept and reject test papers correct"],
               ["X5", "Borderline class", f"Recall {F.f2(F.PER_CLASS['borderline']['recall'])} (cannot be recovered from the text by construction of the synthetic labels)"],
               ["X6", "Matcher on 40 probe papers (MiniLM, shipped weights)", f"Top-1 {F.f2(M['full_hybrid_shipped_weights']['top1'])} against {F.f2(M['random_expectation_top1'])} for a random ranking; top-3 {F.f2(M['full_hybrid_shipped_weights']['top3'])}; MRR {F.f3(M['full_hybrid_shipped_weights']['mrr'])}"],
               ["X7", "Lexical overlap alone; offline embedder", f"Top-1 {F.f2(M['lexical_only_keyword_and_method']['top1'])}; top-1 {F.f2(T['full_hybrid_shipped_weights']['top1'])} and top-3 {F.f2(T['full_hybrid_shipped_weights']['top3'])}"],
               ["X8", "Literal conflict links injected", f"{literal} of {literal_n} flagged"],
               ["X9", "Reworded affiliation, first name only", f"{miss} of {miss_n} missed, as expected of string matching"],
               ["X10", "False conflict flags on clean pairs", f"{cf['false_flags_on_clean_papers']} of {cf['clean_pairs_checked']} paper-reviewer pairs flagged"]],
              widths=[0.5, 2.3, 3.6], align=["c", "l", "l"], size=9.5)]
    b += [H2("7.7 Regression and known failures on real PDFs"),
          TAB("Real PDFs through the pipeline", ["Document", "Pages", "Words", "Sections found", "Not detected", "Refs", "Structural score", "Decision signal"], real_rows(),
              widths=[1.5, 0.45, 0.6, 0.6, 1.5, 0.4, 0.6, 0.9], align=["l", "c", "r", "c", "l", "c", "c", "l"], size=8.5),
          P("Section detection is brittle: the IEEE paper's roman-numeral headings (`I. INTRODUCTION`) are not matched, so its introduction is missed "
            f"(structure completeness {F.REAL[3]['structure_completeness']:.1f}) and its first line, a digital object identifier, becomes the title. The decision signal is not informative on real papers: "
            f"all four receive *borderline* at confidence {min(r['ml_confidence'] for r in F.REAL):.2f} to {max(r['ml_confidence'] for r in F.REAL):.2f}, as expected of a classifier trained on template sentences. "
            f"The structural scores ({min(r['structural_score'] for r in F.REAL):.0f} to {max(r['structural_score'] for r in F.REAL):.0f}) look plausible but nothing shows that they track quality.")]
    b += [H2("7.8 User acceptance testing and the limits of the testing done"),
          P("**No user-acceptance test was run**: no editor, reviewer or chair used the application, so usability, trust and time saved are unmeasured. A scripted walkthrough (upload, read the five result tabs, open an "
            "audit table, add a reviewer, export) was performed by the capture script and recorded as screenshots (Chapter 8)."),
          B(f"**Few automated tests:** seven pytest tests and a smoke script of {_val(F.SMOKE_TOTAL)} checks; the scoring rules, section detector and review rules have no unit tests.",
            "**Probe data written by the team:** 40 abstracts and 15 conflict cases with the team's own labels show that the mechanism works as designed, not that it ranks real reviewers as an editor would.",
            "**Synthetic training data and no judgement of the language model's text;** it was read for the screenshots but not rated or fact-checked.",
            "**One CPU-only machine, one browser at 1440 x 900;** no concurrent users, phones or GPU, and no security assessment beyond the probes above."),
          P("The system is demonstrated, not validated: the tests support the claims that the pipeline runs end to end, rejects bad input politely, degrades visibly and produces an auditable ranking, but not any claim "
            "about the correctness of its assessments on real submissions.")]
    return b


def blocks():
    return _report_blocks() if F.REPORT else _full_blocks()
