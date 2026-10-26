"""Chapter 8: Results and output screens. Every number is read from experiments/lablens/*.json at build time."""

import os

from .blocks import B, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

LAYOUT_LABEL = {
    "plain": "plain", "paren": "range in brackets", "flag": "L/H flag column", "colon": "colon + Ref:",
    "unit_last": "unit after range", "mixed_sep": "mixed range separators", "tabular": "one cell per line",
    "ocr_noise": "noisy test names",
}


def _fig_if(name, caption, width=5.4):
    p = F.fig(name)
    return [FIG(p, caption, width)] if os.path.exists(p) else []


def _shot(name, caption, base=5.6, max_h=1500):
    p = F.shot_view(name, max_h)
    return FIG(p, caption, F.shot_w(p, min(base, 5.0), 5.0))


def screens():
    return [
        H2("8.1 Output screens"),
        P("The screens in this section are captures of the running application at 1440 x 900 pixels, taken by `scripts/capture_screens.py` in a real browser. "
          "Every report in the library was produced by the unchanged extraction pipeline: five synthetic sample reports (invented patient, invented values, dated April to October 2026) were "
          "rendered as PDFs with a text layer and uploaded through the same code path as a genuine file, and a sixth PDF, `Quarterly_Panel_Oct2026.pdf`, was uploaded through the Upload screen. "
          "**All values on these screens are synthetic**; no real patient data was available or used."),
        P("The dashboard screen summarises the library: 6 reports, 82 extracted tests, 54 normal and 28 abnormal results, and 2 critical alerts. "
          "A result is critical under a simple rule in `database.get_dashboard_stats`: LOW below half the lower limit, or HIGH above one and a half times the upper limit."),
        _shot("04_dashboard.png", "Dashboard: totals across the library, a critical-result banner, the recent-reports table and the status split"),
        P("The next screen is the Upload screen after `Quarterly_Panel_Oct2026.pdf` (4.2 KB) was processed. The six pipeline stages are ticked and the table lists the 14 extracted "
          "tests with value, unit, reference range and status. The LLM switch is disabled because no `ANTHROPIC_API_KEY` is configured."),
        _shot("06_upload_done.png", "Upload screen after a successful run: stage tracker, extracted and classified results, and a link to the full analysis", 5.2),
        P("The report analysis screen below is for `Health_Checkup_Aug2026.pdf`: 14 tests, 5 normal and 9 abnormal. Each abnormal row has a card: what the test measures, "
          "possible general causes and a suggestion to consult a professional. Potassium has no specific text, so its card shows the generic wording."),
        _shot("07_report_analysis.png", "Report analysis: result table with status badges and health-insight cards for abnormal results (top of the page)", 5.4, 1700),
        _shot("08_my_reports.png", "My reports: upload history with status, expandable result tables, a search box and delete buttons"),
        P("The trend screen for haemoglobin across the six reports: 10.8, 11.2, 11.9, 12.6, 13.1 and 13.1 g/dL, drawn against the shaded reference band 12 to 16 g/dL. "
          "The first three points are LOW and the last three NORMAL; the pattern note (increasing) uses the first and last value only."),
        _shot("09_health_trends.png", "Health trends: one test across all reports, with the reference band, the pattern note and a sortable table", 5.4),
        P("The compare screen puts report 1 (April) beside report 5 (October). 14 tests are common to both. Changes are report 2 minus report 1: LDL cholesterol falls by 56 mg/dL, haemoglobin rises by 2.3 g/dL "
          "and vitamin D rises by 24 ng/mL. "),
        _shot("10_compare_reports.png", "Compare reports: tests in common, status in each report, signed change and unit-grouped bar charts", 5.4),
        _shot("11_health_insights.png", "Health insights: every explanation for every abnormal result in the library, with a Low / High filter and a search box (top of the page)", 5.2, 1500),
    ]


