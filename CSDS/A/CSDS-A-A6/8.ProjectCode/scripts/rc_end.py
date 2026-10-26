"""Chapters 9 and 10, implementation decisions, references and appendices for ClauseGuard."""
from __future__ import annotations

from docx.shared import Inches

from doc_common import REFERENCES, ROOT
from rc_results import CL, CO, RU, extra_block

APP = ROOT / "backend" / "app"
S = RU["shipped_set"]["overall"]
P = RU["probe_set"]["overall"]


def _grab(rel: str, marker: str, n: int) -> str:
    """n lines of a real source file, starting at the first line that contains `marker`."""
    lines = (APP / rel).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if marker in ln)
    return "\n".join(lines[i:i + n])


def _block(rel: str, marker: str) -> str:
    """A whole top-level function or indented block: from the line containing `marker` to the next line without indentation."""
    lines = (APP / rel).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if marker in ln)
    out = [lines[i]]
    for ln in lines[i + 1:]:
        if ln.strip() and not ln.startswith((" ", "\t")):
            break
        out.append(ln)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.p("The table lists the main implementation decisions and the reason for each. Several are consequences of three constraints: the build had to run on one ordinary computer without a graphics card, the only language model "
        "available was a shared free-tier Gemini key, and no labelled corpus of Indian contracts existed.")
    d.table([["Decision", "Why (and what it costs)"],
             ["Decide 'predatory or not' with eight regular expressions; use Gemini only to word the reason, quote the provision and draft a safer clause",
              "The verdict is auditable, repeatable and needs no API call, so it can be tested offline (73 automated test cases, `ml/eval.py`). The cost is recall: keyword-free paraphrases are missed (independent probe recall 0.458)"],
             ["Tie each rule to an Indian statute (Indian Contract Act 1872 sections 27, 73 and 74 [20]; Arbitration and Conciliation Act 1996 [21]; Consumer Protection Act 2019 [22]; Copyright Act 1957 [23])",
              "The rule's `legal_basis` text is placed in the explanation prompt, so the generated reason names the right provision. It is grounding by prompt, not retrieval from a legal corpus, which the build does not have"],
             ["Classify by the nearest of 20 category centroids of Gemini embeddings [13] instead of training a classifier",
              f"25 labelled CUAD spans per category give a usable centroid with no training and no fitted model file beyond a cached array; a logistic regression on the same vectors is only 0.008 better in top-1 ({CL['baselines_top1']['Gemini embedding + logistic regression']:.3f} against {CL['centroid']['top1']:.3f})"],
             ["Use 20 substantive CUAD categories, not all 41", "Administrative categories (document name, parties, dates) are metadata rather than clause types; the 20 chosen categories are the ones a signatory cares about"],
             ["Embeddings from the Gemini API (3,072 dimensions) instead of a local sentence encoder [12]", "No model download or GPU is needed; the cost is a network dependency, free-tier limits and about 0.7 s per clause"],
             ["Keep vectors in SQLite as float32 blobs and compare with NumPy, not pgvector", "There is no database server to install and a contract has tens to hundreds of clauses, so a brute-force cosine is instant. The stored clause vectors are written but never read again by the application; they would matter only for cross-contract search"],
             ["Rebuild the clause graph per request with NetworkX [16] and three fixed combination patterns, not Neo4j", "The graph is cheap and derived from the stored flags, so nothing needs persisting. The cost is that the graph holds no legal concepts or precedents and a combination fires on rule ids anywhere in the contract, whatever the distance between the clauses"],
             ["Complexity score as a weighted sum of four lexical measures (0.35 Flesch [15], 0.30 legalese density, 0.20 cross-references, 0.15 sentence length) with grade cut-offs at 20, 40, 60 and 80",
              "Readable, cheap and explainable on the report. The weights and cut-offs were chosen by the authors and never validated against human ratings"],
             ["Segment by numbered headings, falling back to blank-line paragraphs of about 400 characters; PDF per page, DOCX as one page",
              "Simple and page-aware. It drops text before the first heading, ignores `Article I` style headings (84 of 510 CUAD contracts give fewer than five clauses) and splits clauses that cross a page"],
             ["Constants for the tie-break (margin 0.03, similarity 0.60) and the floor (0.35)", "Intended to hand ambiguous clauses to the language model and to refuse clearly unrelated ones. With the current embedding model similarities lie between 0.657 and 0.849, so neither ever acts; they were not calibrated"],
             ["Model names and key from `.env`; override of `GEMINI_TEXT_MODEL` for one process", "The default `gemini-flash-latest` timed out on the free tier at the start of the run (20 requests per day per model), so the demonstration backend was started with `gemini-3.1-flash-lite` without changing any file. The shipped `.env.example` still names two retired models (`gemini-2.0-flash`, `models/text-embedding-004`)"],
             ["FastAPI, SQLAlchemy and SQLite; JWT (HS256, 1,440 minutes) [19] and bcrypt [18]", "Typed request and response models, no database server, stateless tokens and slow password hashing; every contract route checks ownership and answers 404 for other users' contracts so that their existence is not revealed"],
             ["Write the upload to a random file name, delete it in a `finally` block, commit once at the end", "A failure in Gemini or in the pipeline leaves no contract row and no file behind (tested); the price is that a long analysis is lost entirely when its last call fails"],
             ["React 19, Vite and TanStack Query with a 180 s upload timeout and a dev-server proxy for `/api`", "One origin for the browser and a response cache for the report screens; the timeout is shorter than the upload of a contract with about 14 flags"],
             ["No fake data path; the Evaluation page reads `experiments/eval/metrics.json`", "Every number on screen comes from the real pipeline or a real evaluation run, but the page also repeats the claim 'held-out set' for a development set"]],
            "Implementation decisions", widths=[0.38, 0.62], font=8.5)


