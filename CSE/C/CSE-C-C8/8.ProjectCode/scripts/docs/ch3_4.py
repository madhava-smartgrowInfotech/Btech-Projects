"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

_REAL = F.REAL
_EXTRACT_MS = [r["timings_ms"]["extract_ms"] for r in _REAL[1:]]          # the three real papers (17-30 pages)
_PAGES = [r["pages"] for r in _REAL[1:]]
_POOL6 = F.MINILM["scaling_ms"][0]["median_ms"]
_POOL500 = F.MINILM["scaling_ms"][-1]["median_ms"]
_LIT_MS = [x["ms"] for x in F.LIT]
_PK = F.ENV["packages"]


def _api_note():
    api = F.LATENCY.get("http_api")
    if not api:
        return ""
    return (f" Over HTTP on 127.0.0.1 the directory and history reads take a median of {api['reviewers_list']['median_ms']:.0f} ms and "
            f"{api['analyses_list']['median_ms']:.0f} ms, and a complete analysis without the local language model takes a median of "
            f"{api['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s for the three-page demo paper.")


def blocks():
    if F.REPORT:
        return report3() + report4()
    return chapter3() + chapter4()


# =====================================================================================================================
def chapter3():
    llm_load = F.LATENCY.get("llm_load_s")
    llm_row = (f"Qwen2.5-1.5B-Instruct (fp32, CPU) loads in {llm_load:.0f} s; one complete analysis with the three-step AI review takes {F.lat_demo_text()} "
               if llm_load else f"Qwen2.5-1.5B-Instruct (fp32, CPU) runs; one complete analysis with the three-step AI review takes {F.lat_demo_text()} ")
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built, run and maintained with the resources at hand. For PeerScope the question was answered partly by analysis "
          "and partly by building the system and measuring it on the development machine, so most entries below carry a measured value rather than an estimate. Where a "
          "question could not be settled with the data available to the team, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk of the project lay in four places: whether PDF text, sections and references could be extracted reliably on a local machine; whether a "
          "text classifier and a sentence-embedding model could run on an ordinary processor without a graphics card; whether a small open-weight language model could "
          "draft a review on the same hardware; and whether the pieces could be combined into one auditable reviewer ranking. The development machine is a desktop with "
          f"an {F.ENV['cpu']} (6 cores, 12 threads), {F.ENV['ram_gb']} GB of RAM and no graphics processor in use, running Windows 11. On that machine:"),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can PDF text, sections and references be extracted locally?",
             f"PyMuPDF extracts {min(_PAGES)}-{max(_PAGES)} page papers in {min(_EXTRACT_MS):.0f}-{max(_EXTRACT_MS):.0f} ms; section and reference detection is regex based (Chapter 8 lists where it fails)", "Feasible, with known misses"],
            ["Can the decision model be trained and evaluated on a CPU?",
             "TF-IDF plus logistic regression: the whole evaluation (reload, three baselines, five refits) took about 9 s", "Feasible"],
            ["Is the decision model's accuracy useful?",
             f"accuracy {F.pct(F.SHIPPED['accuracy'], 1)}, macro F1 {F.f3(F.SHIPPED['f1_macro'])}, ROC-AUC {F.f3(F.SHIPPED['roc_auc'])} on {F.DM['test']} synthetic held-out papers", "Demonstration only"],
            ["Can sentence embeddings rank reviewers on a CPU?",
             f"MiniLM loads in {F.MATCH['minilm_status']['load_seconds']:.0f} s; ranking 6 reviewers takes {_POOL6:.0f} ms and 500 reviewers {_POOL500 / 1000:.1f} s", "Feasible"],
            ["Is the matching useful?",
             f"top-1 {F.pct(F.MINILM['full_hybrid_shipped_weights']['top1'], 1)} and top-3 {F.pct(F.MINILM['full_hybrid_shipped_weights']['top3'], 1)} on 40 team-written probe papers against 6 demo reviewers", "Feasible (small test)"],
            ["Can a local language model draft the review?", llm_row + "(no GPU)", "Feasible but slow"],
            ["Can related literature be fetched?",
             f"OpenAlex answered {len(_LIT_MS)} test queries with 6 works each in {min(_LIT_MS) / 1000:.1f}-{max(_LIT_MS) / 1000:.1f} s; offline, the tab reports 'unavailable'", "Feasible, needs internet"],
            ["Can everything run behind one local API?",
             f"{F.LOC['backend_app']:,} lines of Python in app/, SQLite storage, no external service except the optional OpenAlex query", "Feasible"],
        ], widths=[1.9, 3.3, 1.1], size=10, align=["l", "l", "l"]),
        P("Where the checks are weakest is realism of the data. The decision model could not be trained on real peer-review decisions, because the public probe in "
          "the data-preparation script did not return a usable dataset and the project had no access to confidential review records. It was therefore trained on a "
          "synthetic corpus of 1,400 labelled texts, and Chapter 8 explains why its accuracy cannot exceed about "
          f"{F.GEN['best_possible_accuracy_from_phrases']:.2f} on that corpus. The technical feasibility of predicting real decisions was therefore not established; "
          "the feasibility of the pipeline around such a signal was. The reviewer-matching test is similarly small: six demo reviewers and forty probe abstracts."),
        P("A second, smaller risk is the dependency chain. The model files were written by scikit-learn 1.9 and are unpickled by the "
          "installed version; a much older scikit-learn can load the estimator but fail to return class probabilities, in which case the service returns the label only. "
          "The launcher run.bat therefore rebuilds a broken virtual environment, and the models can be retrained in seconds if the artefacts are deleted."),

        H2("3.2 Economic Feasibility"),
        P("The whole software stack is open source: Python, FastAPI, Uvicorn, SQLAlchemy, PyMuPDF, scikit-learn, sentence-transformers, PyTorch, Transformers, ReportLab, React, "
          "Vite, Recharts, Framer Motion, GSAP and three.js. No paid API is used at run time. The decision model, the embedding model and the language model all run "
          "on the user's own machine, and the only outgoing request is the title or keyword query sent to OpenAlex, a public API that needs no key [32]. "
          "There is therefore no per-analysis fee and no subscription."),
        P("The costs that remain are real but were not measured in money. The team used an existing desktop computer, so no hardware was bought for the project, and "
          "we did not record electricity or labour costs; any rupee figure would be an invention, so none is given. The resources that were measured are disk and memory: "
          "the cached Qwen2.5-1.5B-Instruct weights occupy about 2.9 GB of disk, and the Python process that held the model used roughly 4 to 6 GB of memory while analysing a "
          "paper on the development machine. An institution that wished to deploy the system would add the cost of a server with that much memory and of staff time to maintain the "
          "reviewer directory; compared with the staff time spent on manual first-pass screening, the team expects this to be modest, but that comparison was not measured."),
        P("Software licences must be checked before the system is redistributed. PyMuPDF is distributed under the GNU Affero General Public Licence or a commercial licence, "
          "which matters if PeerScope is offered as a network service to other organisations. The model weights and the Hugging Face libraries have their own licences, which "
          "the team read only at the level of the model cards and did not audit. The reviewer profiles shipped with the project are marked demo data and describe no real person."),

        H2("3.3 Operational Feasibility"),
        P("A user starts the whole system with one script, run.bat. On the first run it checks that Python and Node.js are present, creates the virtual environment, installs the "
          f"Python packages, prepares the dataset and trains the decision model if the model files are missing, generates the demo PDF, installs the web-app packages, and starts the API on port "
          f"{F.API_PORT} and the web app on port {F.WEB_PORT}. The browser then opens on the landing page. The interface has the landing page and seven working screens "
          "(Dashboard, Analyze, Saved analysis, Reviewers, Model performance, History and About). An editor can upload a paper and read a result without any command-line work."),
        P("Operating the system needs little attention. Settings such as the ports, the upload limit, the model names, the literature count and the matching weights live in a "
          "single .env file, and the reviewer directory is edited in the browser or imported from CSV. A Docker image of the API is also provided. Two operational facts "
          "deserve to be stated. First, the first analysis after start-up is slow, because the embedding model and the language model are loaded lazily; later analyses reuse them. "
          "Second, because there is no login, the system is suitable for one trusted user or a small office on a private network, not for open exposure."),
        P("Maintenance is simple because the application is organised as small modules with one responsibility each (Chapter 5). A change to the matching weights is a change to three "
          "lines of configuration, a new reviewer is a form submission, and the decision model is retrained with one script. The test suite and the smoke test (Chapter 7) "
          "check the main flows after a change."),

        H2("3.4 Schedule Feasibility"),
        P("The calendar dates of the work were not recorded in the project artefacts, so none are given. The work was organised in dependent phases; the table lists them in "
          "the order in which their products exist in the repository."),
        TAB("Project phases and their products", ["Phase", "Work", "Product"], [
            ["1", "Literature survey, base paper study, problem statement and objectives", "Batch documents 2 to 6"],
            ["2", "Dataset preparation and decision-model training", "scripts/prepare_dataset.py, scripts/train_model.py, models/"],
            ["3", "Extraction, features, review, literature, embeddings and matching services", "app/services/ (12 modules)"],
            ["4", "API, validation, SQLite storage and export", "app/main.py, app/models.py, app/schemas.py"],
            ["5", "Web interface (first a plain static page, then the React application)", "static/, frontend/src/ (8 pages)"],
            ["6", "Tests, smoke test, measurements and screenshots", "tests/, scripts/smoke_test.py, scripts/measure_metrics.py, docs/"],
            ["7", "Documentation, decks and report", "Batch documents 7 to 19"],
        ], widths=[0.6, 3.3, 2.4], size=10.5, align=["c", "l", "l"]),
        P("Phases 3 and 4 are loosely coupled, because the services are written as functions that take and return plain dictionaries; they can be developed and tested "
          "separately, and the unit tests do exactly that. The evaluation of reviewer matching needed a hand-written probe set because no real labelled data existed "
          "for it, which is why that evaluation is small and is described as such in Chapter 8."),

        H2("3.5 Advantages and Constraints"),
        TAB("Advantages and constraints of the proposed system", ["Aspect", "Advantage", "Constraint"], [
            ["Privacy", "PDFs are processed on the user's machine; only a title query leaves it", "OpenAlex receives the title or keywords of every analysed paper"],
            ["Transparency", "Every recommendation lists its score breakdown, matching terms and conflict check", "The weights are expert guesses, not fitted to data"],
            ["Robustness", "If the language model or OpenAlex is unavailable the rest of the result is still shown", "The deterministic review is rule based and less informative"],
            ["Cost", "No paid API, no GPU, open-source stack", "Licences of PyMuPDF and the model weights must be checked"],
            ["Speed", "Extraction, features, decision signal and matching complete in well under a second after warm-up", "The local language model needs minutes per paper on a CPU"],
            ["Data", "Runs without any real review data", "The decision signal is trained on synthetic data and is a demonstration"],
            ["Scale", "Ranking time grows linearly with the pool", f"Every profile is re-embedded per request: {_POOL500 / 1000:.1f} s for 500 reviewers"],
            ["Security", "Upload type, size and header checks; local processing", "No authentication; a PDF could carry hidden instructions aimed at an AI reviewer [2], [27]"],
        ], widths=[1.0, 2.7, 2.6], size=10, align=["l", "l", "l"]),
        H2("3.6 Risk Analysis"),
        P("The main risks were identified during development and each has a mitigation that is part of the implementation. The ratings are the team's qualitative judgement, not measured probabilities."),
        TAB("Risks and mitigations", ["Risk", "Effect", "Mitigation in PeerScope"], [
            ["The language model cannot be loaded (memory, download, version)", "No AI review text", "Automatic fallback to the 0.5B model, then to the deterministic review, with a visible status and note"],
            ["OpenAlex unreachable or slow", "No related literature", "8 s timeout; the literature tab reports 'unavailable' and the rest of the result is kept"],
            ["Embedding model cannot be downloaded", "Weaker ranking", "TF-IDF fallback keeps matching working; the status is shown in the health route"],
            ["Section detection or title heuristic fails on an unusual layout", "Wrong structural signals", "Signals are labelled as preliminary; evidence excerpts are shown so a human can check"],
            ["Reviewer directory is out of date", "Wrong availability or missing experts", "Editable in the browser; active flag and load fields; CSV import"],
            ["A conflict is expressed in words the matcher does not know", "A conflicted reviewer is not penalised", "Disclaimer asks the user to verify conflicts independently; the limit is measured and reported"],
            ["Misuse of the decision signal as a verdict", "Unfair treatment of a paper", "Synthetic-data banner, 'not a judgment of scientific correctness' wording, human-in-the-loop framing"],
            ["Hidden instructions inside a PDF aimed at an AI reviewer", "Manipulated AI text", "Local processing and a deterministic review that does not obey text; no filter is claimed [2], [27]"],
        ], widths=[2.1, 1.5, 2.7], size=9.5, align=["l", "l", "l"]),
        H2("3.7 Feasibility Conclusion"),
        P("In summary, the project is technically, economically and operationally feasible as a decision-support tool for a single editor or programme committee, and it was "
          "completed on the available hardware. It is not feasible, with the data and time available, to claim that the system predicts real editorial decisions, and the "
          "documents of this project do not make that claim."),
    ]


