"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry (ClauseGuard).

Diagrams are drawn by scripts/make_diagrams.py from the real models (backend/app/db.py), routes and services; each paragraph below was
checked against the picture and against backend/app and frontend/src/pages. Facts: docs/REPORT_FACTS.md.
"""
from __future__ import annotations

from doc_common import DIAG, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of ClauseGuard",
                     ["The diagram shows four zones. On the left is the browser: a React 19 single-page application built with Vite. Its pages are grouped as "
                      "landing, sign-up and log-in; upload; my contracts and the contract report; clause detail and clause graph; and the evaluation page. The "
                      "application talks to the server through Axios and TanStack Query, and it keeps the JSON Web Token in the browser's local storage. In "
                      "development the Vite server on port 5106 proxies every `/api` call to the backend, so the browser sees one origin.",
                      "In the centre is the FastAPI backend on port 8106. A thin router layer (`auth`, `contracts` and `eval`, plus `/api/health`) validates "
                      "requests; `auth.py` hashes passwords with bcrypt, signs HS256 tokens and is the dependency that identifies the caller, and every contract "
                      "route checks that the contract belongs to that caller. Below it, `pipeline.process_upload()` orchestrates six services: parsing "
                      "(PyMuPDF and python-docx), classification (centroids and an optional tie-break), the eight regular-expression rules, the NetworkX "
                      "combination graph, the complexity score and the explanation service that writes the wording. Two helpers sit underneath: the NumPy "
                      "cosine routines and the Gemini client with its retries.",
                      "On the right, local storage holds the SQLite file `data/app.db` (users, contracts, clauses with their embedding blobs, flags), the cached "
                      "centroid file `data/cuad_centroids.npz`, and the JSON files that carry the CUAD splits, the 40-clause test set and the evaluation "
                      "results. The only external dependency is the Google Gemini API, called over HTTPS for embeddings (gemini-embedding-001, 3,072 values per "
                      "vector) and for text (tie-break, reasons, safer wording and summaries). The footnote of the figure states what the design does not "
                      "contain: no vector database and no graph database."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["Ten steps take one contract from upload to report. A signed-in user uploads a PDF or DOCX (1); the file is parsed, page by page for a PDF and as "
                  "a single page for a DOCX (2); each page is segmented at numbered headings or, failing that, at paragraphs (3). Each clause is then embedded "
                  "and given the label of the nearest of 20 CUAD category centroids (4), and the eight Indian-law rules are tested on its text (5). Every rule hit "
                  "is sent to Gemini together with the rule's legal basis, and the answer supplies the plain-language reason, the quoted provision and the safer "
                  "wording (6). After the last clause, the risky combinations are looked up (7), the complexity score and grade are computed (8) and a second "
                  "Gemini call writes the summary and the list of obligations (9). Everything is committed in one transaction and the report is shown (10).",
                  "The pink boxes are the steps that call Gemini (4, 6 and 9); every other step is local code. The decision that a clause is risky is made by "
                  "step 5, never by Gemini. A failed Gemini call after three attempts stops the whole upload, and nothing is saved."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["At the highest level ClauseGuard is one process with four external entities. The signatory, who may be a freelancer, an individual or a small "
              "business, sends credentials and a contract file and receives the complexity grade, the flagged clauses with reasons and safer wording, and the "
              "clause graph. Google Gemini receives clause text and prompts and returns vectors and JSON text. The evaluator, who is whoever runs `ml/eval.py`, "
              "starts an evaluation and receives `metrics.json` with the precision, recall and top-k scores; the CUAD v1 corpus supplies the labelled clause "
              "spans from which the training and held-out sets were drawn. The data stores are inside the single process and are not drawn at this level."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 splits the system into seven processes: authenticate (1.0), parse and segment (2.0), classify clauses (3.0), detect predatory clauses (4.0), "
              "combine risks and score complexity (5.0), explain and summarise (6.0), and report and browse (7.0). The stores are D1 users, D2 contracts, D3 "
              "clauses (with the embedding), D4 flags and D5 the centroid cache; D2 and D4 are drawn twice because two processes use each. Process 1.0 issues "
              "the token, and every later process checks it and the owner of the contract. Process 2.0 creates the contract row and produces clauses; 3.0 reads "
              "D5, calls Gemini for vectors and writes the clause type to D3; 4.0 produces the rule ids and writes the flags to D4; 5.0 finds the combinations, "
              "computes the grade and writes both to D2; 6.0 calls Gemini and writes reasons and wording to D4 and the summary to D2; 7.0 only reads.",
              "The order of the numbers is logical, not temporal. In the code the explanation for a flag is requested as soon as the rule fires for a clause, "
              "inside the loop of the pipeline, and the combinations and the complexity score are computed after the last clause. The offline evaluation "
              "script is not part of this diagram; it appears in level 0."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: Classify clauses (process 3.0)",
             ["Process 3.0 expands into seven steps that follow `classify_clause()`. The 20 category centroids are loaded from the cache, or built from the 500 "
              "training spans if the cache is missing (3.1). The clause is embedded with the task type RETRIEVAL_QUERY through the Gemini API (3.2), and its cosine "
              "similarity to every centroid is computed and ranked (3.3). A margin test then asks whether the best two categories are within 0.03 of each other "
              "and the best similarity is below 0.60 (3.4). If so, Gemini is asked to choose among the top three categories (3.5); if not, the top category "
              "is kept. A floor test replaces the label by \"Other / Unclassified\" when the confidence is below 0.35 (3.6), and the label, confidence, method and "
              "embedding blob are written to the clause row (3.7).",
              "The note under the figure records a measurement: on the 240 held-out CUAD spans the best similarity ranges from 0.657 to 0.849, so the 0.60 and "
              "0.35 tests never fire and every clause receives one of the 20 labels (Chapter 6, section on the model, shows the distributions)."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["Four actors appear. The signatory (a registered user) registers or logs in (UC1), uploads a contract (UC2), views the grade and plain summary (UC3), "
                 "opens a flagged clause to read the reason, the quoted provision and the safer wording (UC4), views the clause graph and the risky combinations "
                 "(UC5), and lists the contracts (UC6). The visitor, who is not signed in, can register or log in and can open the evaluation page (UC7), which is "
                 "public. The evaluator runs `ml/eval.py`, which produces the figures that UC7 shows. Google Gemini is a secondary actor attached to the use "
                 "cases that call it: uploading (classification and explanation), the summary and the clause explanation.",
                 "Use cases UC2 to UC6 need a valid token and work only on the caller's own contracts. There is no administrator role, no sharing between users "
                 "and no way to edit or delete a contract in the interface."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: uploading a contract and reading the report",
                 ["The diagram follows one upload through seven participants. The user chooses a file and presses Analyse; the React app posts the multipart request "
                  "with the bearer token; the route decodes the token and loads the user from SQLite (a bad token ends here with 401); the file is written under a random "
                  "name and the pipeline is called. The pipeline reads the pages and splits them into clauses, then loops over the clauses: it requests the "
                  "embedding from Gemini, sends a tie-break prompt only when the margin and similarity tests require it (which did not occur in the measured "
                  "runs), applies the rules locally, requests an explanation for each hit and flushes the clause and flag rows. After the loop the combinations "
                  "and the complexity score are computed locally, one more Gemini call returns the summary, and the contract is committed. The route deletes the "
                  "temporary file and returns the report, the browser navigates to the report, and later requests for a clause or the graph read the rows again "
                  "after the ownership check.",
                  "The sequence makes the cost visible: the number of Gemini calls is the number of clauses plus the number of flags plus one, and they run one after "
                  "another. This is why the measured upload of an eleven-clause, eight-flag contract took 113.6 s and the fair eight-clause contract 15.5 s."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram",
           ["The database has four tables joined by three one-to-many relations: a user owns many contracts, a contract contains many clauses, and a clause "
            "raises many flags. The foreign keys are `contracts.user_id`, `clauses.contract_id` and `flags.clause_id`. The two JSON values of a contract "
            "(`key_obligations` and `combo_flags`) are stored as text columns, and the clause vector is a float32 blob of 3,072 values. The box in the figure notes "
            "that deleting a user cascades to everything below it through the SQLAlchemy relationships, and that the clause graph has no table because it is "
            "rebuilt from clauses and flags whenever it is requested."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The upper part shows the four persistent entities (`User`, `Contract`, `Clause` and `Flag`) with their attributes and the 1..* associations, the "
             "`Rule` dataclass with its pattern and legal basis, and `ParsedPage`, the small value object that the parsing module passes to the segmenter. A "
             "`Rule` produces `Flag` rows; a `ParsedPage` feeds the classification service through the clause text. The lower part shows the services as "
             "classes of functions: `Classification`, `RiskGraph`, `Complexity`, `Explain`, `GeminiClient`, `VectorStore`, `Pipeline` and the routers with the "
             "authentication helpers. `Pipeline` coordinates the others; `Classification` and `Explain` use `GeminiClient`; `VectorStore` does the cosine "
             "arithmetic. The service modules are plain Python modules, so the diagram shows them as classes only to make their operations visible."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core algorithms",
                  ["Algorithm 1 is `process_upload()`. The extension must be `.pdf` or `.docx` (otherwise HTTP 400); the pages are extracted and split, and at least one "
                   "clause of 25 or more characters must remain (otherwise HTTP 400 \"no readable clauses\"). For every clause the pipeline classifies, applies the eight "
                   "rules and asks Gemini to explain each hit; a Gemini failure after three retries raises an error that the route reports as HTTP 502 and the "
                   "transaction is rolled back. After the loop come the combinations, the complexity score, the summary and one commit.",
                   "Algorithm 2 is `classify_clause()`. The clause is embedded and ranked against the 20 centroids. If the best two categories differ by less "
                   "than 0.03 and the best similarity is below 0.60, Gemini chooses among the top three; an answer outside the candidates falls back to the first "
                   "candidate with the embedding similarity as its confidence. Finally, a confidence below 0.35 changes the label to \"Other / Unclassified\". The "
                   "result carries the label, the confidence, the method (`embedding` or `gemini_tiebreak`) and the vector."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    d.figure(DIAG / fname, caption, width=width, max_h=3.3 if getattr(d, "report", False) else 4.5)
    for p in paras:
        d.p(p)


def sec_arch(d):
    d.h2("System Architecture")
    d.p("ClauseGuard is a single-machine web application: a React front end, a FastAPI back end, a SQLite database and a client for the Google Gemini API. "
        "It contains no model that was trained for this project; the two learned components, the embedding model and the text model, are remote services. "
        "The figure below shows the layers.")
    diagram(d, "architecture")
    d.p("The design follows five principles. **Decide with rules, explain with a language model.** Whether a clause is predatory is decided by a "
        "deterministic, auditable rule, so the same clause always gives the same flag; Gemini only writes the reason, quotes the trigger and drafts the "
        "safer wording. **Keep every claim traceable.** Each flag stores the rule id, the clause and the page, and the interface repeats this to the user. "
        "**Enforce ownership on the server.** The browser hides other users' contracts, but the decision is made by `_get_owned_contract()` in the API, which "
        "returns 404 for a contract of another user. **Keep storage local and simple.** Vectors are float32 blobs in SQLite and the clause graph is rebuilt "
        "per request, which removes the need for a vector or graph server at the cost of linear scans and no graph persistence. **Isolate the network "
        "dependency.** Gemini is reached through one module (`gemini_client.py`), so the model names, the retry policy and a future replacement of the provider "
        "are confined to a single file.")
    d.p("The design differs from the abstract of the project in three places that should be stated here: the abstract names the Claude API, pgvector and Neo4j, while "
        "the build uses Gemini, SQLite with NumPy, and NetworkX. The reasons and consequences are discussed in Chapters 1 and 6.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams show how data moves through ClauseGuard at three levels of detail: the context (level 0), the seven main processes with their data "
        "stores (level 1) and the expansion of the classification process (level 2).")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Three UML views describe the design: the use-case diagram (who does what), the class diagram (what the code contains) and the sequence diagram "
        "(how the main flow runs). The two core algorithms are shown as flowcharts in the same chapter.")
    diagram(d, "usecase")
    diagram(d, "uml")
    diagram(d, "sequence")
    diagram(d, "flowchart")


def sec_database(d):
    d.h2("Database Design")
    d.p("The database is SQLite, created by SQLAlchemy 2 at start-up with `create_all`; there are no migrations. Results that are read and written whole "
        "(the key obligations and the risky combinations of a contract) are stored as JSON text. The uploaded file itself is not kept: it is written to "
        "`data/uploads` under a random name, parsed and deleted, and only its clause text, vectors and flags remain.")
    diagram(d, "er")
    d.table([["Table", "Purpose", "Columns"],
             ["users", "Accounts", "id (PK), email (unique, indexed), password_hash (bcrypt, 255), created_at"],
             ["contracts", "One analysed contract", "id (PK), user_id (FK users), filename, contract_type_guess (default \"general\"; never set by any code), uploaded_at, complexity_grade, complexity_score, readability_score, legalese_density, cross_reference_count, avg_sentence_length, plain_summary, key_obligations (JSON text), combo_flags (JSON text)"],
             ["clauses", "One segmented clause", "id (PK), contract_id (FK), index_in_doc, page_number, text, clause_type (one of 20 CUAD labels or \"Other / Unclassified\"), classification_confidence (cosine), classification_method (\"embedding\" or \"gemini_tiebreak\"), embedding (float32 blob, 3,072 values = 12,288 bytes)"],
             ["flags", "One rule hit on one clause", "id (PK), clause_id (FK), rule_id, rule_label, severity (low, medium, high), reason, provision, safer_wording"]],
            "Database tables", widths=[0.13, 0.2, 0.67], font=9)
    d.p("Four design points should be noted. First, the relationships carry `cascade=\"all, delete-orphan\"` in SQLAlchemy, so deleting a user removes their contracts, "
        "clauses and flags, but no foreign key declares an `ON DELETE` rule in SQLite itself and no route offers deletion. Second, the combinations are kept as "
        "JSON in `contracts.combo_flags` (combination id, reason, rule ids, clause ids); the clause graph is derived from `clauses`, `flags` and this "
        "column on every request, so there is no graph table and no graph database. Third, the foreign keys are not indexed, which is acceptable for "
        "the measured sizes (a report of eleven clauses is returned in a median of 9.3 ms) but would matter at scale. Fourth, the severity and the "
        "classification method are plain strings, not enumerations, and timestamps use `datetime.utcnow`. Passwords are never stored in clear text.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([["Module", "Code (lines)", "Responsibility"],
             ["Application", "backend/app/main.py (35)", "Creates the FastAPI app, CORS, table creation at start-up and `/api/health`; includes the three routers"],
             ["Configuration", "app/config.py (28)", "Reads `.env`: Gemini key and model names, ports, JWT secret and lifetime; creates the data, upload and experiment folders"],
             ["Database", "app/db.py (103)", "Engine, session dependency and the four models (`User`, `Contract`, `Clause`, `Flag`)"],
             ["Security", "app/auth.py (47)", "bcrypt hashing and checking, HS256 token creation and decoding, `get_current_user` dependency"],
             ["Schemas", "app/schemas.py (79)", "Pydantic request and response types (registration with e-mail and 6-character password, report, clause, flag)"],
             ["Auth routes", "app/routes/auth.py (33)", "`POST /api/auth/register` and `/login`"],
             ["Contract routes", "app/routes/contracts.py (133)", "Upload with validation, list, report, clause detail, graph, ownership check"],
             ["Evaluation route", "app/routes/eval.py (22)", "Serves `experiments/eval/metrics.json`"],
             ["Parsing", "app/services/parsing.py (95)", "PDF and DOCX text extraction, heading-based segmentation with paragraph fallback"],
             ["Classification", "app/services/classification.py (109)", "Centroid cache, nearest-centroid classification, Gemini tie-break, confidence floor"],
             ["Rules", "app/services/rules.py (134)", "The eight predatory-clause rules with severity and legal basis; `detect_flags()`"],
             ["Combination graph", "app/services/graph.py (79)", "Three risky combinations, NetworkX graph, JSON for the interface"],
             ["Complexity", "app/services/complexity.py (110)", "Flesch reading ease, legalese density, cross-references, sentence length, weighted score and grade"],
             ["Explanation", "app/services/explain.py (54)", "Prompts for the reason, provision and safer wording of a flag and for the contract summary"],
             ["Gemini client", "app/services/gemini_client.py (65)", "Embedding and text calls, three retries, JSON extraction"],
             ["Vector store", "app/services/vectorstore.py (31)", "float32 blob conversion and cosine similarity with NumPy"],
             ["Pipeline", "app/services/pipeline.py (89)", "`process_upload()`: the loop over clauses, combinations, score, summary, commit"],
             ["Evaluation", "ml/eval.py (144)", "Rule precision, recall and F1 on the 40-clause set; CUAD top-1 and top-3; writes `metrics.json`"],
             ["Data scripts", "scripts/build_cuad_samples.py (82), download_data.py (43), smoke_test.py (149)", "Seeded CUAD train and held-out split, corpus download, live end-to-end smoke test"],
             ["Tests", "tests/ (5 files)", "68 passing tests and 5 expected failures, with Gemini stubbed"],
             ["Web application", "frontend/src/ (56 files, 4,507 lines)", "9 pages, 17 interface-kit components, motion and landing components, the API client, authentication and theme providers"]],
            "Modules of ClauseGuard", widths=[0.16, 0.3, 0.54], font=9)
    d.p("The backend application code is about 1,250 lines in 17 files. The directory `backend/app/services` holds all of the analysis logic; the routers contain "
        "no business rules except the ownership check and the status-code mapping.")


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The web application has nine pages. The public pages are the landing page, sign-up, log-in and the evaluation page. After log-in a sidebar layout "
        "offers two entries, My contracts and Upload contract, and the contract pages are reached from the list: the contract report, the clause detail "
        "page with two tabs (Flags and Clause text) and the clause graph. Four pages (landing, evaluation, contract report and clause graph) are loaded on demand, and a "
        "protected-route component sends a visitor without a token to the log-in page; the older paths `/upload` and `/contracts` redirect to the new ones.",
        "The design decisions follow from the users, who are not lawyers. The report opens with the grade as a large badge and six figures (readability, legalese "
        "density, cross-references, average sentence length, flagged clauses and the score), followed by the plain-language summary, the key obligations and a "
        "chart of the clauses by their highest severity. Risky combinations are shown in their own warning-coloured panel. Each flagged clause shows the reason, the "
        "quoted provision and the safer wording in separate blocks, with severity as a coloured badge that is also written as a word. The upload page "
        "validates the extension in the browser, shows a progress bar and then an indeterminate bar while the server works, and states that the file is removed "
        "after analysis. The sidebar repeats the promise that every flag is tied to the exact clause and page. A theme toggle switches between light and dark.",
        "Three limitations of the interface should be stated. The clause graph places its nodes evenly on a circle, so the position of a node carries no "
        "meaning; only the red colour and the lines between clauses of the same combination do. The upload request has a client timeout of 180 s, which a "
        "contract with many flags can exceed because the server makes one Gemini call per flag (the measured eight-flag contract needed 113.6 s). And "
        "the evaluation page describes its scores as measured \"on a held-out set\" although the 40 clauses behind them were written together with the rules, a "
        "point examined in Chapter 8. The screens below were captured from the running application with the three real uploads of this project; the complete "
        "set is in Chapter 8 and Appendix C.")
    d.figure_pair([(SHOTS / "03_register.png", "Sign-up page"), (SHOTS / "05_upload_empty.png", "Upload page before a file is chosen")])
    d.figure_pair([(SHOTS / "08_report_freelance_top.png", "Contract report: grade, six figures, summary and severity chart"),
                   (SHOTS / "10_report_freelance_table.png", "Clause table with type, flags and risk")])
    d.figure_pair([(SHOTS / "11_clause_detail_termination.png", "Clause detail: reason, quoted provision and safer wording"),
                   (SHOTS / "14_clause_graph.png", "Clause graph with the risky combinations")])
    d.figure_pair([(SHOTS / "19_contracts_list.png", "My contracts list with three analysed contracts"),
                   (SHOTS / "20_evaluation.png", "Evaluation page with the measured scores")])