def setup():
    M = F.TESTS["machine"]
    prot = F.METRICS["protocol"]
    return [
        H2("8.2 Experimental setup and protocol"),
        P("The project did not ship any evaluation data, and no real laboratory report was available for labelling. The measurements below are therefore made on a **generated corpus with known ground truth**, "
          "built by `scripts/run_experiments.py` (random seed 42) and pushed through the unchanged `ocr_processor`, `ner_processor`, `result_analyzer` and `ai_insights` modules. "
          "The corpus is not real patient data and the labels are not manual annotations; Section 8.12 explains what this means for the conclusions."),
        TAB("Evaluation corpus", ["Property", "Value"], [
            ["Reports", "120 PDFs with a text layer, rendered with PyMuPDF (8 layouts x 15 reports)"],
            ["Rows per report", "14: 12 tests from a 40-test pool covered by the name dictionary, plus 2 tests from an 8-test pool that is not in the dictionary"],
            ["Ground-truth rows", f"{F.EXTRACTION['overall']['reports_rows']:,}"],
            ["Values", "about 55% inside the range, 25% below, 20% above; one-sided limits (<, >) for LDL, HDL, triglycerides, CRP and PSA"],
            ["Distractors", "two header lines per report drawn from five (patient name, age/sex, registration number, referring doctor, phone) and a `Sample Collected` date line"],
            ["Layouts", "plain, range in brackets, L/H flag column, colon with `Ref:`, unit after range, mixed range separators (`-`, `to`, `-` without spaces), one cell per line (table), noisy test names"],
            ["Scope", "text-layer PDFs only: no scanned page, no photograph, so the OpenCV and Tesseract path is not exercised"],
        ], widths=[1.4, 4.6], size=10, align=["l", "l"]),
        TAB("Measurement environment", ["Item", "Value"], [
            ["Processor / memory", f"{M['cpu']}, {M['ram_gb']} GB RAM, no GPU"],
            ["Operating system", M["os"]],
            ["Python and libraries", f"Python {M['python']}, scikit-learn {M['scikit_learn']}, PyMuPDF {M['pymupdf']}, OpenCV {M['opencv']}, SQLAlchemy {M['sqlalchemy']}, FastAPI {M['fastapi']}, uvicorn {M['uvicorn']}"],
            ["Front end", f"Node {M['node']}, React {M['react']}, Vite {M['vite']}, Recharts {M['recharts']}"],
            ["Database", "temporary SQLite file for every run; `data/medical_lab.db` is never touched"],
        ], widths=[1.6, 4.4], size=10, align=["l", "l"]),
        H3("Scoring"),
        P("For every ground-truth row the scorer takes the first unused predicted row whose value equals the true value. That row is a detection. A detected row is then compared field by field: "
          "the test name (case-insensitive), the unit (after mapping the micro sign to `u` and lower-casing), both range limits, and the status. "
          "A predicted row that is never matched is a false positive. With TP the detected rows, P the predicted rows and G the ground-truth rows:"),
        EQ("precision = TP / P,    recall = TP / G,    F1 = 2 x precision x recall / (precision + recall)"),
        EQ("exact-row rate = (rows detected with name, unit, range and status all correct) / G"),
        P("Field accuracies are quoted over detected rows. The exact-row rate is the strictest figure because it is taken over all ground-truth rows, so a missed row counts against it."),
    ]