# =====================================================================================================================
def chapter4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the situation that PeerScope addresses, what the system must do, and the environment in which it runs. The requirements are numbered so that "
          "the design in Chapter 5, the tests in Chapter 7 and the results in Chapter 8 can refer to them."),

        H2("4.1 Existing System and its Limitations"),
        P("In most journals and conferences the assignment of submissions to reviewers is still a human activity. An editor or programme chair reads the title and abstract, "
          "recalls who works on the topic, searches the reviewer list by keyword, and checks by hand whether the candidate is free and has no relationship with the authors. "
          "Conferences that use a submission system add reviewer bidding and keyword or topic-area matching, and researchers have studied the reviewer assignment problem for about "
          f"thirty years [{R['rap_scoping']}], [{R['rap_survey']}], but the affinity score between a paper and a reviewer remains the hard part, and learned or embedding-based scores are difficult to audit [{R['base']}]. "
          "The first reading of a submission, which decides whether it is worth sending out at all, is also manual."),
        P(f"Human judgement is not a reliable fixed point either. In the NeurIPS 2021 consistency experiment two independent committees reviewed the same papers and disagreed on about "
          f"23 % of the accept or reject outcomes [{R['neurips_consistency']}]. The existing practice therefore has the following limitations."),
        TAB("Limitations of the existing system", ["Limitation", "Consequence"], [
            ["Reviewer choice depends on the editor's memory", "Experts outside the editor's network are missed; mismatched reviewers produce weak reviews and delays"],
            ["Keyword matching shares vocabulary, not expertise", "Reviewers who use the same words but work in a different area are proposed"],
            ["Workload and availability are tracked separately", "Assignments reach reviewers who are already at their limit"],
            ["Conflicts of interest are checked by eye", "A relationship hidden in the text of the paper can be overlooked"],
            ["First-pass screening is manual", "Obvious structural problems (no method section, almost no references) consume editor time"],
            ["No consistency check between reviewers", "The same paper can receive very different assessments"],
            ["Decisions are rarely explained", "Neither authors nor editors can see why a reviewer was chosen"],
        ], widths=[2.6, 3.7], size=10.5, align=["l", "l"]),

        H2("4.2 Proposed System and its Advantages"),
        P("PeerScope is a local web application that takes one research-paper PDF and returns two things: a preliminary assessment of the paper and a ranked, explained list of "
          "candidate reviewers. The assessment combines deterministic structural signals, a trained decision signal and, when the local model loads, a three-step AI review, "
          "together with related literature from OpenAlex. The ranking scores every reviewer in the directory by semantic similarity to the paper, keyword and method overlap and "
          "availability, and subtracts a penalty when the paper's text points to a conflict. The result is stored and can be exported as JSON or PDF. Final judgement stays with the editor."),
        P(f"The system adopts the central idea of the base paper [{R['base']}], that reviewer recommendations should be auditable, and adds what that paper does not cover: intake of the paper "
          "itself, a first-pass assessment, availability and conflict terms inside the score, a reviewer directory with CRUD and CSV, history and export."),
        TAB("Existing practice compared with PeerScope", ["Aspect", "Existing practice", "PeerScope"], [
            ["Reviewer choice", "Editor's memory and keyword search", "Cosine similarity of MiniLM embeddings plus keyword and method overlap"],
            ["Explanation", "None or informal", "Per-reviewer breakdown, matching terms and a sentence of reasoning"],
            ["Workload", "Separate spreadsheet", "Availability = 1 - current load / maximum load, inside the score"],
            ["Conflict check", "Manual", "Conflict terms, full name and affiliation searched in the paper text"],
            ["First-pass screening", "Manual reading", "Structural score, concerns and recommendations, with page-anchored evidence"],
            ["Related work", "Manual search", "OpenAlex works ranked by similarity to the title"],
            ["Record keeping", "Email threads", "Stored analyses with JSON and PDF export"],
            ["Privacy", "Depends on the tool", "Local processing; only a title query leaves the machine"],
        ], widths=[1.3, 2.3, 2.7], size=10, align=["l", "l", "l"]),
        P("The advantages are the ones the team could demonstrate: every number in the ranking can be reproduced from the stored breakdown; the system degrades gracefully "
          "when the language model or the internet is missing; and the cost is low. What the system does not do is replace a reviewer, validate scientific claims or prove novelty, "
          "and the interface says so on every screen."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Realised by"], [
            ["FR-1", "Accept a research-paper PDF of up to 20 MB, reject other types, empty files, files without the %PDF header and oversize files with a clear message", "POST /api/analyze; Analyze page"],
            ["FR-2", "Extract page text, title, nine standard sections and references from the PDF", "pdf_extract.extract_pdf"],
            ["FR-3", "Compute word and sentence counts, keywords, method terms, topic hints and four structural signals with an overall structural score", "features.extract_features"],
            ["FR-4", "Give a three-class (accept, borderline, reject) historical decision signal with class probabilities", "ml_predict.predict_decision"],
            ["FR-5", "Produce strengths, major and minor concerns, recommendations and a coverage view deterministically", "review_synthesis.deterministic_review"],
            ["FR-6", "Produce an AI review with a local language model when it can be loaded, and state plainly when it cannot", "review_synthesis.llm_review, llm_service"],
            ["FR-7", "Retrieve related literature and rank it by similarity; report 'unavailable' on failure", "literature.retrieve_literature"],
            ["FR-8", "Maintain a reviewer directory: list, create, edit, delete, activate or deactivate", "/api/reviewers routes; Reviewers page"],
            ["FR-9", "Import and export the directory as CSV", "POST /api/reviewers/import, GET /api/reviewers/export/csv"],
            ["FR-10", "Rank reviewers by a weighted score with a per-reviewer breakdown and explanation", "matching.match_reviewers"],
            ["FR-11", "Detect and penalise conflicts of interest found in the paper text", "matching.detect_conflict"],
            ["FR-12", "Filter the ranking by active status, minimum score, topic and method; return the top five", "pipeline.run_analysis; Analyze filters"],
            ["FR-13", "Store every analysis and list, reopen and search the history", "analyses table; History, Saved analysis pages"],
            ["FR-14", "Export a stored analysis as JSON or as a PDF report", "GET /api/analyses/{id}/export"],
            ["FR-15", "Show the measured metrics of the decision model, with a notice when the data are synthetic", "GET /api/model/metrics; Model page"],
            ["FR-16", "Show system status and counts on a dashboard", "GET /api/health; Dashboard page"],
            ["FR-17", "Show a responsible-use disclaimer on the product", "About page, footer, exports"],
            ["FR-18", "Seed clearly marked demo reviewers when the directory is empty", "seed.seed_if_empty"],
        ], widths=[0.6, 3.7, 2.0], size=9.5, align=["c", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and how they are met", ["ID", "Requirement", "How met / measured"], [
            ["NFR-1", "Privacy: documents are not sent to a third party", "All processing is local; the only outgoing call is the OpenAlex title or keyword query"],
            ["NFR-2", "Responsiveness of routine operations",
             f"Model metrics, reviewer and history reads are database or file reads.{_api_note()}"],
            ["NFR-3", "Bounded cost of one analysis without the language model",
             f"Extraction {min(_EXTRACT_MS):.0f}-{max(_EXTRACT_MS):.0f} ms for 17-30 page papers, then features, decision signal and matching in milliseconds (Chapter 8)"],
            ["NFR-4", "Graceful degradation", "Missing language model, embedding model or OpenAlex leaves the rest of the result and a visible status"],
            ["NFR-5", "Auditability", "Weights, per-signal values, matched terms, conflict reason and model status are shown and exported"],
            ["NFR-6", "Input safety", "Extension, content type, 20 MB size, %PDF header; temporary file deleted after each request"],
            ["NFR-7", "Reproducibility", "Fixed random seed 42, stratified split, saved metrics, measurement scripts in scripts/"],
            ["NFR-8", "Usability", "One launcher; responsive layout, dark and light themes, empty, loading and error states, keyboard-accessible controls"],
            ["NFR-9", "Portability", "Windows launcher run.bat; Docker image of the API; Python 3.11 or 3.12; Node.js 18 or newer"],
            ["NFR-10", "Honesty of output", "Disclaimers on every screen; synthetic-data banner on the model page; no fabricated content when a component is down"],
            ["NFR-11", "Configurability", "Weights, model names, limits and ports in .env without code changes"],
        ], widths=[0.7, 2.2, 3.4], size=10, align=["c", "l", "l"]),
        P("Two requirements were deliberately not set. No accuracy target was fixed for the decision signal, because no real labelled data exist for the project and any target would "
          "have been arbitrary; and no throughput target was set for the AI review, which depends on the hardware. Both are reported as measurements in Chapter 8."),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware used and observed needs", ["Item", "Used for development and all measurements", "Observation"], [
            ["Processor", f"{F.ENV['cpu']}", "CPU only; no GPU code path"],
            ["Memory", f"{F.ENV['ram_gb']} GB", "The language-model process used about 4 to 6 GB; the rest of the stack needs far less"],
            ["Disk", "Local SSD", "About 2.9 GB for the cached Qwen2.5-1.5B-Instruct weights, plus the embedding model and the Python environment"],
            ["Display", "1440 x 900 viewport for screenshots", "Layout is responsive; on narrow screens the sidebar becomes a drawer"],
            ["Network", "Internet on first use", "Needed to download the models once and for OpenAlex lookups"],
        ], widths=[1.0, 2.4, 2.9], size=10, align=["l", "l", "l"]),
        P("Smaller machines were not tested, so no minimum configuration is claimed. A machine with less memory can use the 0.5B fallback model named in the configuration, or run "
          "without the language model, in which case the deterministic review is used."),

        H2("4.6 Software Requirements"),
        TAB("Software requirements", ["Component", "Requirement", "Version used in the measurements"], [
            ["Operating system", "Windows (run.bat); Linux or macOS by manual start", F.ENV["os"].replace("Windows-10-10.0.26200-SP0", "Windows 11, build 10.0.26200")],
            ["Python", "3.11 or 3.12", F.ENV["python"]],
            ["Web framework", "FastAPI, Uvicorn, Pydantic, python-multipart", f"FastAPI {_PK['fastapi']}, Uvicorn {_PK['uvicorn']}, Pydantic {_PK['pydantic']}"],
            ["Database", "SQLite through SQLAlchemy", f"SQLAlchemy {_PK['SQLAlchemy']}"],
            ["PDF", "PyMuPDF", f"PyMuPDF {_PK['PyMuPDF']}"],
            ["Machine learning", "scikit-learn, pandas, numpy, scipy, joblib", f"scikit-learn {_PK['scikit-learn']}, pandas {_PK['pandas']}, numpy {_PK['numpy']}, scipy {_PK['scipy']}"],
            ["Embeddings and language model", "sentence-transformers, PyTorch, Transformers, accelerate", f"sentence-transformers {_PK['sentence-transformers']}, torch {_PK['torch']}, transformers {_PK['transformers']}"],
            ["Reports and HTTP", "ReportLab, requests", f"ReportLab {_PK['reportlab']}, requests {_PK['requests']}"],
            ["Web app", "Node.js 18 or newer; React 19, Vite 8, React Router 7, Recharts 3, Framer Motion, GSAP, three.js", "as pinned in frontend/package.json"],
            ["Browser", "A current Chrome, Edge or Firefox", "Chrome (screenshots)"],
            ["Tests", "pytest, httpx", "pytest suite and scripts/smoke_test.py"],
        ], widths=[1.4, 2.6, 2.3], size=9.5, align=["l", "l", "l"]),

        H2("4.7 Data Requirements"),
        P("The system works with three kinds of data. The paper is an uploaded PDF. The reviewer profile is a record with the fields below, validated by a Pydantic schema before it is stored. "
          "The analysis result is a structured document that is stored as JSON text and exported."),
        TAB("Reviewer profile fields and their validation", ["Field", "Meaning", "Limit"], [
            ["display_name", "Name shown in the directory (required)", "1 to 200 characters"],
            ["affiliation", "Institution; also used for conflict detection", "up to 300 characters"],
            ["expertise_description", "Free-text description embedded for similarity", "up to 4,000 characters"],
            ["research_topics, methods, keywords", "Comma-separated terms used for overlap scores", "up to 2,000 characters each"],
            ["publication_titles", "Titles of the reviewer's work, embedded with the description", "up to 4,000 characters"],
            ["current_load, maximum_load", "Papers now assigned and the most the reviewer accepts", "0 to 100 and 1 to 100"],
            ["is_active", "Whether the reviewer can be proposed", "true or false"],
            ["conflict_terms", "Comma-separated strings that signal a conflict when found in a paper", "up to 2,000 characters"],
        ], widths=[1.9, 2.9, 1.5], size=10, align=["l", "l", "l"]),
        P("The output of an analysis contains the paper's metadata and sections, the features, the decision signal, the structural assessment, the review, the review-quality counts, the "
          "literature, the top five reviewers with breakdowns, the reviewer pool size, the disclaimer and a responsible-use statement."),

        H2("4.8 User Roles"),
        P("PeerScope has no login, so roles describe what a person does, not what the system enforces. Everyone who can open the web address can do everything."),
        TAB("User roles", ["Role", "Goal", "Main screens"], [
            ["Editor or programme chair", "Screen a submission and choose reviewers", "Analyze, Saved analysis, History, Dashboard"],
            ["Reviewer-directory administrator", "Keep reviewer profiles, loads and conflict terms current", "Reviewers (create, edit, activate, import, export)"],
            ["Operator or developer", "Install, configure, retrain, test", "run.bat, .env, scripts/, API documentation at /docs"],
        ], widths=[2.0, 2.4, 1.9], size=10.5, align=["l", "l", "l"]),
        P("The two human roles are normally one person in a small office, which is why the system was built without accounts. Adding authentication, and separating the "
          "administrator from the editor, is listed as future work."),

        H2("4.9 Constraints and Assumptions"),
        B("**Text PDFs.** Extraction reads the text layer; scanned image-only PDFs yield very little text and the response then carries a warning.",
          "**English.** The section patterns, the method lexicon and the demo reviewers are English; other languages were not tested.",
          "**Small directory.** The measurements use six demo reviewers; behaviour with hundreds of real profiles was only timed, not evaluated for quality.",
          "**Synthetic training data.** The decision model is trained on a synthetic set; its output is a demonstration, not evidence about real decisions.",
          "**Literal conflict matching.** Conflicts are found only when a conflict term, the full name or the affiliation string appears in the first 3,000 characters.",
          "**Single user, local network.** No authentication, open CORS and a single SQLite file.",
          "**Time.** The language-model review is optional because it takes minutes per paper on a CPU."),

        H2("4.10 Requirements Against Objectives"),
        P("The six project objectives are traced to the requirements in the following table; the degree to which each was met is assessed in Chapter 8."),
        TAB("Objectives and the requirements that serve them", ["Objective", "Requirements"], [
            ["1. Build a corpus of submitted papers and reviewer profiles", "FR-8, FR-9, FR-13, FR-18"],
            ["2. Extract topics, methods and keywords with NLP", "FR-2, FR-3"],
            ["3. Represent reviewer expertise as comparable vectors", "FR-10"],
            ["4. Rank reviewers by semantic similarity", "FR-10, FR-12"],
            ["5. Preliminary assessment of structure, novelty signals and completeness", "FR-3, FR-4, FR-5, FR-6, FR-7"],
            ["6. Evaluate assignment quality and conflict handling", "FR-11, NFR-5, NFR-7"],
        ], widths=[3.9, 2.4], size=10.5, align=["l", "l"]),
    ]


