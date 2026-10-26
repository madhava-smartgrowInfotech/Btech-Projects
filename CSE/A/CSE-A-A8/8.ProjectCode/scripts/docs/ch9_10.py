"""Chapters 9 and 10 and the sections reused by the scope, methodology, design and conclusion documents."""

from .appendix import source
from .blocks import B, CODE, H1, H2, H3, N, P, TAB
from .ch1 import ASSUMPTIONS, CONTRIBUTIONS, LIMITATIONS, SCOPE_IN, SCOPE_OUT
from .refs import n
from . import facts as F


def _trim(code):
    """Drop trailing divider comment lines (`# -----`) that precede the next section in a source file."""
    lines = code.split("\n")
    while lines and (not lines[-1].strip() or set(lines[-1].strip()) <= set("#- ")):
        lines.pop()
    return "\n".join(lines)


# ------------------------------------------------------------------ methodology document extras
def novelty_blocks():
    o = F.EXTRACTION["overall"]
    return [
        P(f"The base paper {n(1)} is a retrieval-augmented question-answering assistant for one condition. This project is a different kind of system, so the comparison is about scope and "
          "evidence, not about a better score on a shared benchmark. No benchmark is shared."),
        TAB("Base paper and this project", ["Aspect", "Base paper", "LabLens"], [
            ["Purpose", "advice on metabolic syndrome from a blood report", "a general reader for any laboratory report: extract, flag, explain, store, track"],
            ["Parameters", "33 fixed metabolic-syndrome parameters", f"any `name value unit range` row; a {F.NAMES['n_dictionary_names']}-name dictionary only normalises spelling"],
            ["Explanation engine", "LLaMA-3 8B with retrieval over books and transcripts", "curated rules, optional LLM rewrite; deterministic by default and never diagnostic"],
            ["Memory across reports", "stored reports are consulted in later queries; trends are future scope", "per-test trend chart against the reference band and two-report comparison"],
            ["Evidence", "20 responses rated by GPT-4", f"{o['reports_rows']:,} labelled rows in 120 generated reports, 20,000 classification cases, 36 tests, latency"],
        ], widths=[1.2, 2.3, 2.5], size=10, align=["l", "l", "l"]),
        H3("What is new"),
        B("**Breadth of input.** The base paper's system answers about 33 chosen parameters. LabLens reads whatever rows a report contains, keeps tests it does not know under the name printed, and snaps only close spellings.",
          "**Longitudinal use.** Results are stored per report and organised by test, so a user sees a value against its reference band over time and compares two reports.",
          "**A measured extraction stage.** The base paper does not report extraction accuracy. Here the extraction is scored on a labelled corpus, per layout and per field, with its failures listed.",
          "**Conservative explanation design.** Every explanation is general, framed as possible causes, ends with a suggestion to see a professional and cannot be produced without the disclaimer."),
        H3("What is not new"),
        P(f"None of the individual techniques is original: PDF text-layer reading {n(20)}, Tesseract OCR {n(13)}, regular-expression line parsing, TF-IDF vectors {n(15)} with cosine similarity {n(16)}, "
          f"threshold rules, a SQL store {n(19)} and a REST service {n(21)} are all standard. The abstract's PP-OCR {n(12)}, CRF tagging {n(14)} and retrieval-augmented generation {n(6)} would be the "
          "more current techniques; they were not built, and Chapter 8 shows where that costs accuracy (names, units and unseen tests). The contribution is the integration, the longitudinal feature set and the honest measurement."),
    ]


def contribution_blocks():
    return [
        P("The contributions below are stated with the evidence that supports each; none is a claim of state-of-the-art performance."),
        N(*CONTRIBUTIONS),
    ]


def scope_blocks():
    return [
        P("LabLens is an educational tool that helps a reader understand the structure of a laboratory report. The boundaries of what it does and does not do are listed explicitly, "
          "because the product handles health information and users must not over-trust it."),
        H2("1.1 In scope"),
        B(*SCOPE_IN),
        H2("1.2 Out of scope"),
        B(*SCOPE_OUT),
    ]


def assumption_blocks():
    return [
        P("The design and every measurement in this report rest on the following assumptions. If one fails, results degrade as described under the limitations."),
        B(*ASSUMPTIONS),
        P("Constraints of the build itself: the work was done by a four-member team on one desktop computer without a GPU, with no access to real patient reports, "
          "no Tesseract installation on the measurement machine and no LLM API key. Each constraint shaped what could be measured."),
    ]