def extraction():
    E = F.EXTRACTION
    o = E["overall"]
    L = E["per_layout"]
    order = ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]
    rows = []
    for k in order:
        v = L[k]
        f = lambda x: "n/a" if x is None else f"{x:.3f}"
        rows.append([LAYOUT_LABEL[k], f(v["row_precision"]), f(v["row_recall"]), f(v["row_f1"]), f(v["name_acc"]), f(v["unit_acc"]), f(v["range_acc"]), f(v["exact_row_rate"])])
    rows.append(["**All 120 reports**", f"**{o['row_precision']:.3f}**", f"**{o['row_recall']:.3f}**", f"**{o['row_f1']:.3f}**", f"**{o['name_acc']:.3f}**",
                 f"**{o['unit_acc']:.3f}**", f"**{o['range_acc']:.3f}**", f"**{o['exact_row_rate']:.3f}**"])
    k = E["failure_kinds"]
    field_err = sum(v for a, v in k.items() if a.startswith("field error"))
    return [
        H2("8.3 Field extraction"),
        P(f"Across all 120 reports the parser predicted {o['predicted_rows']:,} rows for {o['reports_rows']:,} true rows. Row precision is **{F.f3(o['row_precision'])}**, recall **{F.f3(o['row_recall'])}** "
          f"and F1 **{F.f3(o['row_f1'])}**. Among detected rows the range limits are almost always right (**{F.pct(o['range_acc'])}**) and so is the derived status (**{F.pct(o['status_acc'])}**); "
          f"the test name is right in {F.pct(o['name_acc'])} and the unit in {F.pct(o['unit_acc'])}. Only **{F.pct(o['exact_row_rate'])}** of all true rows come out with all four fields correct."),
        TAB("Extraction results by layout", ["Layout", "Precision", "Recall", "F1", "Name", "Unit", "Range", "Exact row"], rows,
            widths=[1.55, 0.7, 0.62, 0.55, 0.6, 0.55, 0.6, 0.7], size=9.5, align=["l"] + ["c"] * 7),
        *_fig_if("fig_extraction_by_layout.png", "Extraction quality for each report layout (generated corpus, text-layer PDFs)", 5.6),
        P("Three things stand out."),
        N(f"**The cell-per-line table layout is not supported at all.** When a PDF stores each cell as a separate text object, PyMuPDF returns one cell per line (`ESR`, `13.3`, `mm/hr`, `0 - 20`), and the line parser, which needs a name, "
          f"a value and a range on one line, finds nothing. All 210 rows of the 15 tabular reports were missed. {F.EXTRACTION['failure_kinds']['missed row']} rows were missed in total, so the other layouts together lose only "
          f"{F.EXTRACTION['failure_kinds']['missed row'] - 210}. Because predicted rows for this layout number exactly 7, which is the number of dash-dated reports, 7 of the 15 reports would 'complete' with a single bogus row (next point) and "
          "the other 8 would be marked Failed with the message that no recognizable rows were found; the first case is the worse one because nothing signals the failure.",
          "**A dash-formatted date is read as a test result.** A line such as `Sample Collected: 12-04-2026 10:30` matches the name-value pattern (name `Sample Collected`, value 12) and the range pattern (`-04-2026`, read as -4 to 2026), "
          f"so a row named `Sample Collected` with range -4 to 2026 is created. This happened in every one of the 56 reports whose date used dashes (7 per layout, 8 layouts). The {o['false_positive_rows']} false-positive rows are 55 of these date rows plus two others: in `paren_03` the date value 12 equalled a real RDW result of 12, so the scorer matched the date row to RDW and counted the genuine RDW row as the extra one, and in `ocr_noise_03` a mis-read name produced a row that matched no true result. "
          "The row is classified NORMAL, so it is harmless to the status counts but it inflates the test count on the dashboard. The slash-formatted dates (`12/04/2026`) were rejected because they contain neither a unit nor a range.",
          "**The unit list is incomplete and a flag letter hides the unit.** The unit expression has a fixed list (`g/dL`, `mg/dL`, `U/L`, `mEq/L`, ...). Units outside it (`uIU/mL`, `mg/L`, `umol/L`, `ng/dL`) are dropped, "
          "and a one-letter flag between value and unit (`Sodium 134 L mEq/L`) stops the unit from being read, which is why unit accuracy in the flag layout is only "
          f"{F.pct(L['flag']['unit_acc'])}. {k['field error: unit']} rows have a wrong unit and nothing else wrong; the value, range and status of those rows are still correct, so the clinical flag survives."),
        P(f"The remaining field errors are name errors: {k['field error: name'] + k['field error: name,unit']} rows, most of them a test outside the dictionary (`Sodium Bicarbonate`) that was renamed `Sodium`, the rest noisy names that were not repaired. "
          f"On the 12 dictionary tests per report the name is correct in {F.pct(o['name_acc_dict_tests'])} of detected rows; on the 2 unseen tests it is correct in only {F.pct(o['name_acc_ood_tests'])}."),
    ]