def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project built ClauseGuard, a full-stack tool that reads an Indian-style contract in PDF or DOCX, splits it into clauses with page numbers, assigns each clause one of 20 CUAD clause types with Gemini embeddings and a nearest-centroid search, "
        "flags eight kinds of predatory clause with Indian-law rules, finds three risky combinations of clauses, scores the complexity of the wording as a grade from A to F, and has Gemini explain each flag in plain language with the quoted provision and a safer wording. "
        "A React web application shows the report, the clause detail, a clause graph, the user's contracts and an evaluation page; a FastAPI backend with SQLite, JWT and bcrypt serves it through nine endpoints; and a pytest suite of 73 cases (68 passing, 5 documenting known gaps) checks the code without calling Gemini.",
        f"The two measurable parts were evaluated separately. On 240 held-out CUAD spans the classifier reaches top-1 accuracy {CL['centroid']['top1']:.3f} and top-3 accuracy {CL['centroid']['top3']:.3f}, well above TF-IDF baselines (0.621 and 0.675). "
        f"The rule engine scores precision {S['precision']:.2f} and recall {S['recall']:.3f} on the 40 clauses that shipped with it, but only precision {P['precision']:.3f} and recall {P['recall']:.3f} on 40 independently phrased clauses, so its real recall is closer to one half. "
        f"The non-API pipeline processed all {CO['contracts']} CUAD contracts in {CO['total_seconds']} s. Three real uploads through the browser behaved as designed: the one-sided contract produced 8 flags and 3 combinations, the fair contract none, and a real supply agreement one.",
        "The build differs from the batch abstract: it uses Gemini instead of the Claude API, SQLite and NumPy instead of pgvector, and an in-memory NetworkX graph instead of Neo4j, and it has no retrieval from a legal corpus. These differences, and the limits found by testing, are stated in this report rather than hidden.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p("Of the six objectives, three are achieved as stated or nearly so, one in a limited form and two only in part. Segmenting contracts and classifying clauses (objective 1) works with limits, because the segmenter recognises only some heading styles and the classifier "
        "must give every clause one of 20 labels. The complexity score and the plain-language summary (objective 5) and the separate evaluation of classification and detection (objective 6) are in place. Flagging predatory clauses and combinations under Indian law (objective 4) is implemented as eight rules and three combinations, "
        "with the recall limits above. The RAG pipeline with the Claude API and pgvector (objective 2) and the Neo4j knowledge graph of concepts and precedents (objective 3) were not built as stated: Gemini replaces Claude, there is no retrieval over a legal corpus, vectors are SQLite blobs, and the graph is a per-contract NetworkX graph without concepts or precedents. Chapter 8 gives the evidence for each.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([
        f"**A high score on a test set written with the rules is not evidence of generalisation.** Precision {S['precision']:.2f} and recall {S['recall']:.3f} on the shipped 40 clauses become {P['precision']:.3f} and {P['recall']:.3f} on 40 independently phrased clauses; the rules miss 13 of 24 paraphrases and flag three fair clauses.",
        f"**Dense embeddings classify clause topics well.** Top-1 {CL['centroid']['top1']:.3f} and top-3 {CL['centroid']['top3']:.3f} on 240 CUAD spans, against 0.621 and 0.675 for TF-IDF baselines; the score is {CL['contract_disjoint']['top1']:.3f} when training spans from the same contract are removed, so the span-level split did not inflate it.",
        "**The classifier's safeguards never act.** Top-1 similarities lie between 0.657 and 0.849, so the tie-break (needs below 0.60) and the 'Other / Unclassified' floor (below 0.35) are dead code and every clause gets one of 20 labels; on whole clauses of real contracts only about half of the labels are plausible (19 clauses read).",
        "**The input format changes the verdict.** The same contract text gives 8 of 8 rules as DOCX and 6 of 8 as PDF, because the rules use `.{0,N}` across line breaks; text before the first heading is discarded and 84 of 510 CUAD contracts yield fewer than five clauses.",
        "**Complexity is not fairness.** The one-sided freelance contract is grade B (23.3) and the fair one grade A (13.7); real CUAD contracts are mostly B or C (437 of 510).",
        f"**The local pipeline is cheap; the language model is the cost.** 56 ms per contract for segmentation, rules and scoring, against 15.5 s to 113.6 s per upload because each flag needs a Gemini call, and a free-tier quota of 20 text requests a day per model.",
        "**Generated text is plausible but unverified.** Reasons and quoted provisions were faithful in the examples read, but the safer wording of the non-compete still restrains the consultant for six months, the Fusion reason overstates the absence of a reciprocal right, and every report is framed as Indian law whatever the contract's jurisdiction.",
        "**The build is lighter than the abstract.** Gemini, SQLite with NumPy and NetworkX replace Claude, pgvector and Neo4j; the project states this openly.",
    ])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.p("In its present form ClauseGuard is a working prototype and a teaching platform for contract review, not a legal service; its output is information and not legal advice. With the improvements of Chapter 10, "
        "the same structure could support four uses: a first-pass reading of a freelance, consulting or small-business contract that lists the clauses worth a second look and explains them in plain language; a checklist for a lawyer reviewing a batch of contracts, "
        "using the page-linked flags to save time; a teaching aid that shows how Section 27, Section 74 and similar provisions bear on common clauses; and a benchmark harness for comparing rule-based, embedding-based and language-model detectors on the same clause sets.")


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "The rule engine is eight regular expressions: recall on independently phrased clauses is 0.458 and fair clauses are sometimes flagged; combinations are matched on rule ids anywhere in the contract.",
        "The test sets are small, written by project members and not labelled by lawyers; no Indian contract corpus was used, because none was available (CUAD contains US filings).",
        "Input handling: PDF line breaks defeat some rules, text before the first heading is dropped, only some heading styles split clauses, clauses crossing a page are cut, DOCX has no page numbers, and scanned PDFs cannot be read.",
        "Classification forces 20 labels, its fallback branches never act, and it was trained on spans rather than whole clauses.",
        "The complexity score is lexical and unvalidated; the generated explanations and summaries are not verified by a lawyer and carry an Indian-law framing for every contract.",
        "Dependence on Gemini: free-tier quota, 12 s or more per call, a 180 s browser timeout, contract text sent to an external service, and no partial result when an upload fails.",
        "Engineering: malformed Gemini JSON is reported as HTTP 400 instead of 502 (a `JSONDecodeError` is a `ValueError`); CORS open to all origins, no rate limiting, a default JWT secret fallback, no browser tests and no load test; the shipped `.env.example` names retired Gemini models.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Normalise the text before matching.** Collapse whitespace and line breaks before the rules run (8 of 8 rules on the PDF in the experiment), keep the preamble, recognise `Article I`, roman-numeral and lettered headings, and merge clauses that run across a page.",
        "**Widen and test the rules.** Add the paraphrase families that the probe set exposed, replace key-word patterns by pattern-plus-context checks, and re-measure on a held-out set that no rule author has seen; keep the 40-clause set as a regression test and relabel it a development set on the Evaluation page.",
        "**Calibrate the classifier.** Set the tie-break and floor thresholds from the observed similarity distribution (the margin test alone would fire on 152 of 240 spans), add an explicit 'none of the 20' class trained on boilerplate clauses, and build the classification test from whole clauses with a contract-disjoint split.",
        "**Fix the engineering gaps:** a time budget or background job for long uploads with progress on the page, partial results when Gemini fails, a stricter CORS policy, rate limiting, a mandatory JWT secret and an updated `.env.example` with current model names.",
        "**Show uncertainty.** Display the classifier's confidence and a warning that labels are advisory, and mark flags that rest on a single pattern.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "Missing-clause detection against a checklist of essential clauses (payment, termination, liability, confidentiality, governing law, dispute resolution), as in the base paper [1], to complement the flags on clauses that are present.",
        "A jurisdiction setting (India, other) that changes the rule set and the prompt, and detection of the governing-law clause so that a foreign contract is not read under Indian law.",
        "Export of the report to PDF or DOCX with the flags and safer wording as tracked changes, and a side-by-side view of the original and the proposed clause.",
        "A comparison of two versions of the same contract, and a library of vetted fair clauses to suggest in place of generated wording.",
        "A question-and-answer panel over the uploaded contract using retrieval over its own clauses, which would finally give the retrieval-augmented component that the abstract describes.",
        "Support for Hindi and other Indian languages and for scanned contracts through optical character recognition.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.p("The next step is a hosted deployment: a managed database in place of SQLite, a background worker that analyses contracts asynchronously and streams progress to the page, a paid Gemini tier or a locally hosted open model so that quotas and confidentiality "
        "are under the operator's control, HTTPS, a secret key from the environment, rate limiting and structured logging. Batching the embedding and explanation calls would cut the upload time from minutes to seconds. "
        "pgvector or Neo4j should be introduced only if a feature needs them (cross-contract similarity search, or a graph of concepts and precedents); at the scale of one contract per request the current brute-force cosine and the NetworkX graph are sufficient. "
        "A continuous-integration run of the 73 test cases, a monitored distribution of classifier confidence, and a load test with concurrent users would turn the single-machine timings of this report into capacity figures.")


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "**An Indian contract corpus with lawyer labels.** Collect and annotate Indian freelance, employment, lease and service contracts for predatory terms under Sections 27, 73 and 74 of the Indian Contract Act and the Consumer Protection Act, with agreement between several lawyers, so that precision and recall can be reported on real, unseen data.",
        "**A whole-clause classification set with a contract-disjoint split**, to measure what the product actually does rather than what CUAD spans suggest.",
        "**A hybrid detector.** Combine the rules (high precision, auditable) with a language-model judge or a fine-tuned small model [3], measure the gain on the probe-style paraphrases and the cost in time and money, and follow the evaluation design of ContractEval [2] (F2, Jaccard overlap, 'no related clause' rate).",
        "**Risk scoring validated against experts.** Learn or calibrate the weights of the complexity score and of a combined risk score from lawyer ratings, in the manner of the correlation study of [4].",
        "**Graph reasoning that is more than three patterns:** a knowledge graph of clause types, legal concepts and precedents, with combination detection that respects the party affected and the distance between clauses.",
        "**Faithfulness of generated explanations.** Measure how often the quoted provision is a verbatim substring, how often the cited section is correct, and how often the safer wording introduces new obligations.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        rep = getattr(d, "report", False)
        p = d.p(f"[{i}]\t{ref}", align="left", size=10.5 if rep else 11, line=1.1 if rep else 1.2, space_after=3 if rep else 4)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)


