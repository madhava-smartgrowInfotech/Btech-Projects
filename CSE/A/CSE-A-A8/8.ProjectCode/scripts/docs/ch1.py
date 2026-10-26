"""Chapter 1: Introduction (the lists are shared with the scope / limitations document, the decks and the paper)."""

from .blocks import B, H1, H2, N, P, TAB
from .refs import n
from . import facts as F

OBJECTIVES = [
    "Accept lab reports in PDF or scanned image form and extract text using high-speed OCR.",
    "Apply named entity recognition to identify test parameters, values, units and reference ranges.",
    "Compare each extracted value against its reference range and flag abnormal results.",
    "Generate plain-language explanations for abnormal findings, grounded in trusted medical sources.",
    "Track parameters across successive reports to display health trends over time.",
    "Present results through a dashboard and evaluate extraction accuracy against manually labelled reports.",
]

SCOPE_IN = [
    "Upload of PDF, JPG, JPEG and PNG reports up to 15 MB. Digital PDFs are read from their text layer; scanned pages and photographs go through OpenCV clean-up and Tesseract OCR.",
    "Line-oriented extraction of test name, numeric result, unit, reference range (two-sided such as `12 - 16`, one-sided such as `<100` or `>40`) and report date.",
    "Snapping of noisy test names to a dictionary of 55 common tests with a TF-IDF character n-gram matcher (cosine threshold 0.55).",
    "Classification of every result as LOW, NORMAL, HIGH or UNKNOWN against the reference range printed on the same report (limits inclusive).",
    "Plain-language insight cards for every LOW or HIGH result: what the test measures, general possible causes and a suggestion to consult a doctor. An optional LLM rewrite is available when an API key is configured.",
    "A SQLite library of reports, results and insights, with a dashboard, report list, report analysis, health trends, report comparison and insights pages.",
    "A FastAPI service and a React interface with a demo login, plus the original Streamlit application; five synthetic sample reports for first use; an automated test suite.",
]

SCOPE_OUT = [
    "Diagnosis or treatment advice. The system is an educational aid, not a medical device, and every screen carries a disclaimer.",
    "The abstract's PP-OCR engine, CRF-based NER model, retrieval-augmented generation over a medical knowledge base, Supabase with row-level security, Tailwind CSS and Google Cloud Functions. None of these was built (Section 3.1 explains why).",
    "Age- or sex-specific reference ranges. The range printed on the report is used as given.",
    "Handwritten reports, non-Latin scripts, and layouts in which every table cell is a separate line of text (measured recall 0 on such reports).",
    "Per-user data separation, registration, HTTPS, encryption at rest and audit logging; only one shared demo account exists.",
    "Validation on real patient reports or against manually labelled reports. No such data was available to the project.",
]

ASSUMPTIONS = [
    "A report lists one test per line in the order name, result, unit, reference range (or a close variant) and prints a reference range for each test.",
    "The input is a PDF with a text layer, or a legible scan or photograph in English and Latin script, no larger than 15 MB.",
    "The reference range printed on the report is the correct range for the patient; the application does not adjust it.",
    "One trusted user group on one machine. The demo account is a convenience, not an identity system.",
    "The host has Python 3.11 or newer and Node.js 20 or newer; Tesseract OCR is installed only if images or scans are to be read.",
]

LIMITATIONS = [
    "**Layout dependence.** On reports where each table cell is a separate text line, the parser extracted no rows at all (recall 0.000 on 210 rows); a date line such as `12-04-2026` was read as a test named \"Sample Collected\" in every one of the 56 corpus reports that print the date with hyphens.",
    "**Unit gaps.** Unit accuracy is 87.1% overall and 57.6% when a flag letter sits between the value and the unit; units such as mg/L, umol/L, ng/dL and uIU/mL are not in the parser's unit list.",
    "**Name matching.** The TF-IDF matcher loses accuracy under character noise (89.0% at 10% noise against 98.1% for a plain `difflib` baseline) and renames some unseen tests, for example Sodium Bicarbonate to Sodium.",
    "**Thin explanation coverage.** Only 17 of the 55 dictionary tests (30.9%) have test-specific explanation text; the rest receive a generic paragraph. The explanations are rule-based, with no retrieval and no citations.",
    "**Evaluation data.** All accuracy figures come from 120 generated reports (1,680 rows) with generated ground truth, not from real, manually labelled reports. Scanned-image OCR accuracy and latency were not measured because Tesseract was not installed on the test machine, and the optional LLM rewrite was not exercised.",
    "**Trends.** Trend direction compares only the first and last values, and the time axis is the upload date, not the date the sample was taken.",
    "**Demonstration-grade security** and **not a medical device**: outputs must not be used as the sole basis for any health decision.",
]