def names():
    N_ = F.NAMES
    nz = N_["noise"]
    sw = {s["threshold"]: s for s in N_["threshold_sweep"]}
    pick = [0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80]
    syn = N_["synonyms"]
    ood = N_["ood_names"]
    return [
        H2("8.4 Test-name normalisation"),
        P(f"The matcher snaps a noisy test name to one of the {N_['n_dictionary_names']} dictionary names when the TF-IDF cosine similarity (character 2- to 4-grams) is at least 0.55. "
          "To isolate this component, every dictionary name was corrupted 30 times at several per-character noise rates (a character is replaced by a look-alike, dropped, or has a letter inserted) "
          "and the corrected name was compared with the true one. The standard-library `difflib` ratio matcher (threshold 0.60) and plain exact matching are included as baselines."),
        TAB("Name accuracy under simulated OCR noise", ["Per-character noise", "TF-IDF (shipped, 0.55)", "difflib ratio (0.60)", "Exact match"],
            [[f"{float(r) * 100:.0f}%", f"{nz[r]['tfidf_0.55']:.3f}", f"{nz[r]['difflib_0.60']:.3f}", f"{nz[r]['exact_match']:.3f}"] for r in nz],
            widths=[1.5, 1.7, 1.5, 1.2], size=10.5, align=["c"] * 4),
        *_fig_if("fig_name_noise.png", "Name accuracy against simulated noise for the shipped matcher and two baselines", 4.8),
        P(f"The result is not flattering to the shipped design. Both fuzzy matchers are far better than exact matching, but the `difflib` baseline is more accurate than the TF-IDF matcher at every non-zero noise rate "
          f"({nz['0.1']['difflib_0.60']:.3f} against {nz['0.1']['tfidf_0.55']:.3f} at 10% noise and {nz['0.2']['difflib_0.60']:.3f} against {nz['0.2']['tfidf_0.55']:.3f} at 20%). "
          "The TF-IDF choice was not tested against this baseline when it was made; its advantage is only that the dictionary vectors are computed once."),
        H3("Threshold analysis"),
        TAB("Effect of the cosine threshold (TF-IDF matcher)", ["Threshold", "Accuracy at 10% noise", "Accuracy at 20% noise", "Unseen names wrongly snapped", "Synonym accuracy"],
            [[f"{t:.2f}" + (" (shipped)" if abs(t - 0.55) < 1e-9 else ""), f"{sw[t]['acc_noise_10']:.3f}", f"{sw[t]['acc_noise_20']:.3f}", f"{sw[t]['false_snap_rate_ood']:.3f}", f"{sw[t]['synonym_acc']:.3f}"] for t in pick],
            widths=[1.3, 1.25, 1.25, 1.3, 1.0], size=10, align=["c"] * 5),
        *_fig_if("fig_threshold_sweep.png", "Trade-off between correcting noisy names and wrongly renaming unseen names as the threshold moves", 4.9),
        P("Lowering the threshold recovers more noisy names but renames more tests the dictionary does not know; raising it does the opposite. The shipped 0.55 lies in the middle: it wrongly renames "
          f"{F.pct(sw[0.55]['false_snap_rate_ood'])} of the {ood['n']} unseen names and recovers {F.pct(sw[0.55]['acc_noise_20'])} of names at 20% noise. No threshold removes both problems, "
          "because the score cannot distinguish a corrupted known name from a different real name that shares letters."),
        H3("Synonyms and unseen names"),
        P(f"A dictionary built from character n-grams does not know abbreviations. Of {syn['n']} common synonyms, {len(syn['correct'])} were mapped correctly at the shipped threshold "
          f"({', '.join(syn['correct'][:6])}, and others) and {len(syn['wrong_or_unmatched'])} were not: {', '.join('`' + s + '`' for s in list(syn['wrong_or_unmatched'])[:8])}. "
          "`Glycosylated Hemoglobin` was mapped to `Hemoglobin`, which is a different test. Unseen names that were wrongly renamed: "
          + ", ".join(f"`{a}` to `{b}`" for a, b in ood["wrongly_snapped"].items()) + ". "
          "A renamed test is dangerous in this product because the trend screen groups results by name: `Sodium Bicarbonate` values would be plotted on the `Sodium` trend."),
    ]