def appendix_a(d):
    d.p("The listings below are extracted from the source files when this report is built, so they match the code that produced the results.")
    d.h2("Nearest-Centroid Classification with Tie-Break")
    d.code(_block("services/classification.py", "def classify_clause"), "classify_clause() in backend/app/services/classification.py")
    d.h2("One Predatory-Clause Rule and the Detector")
    d.code(_grab("services/rules.py", "Rule(", 14) + "\n    ...\n" + _block("services/rules.py", "def detect_flags"), "The first of the eight rules and detect_flags() in backend/app/services/rules.py")
    d.h2("Complexity Score")
    d.code(_block("services/complexity.py", "def score_contract"), "score_contract() in backend/app/services/complexity.py")
    d.h2("Risky Combinations")
    if getattr(d, "report", False):
        d.code(_block("services/graph.py", "def detect_risky_combinations"), "detect_risky_combinations() in backend/app/services/graph.py")
    else:
        d.code(_grab("services/graph.py", "RISKY_COMBOS = [", 8) + "\n    ...\n" + _block("services/graph.py", "def detect_risky_combinations"), "RISKY_COMBOS and detect_risky_combinations() in backend/app/services/graph.py")
    if getattr(d, "report", False):
        d.p("The listings of the clause splitter, the explanation prompt, the upload pipeline and the ownership check are given in the code walkthrough of Chapter 6 and are not repeated here.")
        return
    d.h2("Clause Splitting")
    d.code(_grab("services/parsing.py", "CLAUSE_HEADER_RE", 6) + "\n    ...\n" + _block("services/parsing.py", "def _split_page_text"), "CLAUSE_HEADER_RE and _split_page_text() in backend/app/services/parsing.py")
    d.h2("Explanation Prompt")
    d.code(_block("services/explain.py", "def explain_flag"), "explain_flag() in backend/app/services/explain.py")
    d.h2("Upload Pipeline")
    d.code(_block("services/pipeline.py", "def process_upload"), "process_upload() in backend/app/services/pipeline.py")
    d.h2("Ownership Check and Upload Route")
    d.code(_block("routes/contracts.py", "def _get_owned_contract") + "\n\n" + _grab("routes/contracts.py", "async def upload_contract", 22), "_get_owned_contract() and the start of upload_contract() in backend/app/routes/contracts.py")