# =====================================================================================================================
# Compact variant used inside the full report (F.REPORT = True); the chapter documents keep the full text above.
def report3():
    llm_load = F.LATENCY.get("llm_load_s")
    llm_row = (f"Qwen2.5-1.5B-Instruct (fp32, CPU) loads in {llm_load:.0f} s; one analysis with the three-step AI review takes {F.lat_demo_text()}"
               if llm_load else f"Qwen2.5-1.5B-Instruct (fp32, CPU) runs; one analysis with the three-step AI review takes {F.lat_demo_text()}")
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("The feasibility of PeerScope was settled partly by analysis and partly by building the system and measuring it. Where a question could not be settled with the data "
          "available to the team, the entry says so."),
        H2("3.1 Technical Feasibility"),
        P("The risks lay in PDF extraction, in running a classifier, an embedding model and a small language model without a GPU, and in combining them into one auditable ranking. "
          f"The development machine is a desktop with an {F.ENV['cpu']} (6 cores, 12 threads) and {F.ENV['ram_gb']} GB of RAM."),
        TAB("Technical feasibility checks", ["Question", "Measurement", "Verdict"], [
            ["PDF text, sections, references locally?",
             f"PyMuPDF reads {min(_PAGES)}-{max(_PAGES)} page papers in {min(_EXTRACT_MS):.0f}-{max(_EXTRACT_MS):.0f} ms; section detection is regex based", "Feasible, with misses"],
            ["Decision model on a CPU, and is it useful?",
             f"full evaluation took about 9 s; accuracy {F.pct(F.SHIPPED['accuracy'], 1)}, macro F1 {F.f3(F.SHIPPED['f1_macro'])} on {F.DM['test']} synthetic papers", "Demonstration only"],
            ["Embeddings rank reviewers on a CPU?",
             f"MiniLM loads in {F.MATCH['minilm_status']['load_seconds']:.0f} s; 6 reviewers ranked in {_POOL6:.0f} ms, 500 in {_POOL500 / 1000:.1f} s; "
             f"top-1 {F.pct(F.MINILM['full_hybrid_shipped_weights']['top1'], 1)} on 40 team-written probes", "Feasible (small test)"],
            ["Local language model drafts the review?", llm_row + " (no GPU)", "Feasible but slow"],
            ["Related literature?",
             f"OpenAlex answered {len(_LIT_MS)} queries in {min(_LIT_MS) / 1000:.1f}-{max(_LIT_MS) / 1000:.1f} s; offline the tab reports 'unavailable'", "Needs internet"],
        ], widths=[1.8, 3.4, 1.1], size=9.5, align=["l", "l", "l"]),
        P("The weakest check is the data. The decision model was trained on a synthetic corpus of 1,400 texts, so predicting real decisions was not shown to be feasible; the pipeline "
          "around the signal was. The matching test is also small: six demo reviewers and forty probe abstracts."),
        H2("3.2 Economic Feasibility"),
        P("The stack is open source and no paid API is used; the only outgoing request is a title query to OpenAlex, which needs no key [32]. No hardware was bought and no money "
          "figures were measured, so none are given. Measured resources are about 2.9 GB of disk for the cached language-model weights and roughly 4 to 6 GB of memory in the process that held "
          "the model. PyMuPDF is distributed under the AGPL or a commercial licence, and the model licences were not audited; both must be checked before redistribution."),
        P("The software stack is open source: Python, FastAPI, Uvicorn, SQLAlchemy, PyMuPDF, scikit-learn, sentence-transformers, PyTorch, Transformers, ReportLab, React, Vite, Recharts, "
          "Framer Motion, GSAP and three.js. The decision model, the embedding model and the language model all run on the user's machine, so there is no per-analysis fee and no subscription. "
          "An institution that deployed the system would add a server with that much memory and staff time to keep the reviewer directory current; compared with the staff time spent on "
          "manual first-pass screening the team expects this to be modest, but that comparison was not measured. The reviewer profiles shipped with the project are marked demo data."),
        H2("3.3 Operational Feasibility"),
        P(f"One script, run.bat, creates the environment, installs the packages, trains the decision model if its files are missing, and starts the API on port {F.API_PORT} and the web app on "
          f"port {F.WEB_PORT}. Settings live in one .env file and the reviewer directory is edited in the browser or imported from CSV. The first analysis after start-up is slow because the models "
          "load lazily. There is no login, so the system suits one trusted user or a small office on a private network."),
        H2("3.4 Schedule Feasibility"),
        P("Calendar dates were not recorded in the project artefacts, so none are given. The work was organised in dependent phases, listed in the order in which their products exist in the repository."),
        TAB("Project phases and their products", ["Phase", "Work", "Product"], [
            ["1", "Literature survey, base paper study, problem statement and objectives", "Batch documents 2 to 6"],
            ["2", "Dataset preparation and decision-model training", "scripts/prepare_dataset.py, scripts/train_model.py, models/"],
            ["3", "Extraction, features, review, literature, embeddings and matching services", "app/services/ (12 modules)"],
            ["4", "API, validation, SQLite storage and export", "app/main.py, app/models.py, app/schemas.py"],
            ["5", "Web interface (first a plain static page, then the React application)", "static/, frontend/src/ (8 pages)"],
            ["6", "Tests, smoke test, measurements and screenshots", "tests/, scripts/smoke_test.py, scripts/measure_metrics.py, docs/"],
            ["7", "Documentation, decks and report", "Batch documents 7 to 19"],
        ], widths=[0.6, 3.3, 2.4], size=10, align=["c", "l", "l"]),
        P("The services are functions that take and return plain dictionaries, so phases 3 and 4 are loosely coupled and can be developed and tested separately, as the unit tests do. "
          "The matching evaluation needed a hand-written probe set because no real labelled data existed for it."),
        H2("3.5 Advantages, Constraints and Risks"),
        TAB("Advantages, constraints and mitigated risks", ["Aspect", "Advantage", "Constraint or risk and mitigation"], [
            ["Privacy", "PDFs are processed locally", "A title query reaches OpenAlex; hidden instructions in a PDF are possible [2], [27] (local, deterministic fallback)"],
            ["Transparency", "Score breakdown, matched terms, conflict reason", "Weights are not fitted to data"],
            ["Robustness", "A missing model or OpenAlex leaves the rest of the result", "Deterministic review is less informative; status always shown"],
            ["Speed and scale", "Everything but the language model finishes in well under a second", f"AI review takes minutes; profiles re-embedded per request ({_POOL500 / 1000:.1f} s for 500)"],
            ["Data", "Runs without real review data", "Decision signal is synthetic; banner and wording say so"],
            ["Conflicts", "Literal terms, names and affiliations are caught", "Reworded links are missed; disclaimer asks for independent checks"],
        ], widths=[1.0, 2.4, 2.9], size=9.5, align=["l", "l", "l"]),
        H2("3.6 Risk Analysis"),
        P("The main risks were identified during development and each has a mitigation in the implementation. The ratings are the team's qualitative judgement, not measured probabilities."),
        TAB("Risks and mitigations", ["Risk", "Effect", "Mitigation in PeerScope"], [
            ["The language model cannot be loaded", "No AI review text", "Fallback to the 0.5B model, then to the deterministic review, with a visible status and note"],
            ["OpenAlex unreachable or slow", "No related literature", "8 s timeout; the literature tab reports 'unavailable'"],
            ["Embedding model cannot be downloaded", "Weaker ranking", "TF-IDF fallback keeps matching working; status shown in the health route"],
            ["Unusual PDF layout defeats section or title detection", "Wrong structural signals", "Signals labelled preliminary; evidence excerpts shown for checking"],
            ["Reviewer directory out of date", "Wrong availability or missing experts", "Editable in the browser; active flag, load fields, CSV import"],
            ["A conflict is worded in a way the matcher does not know", "A conflicted reviewer is not penalised", "Disclaimer asks the user to verify conflicts; the limit is measured and reported"],
            ["Decision signal misused as a verdict", "Unfair treatment of a paper", "Synthetic-data banner, 'not a judgment of scientific correctness' wording, human in the loop"],
        ], widths=[2.1, 1.5, 2.7], size=9.5, align=["l", "l", "l"]),
        H2("3.7 Feasibility Conclusion"),
        P("The project is technically, economically and operationally feasible as a decision-support tool for a single editor or committee and was completed on the available hardware. It is "
          "not feasible, with the data available, to claim that the system predicts real editorial decisions, and the documents do not make that claim."),
    ]


