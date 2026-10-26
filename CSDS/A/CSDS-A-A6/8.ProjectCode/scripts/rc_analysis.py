"""Chapters 3 and 4 content: feasibility study, existing and proposed system, requirements, platform and roles (ClauseGuard).

Figures come from docs/REPORT_FACTS.md and experiments/**/metrics.json. References as in doc_common.REFERENCES.
"""
from __future__ import annotations


def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.paras(
        "ClauseGuard needs six capabilities: reading PDF and DOCX files, splitting text into clauses, turning clauses into vectors, "
        "applying rules, scoring text and generating explanations. Each one was available as an existing library or service, and each "
        "was exercised in this project. PDF text with page numbers is read by PyMuPDF and DOCX text by python-docx. Segmentation is a "
        "regular expression over numbered headings. Clause vectors (3,072 dimensions) come from the Gemini embedding model [13] and "
        "are compared with NumPy. Rules are Python regular expressions. The complexity score needs only string processing. "
        "Explanations come from a Gemini text model. The API layer is FastAPI with SQLAlchemy and SQLite, and the interface is a React "
        "application. No capability required training a model or a GPU.",
        "Technical feasibility was confirmed by measurement. The non-API part of the pipeline (segmentation, rules, combinations, "
        "complexity) processed all 510 CUAD contracts, 23,869 clauses, in 28.5 s, which is 56 ms per contract. The API endpoints that do "
        "not call Gemini answered in 2.5 ms to 15.3 ms (median), except the bcrypt operations at about 255 ms to 265 ms. The 73 "
        "automated tests (68 pass, 5 expected failures documenting known limits) run in about 10 s with the language model replaced by "
        "stubs. Three contracts were uploaded through the browser with real Gemini calls and each produced a report.")
    d.p("The principal technical risks, with the measured effect and the mitigation used in the prototype, are listed below.")
    d.table([["Risk", "Likelihood and effect (measured)", "Mitigation in the prototype"],
             ["Gemini quota and latency", "The default text model `gemini-flash-latest` resolved to `gemini-3.8-flash` with a free tier of 20 generate requests per day; it returned 429 and timed out at the start of the work. A text call took about 12 s", "The backend reads the model name from `.env`; the measured run used `gemini-3.1-flash-lite`. Embedding calls were not limited in practice (about 740 in 7 minutes)"],
             ["Keyword rules miss paraphrases", "Recall 0.458 on 24 independently written predatory clauses; 3 of 16 benign look-alikes flagged", "Rules are auditable; each flag is shown with the quoted provision so a reader can judge it; the limitation is stated"],
             ["PDF text differs from DOCX text", "Same contract: 8 of 8 rules in DOCX, 6 of 8 in PDF, because line breaks break bounded-gap patterns", "Documented; whitespace collapsing before matching restored 8 of 8 in the experiment but is not applied in the shipped code"],
             ["Segmentation by numbered headings", "84 of 510 CUAD contracts gave fewer than 5 clauses; text before the first heading is dropped", "A paragraph-merging fallback exists when a page has fewer than two headings; documented as a limit"],
             ["Classification confidence", "All similarities lie between 0.657 and 0.849, so the tie-break and Unclassified branches never act", "Reported; top-3 accuracy (0.979) shows the right category is almost always among the first three"],
             ["Upload time", "15.5 s to 113.6 s for the three uploads; the browser request times out at 180 s", "Progress is shown; the number of language-model calls grows with the number of flags"],
             ["No GPU", "Not needed: all models are remote API calls", "None required"]],
            "Technical risks and mitigations", widths=[0.2, 0.42, 0.38], font=9)


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.p("The project was built with open-source software, an existing computer and a shared free-tier API key, so no direct cost was "
        "incurred. The table lists the items.")
    d.table([["Item", "Choice", "Cost in this project"],
             ["Hardware", "One Windows 11 PC, Intel Core i5-12500, 15.7 GB RAM, no GPU", "Existing equipment"],
             ["Back-end software", "Python 3.11.9, FastAPI, SQLAlchemy, SQLite, PyMuPDF, python-docx, NumPy, NetworkX", "Free and open source"],
             ["Front-end software", "Node 24, React 19, Vite 6, Tailwind CSS 4, TanStack Query, Recharts", "Free and open source"],
             ["Dataset", "CUAD v1 [8], CC BY 4.0", "Free"],
             ["Embeddings", "`gemini-embedding-001` through the Gemini API", "Free tier; the price of a paid tier was not measured"],
             ["Text generation", "`gemini-flash-latest` by default; `gemini-3.1-flash-lite` in the measured run", "Free tier with 20 text requests per day per model observed"],
             ["Hosting", "Local machine; two processes (ports 8106 and 5106)", "None"]],
            "Items and costs", widths=[0.2, 0.5, 0.3], font=10)
    d.paras(
        "The running cost of the product is dominated by the language-model calls. For one upload the number of calls is the number of "
        "clauses (embeddings) plus one explanation call per flag plus one summary call; a tie-break call is added when two categories "
        "are close and the best similarity is below 0.60, which did not happen in any measured case. The invented one-sided contract "
        "(11 clauses, 8 flags) therefore needed 11 embedding calls and 9 text calls; the fair contract (8 clauses, no flags) 8 embedding "
        "calls and 1 text call; the real CUAD contract as PDF (11 clauses, 1 flag) 11 embedding calls and 2 text calls. With a limit of "
        "20 text requests per day, a free key supports two contracts like the first one per day, or many contracts with few flags. "
        "The cost per contract on a paid tier was **not measured**, so no figure is given. For comparison, a surveyed paper puts the "
        "cost of running GPT-4.1 on the CUAD test set at about $50 [2], and another reports a cost of $0.018 per contract for a "
        "self-hosted domain model [3]; neither figure applies to ClauseGuard.",
        "Economic feasibility is therefore established for a prototype and for low volumes. At higher volumes the paid price of the "
        "language-model calls would have to be measured, and the free-tier quota would be the first constraint to be reached.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.paras(
        "The intended users are freelancers, individuals and small businesses that sign contracts without in-house counsel, and "
        "legal-operations staff who want a first pass. The use is simple: register with an e-mail address and a password of at least six "
        "characters, upload a PDF or DOCX file, wait for the analysis, read the report and open the flagged clauses. The interface "
        "shows an upload progress bar and then an indeterminate bar while the server works, and it states the reason when a file of the "
        "wrong type is chosen. Setup on a new machine is two commands (`setup.bat`, then `run.bat`) plus a Gemini key in `.env`.",
        "Operation needs little maintenance: nothing is trained, the centroids are cached in a file, and the rules and combinations "
        "are constants in two source files. The things that need attention are the API key and its quota, the choice of model name, and "
        "the rule wording when a legal provision or a drafting style changes. Privacy deserves a plain statement: the text of every "
        "uploaded clause is sent to Google's Gemini API for embedding and explanation, the uploaded file is deleted from the server "
        "after analysis, and the extracted text and results are kept in the local database under the uploading user's account. A "
        "deployment that handles confidential contracts would need a decision on whether a hosted model is acceptable.",
        "The operational limit that users will feel first is waiting time (about 15 s for a short contract without flags to nearly two "
        "minutes for a contract with eight flags) and the 180 s timeout of the browser request.")


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The dates below are those recorded in the repository history or in file timestamps; the duration of the other phases was not "
        "recorded and is not claimed.")
    d.table([["Date (2026)", "Milestone", "Evidence"],
             ["19 Sep", "Batch details, abstract, base paper, literature survey and objectives fixed", "Batch documents 1 to 6"],
             ["21-25 Sep", "Project prompts prepared; CUAD v1 and the derived samples obtained", "Repository history; `data/` timestamps"],
             ["22 Sep", "First evaluation run: predatory detection only, classification not computed (no key)", "`experiments/eval/metrics.json` of that date"],
             ["15 Oct", "Front end rebuilt (React, Vite)", "Commit \"Rebuild frontend with kit V1\""],
             ["26 Oct", "Classification evaluation, probe set, corpus run, tests, screenshots, diagrams, decks, documents", "Documentation run"]],
            "Project milestones with recorded dates", widths=[0.14, 0.56, 0.3], font=10)
    d.p("The schedule was feasible because every heavy component was an existing library or hosted service, and because the data needed "
        "for the first predatory-detection result was written together with the rules. The same fact explains why the evidence for "
        "real-world accuracy was weak until independent clauses were written and the CUAD experiments were run late in the work.")


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.table([["Advantages", "Constraints"],
             ["Runs on one ordinary PC with no GPU, no training and no licence fee", "Depends on a hosted model: quota (20 text requests per day observed), cost on a paid tier unmeasured, about 12 s per call"],
             ["Every flag shows the quoted provision, the rule's legal basis and a safer wording", "Eight regular-expression rules: recall 0.458 on independently written clauses"],
             ["Classification and predatory detection are scored separately (top-1 0.792; precision/recall on two sets)", "No Indian contract corpus; CUAD is US data; spans, not whole clauses, were scored"],
             ["Combinations of clauses are reported, which clause-by-clause tools do not do", "Only three combinations, matched anywhere in the contract"],
             ["Non-API processing is fast (56 ms per contract; 2.5-15 ms for read endpoints)", "PDF line breaks lose some rules; scanned PDFs cannot be read; no OCR"],
             ["Authenticated API: bcrypt, JWT, owner check on every contract route", "CORS is open, the default signing key applies when `.env` has none, and there is no rate limiting"]],
            "Advantages and constraints of the project", widths=[0.5, 0.5], font=10)