def appendix_b(d):
    d.h2("Installation Guide")
    d.p("ClauseGuard runs on Windows with Python 3.10 or later and Node.js (the build used Python 3.11.9 and Node 24). The commands below are those of the project's `setup.bat`, `run.bat` and README; the ports 8106 (backend) and 5106 (frontend) are fixed.")
    d.numbered([
        "Run `setup.bat` in the `8.ProjectCode` folder. It creates `.env` from `.env.example`, creates `venv`, installs `backend\\requirements.txt`, runs `npm install` in `frontend` and downloads CUAD if `data\\cuad\\CUADv1.json` is missing (it is committed, so this normally does nothing).",
        "Open `.env` and set `GEMINI_API_KEY` (a free key from https://aistudio.google.com/apikey), `GEMINI_TEXT_MODEL` and `GEMINI_EMBEDDING_MODEL`. The embedding name must begin with `models/`. The example file names two models that Google has retired (`gemini-2.0-flash`, `models/text-embedding-004`); use current names such as `gemini-flash-latest` or `gemini-3.1-flash-lite` and `models/gemini-embedding-001`.",
        "Run `run.bat`. It opens two windows, the backend (`uvicorn app.main:app` on port 8106) and the frontend (`npm run dev` on port 5106), and opens http://localhost:5106 in the browser. Use `localhost`, not `127.0.0.1`, for the page: the Vite server listens on `localhost`.",
        "Sign up with any e-mail and a password of at least six characters; there is no pre-seeded account.",
        "Tests: `venv\\Scripts\\python.exe -m pytest` (the suite stubs Gemini and needs `pytest` and `httpx` in the virtual environment). Live smoke test: `venv\\Scripts\\python.exe scripts\\smoke_test.py` (needs a working key).",
        "Evaluation: `venv\\Scripts\\python.exe ml\\eval.py` writes `experiments\\eval\\metrics.json`. The extra experiments of this report are `scripts\\exp_embed_cache.py`, `scripts\\exp_classification.py`, `scripts\\exp_rules_corpus.py` and `scripts\\exp_format_parity.py`; the sample contracts are written by `scripts\\make_sample_inputs.py`.",
    ])
    d.table([["Problem", "Remedy"],
             ["Upload fails with 'GEMINI_API_KEY is not configured' (HTTP 503)", "Set the key in `.env` and restart the backend"],
             ["Upload fails with 429 or 'over its quota' (HTTP 502)", "Wait for the quota to reset, use another key, or set `GEMINI_TEXT_MODEL` to a model with quota; in this run `gemini-flash-latest` hit a limit of 20 text requests per day"],
             ["Upload fails with 404 or 'Invalid model name'", "A retired model name is in `.env`; set a current one"],
             ["The page shows an error after about three minutes of analysis", "The browser request timed out at 180 s; the contract has too many flags for one request"],
             ["Port already in use", "Stop the other process or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`"]],
            "Common problems", widths=[0.45, 0.55], font=9.5)
    d.h2("User Guide")
    d.table([["Task", "How"],
             ["Create an account", "Sign up from the landing page; any e-mail and a password of six or more characters; you land on the upload page"],
             ["Analyse a contract", "Upload contract: drop or choose a PDF or DOCX, press Analyse contract and wait; a long contract with many flags can take two minutes. Scanned images without text cannot be read"],
             ["Read the report", "The report shows the complexity grade and its four components, the plain-language summary, the key obligations, the risky combinations and the clause table with type, page, flags and risk"],
             ["Open a flagged clause", "Select a row: the Flags tab shows the rule, severity, why it is flagged, the quoted provision and the safer wording; the Clause text tab shows the clause"],
             ["See the clause graph", "Report, Clause graph: red nodes triggered a rule, orange lines join clauses of a risky combination; hover a node for its text"],
             ["Find earlier contracts", "My contracts lists every contract with grade, flag count and upload time; select one to reopen it"],
             ["Check the measured quality", "Evaluation (public): precision, recall and F1 of the rules on the 40-clause set, the per-rule table and the CUAD classification accuracy"]],
            "User guide", widths=[0.26, 0.74], font=10)
    d.p("ClauseGuard is a prototype. Its flags, explanations and summaries are produced by pattern rules and a language model and have not been reviewed by a lawyer; they are information, not legal advice. "
        "The text of every uploaded contract is sent to the Gemini service for embedding, explanation and summary.")


def appendix_c(d):
    d.p("Additional captures of the running application (26 October 2026, 1440 by 900 pixels).")
    extra_block(d)