def limitation_blocks():
    o = F.EXTRACTION["overall"]
    return [
        P("The limitations below come from measurement, not from speculation. Each is traced to a table or a failure case in Chapter 8."),
        B(*LIMITATIONS),
        TAB("Effect of the main limitations on a user", ["Limitation", "What the user sees", "Remedy (see future scope)"], [
            ["Cell-per-line tables unsupported", "report marked Failed, or a single bogus row if the date uses hyphens", "table-aware parser using word positions"],
            ["Date line read as a test", "an extra `Sample Collected` row; test count one too high", "reject rows whose range contains a year or whose name is a header word"],
            ["Unit list incomplete", "unit shown as blank; value and flag still right", "extend the unit expression; read units from the range side"],
            ["Name snapping to a wrong test", "a result plotted under the wrong test", "word-boundary and length checks, synonym table, show a confidence badge"],
            ["Thin explanation coverage", f"generic text for {F.pct(1 - F.INSIGHT['abnormal_rows_specific_rate'], 0)} of abnormal rows", "extend the knowledge base; add cited retrieval"],
        ], widths=[1.8, 2.3, 1.9], size=9.5, align=["l", "l", "l"]),
        P(f"The extraction F1 of {F.f3(o['row_f1'])} should be read with the corpus caveat: it comes from generated reports and probably overstates performance on real ones."),
    ]


def not_measured_blocks():
    return [
        P("Several things a reader might expect have no number in this report. They are listed here so that their absence is not mistaken for a result."),
        TAB("Not measured", ["Item", "Reason", "Consequence"], [
            ["Accuracy and latency of scanned-image and photograph OCR", "Tesseract is not installed on the measurement machine", "the OpenCV + Tesseract path is untested; the abstract's low-quality-scan claim is unsupported"],
            ["Comparison with PP-OCR", "PP-OCR was not integrated", "no evidence either way for the abstract's choice"],
            ["Quality of the optional LLM rewrite", "no `ANTHROPIC_API_KEY` was available", "its wording, correctness and latency are unknown"],
            ["Helpfulness and correctness of explanations", "no clinician or model rating was done", "coverage is counted, quality is not"],
            ["Accuracy on real, manually labelled reports", "no such reports were available", "the corpus is generated; real-world accuracy is unknown"],
            ["Many simultaneous users, large libraries", "single-user tests only", "scalability of SQLite and the in-process pipeline is unknown"],
            ["Responsive and accessibility checks", "`scripts/ui_check.py` was not re-run for this report", "the screens were seen at 1440 x 900 only in these documents"],
        ], widths=[2.0, 1.8, 2.2], size=9.5, align=["l", "l", "l"]),
    ]


# ------------------------------------------------------------------ design document extras
def walkthrough_blocks():
    s = source
    return [
        P("The excerpts below are taken from the repository by the build script, so they are the code that was tested and measured."),
        H2("3.1 Reading one line of a report (`ner_processor.py`)"),
        P("A row is recognised in two stages. The first pattern requires a name followed by a number and optionally a unit; the rest of the line is then searched for a two-sided range, then a one-sided limit, "
          "then a trailing unit. Keeping the stages separate lets the range appear in any common format without one very long pattern."),
        CODE(_trim(s("ner_processor.py", "_NAME_VALUE_PATTERN = re.compile(", "# Common test-date formats")), 8.5),
        P("The extraction loop applies the patterns line by line, assigns a confidence of 0.9 when both limits were found and 0.6 otherwise (minus 0.1 without a unit) and discards a row that has neither a range nor a unit. "
          "That last rule is why a slash-formatted date is rejected, and why a hyphenated one is not."),
        CODE(_trim(s("ner_processor.py", "    for raw_line in text.splitlines():", "def _deduplicate")), 8.5),
        H2("3.2 Normalising a test name (`ner_processor.py`)"),
        CODE(_trim(s("ner_processor.py", "def normalize_test_name", "# Regex patterns for line-level extraction")), 8.5),
        P("The dictionary vectors are computed once at import. A name is snapped only when the best cosine similarity reaches 0.55; below that, the cleaned name is kept, which is how unseen tests survive "
          "and also how a close-but-different test can be renamed."),
        H2("3.3 Classification (`result_analyzer.py`)"),
        CODE(_trim(s("result_analyzer.py", "def classify_result", "def analyze_results")), 8.5),
        H2("3.4 Running the stages for one report (`report_processor.py`)"),
        P("The report row is created first, so that a failure at any later stage leaves a visible `Failed` record with its error message and the text already extracted."),
        CODE(_trim(s("report_processor.py", "    # 2. OCR / text extraction", "    # 4. Classification")), 8.5),
        H2("3.5 Trends and comparison (`backend/main.py`)"),
        CODE(_trim(s("backend/main.py", '@app.get("/api/trends")', '@app.get("/api/compare")')), 8.5),
        P("The trend direction is decided by comparing only the last and first value; a rise followed by a fall back to the start is reported as stable. This is simple and visible, and it is listed as a limitation."),
    ]


