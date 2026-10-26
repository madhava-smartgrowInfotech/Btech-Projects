"""Chapter 6: Methodology and software implementation. Numbers are read from experiments/lablens/*.json through facts.py."""

import os

from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from . import facts as F


def _opt_fig(name, caption, width=5.6):
    """Chart produced by scripts/make_figures.py; skipped (not faked) when the file is absent."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _sweep_rows():
    keep = {0.35, 0.45, 0.55, 0.65, 0.75}
    rows = []
    for s in F.NAMES["threshold_sweep"]:
        if round(s["threshold"], 2) in keep:
            mark = " (shipped)" if abs(s["threshold"] - 0.55) < 1e-9 else ""
            rows.append([f"{s['threshold']:.2f}{mark}", F.pct(s["acc_noise_10"]), F.pct(s["acc_noise_20"]),
                         F.pct(s["false_snap_rate_ood"]), F.pct(s["synonym_acc"])])
    return rows


def methodology_blocks():
    ov = F.EXTRACTION["overall"]
    nz = F.NAMES["noise"]
    return [
        H2("6.1 Overall methodology"),
        P("LabLens is a pipeline of deterministic stages, not a trained model. A report file enters, text comes out of it, the text is parsed into rows, each row is "
          "compared with its own reference range, and a plain-language note is attached to every abnormal row. No stage learns from data: the only fitted object "
          "is the term-weighting of a 55-name dictionary, computed when the module is loaded. This keeps every decision inspectable (a row is flagged because a "
          "number is outside a printed range) and keeps the whole system runnable on a laptop without a GPU or a download of model weights."),
        FIG(F.diag("02_high_level_workflow.png"), "Overall workflow of the LabLens pipeline", 5.6),
        N("**Validate** the upload: extension in {pdf, jpg, jpeg, png}, not empty, at most 15 MB (`ocr_processor.validate_file`).",
          "**Extract text**: the PDF text layer for digital reports; OpenCV preprocessing and Tesseract for scanned pages and photographs.",
          "**Parse rows**: a line-level regular-expression parser finds the name, value, unit and reference range of each result.",
          "**Normalise names**: a TF-IDF character n-gram matcher snaps noisy test names to a dictionary of 55 canonical names.",
          "**Classify**: LOW, NORMAL, HIGH or UNKNOWN by comparison with the row's own reference range.",
          "**Explain**: a curated knowledge base (and optionally a language model) writes what the test measures, general possible causes and a suggestion to consult a clinician, for LOW and HIGH rows only.",
          "**Store and trend**: rows go to SQLite; later reports of the same test form a trend, and any two reports can be compared."),
        H2("6.2 Data used for development and evaluation"),
        P("The project ships no dataset, and no real patient report was available for the evaluation. All measurements therefore use **generated** data with known "
          "ground truth, and this limit applies to every number in Chapters 7 and 8. Two generated sources exist."),
        P("**Demonstration reports.** `backend/demo_data.py` draws five one-page PDFs with an embedded text layer (14 tests each, an invented patient, dates from "
          "April to October 2026) and sends them through the unchanged pipeline. They provide the data behind every screenshot and the latency measurements; their "
          "values are chosen so that haemoglobin rises and cholesterol falls across the five reports."),
        P("**Evaluation corpus.** `scripts/run_experiments.py` generates 120 PDF reports with a fixed random seed of 42: eight layouts of 15 reports. Each report lists 14 "
          "tests: 12 drawn from a pool of 40 tests that are in the dictionary and 2 drawn from a pool of 8 that are not (for example lipase and cortisol), together "
          "with header lines that look like data (a phone number, a registration number) and a collection-date line. Values are drawn so that about 55 % lie "
          "inside the range, 25 % below and 20 % above. The corpus holds 1,680 labelled rows. The ground-truth status uses the same comparison rule as the code, so the "
          "status accuracy reported later measures whether errors in parsing propagate, not whether the rule is clinically right."),
        TAB("Layouts of the evaluation corpus (15 reports each)", ["Layout", "Example of one row as it appears in the text layer"], [
            ["plain", "`Hemoglobin 10.8 g/dL 12 - 16`"],
            ["paren", "`Hemoglobin 10.8 g/dL (12 - 16)`"],
            ["flag", "`Hemoglobin 10.8 L g/dL 12 - 16` (a flag letter after the value)"],
            ["colon", "`Hemoglobin: 10.8 g/dL   Ref: 12 - 16`"],
            ["unit_last", "`Hemoglobin 10.8 12 - 16 g/dL`"],
            ["mixed_sep", "`Hemoglobin 10.8 g/dL 12 to 16` (separator `-`, `to` or no spaces)"],
            ["tabular", "name, value, unit and range as four separate text cells, one per line when extracted"],
            ["ocr_noise", "`Hemogl0bin 10.8 g/dL 12 - 16` (10 % of name characters corrupted, simulated)"],
        ], widths=[1.0, 5.3], size=9.5),
        P("Two simplifications must be stated. The `ocr_noise` layout corrupts characters in a **text-layer** PDF, so it imitates the effect of OCR noise on names but "
          "does not exercise Tesseract or the OpenCV stage; and no layout of the corpus comes from a real laboratory. The performance of the OCR path on scanned reports "
          "is therefore **not measured** (Tesseract is not installed on the test machine)."),
        H2("6.3 Text extraction and image preprocessing"),
        P("For a PDF, PyMuPDF [20] reads the text layer of every page. A page whose layer holds fewer than 30 characters is treated as scanned: it is rendered at 300 dpi "
          "(zoom 300/72), preprocessed and recognised by Tesseract [13]. This is the same decision rule for a mixed document, so a report that combines digital and "
          "scanned pages is handled page by page. A JPG or PNG upload is decoded with Pillow and goes straight to the image branch. The preprocessing parameters are those of "
          "`preprocess_image_for_ocr`:"),
        TAB("Image preprocessing before Tesseract", ["Step", "OpenCV call and parameters", "Purpose"], [
            ["1 Grayscale", "`cvtColor` BGR to gray", "Colour carries no information for printed text"],
            ["2 Denoise", "`fastNlMeansDenoising`, h = 10", "Removes scanner noise while keeping stroke edges"],
            ["3 Threshold", "`adaptiveThreshold`, Gaussian, block size 31, C = 15", "Copes with uneven lighting and shadows better than one global threshold"],
            ["4 Deskew", "`minAreaRect` of the foreground pixels, rotation by the estimated angle with cubic interpolation", "Straightens a tilted page; skipped when fewer than 20 foreground pixels or an angle below 0.5 degrees"],
            ["5 Recognise", "`image_to_string`, `--psm 6`", "Page segmentation mode 6 assumes one uniform block of text, which suits line-by-line result tables"],
        ], widths=[1.0, 2.9, 2.4], size=9.5),
        P("Tesseract is an optional dependency. If it is missing, an image upload fails with an OCR error message, the report is kept as Failed and "
          "digital PDFs are unaffected. The base paper [1] describes PDF parsing of the uploaded report and no image or scan branch; the survey paper [2] addresses reports "
          "photographed with a phone."),
        H2("6.4 Row parsing"),
        P("A laboratory report is semi-structured: most rows follow the pattern *name, value, unit, range*. The parser therefore works line by line with regular "
          "expressions in two stages, so that the range can be written in any common way without one giant pattern having to match the whole line."),
        P("**Stage 1** anchors at the start of the line: a name (a letter followed by letters, digits and `()/,.-` and spaces, lazily up to 60 characters), an optional "
          "`:` or `-`, whitespace, a signed decimal value, and an optional unit chosen from a fixed list of 23 patterns (for example `%`, `g/dL`, `mg/dL`, `mmol/L`, `IU/L`, "
          "`ng/mL`, `U/L`, `mEq/L`, `fL`, `pg`, `mm/hr`, `10^3/uL`). **Stage 2** searches the remainder of the line for a two-sided range (`low` and `high` separated by `-`, "
          "`to`, an en dash or an em dash) and, failing that, for a one-sided limit: `<5` becomes an upper limit of 5 and `>40` a lower limit of 40. If no unit was found "
          "in stage 1, a unit at the very end of the remainder is accepted."),
        CODE('''_NAME_VALUE_PATTERN = re.compile(
    r"^\\s*(?P<name>[A-Za-z][A-Za-z0-9()/,.\\- ]{1,60}?)\\s*[:\\-]?\\s+"
    r"(?P<value>-?\\d+\\.?\\d*)\\s*(?P<unit>" + _UNIT_RE + r")?", re.IGNORECASE)
_TWO_SIDED_RANGE_PATTERN = re.compile(r"(?P<low>-?\\d+\\.?\\d*)\\s*(?:-|to|–|—)\\s*(?P<high>-?\\d+\\.?\\d*)")
_ONE_SIDED_RANGE_PATTERN = re.compile(r"([<>])\\s*(-?\\d+\\.?\\d*)")'''),
        P("Before parsing, a line is skipped if it is shorter than three characters, matches a header word on its own (patient, name, age, date, sample, result, "
          "reference, unit and similar) or contains no digit. After parsing, a row is **dropped** if it has neither a range nor a unit, because a bare name and "
          "number is more likely a header or a phone number than a result. Each kept row receives a confidence score:"),
        EQ("c = 0.9 if both limits are present, else 0.6;   c ← c − 0.1 if no unit;   c ← max(c, 0.1)"),
        P("The report date is the first match of three patterns (`dd/mm/yyyy` and `dd-mm-yyyy`, `yyyy-mm-dd`, `dd Month yyyy`) that parses with one of eight formats. "
          "Finally exact duplicates (same lower-cased name, value and unit) are removed, which repairs the doubled lines that OCR sometimes produces."),
        P("Because the parser is a set of fixed patterns, its failure modes are predictable and were found by the experiments of Chapter 7: a date such as "
          "`12-04-2026` on a line that starts with a word is read as a row with value 12 and a range of -4 to 2026; a layout in which every table cell is on its own line "
          "yields no row at all; and a unit outside the fixed list (for example `mg/L`, `umol/L` or `ng/dL`) is left empty."),
        H2("6.5 Test-name normalisation"),
        P("OCR corrupts names (\"Hemogl0bin\"), laboratories spell them differently (\"Haemoglobin\") and the same test is the key of every trend, so names are matched "
          "to a dictionary of 55 canonical names. Each name is represented by its character n-grams of length 2 to 4 inside word boundaries (scikit-learn "
          "`TfidfVectorizer` with `analyzer=\"char_wb\"` [16]) and weighted with TF-IDF [15]. With *n* dictionary entries and *df(t)* the number of entries that contain "
          "n-gram *t*, the smoothed inverse document frequency and the weight of *t* in a name *d* are"),
        EQ("idf(t) = ln((1 + n) / (1 + df(t))) + 1,     w(t, d) = tf(t, d) · idf(t),     vectors scaled to unit length"),
        P("A cleaned query name *q* (non-alphanumeric characters removed) is compared with every dictionary vector *k* by cosine similarity, which for unit-length "
          "vectors is the dot product, and is snapped to the best entry when the similarity reaches the threshold of 0.55:"),
        EQ("cos(q, k) = (q · k) / (‖q‖ ‖k‖);     name = K[argmax cos(q, k)] if max cos ≥ 0.55, else the cleaned query"),
        P("A name that matches nothing is kept, upper- or lower-case names being converted to title case, so a test outside the dictionary is still extracted. The "
          "threshold is a compromise that the experiments make visible. At 0.55 the matcher recovers "
          f"{F.pct(nz['0.05']['tfidf_0.55'])}, {F.pct(nz['0.1']['tfidf_0.55'])} and {F.pct(nz['0.2']['tfidf_0.55'])} of the names at 5 %, 10 % and 20 % simulated "
          "character noise, but a simple edit-distance baseline (`difflib`, ratio 0.60) recovers "
          f"{F.pct(nz['0.05']['difflib_0.60'])}, {F.pct(nz['0.1']['difflib_0.60'])} and {F.pct(nz['0.2']['difflib_0.60'])}. Raising the threshold removes false "
          "matches of unseen names but loses noisy ones:"),
        TAB("Effect of the snap threshold (55 names x 30 noisy trials; 24 unseen names; 19 synonyms)",
            ["Threshold", "Accuracy, 10 % noise", "Accuracy, 20 % noise", "Unseen names wrongly snapped", "Synonyms resolved"],
            _sweep_rows(), widths=[1.3, 1.2, 1.2, 1.4, 1.2], size=9.5, align=["l", "c", "c", "c", "c"]),
        *_opt_fig("fig_threshold_sweep.png", "Name-matcher accuracy, false-snap rate and synonym accuracy against the similarity threshold", 5.2),
        P("The method was kept because it needs no training data, is fast (about 0.6 ms per row) and handles inserted, missing and substituted letters; its documented "
          "weaknesses are abbreviations and synonyms (\"Hb\", \"TLC\", \"LDL\" are not matched at 0.55) and names that contain a dictionary name (\"Sodium Bicarbonate\" "
          "becomes \"Sodium\")."),
        H2("6.6 Result classification"),
        P("Classification compares the value *v* with the reference limits *ℓ* (low) and *h* (high) printed **on the same row**, so the result follows the "
          "laboratory's own range for that patient and method instead of a generic table:"),
        EQ("status(v) = LOW if v < ℓ;   HIGH if v > h;   NORMAL if ℓ ≤ v ≤ h;   with only h: HIGH if v > h else NORMAL;   with only ℓ: LOW if v < ℓ else NORMAL;   with neither: UNKNOWN"),
        P("The bounds are inclusive. A value of exactly 5 or 10 against a range of 5 to 10 is NORMAL, and a missing value is UNKNOWN. The dashboard separately counts a "
          "result as **critical** when it is far outside its range, using a fixed heuristic:"),
        EQ("critical = (LOW and v < 0.5 ℓ)  or  (HIGH and v > 1.5 h)"),
        P("This is a screening heuristic for ordering attention, not a clinical severity score, and the interface says so by phrasing the alert as results \"far "
          "outside the reference range\"."),
        H2("6.7 Explanation generation"),
        P("For each LOW or HIGH row `ai_insights.generate_insight` returns an explanation, possible causes and a recommendation. The text comes from a curated "
          f"knowledge base of {F.INSIGHT['knowledge_base_entries']} tests (`TEST_KNOWLEDGE`), each entry holding what the test measures and a sentence for a low and a high result, "
          "worded as \"can generally be associated with\". Tests outside the knowledge base get a generic sentence (\"a number of general, non-specific causes\"). The recommendation "
          "is always the same sentence: discuss the result with a doctor, especially if it is far outside the range, if there are symptoms or if it is a new change. The "
          "design rules are written into the module header: never diagnose, never say a value confirms a condition, always show the disclaimer."),
        P("An optional second path rewrites the explanation in friendlier wording. When the `use_llm` switch is on and `ANTHROPIC_API_KEY` is set, the Anthropic "
          "Messages API [23] is called with the configured model identifier and a limit of 300 output tokens, with a prompt that asks for 3 to 4 plain sentences, forbids "
          "diagnosis and forbids new medical facts. Any exception, including a missing key, an outage or an empty reply, silently keeps the rule-based text, so the report "
          "never fails because of the language model. No key was available during development, so **this path was not executed or measured**."),
        P(f"Coverage is limited: the knowledge base covers {F.INSIGHT['dictionary_tests_with_specific_text']} of the {F.INSIGHT['dictionary_tests']} dictionary tests "
          f"({F.pct(F.INSIGHT['coverage_of_dictionary'])}); in the evaluation corpus {F.INSIGHT['abnormal_rows_with_specific_text']} of "
          f"{F.INSIGHT['abnormal_dictionary_rows_in_corpus']} abnormal dictionary rows ({F.pct(F.INSIGHT['abnormal_rows_specific_rate'])}) received test-specific text and the "
          "rest the generic sentence."),
        *_opt_fig("fig_insight_coverage.png", "Share of abnormal rows that received test-specific explanation text", 4.6),
        H2("6.8 Choices against the project abstract"),
        P("The abstract proposed PP-OCR, a conditional random field tagger and retrieval-augmented generation [1], [6], [12], [14]. The delivered system uses simpler "
          "components, and the reasons and the cost are stated here."),
        TAB("Proposed components and what was built", ["Proposed in the abstract", "Built", "Reason", "Consequence"], [
            ["PP-OCR text extraction [12]", "PyMuPDF text layer, with OpenCV and Tesseract for scans", "Digital PDFs need no OCR; Tesseract is free, widely available and has a Python wrapper", "Scanned-image accuracy not measured; PP-OCR is untested here"],
            ["CRF-based named-entity tagging [14]", "Regular-expression row parser and TF-IDF name matcher", "No labelled lab-report corpus existed to train a tagger; the rows are tabular, so patterns are exact and inspectable", "Fails on layouts the patterns do not cover (cell-per-line tables score 0)"],
            ["Retrieval-augmented explanations from trusted sources [1], [6]", "Curated rule-based text, optional LLM rewording", "A small vetted text is safer than free generation for health content and works offline", "No retrieval and no citations; 31 % of dictionary tests have specific text"],
            ["Supabase (PostgreSQL, row-level security)", "SQLite through SQLAlchemy [19]", "Zero set-up for a local demonstration", "No per-user isolation"],
            ["Serverless Cloud Functions", "FastAPI [21] on one process", "Runs on a laptop; same code can later be containerised", "Not deployed to a cloud"],
            ["React, Tailwind CSS, Recharts", "React, hand-written CSS kit, Recharts [22]", "A design kit gave consistent theming without a utility framework", "Tailwind not used"],
        ], widths=[1.5, 1.6, 1.7, 1.5], size=9),
        P(f"On the generated corpus the delivered parser reaches a row precision of {F.f3(ov['row_precision'])}, a recall of {F.f3(ov['row_recall'])} and an F1 of "
          f"{F.f3(ov['row_f1'])}; Chapter 8 breaks this down by layout and field."),
    ]


def application_blocks():
    lat = F.API_LAT["endpoints"]
    return [
        H2("6.9 Application architecture"),
        P("`backend/main.py` creates the FastAPI application [21] and calls `db.init_db()` at import, which creates the tables if they do not exist. It adds the CORS middleware, "
          "defines the token helpers and the fourteen routes, and imports `process_uploaded_report` from the pipeline; there is no pipeline logic in the web layer. The "
          "Streamlit application `app.py` still runs against the same SQLite file. If `frontend/dist` exists (after `npm run build`) the API also serves the compiled "
          "single-page application and falls back to `index.html` for any non-API path, so the product can run as one process on port 8308."),
        P("The interface is a React 18 single-page application built with Vite 5, react-router 6 and Recharts [22]. During development the Vite server on port 5308 proxies `/api` to "
          "port 8308, so the browser sees one origin. Pages are loaded lazily. `lib/api.js` wraps `fetch`, turns every error response into an `ApiError` that carries the server's "
          "message, and uses an `XMLHttpRequest` for uploads because `fetch` cannot report upload progress. A 401 anywhere clears the stored token and returns the user to "
          "the sign-in page. A small hook, `useAsync`, gives every page the same loading, error and retry behaviour."),
        P("The upload route runs the whole pipeline inside the request. This is simple and, for a one-page report, fast: the end-to-end pipeline including the database takes a "
          f"median of {F.LATENCY['end_to_end_pipeline_with_db']['median_ms']:.0f} ms and the HTTP upload a median of {lat['POST /api/reports (PDF upload)']['median_ms']:.0f} ms. A "
          "long scanned report would block the worker for as long as OCR takes, which is why a job queue is listed as future work."),
        H2("6.10 API design and the upload route"),
        P("Section 5.7 lists the routes. The upload route accepts `file` and `use_llm`, calls the pipeline, and returns the status, the stages completed, the error text, the "
          "first 5,000 characters of extracted text and, for a completed report, every result with its insight. The trend route returns the points of one test in upload order "
          "and a direction: *increasing*, *decreasing* or *stable* by comparing only the last value with the first. The compare route intersects the test names of two reports and "
          "returns the change as the second value minus the first, rounded to two decimals."),
        CODE('''@app.post("/api/reports")
def upload_report(file: UploadFile = File(...), use_llm: bool = Form(False), _: str = Depends(require_user)):
    data = file.file.read()
    result = process_uploaded_report(file.filename or "upload", data, use_llm_insights=use_llm)
    out = {"status": result.status, "report_id": result.report_id,
           "stages_completed": result.stages_completed, "error": result.error,
           "raw_text": result.raw_text[:5000], "results": []}
    if result.status == "Completed" and result.report_id is not None:
        out["results"] = [result_dict(r, with_insight=True) for r in db.get_results_for_report(result.report_id)]
    return out'''),
        H2("6.11 Security and error handling"),
        TAB("Threats, faults and the controls in the code", ["Threat or fault", "Control"], [
            ["Anonymous access", "Every route except health, configuration and login depends on `require_user`, which reads the bearer token and answers 401"],
            ["Token forgery or tampering", "Token = base64url(JSON with subject and expiry) + \".\" + base64url(HMAC-SHA256 of that body with `JWT_SECRET`), compared with `hmac.compare_digest`; expires after 12 hours"],
            ["Credential guessing by timing", "E-mail and password are compared with `hmac.compare_digest`"],
            ["Hostile uploads", "Extension whitelist (pdf, jpg, jpeg, png), empty-file check and a 15 MB limit in `validate_file`; undecodable files raise `OCRError` and the report is marked Failed"],
            ["SQL injection", "All access through the SQLAlchemy ORM with bound parameters"],
            ["Cross-site requests", "CORS allows only `http://localhost:5308` and `http://127.0.0.1:5308`"],
            ["Failure at any pipeline stage", "The report row is created first; each stage is wrapped so that a failure sets status Failed with a readable message and keeps the raw text; an insight failure only shortens the stage list"],
            ["Secrets in source control", "`.env` is ignored by git; `.env.example` documents `JWT_SECRET`, the ports and the optional API key"],
            ["Missing optional services", "No Tesseract: a clear message for images, PDFs unaffected. No API key: the LLM switch is disabled and rule-based text is used"],
        ], widths=[1.8, 4.5], size=9.5),
        P("Weaknesses that remain: the token is kept in the browser's `localStorage`, which a script injected into the page could read; the default signing secret is a "
          "published placeholder until `.env` is edited; there is one shared account and one shared library; the configuration route returns the demonstration password "
          "for the sign-in page; and traffic is plain HTTP on the local machine."),
        H2("6.12 Installation and execution"),
        P("`run.bat` reads `BACKEND_PORT` (8308) and `FRONTEND_PORT` (5308) from `.env`, checks that Python and Node.js are on the path, creates `backend\\.venv` and installs "
          "`backend\\requirements.txt` when the environment is missing or cannot import the required packages, runs `npm install` in `frontend` on first use, warns if Tesseract "
          "is absent, starts the API with uvicorn and the interface with `npm run dev`, and opens the browser. Closing the two console windows stops the product. Appendix B "
          "gives the manual commands and the troubleshooting table."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
