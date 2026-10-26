"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) for LabLens from facts.py, refs.py, experiments/lablens/*.json,
docs/figures, docs/diagrams and docs/screenshots. It does not read the long report chapters.

    python -m scripts.docs.build_paper            # -> <batch>/19.IEEE_Paper.docx
    python -m scripts.docs.build_paper --pdf      # also converts with Word COM and prints the page count
"""

import argparse
import os

from PIL import Image

from . import facts as F
from .paper import Paper

LAYOUT_LABEL = {"plain": "plain", "paren": "paren", "flag": "flag", "colon": "colon", "unit_last": "unit-last",
                "mixed_sep": "mixed-sep", "tabular": "tabular", "ocr_noise": "ocr-noise"}
PLACEHOLDERS = []


def crop_shot(name, out, box):
    p = os.path.join(F.FIGS, out)
    Image.open(F.shot(name)).convert("RGB").crop(box).save(p)
    return p


def diagram(name):
    """Real diagram when it exists; a grey stand-in (reported, never shipped) while the diagrams are still being drawn."""
    p = F.diag(name)
    if os.path.exists(p):
        return p
    PLACEHOLDERS.append(name)
    out = os.path.join(os.environ.get("TEMP", "."), "ph_" + name)
    Image.new("RGB", (1500, 800), (225, 225, 225)).save(out)
    return out


def build(path):
    X, N, C, I, L = F.EXTRACTION, F.NAMES, F.CLASSIF, F.INSIGHT, F.LATENCY
    O, PL, T = X["overall"], X["per_layout"], F.TESTS
    API = F.API_LAT["endpoints"]
    ENV = T["machine"]
    pct, f3 = F.pct, F.f3
    noise = N["noise"]
    sweep = {round(r["threshold"], 2): r for r in N["threshold_sweep"]}
    s30, s55, s80 = sweep[0.3], sweep[0.55], sweep[0.8]
    up = API["POST /api/reports (PDF upload)"]
    e2e = L["end_to_end_pipeline_with_db"]
    scal = L["field_extraction_scaling_by_rows"]
    single = [k for k in PL if k != "tabular"]
    single_fn = sum(PL[k]["reports_rows"] * PL[k]["row_recall"] for k in single) / sum(PL[k]["reports_rows"] for k in single)
    tests_ok = T["pytest"]["passed"]
    smoke = T["smoke_test"]["api_checks_passed"] + T["smoke_test"]["browser_checks_passed"]

    P = Paper()
    st_au = lambda n: [n.title().replace("A Navadeep", "A. Navadeep"), "Dept. of Computer Science and Engineering",
                       "TKR College of Engineering and Technology", "Hyderabad, India", "[email address]"]
    authors = [st_au(n) for n, _ in F.STUDENTS]
    authors.append([F.GUIDE.replace("L.G", "L. G.").title().replace("L. G. Reddy", "L. G. Reddy"), "[DESIGNATION], Dept. of Computer Science and Engineering",
                    "TKR College of Engineering and Technology", "Hyderabad, India", "[email address]"])
    P.title_block("LabLens: Reading, Flagging and Explaining Medical Lab Reports with Trend Tracking", authors)
    P.begin_two_columns()

    P.abstract(
        "Laboratory reports reach patients as PDFs or photographs full of abbreviations, units and reference ranges that most readers cannot interpret, and nothing links "
        "one report to the next. This paper presents LabLens, a web platform that reads an uploaded report, extracts each test name, value, unit and reference range, "
        "labels every result as low, normal or high, explains abnormal results in plain language, and plots each parameter across successive reports. Text comes from the PDF "
        "text layer, with an image-preprocessing and Tesseract fallback for scans; fields are parsed with line-level regular expressions, noisy test names are matched to a "
        "55-name dictionary with a character n-gram TF-IDF matcher, and explanations come from a curated rule base with an optional language-model rewrite. Measured on 120 generated "
        f"report PDFs in eight layouts (1,680 labelled rows), row precision is {f3(O['row_precision'])}, recall {f3(O['row_recall'])} and F1 {f3(O['row_f1'])}; range and status accuracy "
        f"are both above 99 %, while unit accuracy is {pct(O['unit_acc'])} and a layout with one table cell per line yields no rows. The pipeline needs {e2e['median_ms']:.0f} ms per "
        "report. No real or manually labelled report set and no scanned-image OCR run was available, so those results are stated as gaps.",
        ["health insights", "lab report analysis", "named entity extraction", "optical character recognition", "plain-language explanation", "trend tracking", "TF-IDF matching"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("A blood or urine test returns a table of parameters, results, units and reference ranges written for clinicians. The patient who receives it as a PDF or a phone photograph "
           "usually cannot tell which values matter, so understanding the report costs a follow-up consultation, and the delay and fear that come with it. Manual reading by staff is slow "
           "and error-prone, and a single report cannot show whether a parameter is improving or worsening. Recent work therefore either digitises image-based lab reports "
           "{r:2}, asks general vision-language models to interpret them {r:4}, or generates patient-oriented explanations and actions with language models {r:1,3}.")
    P.para("Existing tools digitise reports but do not explain them, and the explanation systems are narrow: the base paper {r:1} applies retrieval-augmented generation to one "
           "condition, metabolic syndrome, and its evaluation measures the quality of generated answers rather than the correctness of the values read from the report. No history is "
           "kept, so trends cannot be seen. The gap addressed here is a general platform for arbitrary lab parameters that extracts, flags, explains and tracks.")
    P.para("The contributions are: (1) a complete, tested pipeline from upload to a stored, flagged and explained result, served by a FastAPI layer and a React interface; "
           f"(2) a labelled evaluation harness, with a generated report corpus of 120 PDFs, that measures extraction, name matching, classification, explanation coverage and latency "
           f"({tests_ok} automated tests accompany it); (3) a measured account of where the extractor fails, with the failures traced to specific lines of the code; and (4) longitudinal "
           "trend and report-comparison views over the stored results. Section II reviews related work, Section III describes the method, Section IV reports the results and Section V concludes.")
    P.para("The project set six objectives: (1) accept reports as PDF or scanned image and extract their text with high-speed OCR; (2) identify test parameters, values, units and reference ranges; "
           "(3) compare each value with its range and flag abnormal results; (4) explain abnormal findings in plain language grounded in trusted sources; (5) track parameters across successive reports; and "
           "(6) present the results on a dashboard and evaluate extraction accuracy against manually labelled reports. Section V reports how far each was met.")
    P.sub("A", "System Hardware")
    P.para(f"All measurements were taken on one desktop: Intel Core i5-12500 ({ENV['cpu'].split('(')[1].split(' ')[0]} cores, 12 threads), {ENV['ram_gb']} GB RAM, no GPU, {ENV['os']}.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {ENV['python']}, PyMuPDF {ENV['pymupdf']} {{r:20}}, OpenCV {ENV['opencv']} {{r:17}}, scikit-learn {ENV['scikit_learn']} {{r:16}}, SQLAlchemy {ENV['sqlalchemy']}, "
           f"FastAPI {ENV['fastapi']} {{r:21}} on uvicorn {ENV['uvicorn']}, Node.js {ENV['node'].split('.')[0]} with React {ENV['react']}, Vite {ENV['vite']} and Recharts {ENV['recharts']} {{r:22}}. "
           "Tesseract {r:13} is used by the code for scans but is not installed on this machine, and no language-model key was set.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Karhade et al. {r:1} build a retrieval-augmented generation (RAG) system {r:6} on the LLaMA-3 8B model that explains blood-test results with a focus on metabolic "
           "syndrome. The knowledge base holds 20 medical books, 383 transcribed videos and a document that defines 33 blood parameters with normal, optimal and possible ranges. Text is "
           "extracted with PyMuPDF, split into 1,024-character chunks with a 100-character overlap, embedded and stored in ChromaDB; the top three chunks above a similarity threshold "
           "are added to the prompt, sources are returned with the answer, and a generic answer is given when nothing relevant is retrieved. Twenty responses were scored from 1 to 100 "
           "by GPT-4 for correctness, clarity, helpfulness and completeness; the paper states averages of 92.4, 89.7, 91.1 and 88.9, whereas the values in its own result table average "
           "94.0, 94.9, 90.1 and 88.7. It reports no extraction accuracy or latency and lists multilingual support, longitudinal personalisation and speech input as future work.")
    P.para("**Digitising and interpreting reports.** Ren et al. {r:2} argue that lab reports photographed by patients for teleconsultation should be turned into structured, stored data and "
           "propose a serialisation method for image-based reports. Bakhsheshi and Beigy {r:4} prompt three general vision-language models with questions about 100 blood-report images and "
           "compare the answers with Sentence-BERT {r:18}; they caution that the dataset is small. Checkup2Action {r:3} turns 2,000 de-identified check-up reports into structured action cards "
           "with priority, department and follow-up window; experts judged 84 % of evaluated outputs fully reasonable, and removing the safety constraints raised problem recall from 0.527 to "
           "0.825 at the price of more diagnostic overstatement.")
    P.para("**Language models for medical text.** Beyond the base paper, Salvagno et al. {r:7} examine the feasibility of ChatGPT in clinical and research scenarios, Liu et al. {r:8} study AI-generated "
           "draft replies in health records, and MEDPLAN {r:10} uses a two-stage RAG design that first assesses and then plans treatment. Medalyze {r:5} fine-tunes three FLAN-T5-Large models "
           "to summarise medical reports and extract health concerns behind a web and mobile interface. All of them generate text; none checks the numbers it was given. Table I sets the closest works side by side.")
    P.table("Representative work compared", ["Ref.", "Approach", "Data", "Reported result", "Limitation"], [
        ["{r:1}", "LLaMA-3 8B + RAG, ChromaDB", "20 books, 383 videos; 20 test answers", "Mean GPT-4 scores 88.7-94.9 of 100", "One condition; no extraction test"],
        ["{r:2}", "Serialising image-based lab reports", "Photographed reports", "Not stated in the abstract read", "Explanations not covered"],
        ["{r:4}", "General vision-language models", "100 blood-report images", "Answer similarity only", "Small set; no label check"],
        ["{r:3}", "Constrained action-card workflow", "2,000 check-up reports", "84 % outputs fully reasonable", "No value tracking"],
        ["{r:5}", "Three FLAN-T5-Large models", "Medical text", "Not stated in the abstract read", "Text only; no trends"],
    ], widths=[0.32, 0.8, 0.78, 0.8, 0.7], size=7, align=["c", "l", "l", "l", "l"])
    P.para("**Positioning.** Compared with these works, LabLens makes a narrower and more checkable claim. It does not ask a language model to read the report, so the numbers on screen are the "
           "numbers on the page, and the rule table makes every statement traceable to its source file; what it gives up is breadth of explanation and tolerance of unusual layouts, which the generated "
           "evaluation below quantifies.")
    P.para("**OCR and field extraction.** PP-OCR {r:12} is a practical, ultra-lightweight OCR system, and the open-source Tesseract engine {r:13} is a widely deployed alternative; conditional random fields "
           "{r:14} are the classical model for labelling sequences such as the name, value and unit of a test line. The work here uses neither a trained tagger nor PP-OCR: it parses the text "
           "layer with regular expressions and falls back to Tesseract. **Gap.** The survey leaves a platform that covers arbitrary lab parameters, checks the extracted values themselves, "
           "explains abnormal results and keeps the history; the abstract's PP-OCR and CRF components were not built, as Section III states.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Pipeline.** An upload (PDF, JPG, JPEG or PNG, at most 15 MB) is validated for extension, size and readability. For a PDF, each page's text layer is read with PyMuPDF; a page with fewer "
           "than 30 characters is rendered at 300 dpi instead. Images and such pages are converted to grayscale, denoised (non-local means, h = 10), thresholded with a Gaussian adaptive threshold "
           "(block 31, C = 15), deskewed from the minimum-area rectangle of the text pixels and read by Tesseract in page-segmentation mode 6. Fig. 1 shows the architecture and Fig. 2 the main flow.")
    P.figure(diagram("01_system_architecture.png"), "System architecture: React interface, FastAPI service, shared pipeline modules and the SQLite store.")
    P.para("**Field extraction.** Lines that look like headers or patient details are skipped. A regular expression takes a test name, a numeric result, an optional unit and a reference range written as "
           "'a - b', 'a to b', '<x' or '>x'. The date is read from the text, rows with neither unit nor range are dropped, and duplicates (same name, value and unit) are removed. A row's confidence "
           "is 0.9 with a two-sided range and 0.6 otherwise, minus 0.1 when the unit is missing.")
    P.figure(diagram("10_core_algorithm_flowchart.png"), "Core flow of one upload: validation, text extraction, parsing, classification, insights and storage.", width=3.3)
    P.para("**Name matching.** Raw names are cleaned and mapped to a dictionary of 55 test names. Each name is a vector of character 2- to 4-gram TF-IDF weights {r:15} computed with scikit-learn {r:16}; "
           "a name is replaced by the dictionary entry with the largest cosine similarity, s(a, b) = a.b / (|a| |b|), only if s >= 0.55; otherwise it is kept, title-cased. The threshold is analysed in Section IV.")
    P.para("**Classification and insights.** With result v and reference bounds l and h (either may be absent), the status is LOW if l is present and v < l, HIGH if h is present and v > h, NORMAL if at "
           "least one bound exists, and UNKNOWN otherwise; bounds are inclusive. The dashboard marks a result critical when v < 0.5 l or v > 1.5 h. For each LOW or HIGH result the insight module looks "
           "the test up in a curated table of 17 tests (what it measures, general causes of a low or high value) or falls back to generic wording, and always adds a suggestion to consult a clinician and "
           "a disclaimer. An optional switch rewrites the text with a language-model API {r:23} (300 output tokens) and silently falls back to the rule text on any error; this switch was not exercised "
           "in the measurements. The design replaces the base paper's retrieval step {r:1,6} by a fixed table: it cannot hallucinate but covers little.")
    P.para("**Storage and interface.** Reports, test results and insights are stored in three SQLite tables through SQLAlchemy with cascading deletes. The API serves the dashboard, report list and "
           "detail, trends, comparison of two reports and an insight feed; a trend's direction is decided from its first and last point. A single demo account protects the routes with a signed "
           "12-hour token. The React interface draws trend charts with the reference range as a shaded band.")
    P.para("**Design choices.** The extractor is rule-based because no labelled training set of real reports existed, because a trained tagger would have been impossible to check against anything, and because "
           "rules run in milliseconds on a CPU and can be read line by line when a value is wrong. Character n-grams suit test names since OCR damage changes single letters, and a similarity threshold gives an "
           "explicit trade-off between repairing noisy names and renaming genuine ones. Explanations come from a fixed table because a medical statement shown to a patient should be one the team has read; "
           "the cost is coverage, and the optional rewrite is the only path by which new wording can enter.")
    P.para("**Errors and testing.** A failure in any stage marks the report as failed, stores a readable message and keeps the text read so far; unsupported extensions, empty files, files over the limit "
           "and corrupt PDFs are rejected before processing, and a page without readable rows produces a 'no recognizable lab test rows' message rather than an empty success. The test suite covers the "
           "classification boundaries, line parsing, name matching, input validation, persistence with cascading deletes, the dashboard's critical rule, login and tampered tokens, and the upload, trend, "
           "comparison and insight routes; a separate smoke test starts its own server on a copy of the code and drives the API and a browser, so the stored data is never touched.")
    P.para(f"**Evaluation data.** No real or manually labelled lab reports were available, so a corpus was generated (seed 42): 120 PDFs with a text layer, 15 for each of eight layouts "
           "(plain, parenthesised range, flag letter, colon, unit last, mixed range separators, one table cell per line, and names corrupted with 10 % simulated per-character OCR noise). Each report "
           "has 12 tests from a pool of 40 dictionary tests and 2 tests outside the dictionary, header decoys and a collection-date line, giving 1,680 ground-truth rows. Values fall in range, below "
           "or above in roughly 55, 25 and 20 % of cases. A predicted row matches a ground-truth row by value; name, unit, range and status are then scored separately. Labels are generated, "
           "and the status label uses the project's own rule, so status accuracy measures propagation, not clinical truth.")

    P.para("**Metrics.** With TP the predicted rows matched to a ground-truth row by value, precision is TP over the rows returned and recall is TP over the ground-truth rows; F1 is their harmonic "
           "mean. Name, unit, range and status accuracy are fractions of the matched rows, and the exact-row rate is the fraction of all ground-truth rows whose four fields are all correct, so a missed row "
           "counts against it. Name matching is also tested alone: each of the 55 dictionary names is corrupted 30 times per noise level (substitution with a look-alike character, deletion or insertion) and "
           "compared with an exact match and with the standard-library difflib similarity ratio at 0.60. Latency is the median of repeated runs on the machine above, and the API is timed on the loopback address.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Extraction.** Over all 1,680 rows the extractor returns {O['predicted_rows']:,} rows with precision {f3(O['row_precision'])}, recall {f3(O['row_recall'])} and F1 {f3(O['row_f1'])} "
           f"(Table II). Among detected rows, range accuracy is {pct(O['range_acc'])}, status accuracy {pct(O['status_acc'])}, name accuracy {pct(O['name_acc'])} and unit accuracy {pct(O['unit_acc'])}; "
           f"{pct(O['exact_row_rate'])} of all ground-truth rows are recovered with every field correct. Name accuracy is {pct(O['name_acc_dict_tests'])} for dictionary tests and "
           f"{pct(O['name_acc_ood_tests'])} for the unseen ones. On the seven layouts with one test per line recall is {pct(single_fn)}; the table layout gives zero rows because every cell reaches the parser on its own line.")
    rows = []
    for k in ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]:
        d = PL[k]
        rows.append([LAYOUT_LABEL[k], d["predicted_rows"], f3(d["row_precision"]), f3(d["row_recall"]), f3(d["row_f1"]),
                     "--" if d["unit_acc"] is None else f3(d["unit_acc"]), f3(d["exact_row_rate"])])
    rows.append(["**All**", O["predicted_rows"], f"**{f3(O['row_precision'])}**", f"**{f3(O['row_recall'])}**", f"**{f3(O['row_f1'])}**", f"**{f3(O['unit_acc'])}**", f"**{f3(O['exact_row_rate'])}**"])
    P.table("Extraction on 210 generated rows per layout (1,680 in total)", ["Layout", "Rows out", "Prec.", "Recall", "F1", "Unit acc.", "Exact row"], rows,
            widths=[0.72, 0.42, 0.4, 0.42, 0.4, 0.46, 0.46], size=7, align=["l", "c", "c", "c", "c", "c", "c"])
    P.figure(F.fig("fig_extraction_by_layout.png"), "Row recall, row precision, unit accuracy and exact-row rate by report layout.", width=3.4)
    P.para(f"**Failures.** The date line was misread as a test row in all 56 reports with a dd-mm-yyyy date: '12-04-2026' becomes a test called 'Sample Collected' with value 12 and range "
           f"-4 to 2026. They account for 55 of the {O['false_positive_rows']} false-positive rows (in one report the misread row was matched to a genuine row of the same value); the other two are stray rows. Unit errors dominate the remaining mistakes ({X['failure_kinds']['field error: unit']}): the unit expression does not know mg/L, umol/L, ng/dL, uIU/mL or pg/mL, and a flag letter between "
           f"value and unit (the flag layout, unit accuracy {pct(PL['flag']['unit_acc'])}) hides the unit. 'Sodium Bicarbonate' is renamed 'Sodium', and a test missing from the dictionary can be "
           f"silently renamed. Range and status errors are rare (accuracy {pct(O['range_acc'])} and {pct(O['status_acc'])}). Figs. 4 and 5 show the screens that present the extracted rows.")
    P.figure(crop_shot("07_report_analysis.png", "paper_analysis.png", (248, 64, 1440, 1000)), "Output screen: report analysis for one stored report, with the flagged results.", width=3.4)
    P.figure(crop_shot("09_health_trends.png", "paper_trends.png", (248, 64, 1440, 720)), "Output screen: haemoglobin across six uploaded reports against its reference band.", width=3.4)
    P.para(f"**Name matching.** At 5, 10 and 20 % per-character noise over {N['n_dictionary_names']} names the shipped matcher is right in {pct(noise['0.05']['tfidf_0.55'], 0)}, "
           f"{pct(noise['0.1']['tfidf_0.55'], 0)} and {pct(noise['0.2']['tfidf_0.55'], 0)} of 30 trials per name, exact matching in {pct(noise['0.05']['exact_match'], 0)}, {pct(noise['0.1']['exact_match'], 0)} and "
           f"{pct(noise['0.2']['exact_match'], 0)}, and a plain difflib ratio at 0.60 in {pct(noise['0.05']['difflib_0.60'], 0)}, {pct(noise['0.1']['difflib_0.60'], 0)} and {pct(noise['0.2']['difflib_0.60'], 0)} (Fig. 6). "
           f"The baseline is more noise-tolerant than the matcher that was shipped. Lowering the threshold from 0.55 to 0.30 lifts accuracy at 10 % noise from {pct(s55['acc_noise_10'])} to {pct(s30['acc_noise_10'])} but "
           f"raises the share of 24 unseen names wrongly snapped to a dictionary entry from {pct(s55['false_snap_rate_ood'], 0)} to {pct(s30['false_snap_rate_ood'], 0)}; at 0.80 nothing is snapped wrongly but accuracy at 10 % noise "
           f"falls to {pct(s80['acc_noise_10'], 0)} (Fig. 7). Common abbreviations (Hb, TLC, LDL, HDL) are not matched, and only {pct(s55['synonym_acc'], 0)} of 19 synonyms are.")
    P.figure(F.fig("fig_name_noise.png"), "Test-name accuracy under simulated character noise: shipped TF-IDF matcher, difflib baseline and exact match.", width=3.0)
    P.figure(F.fig("fig_threshold_sweep.png"), "Effect of the matching threshold on accuracy under noise, on unseen names wrongly snapped and on synonyms; the dashed line is the shipped 0.55.", width=3.2)
    P.para(f"**Classification and explanations.** Against an independently written rule, the classifier disagreed on none of {C['random_cases']:,} random cases, and inclusive bounds behave as specified. "
           f"The explanation table covers {I['dictionary_tests_with_specific_text']} of {I['dictionary_tests']} dictionary tests ({pct(I['coverage_of_dictionary'])}); in the corpus only {I['abnormal_rows_with_specific_text']} of "
           f"{I['abnormal_dictionary_rows_in_corpus']} abnormal dictionary rows ({pct(I['abnormal_rows_specific_rate'])}) receive test-specific text and the rest get the generic wording. Clinical correctness of the "
           "explanations was not evaluated.")
    P.para(f"**Performance and testing.** For a 14-row, one-page text PDF, the median time is {L['text_layer_extraction']['median_ms']:.1f} ms for text extraction, {L['field_extraction']['median_ms']:.1f} ms "
           f"for field extraction and {e2e['median_ms']:.1f} ms for the whole pipeline including the database (95th percentile {e2e['p95_ms']:.1f} ms, 40 runs); field extraction grows linearly, from "
           f"{scal['14']['median_ms']:.0f} ms at 14 rows to {scal['200']['median_ms']:.0f} ms at 200. Through HTTP on the loopback interface an upload takes {up['median_ms']:.0f} ms (95th percentile "
           f"{up['p95_ms']:.0f} ms), and the read endpoints 1-16 ms. {tests_ok} pytest tests and {smoke} smoke checks (24 API, 7 browser) pass. Scanned-image OCR accuracy and speed were not measured, "
           "because Tesseract is absent on the test machine; the <10 s target of the abstract is met for text-layer PDFs only (Fig. 8).")
    P.figure(F.fig("fig_latency_stages.png"), "Median latency of each pipeline stage for the 14-row report.", width=3.0)
    P.para("**Worked example.** The demo library holds five invented report PDFs (April to October 2026, 14 tests each) generated by the product's own seeding route, plus one uploaded file; all pass through "
           "the same pipeline. The dashboard then shows 6 reports and 82 extracted tests, of which 54 are normal, 28 abnormal and 2 critical. For the August report, 5 of 14 results are normal and 9 abnormal, each "
           "with an explanation (Fig. 4); haemoglobin rises from 10.8 to 13.1 g/dL over the six reports and is below its 12 g/dL limit in the first three (Fig. 5). Those values are demonstration data, not patient data.")
    P.para("**Threats to validity.** The corpus and the parser were written by the same team, so layouts the authors did not think of are absent; the generated names, units and ranges come from the same "
           "vocabulary the dictionary was built from, which favours the matcher; noise is simulated on a text layer, not produced by an optical scanner; the status label reuses the project's rule; and every "
           "figure comes from one run on one machine with a fixed seed, with no confidence intervals. The extraction numbers should therefore be read as a regression baseline for this code, not as an "
           "estimate of accuracy on real laboratories' reports. Security is demonstration-grade: one shared account, no per-user separation of reports and no transport encryption.")
    P.para("**What the errors mean for a reader.** Range and status accuracy are above 99 % among detected rows, so a value that is read is almost always flagged correctly. The costly errors are therefore "
           "silent ones: a missed row simply does not appear, so a user of a table-layout report sees nothing and is told that no recognizable rows were found, but one missing row in an otherwise complete report "
           "gives no warning. A date line read as a test is harmless to the flags (its range -4 to 2026 makes it normal) but clutters the list and the counts. A wrong name is worse, because the explanation "
           "that follows belongs to the wrong test, as when Sodium Bicarbonate receives the text for Sodium.")
    P.para("**Comparison with the base paper.** The two studies are not comparable. The base paper {r:1} scores 20 generated answers with GPT-4 and measures no extraction; this study scores extraction "
           "against generated labels and does not evaluate explanation quality. The base paper retrieves from a 20-book and 383-video knowledge base; here explanations come from a 17-entry table. What "
           "this work adds is a measured extraction stage, general parameters instead of 33 chosen for one syndrome, and stored history with trends.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("Of the six objectives, flagging results against reference ranges (3) and tracking parameters over reports (5) were met and tested. Objective 1 was met in part: text-layer PDFs are read in "
           "milliseconds, but scanned-image OCR through Tesseract is unmeasured and PP-OCR is not used. Objective 2 was met in part: the parser is regular-expression based, not a trained CRF tagger. "
           "Objective 4 was met in part: explanations are curated rules for 17 tests, with no retrieval or citations, and the language-model switch is untested. Objective 6 was met in part: the dashboard "
           "exists, but accuracy was evaluated on generated reports, not manually labelled ones. The key finding is that field values are read reliably when each test sits on one line "
           f"(F1 {f3(O['row_f1'])} overall, range and status accuracy above 99 %), while units, table layouts, date lines and name matching are the weak points. Storage is a single-user SQLite file with a demo "
           "login, and the platform is educational, not a medical device.")
    P.para("Future work: parse table cells by position, recognise the unit and date patterns that failed, replace the name matcher by a better-tuned or trained one, widen the explanation base with retrieval and "
           "citations, and measure OCR and the language-model switch on real, manually labelled reports.")

    P.references()
    P.save(path)
    return path, len(P.order)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    print(build(out), "placeholders:", PLACEHOLDERS)
    if a.pdf:
        from .comlock import ComLock
        from .word_finalize import finalize
        with ComLock():
            print(finalize(out, pdf=os.path.join(F.BATCH, "19.IEEE_Paper.pdf")))