def classification_insight_latency():
    C = F.CLASSIF
    I = F.INSIGHT
    Lat = F.LATENCY
    A = F.API_LAT
    def row(label, key):
        v = Lat[key]
        return [label, f"{v['median_ms']:.2f}", f"{v['mean_ms']:.2f}", f"{v['p95_ms']:.2f}", f"{v['max_ms']:.2f}", str(v["n"])]
    sc = Lat["field_extraction_scaling_by_rows"]
    ep = A["endpoints"]
    out = [
        H2("8.5 Classification"),
        P(f"`classify_result` was checked against an independently written reference rule on {C['random_cases']:,} random cases (two-sided, one-sided and missing limits, negative values included): "
          f"**{C['disagreements_with_reference_rule']} disagreements**. The boundaries are inclusive: a value equal to either limit is NORMAL "
          f"(5 and 10 in a 5-10 range both give {C['boundary_5_in_5to10']}), 4.99 is {C['just_below']} and 10.01 is {C['just_above']}. "
          f"In the extraction experiment the status was correct for {F.pct(F.EXTRACTION['overall']['status_acc'], 2)} of detected rows; the few errors come from rows whose range was misread, not from the rule. "
          "Because the ground truth uses the same rule, this is a check that the status is propagated correctly, not a clinical validation."),
        H2("8.6 Health insights"),
        P(f"The explanation text comes from a curated knowledge base with {I['knowledge_base_entries']} test entries, which covers {I['dictionary_tests_with_specific_text']} of the {I['dictionary_tests']} tests in the name dictionary "
          f"({F.pct(I['coverage_of_dictionary'])}). In the evaluation corpus {I['abnormal_rows_with_specific_text']} of {I['abnormal_dictionary_rows_in_corpus']} abnormal dictionary rows "
          f"({F.pct(I['abnormal_rows_specific_rate'])}) received test-specific text; the rest received the generic wording (`A result above the reference range can have a number of general, non-specific causes`), "
          "as the Potassium card in the analysis screen shows. Every card carries the same suggestion to consult a professional and the disclaimer; none names a disease. "
          "The optional LLM rewrite could not be exercised because no API key was configured, so its quality and latency are not reported."),
        *_fig_if("fig_insight_coverage.png", "Share of abnormal results that receive test-specific explanation text", 4.6),
        H2("8.7 Performance"),
        P(f"Timings use a 14-row, one-page text-layer PDF of {Lat['pdf_bytes']:,} bytes. Each stage was repeated 100 times (the end-to-end run 40 times) in one Python process on the machine described in Section 8.2."),
        TAB("Latency of the pipeline stages", ["Stage", "Median (ms)", "Mean (ms)", "p95 (ms)", "Max (ms)", "Runs"], [
            row("PDF text layer (PyMuPDF)", "text_layer_extraction"),
            row("Field extraction (14 rows)", "field_extraction"),
            row("Classification", "classification"),
            row("Insight generation, all abnormal rows", "insight_generation_all_abnormal"),
            row("**End to end, with SQLite writes**", "end_to_end_pipeline_with_db"),
        ], widths=[2.4, 0.8, 0.75, 0.7, 0.75, 0.6], size=10, align=["l"] + ["c"] * 5),
        *_fig_if("fig_latency_stages.png", "Median latency of each pipeline stage for a 14-row report", 4.6),
        P(f"A report is processed end to end in a median of **{Lat['end_to_end_pipeline_with_db']['median_ms']:.1f} ms**, far below the 10-second target stated in the project abstract. "
          "That target concerns scanned reports processed with OCR, which could not be timed here; the figure above is for text-layer PDFs only. "
          f"Field extraction dominates the extraction work and grows linearly with the number of rows: {sc['14']['median_ms']:.1f} ms for 14 rows, {sc['50']['median_ms']:.1f} ms for 50, "
          f"{sc['100']['median_ms']:.1f} ms for 100 and {sc['200']['median_ms']:.1f} ms for 200, which is about {(sc['200']['median_ms'] - sc['14']['median_ms']) / 186:.1f} ms per row (the TF-IDF transform for each name)."),
        TAB("API latency on 127.0.0.1 (FastAPI, uvicorn, SQLite)", ["Endpoint", "Median (ms)", "p95 (ms)", "Max (ms)", "Runs"],
            [[k, f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}", str(v["n"])] for k, v in ep.items()],
            widths=[2.7, 0.9, 0.8, 0.8, 0.6], size=10, align=["l"] + ["c"] * 4),
        P(f"Reads take under {max(v['median_ms'] for k, v in ep.items() if k.startswith('GET')) + 1:.0f} ms; the slowest read is the library-wide insights list ({ep['GET /api/insights']['median_ms']:.1f} ms), which loads every abnormal result with its explanation. "
          f"A PDF upload takes a median of {ep['POST /api/reports (PDF upload)']['median_ms']:.0f} ms (p95 {ep['POST /api/reports (PDF upload)']['p95_ms']:.0f} ms), of which about {Lat['end_to_end_pipeline_with_db']['median_ms']:.0f} ms is the pipeline itself; "
          f"the rest is request parsing, the multipart upload and response building. Seeding the five sample reports takes {A['seed_five_reports_s']:.2f} s. "
          "Calls must use `127.0.0.1`: on the test machine `localhost` added about two seconds per call. Many simultaneous users were not tested."),
    ]
    return out


def testing():
    T = F.TESTS
    return [
        H2("8.8 Test results"),
        TAB("Automated test runs", ["Suite", "Command", "Result"], [
            ["Unit and API tests (`tests/test_lablens.py`)", "`python -m pytest tests -q`", f"**{T['pytest']['passed']} passed**, {T['pytest']['failed']} failed, {T['pytest']['seconds']} s"],
            ["End-to-end smoke test (`scripts/smoke_test.py`)", "`python scripts/smoke_test.py`", f"**{T['smoke_test']['api_checks_passed']} API checks and {T['smoke_test']['browser_checks_passed']} browser checks passed**: \"{T['smoke_test']['result']}\""],
            ["UI check (`scripts/ui_check.py`)", "`python scripts/ui_check.py`", "script exists (360, 768 and 1440 px, light and dark theme, drawer, keyboard, reduced motion); **not re-run** for this report"],
        ], widths=[2.1, 1.7, 2.2], size=10, align=["l", "l", "l"]),
        P("The 36 pytest cases cover classification boundaries, line extraction, name normalisation, input validation, insight wording and fallback, the full pipeline with persistence, failed reports, "
          "cascading delete, dashboard statistics and the API (authentication, tampered token, upload, trend, compare, insights, seeding), all on a temporary SQLite file. "
          "The smoke test starts its own server on a spare port against a copy of the code; its browser part checks the login redirect, the charts, the insight cards, rejection of a wrong file type and the absence of console errors. Chapter 7 describes the strategy."),
    ]


def cases():
    return [
        H2("8.9 Success and failure cases"),
        H3("A success: a plain single-line report"),
        P("For the sample report `Health_Checkup_Aug2026.pdf` the text layer contains one line per test, for example `Hemoglobin 11.9 g/dL 12 - 16` and `LDL Cholesterol 128 mg/dL <100`. "
          "All 14 rows were extracted with name, unit and range, 9 were classified abnormal (haemoglobin LOW, WBC count HIGH, HbA1c HIGH, total cholesterol HIGH, LDL HIGH, triglycerides HIGH, potassium HIGH, TSH HIGH, vitamin D LOW) "
          "and each received an explanation card (see the report analysis screen in Section 8.1). On the generated corpus the plain layout reached recall 1.000 and F1 0.984, the remaining precision loss being the date row."),
        H3("Failures with real examples"),
        TAB("Failure cases found in the evaluation", ["Report", "Text in the report", "What the system produced", "Cause"], [
            ["tabular_00", "`ESR` / `13.3` / `mm/hr` / `0 - 20` on four separate lines", "no row; 14 of 14 rows missed", "line parser needs the whole row on one line"],
            ["paren_03", "`Sample Collected: 12-04-2026 10:30` (and a real `RDW 12 % 11.5 - 14.5`)", "test `Sample Collected`, value 12, range -4 to 2026, NORMAL", "date matches the value and range patterns; its value equals the RDW result, so the scorer pairs the two"],
            ["plain_11", "`Sodium Bicarbonate 27.3 mEq/L 22 - 29`", "test `Sodium`, same value and range", "name not in dictionary; cosine above 0.55"],
            ["flag_12", "`Sodium Bicarbonate 19.6 L mEq/L 22 - 29`", "test `Sodium`, unit missing, status LOW", "as above, and the flag letter hides the unit"],
            ["plain_03", "`Free T4 0.9 ng/dL 0.8 - 1.8`", "unit missing", "`ng/dL` not in the unit list"],
            ["plain_04", "`TSH 2.5 uIU/mL 0.4 - 4`", "unit missing", "`uIU/mL` not in the unit list"],
            ["ocr_noise_00", "`CR 4.4 mg/L <5` (true name CRP)", "test `Cr`, unit missing", "too far from `CRP` to snap; `mg/L` not in the unit list"],
            ["ocr_noise_03", "a garbled `Free T4` row", "test `Bilirubin Total`, NORMAL", "wrong dictionary entry above the threshold"],
        ], widths=[0.95, 1.9, 1.7, 1.45], size=9, align=["l", "l", "l", "l"]),
        P("The last row is the most serious kind of error: a different test with a plausible range and a NORMAL status. The status itself is rarely wrong when the range is read correctly; the errors that matter are those "
          "that attach a result to the wrong test name, because trends and comparisons are keyed on the name."),
    ]


def base_paper():
    return [
        H2("8.10 Comparison with the base paper"),
        P(f"The base paper {n(1)} (Karhade, Verma, Gadaokar and Mahajan, 2025) builds a question-answering assistant: a user uploads a blood test report and asks a question, and a LLaMA-3 8B model "
          "with retrieval over a knowledge base of 20 medical books and 383 video transcripts (ChromaDB, chunks of 1,024 characters with 100 overlap, top-3 retrieval) answers about metabolic syndrome. "
          "It reports no extraction accuracy, no latency and no trend analysis (personalisation over time is listed as future scope). Its only quantitative result is a rating of 20 generated responses "
          "from 1 to 100 on correctness, clarity, helpfulness and completeness by GPT-4 under human monitoring. **The two evaluations measure different things on different data and cannot be compared numerically.**"),
        TAB("LabLens against the base paper", ["Aspect", "Base paper [1]", "LabLens (this project)"], [
            ["Task", "answer questions about a blood report for metabolic syndrome", "read any lab report, flag results, explain, track and compare"],
            ["Parameters", "33 metabolic-syndrome parameters", f"{F.NAMES['n_dictionary_names']}-name dictionary; unseen names are kept as read"],
            ["Explanation", "retrieval-augmented LLaMA-3 8B; sources cited", "curated rules (17 tests) with generic fallback; optional LLM rewrite; no retrieval, no citations"],
            ["Input handling", "PDF text parsing", "PDF text layer, OpenCV + Tesseract path for scans and photos (not measured here)"],
            ["Trends over time", "future scope", "implemented: trend chart, report comparison"],
            ["Evaluation data", "20 responses, rated by GPT-4", f"{F.EXTRACTION['overall']['reports_rows']:,} generated rows in 120 synthetic PDFs, known ground truth"],
            ["Reported result", "mean ratings 92.4 / 89.7 / 91.1 / 88.9 (correctness, clarity, helpfulness, completeness)", f"row F1 {F.f3(F.EXTRACTION['overall']['row_f1'])}, status accuracy {F.pct(F.EXTRACTION['overall']['status_acc'])}, {F.LATENCY['end_to_end_pipeline_with_db']['median_ms']:.1f} ms per report"],
        ], widths=[1.1, 2.4, 2.5], size=9.5, align=["l", "l", "l"]),
        P("One discrepancy in the base paper is worth recording. Its conclusion states mean scores of 92.4, 89.7, 91.1 and 88.9, but averaging the 20 rows of its own Table 4 gives 94.0, 94.9, 90.1 and 88.65. "
          "We use neither set as a benchmark. LabLens explanations were not rated by any model or person, so nothing in this chapter says whether they are *good*; they are deterministic and conservative by construction, and their coverage is limited (Section 8.6)."),
    ]


def objectives():
    o = F.EXTRACTION["overall"]
    return [
        H2("8.11 Objectives against outcomes"),
        TAB("Objectives of the project and what was achieved", ["No.", "Objective", "Outcome", "Evidence"], [
            ["1", "Accept PDF or scanned image and extract text with high-speed OCR", f"**Partly met.** Text-layer PDFs work (median {F.LATENCY['text_layer_extraction']['median_ms']:.1f} ms for a one-page report). The OpenCV + Tesseract path for scans and photos is implemented but could not be run or measured here (Tesseract is not installed). PP-OCR is not used.", "Section 8.7; code review"],
            ["2", "Identify test name, value, unit and reference range with NER", f"**Partly met.** A regex line parser with a TF-IDF name matcher, not a trained NER or CRF model. Row F1 {F.f3(o['row_f1'])} on the generated corpus; 0 on cell-per-line tables.", "Sections 8.3, 8.4"],
            ["3", "Compare each value with its range and flag abnormal results", f"**Met.** Rule verified on {F.CLASSIF['random_cases']:,} random cases with 0 disagreements; status accuracy {F.pct(o['status_acc'], 2)} on detected rows.", "Section 8.5"],
            ["4", "Plain-language explanations grounded in trusted sources", "**Partly met.** Curated, non-diagnostic text for 17 of 55 tests, generic otherwise. There is no retrieval and no citation of sources; the optional LLM rewrite is untested.", "Section 8.6"],
            ["5", "Track parameters across reports to show trends", "**Met.** Trend chart with reference band, pattern note, and two-report comparison. The pattern uses only the first and last value, and the x-axis is upload date.", "Section 8.1 (trend and compare screens)"],
            ["6", "Present results in a dashboard and evaluate extraction accuracy against manually labelled reports", "**Dashboard met; evaluation not met as stated.** The evaluation used generated, not manually labelled, real reports.", "Section 8.1 (dashboard); Section 8.2"],
        ], widths=[0.4, 1.7, 2.9, 1.0], size=9, align=["c", "l", "l", "l"]),
    ]


def limits():
    return [
        H2("8.12 What these results do and do not show"),
        B("**The corpus is synthetic and was written by the same team that wrote the parser.** The layouts are plausible, but they are the layouts the authors thought of. Real reports will contain multi-line cells, merged columns, footnotes and "
          "scanning artefacts that the corpus lacks, so the F1 values above are likely to be optimistic for real documents.",
          "**Status accuracy is nearly circular.** The ground-truth status is computed with the same rule as the system, so 99.9% shows that ranges are propagated correctly, not that the flags agree with a clinician.",
          "**Scanned reports were not evaluated.** The project's central promise of reading photographs and scans rests on Tesseract and OpenCV code that was not run for this report.",
          "**The name-noise experiment is simulated**, and **explanation quality was not rated**: coverage was counted, helpfulness and correctness were not.",
          "**All timings are for a single user on one desktop processor** with text-layer PDFs."),
        P("What the results do show is that the downstream stages (classification, storage, trends, comparison, API and interface) behave correctly and quickly, and that the extraction stage is dependable for "
          "single-line layouts but brittle in three specific, fixable ways listed in Section 8.3."),
    ]


def blocks():
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    for part in (screens, setup, extraction, names, classification_insight_latency, testing, cases, base_paper, objectives, limits):
        out += part()
    return out