CONTRIBUTIONS = [
    "An end-to-end pipeline from an uploaded report to extracted, classified, explained, stored and trended results, in which the LOW / NORMAL / HIGH rule agreed with an independent reference rule on 20,000 random cases.",
    "A dictionary-snapping name matcher built on TF-IDF character n-grams, analysed with a noise sweep and a threshold sweep that expose its trade-offs.",
    "A rule-based explanation module with a medical disclaimer on every output, an optional LLM rewrite and a silent fall-back to the built-in text.",
    "Longitudinal features that the base paper lacks: per-test trends against the reference band, side-by-side comparison of two reports, a dashboard and an insights page, demonstrated on five synthetic reports sent through the real pipeline.",
    "A measurement harness: a generated corpus of 120 reports in eight layouts, extraction, name-noise and latency experiments, and 36 pytest tests plus a 31-check smoke test, with the failures reported rather than hidden.",
]


def blocks():
    ex = F.EXTRACTION["overall"]
    lat = F.LATENCY["end_to_end_pipeline_with_db"]["median_ms"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain overview"),
        P("A laboratory report is the main document through which a patient learns about their own health, yet it is written for clinicians. A typical report lists "
          "dozens of tests, each with a numeric result, a unit and a reference range, and marks out-of-range values only with a letter or a symbol. Without "
          f"training, a reader cannot tell whether a flagged value is trivial or urgent, and small deviations are easily mistaken for serious illness {n(1)}."),
        P("The domain of this project is healthcare artificial intelligence, natural language processing and medical informatics. Three techniques meet in it: "
          f"optical character recognition (OCR) to turn a PDF or scan into text {n(12, 13)}, information extraction to recover the test name, value, unit and range "
          f"from that text {n(14)}, and language generation to explain an abnormal result in plain words {n(1, 6)}."),
        H2("1.2 Background and motivation"),
        P("Reports reach patients as PDFs from a laboratory portal, as e-mailed scans or as phone photographs. Understanding them normally needs a follow-up "
          "consultation, which adds cost and delay. Many people instead search the web for each test name and meet advice that is generic, alarming or "
          f"wrong. Recent work shows the demand: general-purpose vision-language models are being tried directly on blood report images {n(4)}, and a 2026 benchmark "
          f"turns multimodal check-up reports into patient-oriented action cards {n(3)}."),
        P(f"The base paper for this project {n(1)} applies retrieval-augmented generation (RAG) on LLaMA-3 to blood test reports and produces personalised "
          "dietary and lifestyle advice, but only for metabolic syndrome. It does not extract values from report files, report extraction accuracy or latency, or "
          "compare reports over time. The motivation here is the complementary, general case: any common test, any report layout, with the history of a patient's "
          "own reports kept so that improvement or decline becomes visible."),
        H2("1.3 Problem statement"),
        B("Laboratory reports are written for clinicians, leaving patients unable to interpret their own results.",
          "Manual reading of every parameter is slow and error-prone for both patients and staff.",
          "Existing tools digitise reports but do not explain what an abnormal value means.",
          "No history is retained, so a patient cannot see whether a parameter is improving or worsening."),
        P("The problem addressed is: *given a lab report as a PDF or an image, extract every test with its value, unit and reference range, flag the abnormal ones, "
          "explain each in plain language, and keep the report so that each parameter can be followed across reports.*"),
        H2("1.4 Need for the system"),
        P("The need is for a platform that reads a lab report automatically, explains abnormal values in plain language, and tracks them over time. It should "
          "be open and inspectable, run on an ordinary computer without a GPU or paid service, and be honest about what it cannot do: a research prototype "
          "whose limits are measured and published is more useful to students and developers than a closed tool whose accuracy is asserted."),
        H2("1.5 Objectives"),
        P("The project was proposed with the following six objectives. Chapter 8 states, for each, whether it was achieved."),
        N(*OBJECTIVES),
        H2("1.6 Scope"),
        P("**In scope.**"),
        B(*SCOPE_IN),
        P("**Out of scope.**"),
        B(*SCOPE_OUT),
        H2("1.7 Contributions"),
        N(*CONTRIBUTIONS),
        P(f"For orientation, on the generated test corpus the extraction stage reached a row-level F1 of {F.f3(ex['row_f1'])}, and a 14-row PDF passes through the whole "
          f"pipeline, including the database write, in a median of {lat:.1f} ms. Both figures, and their limits, are explained in Chapter 8."),
        H2("1.8 Limitations and assumptions"),
        P("**Assumptions.**"),
        B(*ASSUMPTIONS),
        P("**Limitations.**"),
        B(*LIMITATIONS),
        H2("1.9 Organisation of the report"),
        TAB("Organisation of this report", ["Chapter", "Content"], [
            ["1  Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations."],
            ["2  Literature Survey", "The base paper in depth, related work by theme, datasets and algorithms, research gap."],
            ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility."],
            ["4  System Requirements and Analysis", "Existing and proposed system, requirements, hardware, software, users."],
            ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, database, modules, API and UI design."],
            ["6  Methodology and Software Implementation", "Data, extraction, matching, classification, explanation, application, security, installation."],
            ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance and edge-case tests."],
            ["8  Results and Output Screens", "Measured performance, comparison with the base paper, output screens, failures, objectives versus outcomes."],
            ["9  Conclusion", "Summary, achievements, findings, applications, known limitations."],
            ["10 Future Scope", "Improvements, features, deployment and research directions."],
            ["Appendices", "A: important code; B: installation and user guide; C: additional screens."],
        ], widths=[2.3, 3.9]),
    ]