def report4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System and its Limitations"),
        P("Reviewer assignment is still largely manual: an editor reads the title and abstract, recalls who works on the topic, searches the reviewer list by keyword and checks workload and "
          f"conflicts by hand. The reviewer assignment problem has been studied for about thirty years [{R['rap_scoping']}], [{R['rap_survey']}], and the paper-reviewer affinity score remains hard "
          f"to audit [{R['base']}]. Human judgement is not a fixed point either: two NeurIPS 2021 committees disagreed on about 23 % of outcomes [{R['neurips_consistency']}]. "
          "The limitations are that reviewer choice depends on memory, keyword matching shares vocabulary but not expertise, workload is tracked separately, conflicts are checked by eye, "
          "first-pass screening is manual, and choices are rarely explained."),
        H2("4.2 Proposed System and its Advantages"),
        P(f"PeerScope takes one PDF and returns a preliminary assessment and a ranked, explained list of reviewers. It adopts the auditable principle of the base paper [{R['base']}] and adds paper "
          "intake, a first-pass assessment, availability and conflict terms inside the score, a reviewer directory, history and export. Final judgement stays with the editor."),
        TAB("Existing practice compared with PeerScope", ["Aspect", "Existing practice", "PeerScope"], [
            ["Reviewer choice", "Memory and keyword search", "MiniLM cosine plus keyword and method overlap"],
            ["Explanation", "None or informal", "Per-reviewer breakdown and reasoning sentence"],
            ["Workload and conflicts", "Spreadsheet and manual check", "Availability and conflict penalty inside the score"],
            ["First-pass screening", "Manual reading", "Structural score, concerns, page-anchored evidence"],
            ["Privacy", "Depends on the tool", "Local processing; only a title query leaves the machine"],
        ], widths=[1.4, 2.0, 2.9], size=9.5, align=["l", "l", "l"]),
        H2("4.3 Functional Requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Realised by"], [
            ["FR-1", "Accept a PDF up to 20 MB; reject other types, empty, headerless and oversize files with a clear message", "POST /api/analyze; Analyze page"],
            ["FR-2, FR-3", "Extract text, title, nine sections and references; compute counts, keywords, lexicon hits and four structural signals", "pdf_extract, features"],
            ["FR-4", "Give a three-class decision signal with probabilities", "ml_predict"],
            ["FR-5, FR-6", "Deterministic review always; AI review when the local model loads, with a plain notice when it cannot", "review_synthesis, llm_service"],
            ["FR-7", "Retrieve and rank related literature; report 'unavailable' on failure", "literature"],
            ["FR-8, FR-9", "Reviewer directory CRUD, activation, CSV import and export", "/api/reviewers routes; Reviewers page"],
            ["FR-10, FR-11", "Weighted ranking with breakdown and explanation; conflict detection and penalty", "matching"],
            ["FR-12", "Filter by active status, minimum score, topic, method; return the top five", "pipeline"],
            ["FR-13, FR-14", "Store analyses; history, reopen, JSON and PDF export", "analyses table; History page; export route"],
            ["FR-15 to FR-18", "Model metrics with synthetic-data notice; dashboard status; disclaimers; seeded demo reviewers", "/api/model/metrics, /api/health, About, seed"],
        ], widths=[0.9, 3.7, 1.7], size=9.5, align=["c", "l", "l"]),
        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements", ["ID", "Requirement", "How met"], [
            ["NFR-1", "Privacy: documents are not sent to a third party", "All processing is local; the only outgoing call is the OpenAlex title or keyword query"],
            ["NFR-2", "Responsiveness of routine operations", f"Reads are database or file reads.{_api_note()}"],
            ["NFR-3", "Bounded cost of one analysis without the language model", f"Extraction {min(_EXTRACT_MS):.0f}-{max(_EXTRACT_MS):.0f} ms for 17-30 page papers, then features, decision signal and matching in milliseconds"],
            ["NFR-4", "Graceful degradation", "A missing language model, embedding model or OpenAlex leaves the rest of the result and a visible status"],
            ["NFR-5", "Auditability", "Weights, per-signal values, matched terms, conflict reason and model status are shown and exported"],
            ["NFR-6", "Input safety", "Extension, content type, 20 MB size, %PDF header; temporary file deleted after each request"],
            ["NFR-7", "Reproducibility", "Fixed seed 42, stratified split, saved metrics, measurement scripts in scripts/"],
            ["NFR-8", "Usability", "One launcher; responsive layout, dark and light themes, empty, loading and error states"],
            ["NFR-9", "Portability", "run.bat; Docker image of the API; Python 3.11 or 3.12; Node.js 18 or newer"],
            ["NFR-10", "Honesty of output", "Disclaimers on every screen; synthetic-data banner; no fabricated content when a component is down"],
            ["NFR-11", "Configurability", "Weights, model names, limits and ports in .env without code changes"],
        ], widths=[0.7, 2.2, 3.4], size=9.5, align=["c", "l", "l"]),
        P("No accuracy target was fixed for the decision signal and no throughput target for the AI review, because no real labelled data exist and speed depends on the hardware; both are reported as measurements."),
        H2("4.5 Hardware Requirements"),
        TAB("Hardware used and observed needs", ["Item", "Used for all measurements", "Observation"], [
            ["Processor", f"{F.ENV['cpu']}", "CPU only; no GPU code path"],
            ["Memory", f"{F.ENV['ram_gb']} GB", "The language-model process used about 4 to 6 GB"],
            ["Disk", "Local SSD", "About 2.9 GB for the cached Qwen2.5-1.5B-Instruct weights"],
            ["Network", "Internet on first use", "Models are downloaded once; OpenAlex needs a connection"],
        ], widths=[1.0, 2.4, 2.9], size=9.5, align=["l", "l", "l"]),
        P("Smaller machines were not tested, so no minimum is claimed; the 0.5B fallback model or the deterministic review can be used on less memory."),
        H2("4.6 Software Requirements"),
        TAB("Software requirements", ["Component", "Version used in the measurements"], [
            ["Operating system, Python", f"{F.ENV['os'].replace('Windows-10-10.0.26200-SP0', 'Windows 11, build 10.0.26200')}; Python {F.ENV['python']} (3.11 or 3.12 supported)"],
            ["Web and database", f"FastAPI {_PK['fastapi']}, Uvicorn {_PK['uvicorn']}, Pydantic {_PK['pydantic']}, SQLAlchemy {_PK['SQLAlchemy']} (SQLite)"],
            ["PDF and machine learning", f"PyMuPDF {_PK['PyMuPDF']}, scikit-learn {_PK['scikit-learn']}, pandas {_PK['pandas']}, numpy {_PK['numpy']}, scipy {_PK['scipy']}"],
            ["Embeddings and language model", f"sentence-transformers {_PK['sentence-transformers']}, torch {_PK['torch']}, transformers {_PK['transformers']}"],
            ["Web app and browser", "Node.js 18 or newer; React 19, Vite 8, Recharts 3 (frontend/package.json); Chrome, Edge or Firefox"],
        ], widths=[1.9, 4.4], size=9.5, align=["l", "l"]),
        H2("4.7 Data Requirements"),
        P("Three kinds of data are handled: the uploaded PDF; the reviewer profile (display name of 1 to 200 characters, affiliation, expertise text, topics, methods, keywords, publication titles, "
          "current and maximum load, active flag and conflict terms), validated by a Pydantic schema; and the analysis result, stored as JSON and exported."),
        H2("4.8 User Roles"),
        P("PeerScope has no login, so roles describe what a person does, not what the system enforces; everyone who can open the web address can do everything."),
        TAB("User roles", ["Role", "Goal", "Main screens"], [
            ["Editor or programme chair", "Screen a submission and choose reviewers", "Analyze, Saved analysis, History, Dashboard"],
            ["Reviewer-directory administrator", "Keep profiles, loads and conflict terms current", "Reviewers (create, edit, activate, import, export)"],
            ["Operator or developer", "Install, configure, retrain, test", "run.bat, .env, scripts/, API documentation at /docs"],
        ], widths=[2.0, 2.4, 1.9], size=10, align=["l", "l", "l"]),
        P("The two human roles are normally one person in a small office, which is why the system has no accounts; authentication is future work."),
        H2("4.9 Constraints and Assumptions"),
        P("Extraction reads the text layer, so scanned PDFs yield little text; the section patterns, lexicon and demo reviewers are English; measurements use six demo reviewers; the decision "
          "model is trained on synthetic data; conflicts are found only as literal strings in the first 3,000 characters; the system is single-user, with open CORS and one SQLite file."),
        H2("4.10 Requirements Against Objectives"),
        TAB("Objectives and the requirements that serve them", ["Objective", "Requirements"], [
            ["1. Corpus of papers and reviewer profiles", "FR-8, FR-9, FR-13, FR-18"],
            ["2. Topics, methods and keywords with NLP", "FR-2, FR-3"],
            ["3. Reviewer expertise as comparable vectors", "FR-10"],
            ["4. Rank reviewers by semantic similarity", "FR-10, FR-12"],
            ["5. Preliminary assessment", "FR-3 to FR-7"],
            ["6. Assignment quality and conflict handling", "FR-11, NFR-5, NFR-7"],
        ], widths=[3.9, 2.4], size=9.5, align=["l", "l"]),
    ]