def decision_blocks():
    return [
        P("Each decision below was taken for a stated reason, and the measured consequence is given where one exists."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason", "Measured consequence"], [
            ["Regex line parser for the four fields", "trained CRF tagger as in the abstract", "no labelled training data exists; a parser is deterministic and fast", f"F1 about 0.98 on single-line layouts ({F.f3(F.EXTRACTION['overall']['row_f1'])} over all eight); fails on cell-per-line tables"],
            ["TF-IDF character n-grams to snap names", "`difflib` ratio; exact match; learned embedding", "one sparse product, vectors computed once", "worse than `difflib` under noise (0.890 against 0.981 at 10%)"],
            ["Keep unmatched names as read", "reject unknown tests", "any lab test should still be extracted", "unseen tests are kept, but some are renamed"],
            ["Reference range read from the report itself", "built-in range table", "ranges depend on laboratory, age and sex", "status accuracy 99.9% when the range is read correctly"],
            ["Rule-based explanations, optional LLM rewrite", "RAG with a vector store", "offline, deterministic and safe by default; no corpus to license", "30.9% of tests have specific text; no citations"],
            ["SQLite through SQLAlchemy", "Supabase PostgreSQL", "no account or network needed; one file", "single-user only; no row-level security"],
            ["FastAPI + React, original Streamlit app kept", "Streamlit only", "a faster, richer interface over the same modules", f"API reads under {max(v['median_ms'] for k, v in F.API_LAT['endpoints'].items() if k.startswith('GET')) + 1:.0f} ms; upload {F.API_LAT['endpoints']['POST /api/reports (PDF upload)']['median_ms']:.0f} ms"],
            ["HMAC-signed 12-hour token, one demo account", "full user registration", "the original product had no login; enough to protect the API in a demo", "no per-user separation"],
            ["Sample reports rendered as PDFs and sent through the pipeline", "hand-inserted database rows", "the demo data then exercises the real code path", "screens show genuine pipeline output"],
            ["Limits inclusive in classification", "exclusive limits", "a value on the printed limit is within the range", "20,000-case check, 0 disagreements"],
        ], widths=[1.5, 1.2, 1.8, 1.5], size=9, align=["l", "l", "l", "l"]),
    ]