def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.paras(
        "Today a contract is reviewed in one of four ways. A lawyer reads it, which is accurate but slow and costly. The signatory reads "
        "it alone and relies on common sense. Commercial contract-analysis software, built for enterprises and trained on US or EU "
        "contracts, extracts clause types and obligations at volume. Or a general-purpose chatbot is asked to summarise the text. "
        "Research systems, such as those surveyed in Chapter 2, classify clause types with datasets such as CUAD [8] or extract fields "
        "with language models [2]-[4].",
        "These approaches share the limitations in the table below, which follow the batch literature survey and were checked against "
        "the surveyed papers.")
    d.table([["Limitation of the existing system", "Consequence"],
             ["Professional review is costly and slow for individuals and small businesses", "Most freelancers and small firms sign without review"],
             ["Tools target enterprises and US or EU law and rarely consider Indian contract law", "Provisions such as section 27 and section 74 of the Indian Contract Act [20] are not applied"],
             ["Clauses are analysed in isolation", "Combinations of clauses that are harmful together are missed"],
             ["Clause classification and predatory-clause detection are conflated in evaluation", "A good classification score is read as good risk detection"],
             ["General chatbot summaries may be inaccurate and give no clause-level references", "The signatory cannot check what the summary relied on"],
             ["Outputs are labels, spans or scores, not advice written for a non-lawyer", "The signatory does not know what to ask for or what to change"]],
            "Limitations of the existing system", widths=[0.55, 0.45], font=10)


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.paras(
        "ClauseGuard accepts a PDF or DOCX contract and returns a clause-by-clause report. Each clause carries its page number, a "
        "CUAD-style type with a confidence value, and, where a rule fires, the flag with a plain-language reason, the quoted words and a "
        "safer wording. The report adds the risky combinations found, an A to F complexity grade with its four component measures, "
        "and a plain-language summary with the signatory's key obligations. A clause graph shows which clauses form a combination, and "
        "an evaluation page shows the measured scores.",
        "The proposed system differs from the batch abstract in three architectural respects, which are stated here so that the "
        "requirement tables below are read correctly: Gemini replaces the Claude API; SQLite with NumPy replaces pgvector; and an "
        "in-memory NetworkX graph replaces Neo4j.")
    d.table([["Feature", "What it does", "Advantage over the existing system"],
             ["Upload and segmentation", "PDF per page and DOCX; numbered headings; paragraph fallback", "Every result points to a clause and a page"],
             ["Clause classification", "Gemini embedding, nearest of 20 CUAD centroids; top-1 0.792, top-3 0.979 on 240 spans", "A first map of what each clause is about; scored separately from risk"],
             ["Predatory-clause rules", "8 rules tied to Indian statutes; reason, quoted provision, safer wording", "Auditable and jurisdiction-aware; the decision is not left to the language model"],
             ["Risky combinations", "3 patterns over rule identifiers; clause graph", "Reports risk that arises only from several clauses together"],
             ["Complexity grade", "Flesch, legalese density, cross-references, sentence length, 0-100 and A-F", "A quick measure of how hard the document is to read"],
             ["Plain-language summary", "Gemini summary and key obligations", "Readable by a non-lawyer; not verified by a lawyer"],
             ["Evaluation page", "Precision, recall per rule, classification top-1 and top-3", "Numbers shown to the user, with the caveats stated in this report"]],
            "Features of ClauseGuard", widths=[0.2, 0.42, 0.38], font=9.5)
    d.table([["Limitation of the existing system", "Answering feature", "Status in the prototype"],
             ["Cost and speed of review", "Automated first reading in 15.5 s to 113.6 s", "Met for first reading; not a substitute for a lawyer"],
             ["Little coverage of Indian law", "Eight statute-tagged rules", "Partly met: keyword patterns, recall 0.458 on independent clauses"],
             ["Clauses analysed in isolation", "Three combinations and the clause graph", "Partly met: three patterns only"],
             ["Conflated evaluation", "Separate classification and predatory scores", "Met; both with stated caveats"],
             ["Ungrounded summaries without references", "Every flag keeps clause, page, quoted provision and legal basis", "Met for flags; the summary is still generated text"]],
            "Limitations answered by the proposed system", widths=[0.34, 0.36, 0.3], font=9.5)


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([["ID", "Requirement", "Satisfied by"],
             ["FR1", "A visitor can register with an e-mail address and a password of at least six characters, and log in", "`POST /api/auth/register`, `POST /api/auth/login`; pages Sign up, Log in"],
             ["FR2", "A signed-in user can upload a PDF or DOCX contract; other types are rejected", "`POST /api/contracts/upload`; HTTP 400 for other extensions; page Upload"],
             ["FR3", "The system splits the contract into clauses with page numbers", "`services/parsing.py` (PDF per page, DOCX as page 1)"],
             ["FR4", "Each clause is classified into one of 20 CUAD categories with a confidence value", "`services/classification.py`, `services/vectorstore.py`"],
             ["FR5", "Each clause is checked against the eight predatory-clause rules", "`services/rules.py` (`detect_flags`)"],
             ["FR6", "Each flag has a plain-language reason, the quoted provision and a safer wording", "`services/explain.py` (`explain_flag`)"],
             ["FR7", "Risky combinations of rules are reported", "`services/graph.py` (3 combinations)"],
             ["FR8", "A complexity score and an A-F grade are computed", "`services/complexity.py`"],
             ["FR9", "A plain-language summary and key obligations are produced", "`services/explain.py` (`summarize_contract`)"],
             ["FR10", "A user can list their contracts and open a report, a clause and the clause graph", "`GET /api/contracts`, `/{id}`, `/{id}/clauses/{cid}`, `/{id}/graph`"],
             ["FR11", "A user cannot see another user's contract", "Ownership check returns HTTP 404"],
             ["FR12", "The evaluation results are visible to anyone", "`GET /api/eval/metrics`; page Evaluation"]],
            "Functional requirements", widths=[0.08, 0.5, 0.42], font=9.5)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "How it is met / measured"],
             ["NFR1 Performance", "Read endpoints respond quickly; the analysis finishes in about a minute", "Median 2.5-15.3 ms for read endpoints; upload 15.5 s, 54.6 s and 113.6 s for the three contracts (dominated by Gemini calls); non-API pipeline 56 ms per contract"],
             ["NFR2 Security", "Passwords hashed; tokens signed; routes protected; ownership enforced", "bcrypt [18]; JWT HS256, 1,440 minutes [19]; missing token gives 403 and an invalid token 401; other users' contracts give 404 (tested). Gaps: open CORS, default signing key when `.env` has none, no rate limiting"],
             ["NFR3 Reliability", "A failure of the language model must not corrupt data", "Gemini failure after 3 retries returns HTTP 502; the transaction is not committed, so no contract is stored; the temporary file is removed (tested). The user loses the partial result"],
             ["NFR4 Usability", "A non-expert can use the tool", "Seven screens; progress bar; plain error messages; flags with reason and safer wording"],
             ["NFR5 Privacy", "Contract files are not kept", "Uploaded file deleted after analysis; text is sent to the Gemini API; results stay in the local database"],
             ["NFR6 Portability", "Runs on a standard Windows PC", "`setup.bat` and `run.bat`; Python 3.10+ (3.11.9 used); Node LTS"],
             ["NFR7 Maintainability", "Rules and thresholds are easy to find and change", "Rules in `rules.py`, combinations in `graph.py`, weights in `complexity.py`; 72 automated tests"],
             ["NFR8 Verifiability", "Results can be regenerated", "Experiment scripts and `metrics.json` files; `ml/eval.py`"]],
            "Non-functional requirements", widths=[0.16, 0.34, 0.5], font=9)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.table([["Item", "Requirement"],
             ["Computer used", "Intel Core i5-12500 (12 threads), 15.7 GB RAM, Windows 11; no GPU is used"],
             ["Minimum to run", "Any modern PC with 8 GB RAM and a network connection to the Gemini API"],
             ["Python and packages", "Python 3.11.9 (3.10+ works); FastAPI 0.115, Uvicorn 0.30, SQLAlchemy 2.0, PyMuPDF 1.24, python-docx 1.1, google-generativeai 0.8, NumPy 1.26, NetworkX 3.3, PyJWT 2.9, bcrypt 4.2"],
             ["Front end", "Node 24 (LTS works); React 19, Vite 6, Tailwind CSS 4, TanStack Query 5, Axios, Recharts, React Router"],
             ["Database", "SQLite (file `data/app.db`), created automatically"],
             ["External service", "Gemini API key in `.env`: embedding model `models/gemini-embedding-001`; text model `gemini-flash-latest` by default"],
             ["Ports", "Back end 8106, front end 5106 (open the app as `localhost`)"],
             ["Test and experiment tools", "pytest, scikit-learn, matplotlib, Playwright with Chrome for the screenshots"]],
            "Hardware and software requirements", widths=[0.22, 0.78], font=10)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.p("ClauseGuard has no separate administrator or reviewer role. Access is decided by whether a valid token is present, and by "
        "whether the contract belongs to the user holding it.")
    d.table([["Role", "Can do", "Cannot do"],
             ["Visitor (no token)", "Open the landing page, register, log in, read the evaluation page and `GET /api/eval/metrics`", "Upload, list or open any contract"],
             ["Signatory (registered user)", "Upload PDF or DOCX files; list own contracts; open own reports, clauses and graphs", "See another user's contract (HTTP 404); delete or edit a contract; upload other file types"],
             ["Evaluator (operator of the machine)", "Run `ml/eval.py` and the experiment scripts; the results appear on the evaluation page", "Not a role in the application; needs shell access"],
             ["Gemini API (system actor)", "Supply embeddings, tie-break answers, explanations and summaries", "Decide whether a clause is predatory: that is decided by the rules"]],
            "User roles", widths=[0.24, 0.4, 0.36], font=10)
    d.h3("Constraints")
    d.bullets([
        "A user needs a network connection and a valid Gemini key on the server; without a key the upload returns HTTP 503.",
        "Only English text with a text layer is analysed; scanned pages are not read.",
        "Headings must be numbered in a form the segmenter recognises, or the fallback groups paragraphs into chunks of about 400 characters.",
        "A report is read-only; to correct an analysis the contract must be uploaded again.",
        "The output is information for the signatory, not legal advice, and was not reviewed by a lawyer.",
    ])