# ------------------------------------------------------------------ chapters 9 and 10
def conclusion_blocks():
    o = F.EXTRACTION["overall"]
    Nn = F.NAMES["noise"]
    T = F.TESTS
    lat = F.LATENCY["end_to_end_pipeline_with_db"]["median_ms"]
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        P("The project set out to turn a laboratory report into something a patient can read. It delivers a working system in which an uploaded PDF or image is read, its test rows are extracted, each result is compared with the "
          "reference range printed beside it, abnormal results receive a plain-language and non-diagnostic explanation, and everything is stored so that values can be followed over time and two reports compared. "
          "A FastAPI service, a React interface, the original Streamlit application, an automated test suite and a reproducible evaluation harness complete the work."),
        H2("9.2 Objectives achieved"),
        P("Two of the six objectives were fully met: flagging abnormal results (objective 3) and tracking parameters across reports (objective 5). Four were met in part. "
          "Text extraction works for digital PDFs, but the scanned-image path could not be run (objective 1). Field extraction is a regex-and-TF-IDF parser, not the trained NER model the abstract names (objective 2). "
          "Explanations are curated rules for 17 tests without retrieval or citations (objective 4). The dashboard exists, but extraction accuracy was measured on generated reports, not on manually labelled real ones (objective 6). Section 8.11 gives the evidence."),
        H2("9.3 Key findings"),
        B(f"On single-line layouts the parser extracts rows well (F1 about 0.98) and, once a row is read, the range and status are almost always right ({F.pct(o['range_acc'])} and {F.pct(o['status_acc'])}); "
          f"over all eight layouts of the generated corpus the F1 is {F.f3(o['row_f1'])}.",
          "The weak points are specific and fixable: cell-per-line tables (recall 0), a hyphenated date read as a test, a short unit list, and names outside the dictionary that are renamed.",
          f"A plain `difflib` matcher beat the shipped TF-IDF matcher on noisy names ({Nn['0.1']['difflib_0.60']:.3f} against {Nn['0.1']['tfidf_0.55']:.3f} at 10% noise), so the choice of TF-IDF is not justified by accuracy.",
          f"The pipeline is fast: a median of {lat:.0f} ms per text-layer report and about {F.API_LAT['endpoints']['POST /api/reports (PDF upload)']['median_ms']:.0f} ms for an HTTP upload, far below the 10-second target, although the target was set for scanned input.",
          f"The system is verified by {T['pytest']['passed']} pytest cases and {T['smoke_test']['api_checks_passed'] + T['smoke_test']['browser_checks_passed']} smoke checks (API and browser), all passing."),
        H2("9.4 Practical applications"),
        B("A patient-facing reader that explains in everyday words what a report lists and which values lie outside their range, with a clear disclaimer.",
          "A library that lets a person keep several reports together and see a test move over months, as the sample data does for haemoglobin and LDL cholesterol.",
          "A teaching and research scaffold for report digitisation: the generated corpus, the scoring script and the failure analysis can be reused to test a better parser."),
        H2("9.5 Known limitations"),
        B(*LIMITATIONS[:5]),
    ]


def chapter9_blocks():
    return conclusion_blocks()


def future_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        H2("10.1 Improvements to the extraction"),
        B("**A table-aware parser.** Use word coordinates from the PDF (PyMuPDF can return them) to rebuild rows from cell-per-line tables, closing the 210-row gap measured in Chapter 8.",
          "**Reject date rows.** Discard candidate rows whose range holds a year or whose name is a header word, which removes almost every false positive found.",
          "**A full unit table** (mg/L, umol/L, ng/dL, uIU/mL and others), and unit detection that tolerates a flag letter between value and unit.",
          "**A synonym table and a safer matcher.** Add abbreviations (Hb, TLC, LDL), test a `difflib` or learned matcher against the TF-IDF one, and refuse to rename names that merely extend a dictionary name.",
          f"**Trained entity recognition** {n(14)} and a layout-aware OCR engine such as PP-OCR {n(12)} once labelled reports exist, compared with the current parser on the same corpus."),
        H2("10.2 Better explanations"),
        B(f"**Retrieval with citations:** a curated, licensed knowledge base with retrieval {n(6)} so that each explanation names its source, as the base paper does {n(1)}.",
          "**More tests covered:** extend the 17-test knowledge base to the whole dictionary, then rate the text with a clinician.",
          "**Optional LLM rewrite:** test it with an API key for quality, cost and failure behaviour.",
          "**Multilingual output** for users who read the report in one language and need the explanation in another."),
        H2("10.3 Evaluation and deployment"),
        B("**Real, labelled reports.** With consent and de-identification, build a small manually labelled set and repeat the extraction experiment on it; evaluate scanned reports and photographs with Tesseract and with PP-OCR.",
          "**Per-user accounts** with registration, row-level separation of data and audit logging, replacing the single demo account.",
          "**Deployment:** containers, HTTPS, a server database in place of SQLite, and monitoring of failed reports and unmatched names.",
          "**Load and accessibility testing** with many users and assistive technology."),
        H2("10.4 Further research"),
        B(f"Comparing general vision-language models, as in {n(4)}, with the parser on the same photographed reports.",
          f"Turning a report into a short list of follow-up actions, as in {n(3)}, with safeguards against unsupported claims.",
          "Trend analysis beyond first-versus-last: slopes, variability and alerts, with the sample date rather than the upload date on the time axis.",
          "A study of how readers understand and act on the explanations."),
    ]


def chapter10_blocks():
    return future_blocks()
