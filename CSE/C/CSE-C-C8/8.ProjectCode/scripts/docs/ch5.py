"""Chapter 5: System Design. Also exposes DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, EQ, FIG, H1, H2, H3, N, P, PAIR, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_D = {k: (t, f, c, p) for k, t, f, c, p in DIAGRAMS}


def dfig(key, width=5.6, max_h=6.6):
    """Real diagram from diagram_index, width limited so that its height stays below max_h inches."""
    _, f, cap, _ = _D[key]
    path = F.diag(f)
    return FIG(path, cap, F.shot_w(path, width, max_h))


def sfig(name, caption, width=5.6, max_h=6.2):
    path = F.shot(name)
    return FIG(path, caption, F.shot_w(path, width, max_h))


def blocks():
    if F.REPORT:
        return report_blocks()
    return (design_goals() + workflow() + dataflow() + uml() + database() + modules() + algorithms() + ui_design() + decisions())


# =====================================================================================================================
def design_goals():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the workflow of one analysis, the data flow diagrams, the UML models, "
          "the database, the module design, the interface design and the reasons for the main design decisions. Every diagram was drawn from the code in the repository "
          "(app/, scripts/ and frontend/), not from a plan, and each is listed again with a short explanation in the block-diagram document."),

        H2("5.1 Design Goals and Architecture"),
        P("Four goals shaped the design. The first is **local-first operation**: a paper should never leave the machine except as a short query. The second is **graceful "
          "degradation**: the system should always return something useful, even when the language model, the embedding model or the internet is unavailable, and it must say "
          "which part is missing instead of inventing it. The third is **auditability**: every number in a reviewer ranking should be explainable from values that are stored with the "
          f"result, which is the principle of the base paper [{R['base']}]. The fourth is **simplicity of operation**: one launcher, one configuration file, one database file."),
        P("The architecture has four tiers over a set of local stores. The presentation tier is a React single-page application served by the Vite development server on "
          f"port {F.WEB_PORT}. It has eight pages and a thin client module, lib/api.js, which calls the API through fetch and turns every failure into a message that is safe to show. "
          f"The application tier is a FastAPI service on port {F.API_PORT} whose routes are all defined in app/main.py. It validates input, opens a database session per request, "
          "calls the service tier and converts errors into JSON responses. The service tier, app/services, holds the working modules. A single function, pipeline.run_analysis, "
          "orchestrates them for one paper. The data tier is SQLite for the reviewer directory and the stored analyses, the decision-model files, the training CSV, and the Hugging Face "
          "cache that holds the language-model weights."),
        dfig("arch", 5.8),
        P("One external system is used: the OpenAlex public API, which receives a title or keyword query and returns related works. The service tier is written as plain Python modules "
          "of functions, not as a class hierarchy. That is a deliberate choice: each stage takes a dictionary and returns a dictionary, so it can be tested on its own, replaced without touching "
          "the others, and the whole result can be stored as JSON. The UML class diagram in Section 5.4 draws these modules as classes only to show their responsibilities. A static page in "
          "static/ from the first version of the interface is still served at the root of the API as a fallback."),
        TAB("Tiers, technologies and responsibilities", ["Tier", "Technology", "Responsibility"], [
            ["Presentation", "React, React Router, Vite, Recharts, Framer Motion, GSAP, three.js", "Eight pages, forms, tables, charts, theme, error and loading states"],
            ["Application", "FastAPI, Uvicorn, Pydantic, SQLAlchemy", "Routes, input validation, upload guards, database sessions, error handler, CORS"],
            ["Service", "PyMuPDF, scikit-learn, sentence-transformers, Transformers, requests, ReportLab", "Extraction, features, decision signal, review, literature, embeddings, matching, export"],
            ["Data", "SQLite, joblib, CSV, JSON, Hugging Face cache", "Reviewers, analyses, model artefacts, training data, metrics, model weights"],
        ], widths=[1.1, 2.6, 2.6], size=10, align=["l", "l", "l"]),
    ]


# =====================================================================================================================
def workflow():
    return [
        H2("5.2 High-Level Workflow"),
        P("The workflow of the system is the workflow of one POST /api/analyze request. It has ten stages. The upload is validated; the PDF text, title, sections and references "
          "are extracted; structural features are computed; the trained classifier gives a decision signal; a review is drafted, by the local language model when it loads and by deterministic rules "
          "otherwise; related literature is requested from OpenAlex; the reviewers in the directory are scored; the filters are applied and the best five are kept; and the whole result is "
          "stored and returned. The interface then shows the result in five tabs: Overview, Review, Literature, Reviewers, and Audit and export."),
        dfig("flow", 5.6),
        P("There are two degradation paths. If the language model cannot be loaded, the review carries llm_status 'unavailable' together with the loader's error message and the deterministic "
          "review is shown. If OpenAlex cannot be reached within eight seconds, the literature block carries literature_retrieval_status 'unavailable' and an empty list. In both cases "
          "the other stages are unaffected. A third, implicit path concerns the embedding model: if it cannot be loaded the matching falls back to TF-IDF vectors."),
        P("Offline, a separate workflow prepares the decision model: prepare_dataset.py writes the training CSV, and train_model.py splits it, fits the vectorisers and the classifier, evaluates "
          "it and saves the artefacts and metrics. That workflow runs once, from run.bat if the model files are missing, and is drawn below."),
        dfig("train", 5.6),
        P("The PDF-reading stage deserves its own diagram because the later stages depend on it. Page text is extracted with PyMuPDF and normalised; the title is chosen by a "
          "heuristic; sections are found by matching short heading lines against nine patterns; the references are split after a References heading; and four structural signals are "
          "combined with fixed weights."),
        dfig("pdf", 5.6),
    ]


# =====================================================================================================================
def dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        P("At the context level PeerScope is one process with three neighbours. The editor or programme chair sends a PDF and filter choices and receives the assessment, the ranked "
          "reviewers, the history and the exports. The reviewer-directory administrator sends profiles or a CSV file and receives the directory and its CSV export. OpenAlex receives a query "
          "and returns related works. The model metrics are read from local files and need no external actor."),
        dfig("dfd0", 5.4),
        H3("5.3.2 Level 1: main processes"),
        P("Level 1 divides the system into seven processes and three stores. The table gives the data that enter and leave each process."),
        TAB("Level 1 processes and their data", ["No.", "Process", "Inputs", "Outputs", "Stores"], [
            ["1.0", "Validate and extract paper", "PDF, filters", "Text, sections, references, validation errors", "-"],
            ["2.0", "Assess paper", "Text, sections, references; model files", "Features, decision signal, review", "D3 (read)"],
            ["3.0", "Retrieve literature", "Title, keywords, topics", "Related works", "OpenAlex (external)"],
            ["4.0", "Match reviewers", "Keywords, methods, topics, summary, reviewer profiles", "Ranked reviewers with breakdown", "D1 (read)"],
            ["5.0", "Manage directory", "Profiles, CSV file", "Directory, CSV export, validation errors", "D1 (read, write)"],
            ["6.0", "Store, show and export", "Assessment, literature, ranked reviewers", "Result, history, JSON and PDF exports", "D2 (read, write)"],
            ["7.0", "Report model performance", "Saved metrics", "Metrics, confusion matrix, status", "D3 (read)"],
        ], widths=[0.5, 1.5, 1.7, 1.7, 0.9], size=9.5, align=["c", "l", "l", "l", "l"]),
        dfig("dfd1", 5.4, 6.0),
        P("The stores are D1, the reviewers table, D2, the analyses table, and D3, the model files with their metrics. Process 6.0 also serves the history lookup and the exports, "
          "which read D2."),
        H3("5.3.3 Level 2: the analysis pipeline"),
        P("Level 2 expands processes 1.0 to 4.0 into the steps of pipeline.run_analysis. Each step adds its output to one result dictionary, which is handed to process 6.0."),
        TAB("Level 2 sub-processes", ["No.", "Sub-process", "Module and function", "Data read"], [
            ["1.1", "Extract page text", "pdf_extract.extract_pdf", "Uploaded temporary PDF"],
            ["1.2", "Detect title, sections, references", "pdf_extract._detect_sections, _extract_references", "Page text"],
            ["2.1", "Structural features", "features.extract_features", "Document dictionary"],
            ["2.2", "Decision signal", "ml_predict.predict_decision", "decision_model.joblib, tfidf_vectorizer.joblib"],
            ["2.3", "Draft review", "review_synthesis.llm_review", "Qwen weights (optional)"],
            ["3.1", "Retrieve literature", "literature.retrieve_literature", "OpenAlex works endpoint"],
            ["4.1", "Profiles and embeddings", "matching.paper_profile, reviewer_profile; embeddings.embed_texts", "Reviewers table, MiniLM weights"],
            ["4.2", "Score and rank reviewers", "matching.match_reviewers", "Profiles, embeddings, paper text"],
        ], widths=[0.5, 1.7, 2.6, 1.6], size=9.5, align=["c", "l", "l", "l"]),
        dfig("dfd2", 5.6),
    ]


# =====================================================================================================================
def uml():
    return [
        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("The class diagram below shows the classes of the system. Two are persistent: Reviewer and Analysis, the ORM classes that map to the two tables. ReviewerIn is the Pydantic schema that validates "
          "reviewer input and states its limits. The FastAPI application is drawn as a class with one method per route. Below it are the service modules, each with the functions it "
          "exposes: the Pipeline calls PdfExtractor, FeatureExtractor and MLPredictor, then ReviewSynthesis, LiteratureService and MatchingService; ReviewSynthesis optionally uses LLMService, "
          "and both LiteratureService and MatchingService depend on EmbeddingService. ExportService produces the JSON and PDF exports, and SeedData fills an empty directory at start-up. "
          "In the code these are modules of functions; the class notation is used to show what each owns."),
        dfig("uml", 5.8, 6.8),
        H3("5.4.2 Sequence diagram"),
        P("The sequence of an analysis has the browser at one end and the database at the other. The browser posts the PDF as multipart form data with the four filter fields. "
          "FastAPI checks the extension, the content type, the size and the %PDF header, writes a temporary file, loads the reviewer rows and calls run_analysis. The pipeline calls the "
          "extraction, feature, decision, review, literature and matching modules in that order, applies the filters, keeps five reviewers and returns the result dictionary. FastAPI "
          "inserts one row into the analyses table, deletes the temporary file in a finally block and returns the JSON with the new analysis identifier."),
        dfig("seq", 5.4, 6.8),
        H3("5.4.3 Use-case diagram"),
        P("The use cases follow the two human roles of Section 4.8. The editor or programme chair uploads a paper, reads the preliminary assessment and review, sees related literature, "
          "obtains ranked reviewers with an audit breakdown, exports the analysis, browses the history and views the model performance. Obtaining reviewers includes the conflict-of-interest check. "
          "The directory administrator manages reviewer records and imports or exports them as CSV. The local language model and OpenAlex appear as supporting systems."),
        TAB("Principal use cases", ["Use case", "Actor", "Main flow", "Alternative flow"], [
            ["Analyze a paper", "Editor", "Choose PDF, set filters, press Analyze, read the five tabs", "Invalid file: message shown; backend offline: error state with retry"],
            ["Obtain reviewers", "Editor", "Open the Reviewers tab, expand Audit details for a score breakdown", "No reviewer passes the filters: empty state"],
            ["Export an analysis", "Editor", "Open Audit and export or History, choose JSON or PDF", "Unknown id: 404"],
            ["Manage reviewers", "Administrator", "Add, edit, activate, deactivate or delete a profile", "Validation error on the form"],
            ["Import reviewers", "Administrator", "Choose a CSV with a display_name column", "Malformed CSV: 400 and the database is rolled back"],
            ["Check model performance", "Editor", "Open Model performance", "Metrics file missing: status 'missing' message"],
        ], widths=[1.3, 0.9, 2.3, 1.8], size=9.5, align=["l", "l", "l", "l"]),
        dfig("uc", 5.2, 6.0),
    ]


# =====================================================================================================================
def database():
    return [
        H2("5.5 Database Design"),
        P("PeerScope keeps two tables in a SQLite file, data/peerscope.db, created by SQLAlchemy's create_all when the API starts. SQLite was chosen because the system is single-user and "
          "local, needs no server and is backed up by copying one file. The check_same_thread restriction is disabled so that FastAPI's worker threads can share the engine, and a session is "
          "opened and closed for every request."),
        dfig("er", 5.6, 5.6),
        H3("5.5.1 The reviewers table"),
        TAB("Table reviewers", ["Column", "Type", "Default", "Purpose"], [
            ["id", "Integer, primary key, indexed", "auto", "Identifier"],
            ["display_name", "String(200), not null", "-", "Name shown and used in the conflict check"],
            ["affiliation", "String(300)", "empty", "Institution; conflict check"],
            ["expertise_description", "Text", "empty", "Free text embedded for semantic similarity"],
            ["research_topics", "Text (comma list)", "empty", "Topic overlap and filter"],
            ["methods", "Text (comma list)", "empty", "Method overlap and filter"],
            ["keywords", "Text (comma list)", "empty", "Keyword overlap"],
            ["publication_titles", "Text", "empty", "Embedded with the description"],
            ["current_load", "Integer", "0", "Papers now assigned"],
            ["maximum_load", "Integer", "5", "Most papers the reviewer accepts"],
            ["is_active", "Boolean", "true", "Whether the reviewer can be proposed"],
            ["conflict_terms", "Text (comma list)", "empty", "Strings that signal a conflict"],
        ], widths=[1.5, 1.7, 0.7, 2.4], size=9.5, align=["l", "l", "c", "l"]),
        P("Lists are stored as comma-separated text, not as a child table. The matching code splits them on commas, semicolons, bars and line breaks and lower-cases them, which keeps "
          "the CSV import and export a straight copy of the columns. The price of this choice is that the database cannot enforce the uniqueness of a term or query by term."),
        H3("5.5.2 The analyses table"),
        TAB("Table analyses", ["Column", "Type", "Default", "Purpose"], [
            ["id", "Integer, primary key, indexed", "auto", "Analysis identifier used in URLs"],
            ["filename", "String(300)", "empty", "Name of the uploaded file"],
            ["created_at", "DateTime", "UTC now", "When the analysis was stored"],
            ["overall_assessment", "String(120)", "empty", "First 120 characters of the overall assessment, for the history list"],
            ["concern_count", "Integer", "0", "Major plus minor concerns"],
            ["recommendation_count", "Integer", "0", "Number of recommendations"],
            ["top_reviewer", "String(200)", "empty", "Name of the best-ranked reviewer at the time"],
            ["status", "String(60)", "'completed'", "Status of the analysis"],
            ["result_json", "Text", "'{}'", "The complete result as JSON"],
        ], widths=[1.5, 1.7, 0.9, 2.2], size=9.5, align=["l", "l", "c", "l"]),
        P("There is **no foreign key** between the two tables. This is a design decision, not an omission: an analysis is a snapshot. Its result_json contains the five ranked reviewers as they were "
          "scored on that day, and top_reviewer is a copy of a name. If a reviewer is later edited or deleted, the stored analysis still shows what the editor saw, and the history never shows a "
          "broken reference. The price is that the history cannot be queried by reviewer through a join. The JSON document carries these top-level keys: product, filename, created_at, paper "
          "(title, summary, page, word and reference counts, sections, a four-page preview), features, ml_decision_signal, structural_assessment, review, review_quality, literature, reviewers, "
          "reviewer_pool_size, overall_assessment, concern_count, recommendation_count, top_reviewer, disclaimer and responsible_use, with analysis_id added after the insert."),
        H3("5.5.3 File-based stores"),
        TAB("Files written and read by the system", ["File", "Written by", "Read by", "Content"], [
            ["data/processed_dataset.csv", "scripts/prepare_dataset.py", "scripts/train_model.py", f"{F.DM['rows']:,} labelled rows: title, text, label, source"],
            ["models/decision_model.joblib", "scripts/train_model.py", "ml_predict", "Class-balanced logistic regression"],
            ["models/tfidf_vectorizer.joblib", "scripts/train_model.py", "ml_predict", "CombinedVectorizer: word and character TF-IDF"],
            ["models/metrics.json", "scripts/train_model.py", "GET /api/model/metrics", "Metrics, confusion matrix, labels, dataset facts"],
            ["models/hf_cache/", "Transformers on first load", "llm_service", "Qwen weights (embedding weights use the sentence-transformers cache)"],
            ["data/demo/demo_paper.pdf", "scripts/make_demo_pdf.py", "tests, smoke test, screenshots", "Three-page demo paper, clearly a fixture"],
            ["data/tmp/", "tempfile", "-", "Temporary location for uploads; each file is deleted after its request"],
        ], widths=[1.9, 1.4, 1.2, 1.8], size=9, align=["l", "l", "l", "l"]),
    ]


# =====================================================================================================================
def modules():
    return [
        H2("5.6 Module Design"),
        P("The service tier has twelve modules, each with one responsibility. The table lists them with the functions they expose; names beginning with an underscore are internal."),
        TAB("Modules of app/ and their public functions", ["Module", "Responsibility", "Functions"], [
            ["main.py", "FastAPI app, routes, upload guards, error handler, start-up seeding", "health, model_metrics, reviewer CRUD, import and export, analyze, list_analyses, get_analysis, export_analysis"],
            ["config.py", "Single source of tunable settings read from the environment and .env", "paths, ports, upload limit, model names, literature settings, MATCH_WEIGHTS"],
            ["database.py, models.py, schemas.py", "SQLAlchemy engine and session, ORM classes, Pydantic validation", "get_db, init_db, Reviewer, Analysis, ReviewerIn, HealthOut"],
            ["services/pipeline.py", "Orchestrates one analysis and applies filters", "run_analysis"],
            ["services/pdf_extract.py", "Text, title, sections, references, summary", "extract_pdf, _normalize, _detect_sections, _extract_references, _build_summary"],
            ["services/features.py", "Counts, keywords, lexicon hits and four structural signals", "extract_features"],
            ["services/ml_predict.py", "Loads the decision model lazily and predicts", "artifacts_exist, predict_decision, load_metrics"],
            ["services/review_synthesis.py", "Deterministic review and 3-step language-model review", "deterministic_review, llm_review, review_quality"],
            ["services/llm_service.py", "Lazy, thread-safe loading of Qwen2.5 with a fallback model", "ensure_llm, generate, llm_status"],
            ["services/embeddings.py", "MiniLM embeddings with a TF-IDF fallback", "embed_texts, cosine, embedding_status"],
            ["services/literature.py", "OpenAlex retrieval and relevance ranking", "retrieve_literature, score_literature"],
            ["services/matching.py", "Profiles, overlaps, conflict check, score and explanation", "paper_profile, reviewer_profile, detect_conflict, match_reviewers"],
            ["services/export_service.py", "JSON and A4 PDF report of an analysis", "analysis_to_json, analysis_to_pdf"],
            ["services/seed.py", "Six demo reviewers when the directory is empty", "seed_if_empty"],
            ["services/textvec.py", "Importable CombinedVectorizer so that the saved vectoriser can be unpickled", "CombinedVectorizer.transform"],
        ], widths=[1.6, 2.4, 2.3], size=9.5, align=["l", "l", "l"]),
        H3("5.6.1 Extraction and features"),
        P("pdf_extract.extract_pdf opens the file with PyMuPDF, takes the text of each page, collapses runs of spaces and blank lines, and joins the pages. The title is the first line "
          "among the first 25 that is between 12 and 220 characters long and does not end with a full stop. Section headings are short lines (at most 80 characters) that match one of nine "
          "pattern groups: summary, introduction, related work, methodology, experiments, results, discussion, conclusion and references. The text between one heading and the next becomes the "
          "section, with its word count and a 600-character preview. References are split after a References or Bibliography heading, or, failing that, taken from bracketed lines. "
          "The summary is the preview of the summary or introduction section, or the first long paragraph."),
        P("features.extract_features turns the document into numbers: pages, words, sentences, average sentence length, reference count and density per page, detected and missing sections, "
          "the share of very short sections, the fifteen most frequent non-stop-word tokens as keywords, hits from a 21-term method lexicon and an 18-term topic list, and four signals. "
          "Structure completeness is the share of the nine expected sections found. Evidence coverage is 22 times the reference density plus 10 if an experiments or results section exists, capped at 100. "
          "Method clarity is 100 for a methodology section of at least 120 words, 70 for a shorter one, 45 if only lexicon terms occur and 25 otherwise. Presentation is 100 for an average sentence "
          "length of 12 to 26 words with few short sections, 75 for 8 to 32 words and 50 otherwise. The overall structural score is 0.35, 0.25, 0.25 and 0.15 of these signals."),
        pdf_note(),
        H3("5.6.2 Decision signal and review"),
        P("ml_predict builds one string from the title, the summary and the first 4,000 characters of the text, transforms it with the saved vectoriser and returns the class "
          "probabilities of the saved model, the most probable label and its confidence, together with a note that the signal is historical and not a judgement of scientific correctness. If the artefacts are "
          "missing it returns the status 'model_unavailable'. review_synthesis.deterministic_review always runs: it turns the features into strengths, major and minor concerns, "
          "five standing recommendations, per-dimension notes, a coverage view, page-anchored evidence excerpts and an overall assessment worded from the structural score "
          "(75 or more: strong preliminary structure; 55 or more: moderate; otherwise early-stage). The novelty text always says that novelty cannot be settled from local text."),
        P("llm_review adds the optional AI review. It takes the first 6,000 characters of the paper and calls the language model three times: an analysis step, a critique step and a synthesis step "
          "with limits of 512, 512 and 700 new tokens. The system prompts tell the model to use only the supplied text and to use cautious words such as 'novelty signal' and 'requires verification'. "
          "llm_service loads the model once under a lock, tries the 1.5-billion-parameter model first and the 0.5-billion one second, runs on the CPU in 32-bit floats with greedy decoding, and "
          "remembers a failed attempt so that later requests do not retry the download. The output is stored as ai_synthesis and the two intermediate steps, and the review's source becomes "
          "'deterministic+llm'."),
        H3("5.6.3 Literature, embeddings and matching"),
        P("literature.retrieve_literature queries the OpenAlex works endpoint with the title (or the first six keywords), asks for the configured number of works with their authors, venue "
          "and DOI, and ranks them by the cosine similarity between the query and each title; if embeddings fail, by word overlap. embeddings.embed_texts encodes the first 2,000 characters of "
          "each text with the all-MiniLM-L6-v2 sentence encoder. If that model cannot be loaded it falls back to a 512-feature TF-IDF vectoriser, which is fitted on the first batch of texts and then "
          "reused. This is cheap and works offline, but its vocabulary is frozen by the first request, which is why the matching evaluation in Chapter 8 reports the two modes separately."),
        P("matching.match_reviewers embeds the paper profile and every reviewer profile in one call and computes, for each reviewer, the cosine similarity, a keyword overlap, a method and "
          "topic overlap and an availability value. The overlap function counts exact and substring matches (a hit such as 'classification~text classification' is recorded in the evidence) and "
          "returns min(1, hits/max(set sizes) + 0.1 x hits/max(set sizes)). The conflict check is described in Section 5.6.4. The final score and the labels follow the flowchart below."),
        dfig("match", 5.2, 6.4),
        H3("5.6.4 Conflict of interest"),
        P("detect_conflict receives the first 3,000 characters of the paper text and lower-cases them. A reviewer is flagged if any of their conflict terms occurs, if their full display name occurs "
          "(a first name alone is not enough), or if their affiliation string, at least five characters long, occurs. The flag carries a reason sentence, and a flagged reviewer has the penalty of "
          "0.60 subtracted before scaling, which in practice moves the reviewer to the bottom of the list. The method is deliberately simple and auditable, and its limit is that it finds only literal strings."),
        H3("5.6.5 Pipeline filters and storage"),
        P("After scoring, run_analysis applies the filters the user chose: active reviewers only (the default), a minimum score, and substring filters on topic and method. It keeps the first five and "
          "builds the result. main.analyze then stores the row and returns the result. The response also carries a warning if fewer than 50 words were extracted, which happens with scanned PDFs."),
        TAB("Configuration read by app/config.py", ["Setting", "Default", "Effect"], [
            ["PEERSCOPE_HOST, PEERSCOPE_PORT", f"127.0.0.1, {F.API_PORT}", "Where the API listens"],
            ["PEERSCOPE_MAX_UPLOAD_MB", str(F.UPLOAD_LIMIT_MB), "Largest accepted PDF"],
            ["PEERSCOPE_LLM_MODEL, PEERSCOPE_LLM_FALLBACK", "Qwen2.5-1.5B-Instruct, Qwen2.5-0.5B-Instruct", "Local language models"],
            ["PEERSCOPE_EMBED_MODEL", "all-MiniLM-L6-v2", "Sentence encoder"],
            ["PEERSCOPE_LITERATURE_COUNT, PEERSCOPE_LITERATURE_TIMEOUT", "6, 8 s", "OpenAlex works requested and timeout"],
            ["PEERSCOPE_W_EXPERTISE, _KEYWORD, _METHOD, _AVAIL, _CONFLICT", "0.55, 0.20, 0.15, 0.10, 0.60", "Matching weights"],
            ["PEERSCOPE_DB, PEERSCOPE_TMP, PEERSCOPE_HF_CACHE", "data/peerscope.db, data/tmp, models/hf_cache", "Storage locations"],
        ], widths=[2.4, 2.0, 1.9], size=9.5, align=["l", "l", "l"]),
    ]


def pdf_note():
    return P("These weights and thresholds are heuristics chosen by the team. They were not fitted to human judgements, and Chapter 8 shows how they behave on four real papers, including two "
             "where the section detection fails.")


def algorithms():
    w = F.MATCH_WEIGHTS
    return [
        H2("5.7 Scoring Design"),
        P("The reviewer score is the central design element, so it is written out in full. For a paper p and a reviewer r, with sim the cosine similarity of the embeddings (negative values "
          "set to zero), kw and me the keyword and method overlaps, av the availability and pen the conflict penalty:"),
        EQ(f"score(p, r) = 100 x clip( {w['expertise_similarity']} sim + {w['keyword_score']} kw + {w['method_score']} me + {w['availability_score']} av - {w['conflict_penalty']} pen , 0 , 1 )"),
        P("where av = clip(1 - current load / maximum load, 0, 1) and pen is 1 for a flagged reviewer and 0 otherwise. The result is labelled Strong at 65 or more, Good at 45 or more, "
          "Possible at 25 or more and Weak below that. The positive weights sum to one, so a score of 100 would need perfect similarity, overlap and availability. Because the weights are read "
          "from the environment, an editor can emphasise availability or similarity without changing code. The explanation sentence is built from the same values: it says whether the "
          "semantic match is close (similarity of 0.45 or more), partial (0.25 or more) or limited, lists up to four overlapping terms and up to four shared methods or topics, "
          "and states whether availability is good (0.5 or more) or limited."),
        P(f"The weights follow the structure of the base paper's affinity construction, which combines text similarity and keyword overlap [{R['base']}], but the particular numbers were set by the team "
          "and were not fitted. Section 5.9 records why the score was kept linear."),
    ]


# =====================================================================================================================
def ui_design():
    return [
        H2("5.8 User Interface Design"),
        P("The interface is a React single-page application with eight routes: the landing page at the root and, under /app, the Dashboard, Analyze, Saved analysis, Reviewers, Model performance, "
          "History and About pages. Pages are loaded lazily, an error boundary keeps a failure in one page from blanking the others, and a not-found screen offers a way back. The look is the "
          "'Depth Studio' kit: Sora, Inter and JetBrains Mono type, a dark theme by default with a light theme that follows the operating system until the user chooses, an emerald accent, rounded "
          "cards, a fixed 248-pixel sidebar and a 64-pixel top bar. The theme choice is kept in the browser's local storage."),
        TAB("Pages of the web application", ["Page", "Route", "Content"], [
            ["Landing", "/", "Hero scene (three.js with a static fallback), how-it-works steps, features, call to action"],
            ["Dashboard", "/app", "Counts of reviewers and analyses, decision-model accuracy with a synthetic-data note, recent analyses, how it works, concerns chart"],
            ["Analyze", "/app/analyze", "PDF drop zone with size check, filters (active only, minimum score, topic, method), progress with elapsed seconds, five-tab result"],
            ["Saved analysis", "/app/analyses/:id", "The same five-tab result for a stored analysis"],
            ["Reviewers", "/app/reviewers", "Searchable table with load bars, add and edit form, activate, delete with confirmation, CSV import and export"],
            ["Model performance", "/app/model", "Accuracy, macro precision, recall and F1, class distribution, confusion matrix, per-class table, training details"],
            ["History", "/app/history", "Sortable, searchable list of analyses with open, JSON and PDF actions"],
            ["About", "/app/about", "Pipeline, scoring formula, responsible use, privacy, live system status"],
        ], widths=[1.2, 1.4, 3.7], size=9.5, align=["l", "l", "l"]),
        sfig("01_landing_dark.png", "Landing page of the web application (dark theme).", 5.4, 3.6),
        P("The result view is organised so that the most important facts come first. Four summary tiles show the structural score, the number of concerns, the number of recommendations and "
          "the top reviewer. The Overview tab shows the paper's metadata and the preliminary assessment, with the historical decision signal, the structural score with its four signals and the status "
          "of the local AI review side by side. The Review tab lists strengths, concerns, recommendations, a coverage view, the AI synthesis if present, and the evidence excerpts. The Literature tab is "
          "a sortable table of related works. The Reviewers tab shows the ranked reviewers with an expandable audit table. The Audit and export tab gives the formula, the analysis identifier, the status of "
          "each component and the export buttons."),
        sfig("06_analyze_result_overview.png", "Analyze page after an analysis: summary tiles and the Overview tab.", 4.6, 6.4),
        sfig("04_dashboard.png", "Dashboard with counts, decision-model accuracy and recent analyses.", 5.4, 4.0),
        sfig("11_reviewers.png", "Reviewer directory with load bars, status and actions.", 5.4, 4.0),
        sfig("13_model_performance.png", "Model performance page with the synthetic-data notice, metrics and confusion matrix.", 4.6, 6.4),
        P("Four design rules were applied throughout. Honest states: every component that can fail has a visible status, and a banner on the Dashboard and Model pages says that the decision "
          "model was trained on synthetic data. Every asynchronous view has loading, empty and error states with a retry. Accessibility: controls are native or labelled, tabs expose "
          "their panel, progress bars carry text and the colour tokens keep text legible in both themes. Responsiveness: tables hide secondary columns on narrow screens and the sidebar becomes a slide-in drawer."),
    ]


# =====================================================================================================================
def decisions():
    return [
        H2("5.9 Key Design Decisions"),
        TAB("Design decisions, alternatives and reasons", ["Decision", "Alternative considered", "Reason"], [
            ["Process PDFs locally; send only a title query out", "Upload the paper to a hosted language model", "Peer review material is confidential, and hosted tools raise the manipulation risks described in the literature [2], [27]"],
            ["Deterministic review always runs; the language model is optional", "Language model only", "The system must give a useful, honest result when the model cannot load or the machine is slow"],
            ["Linear weighted score with explicit availability and conflict terms", "A learned ranking model", f"No labelled assignments were available, and a linear score can be audited line by line, as the base paper recommends [{R['base']}]"],
            ["MiniLM embeddings with a TF-IDF fallback", "TF-IDF only, or a larger encoder", "MiniLM runs quickly on a CPU and is the encoder family used by the base paper's baseline; the fallback keeps the system working offline"],
            ["TF-IDF and logistic regression for the decision signal", "Fine-tuning a transformer", "No real decision data, CPU only, and a linear model is fast to train and to explain; its output is a labelled demonstration"],
            ["Class-balanced weights", "Unweighted fit", "The borderline class is the largest; balancing raises macro recall at the cost of some accuracy"],
            ["SQLite with a JSON snapshot per analysis", "Normalised tables with foreign keys", "Single user, no server, and a stored analysis must not change when the directory changes"],
            ["Comma-separated lists in text columns", "Child tables for topics and methods", "Simple CSV import and export; the lists are short and only read by the matcher"],
            ["Service modules as functions over dictionaries", "Class hierarchy", "Each stage is testable alone and the result is directly storable as JSON"],
            ["Weights and limits read from the environment", "Constants in code", "An editor can tune the ranking without a code change"],
            ["No authentication", "Accounts and roles", "Out of scope for a local single-user tool; listed as future work"],
            ["Top five reviewers returned", "Return all", "A short list is what an editor needs; the pool size is stored with the result"],
        ], widths=[1.9, 1.5, 2.9], size=9.5, align=["l", "l", "l"]),
        P("Two further decisions concern honesty and are visible in the interface. The coverage view in the Review tab uses a fixed value for the Novelty axis, because novelty cannot be measured from "
          "the paper alone, and the novelty text says so; and the Model page shows a notice whenever the metrics file says that the data were synthetic. The design therefore errs on the side of showing "
          "what the system does not know."),
    ]


# =====================================================================================================================
# Compact variant used inside the full report (F.REPORT = True); the chapter documents keep the full text above.
def pfig(key, width=2.7):
    _, f, cap, _ = _D[key]
    return (F.diag(f), cap)


def pshot(name, caption):
    return (F.shot(name), caption)


def report_blocks():
    w = F.MATCH_WEIGHTS
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. Every diagram was drawn from the code in the repository, and all twelve are listed again, with explanations, "
          "in the block-diagram document."),

        H2("5.1 Design Goals and Architecture"),
        P("Four goals shaped the design: local-first operation (a paper never leaves the machine except as a short query); graceful degradation (the system always returns something useful and says "
          f"which part is missing); auditability, as in the base paper [{R['base']}]; and simple operation (one launcher, one configuration file, one database file)."),
        P(f"The architecture has four tiers. The presentation tier is a React application on port {F.WEB_PORT} with eight pages and a thin fetch client. The application tier is a FastAPI "
          f"service on port {F.API_PORT} whose routes are all in app/main.py; it validates input, opens a database session per request and converts errors into JSON. The service tier, app/services, "
          "holds the working modules, orchestrated for one paper by pipeline.run_analysis. The data tier is SQLite, the model files, the training CSV and the Hugging Face cache. OpenAlex is the "
          "only external system. The service modules are plain functions that take and return dictionaries, so each stage can be tested alone and the result stored as JSON."),
        dfig("arch", 5.0, 3.7),

        H2("5.2 High-Level Workflow"),
        P("The workflow is that of one POST /api/analyze request: the upload is validated; text, title, sections and references are extracted; structural features are computed; the classifier gives a "
          "decision signal; a review is drafted by the local language model or, if it cannot load, by deterministic rules; related literature is requested from OpenAlex; reviewers are scored; "
          "the filters are applied and the best five kept; and the result is stored and returned. An unavailable language model or an unreachable OpenAlex leaves the other stages intact. "
          "The training pipeline of the decision model and the PDF extraction and scoring flow are drawn below."),
        dfig("flow", 5.0, 3.7),
        PAIR([pfig("train"), pfig("pdf")], 2.8),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        P("PeerScope is one process with three neighbours: the editor (sends a PDF and filters, receives assessment, ranking, history and exports), the directory administrator (sends profiles or CSV, "
          "receives the directory) and OpenAlex (receives a query, returns related works)."),
        H3("5.3.2 Level 1: main processes"),
        P("Level 1 has seven processes: 1.0 validate and extract, 2.0 assess, 3.0 retrieve literature, 4.0 match reviewers, 5.0 manage the directory, 6.0 store, show and export, and 7.0 report "
          "model performance, over three stores: D1 the reviewers table, D2 the analyses table and D3 the model files."),
        H3("5.3.3 Level 2: the analysis pipeline"),
        P("Level 2 expands processes 1.0 to 4.0 into the steps of run_analysis: page text (1.1), title, sections and references (1.2), structural features (2.1), decision signal (2.2), review (2.3), "
          "literature (3.1), profiles and embeddings (4.1) and scoring and ranking (4.2). Each step adds its output to one result dictionary handed to process 6.0."),
        TAB("Level 1 processes and their data", ["No.", "Process", "Inputs", "Outputs", "Stores"], [
            ["1.0", "Validate and extract paper", "PDF, filters", "Text, sections, references, errors", "-"],
            ["2.0", "Assess paper", "Text, sections; model files", "Features, decision signal, review", "D3 (read)"],
            ["3.0", "Retrieve literature", "Title, keywords, topics", "Related works", "OpenAlex"],
            ["4.0", "Match reviewers", "Keywords, methods, topics, profiles", "Ranked reviewers with breakdown", "D1 (read)"],
            ["5.0", "Manage directory", "Profiles, CSV file", "Directory, CSV export, errors", "D1 (read, write)"],
            ["6.0", "Store, show and export", "Assessment, literature, ranking", "Result, history, JSON and PDF", "D2 (read, write)"],
            ["7.0", "Report model performance", "Saved metrics", "Metrics, confusion matrix", "D3 (read)"],
        ], widths=[0.5, 1.5, 1.7, 1.8, 0.8], size=9.5, align=["c", "l", "l", "l", "l"]),
        PAIR([pfig("dfd0"), pfig("dfd1")], 2.9),
        dfig("dfd2", 5.0, 3.4),

        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("Two classes are persistent, Reviewer and Analysis, mapped to the two tables; ReviewerIn is the Pydantic schema that validates reviewer input. The FastAPI application has one method per "
          "route, and below it the Pipeline calls PdfExtractor, FeatureExtractor, MLPredictor, ReviewSynthesis, LiteratureService and MatchingService; ReviewSynthesis optionally uses LLMService and "
          "both LiteratureService and MatchingService depend on EmbeddingService. In the code these are modules of functions; the class notation shows what each owns."),
        dfig("uml", 5.0, 3.7),
        H3("5.4.2 Sequence diagram"),
        P("The browser posts the PDF with four filter fields. FastAPI checks the extension, content type, size and %PDF header, writes a temporary file, loads the reviewer rows and calls "
          "run_analysis, which calls the extraction, feature, decision, review, literature and matching modules in order, applies the filters and keeps five reviewers. FastAPI inserts one row into "
          "analyses, deletes the temporary file in a finally block and returns the JSON with the new identifier."),
        dfig("seq", 4.6, 3.7),
        H3("5.4.3 Use-case diagram"),
        P("The editor uploads a paper, reads the assessment and review, sees literature, obtains ranked reviewers (which includes the conflict check), exports, browses the history and views model "
          "performance; the administrator manages and imports reviewers. The local language model and OpenAlex appear as supporting systems."),
        dfig("uc", 4.6, 3.3),

        H2("5.5 Database Design"),
        P("Two tables are kept in the SQLite file data/peerscope.db, created by create_all at start-up. SQLite suits a single-user local tool: no server, and a backup is one file copy."),
        dfig("er", 4.6, 3.3),
        H3("5.5.1 The reviewers table"),
        H3("5.5.2 The analyses table"),
        TAB("Columns of the two tables", ["Table", "Columns"], [
            ["reviewers", "id (integer, primary key); display_name (String 200, not null); affiliation (String 300); expertise_description, research_topics, methods, keywords, publication_titles, "
                          "conflict_terms (Text, lists comma-separated); current_load (integer, default 0); maximum_load (integer, default 5); is_active (boolean, default true)"],
            ["analyses", "id (integer, primary key); filename (String 300); created_at (DateTime, UTC now); overall_assessment (String 120); concern_count, recommendation_count (integer); "
                         "top_reviewer (String 200); status (String 60, default 'completed'); result_json (Text, the whole result)"],
        ], widths=[0.9, 5.4], size=9.5, align=["l", "l"]),
        P("There is **no foreign key** between the tables, by design: an analysis is a snapshot. result_json holds the five ranked reviewers as scored that day and top_reviewer is a copy of a name, so "
          "later edits or deletions never break the history. Lists are stored as comma-separated text so that CSV import and export are a straight copy of the columns."),
        H3("5.5.3 File-based stores"),
        P(f"The training CSV (data/processed_dataset.csv, {F.DM['rows']:,} rows) is written by prepare_dataset.py; decision_model.joblib, tfidf_vectorizer.joblib and metrics.json are written by "
          "train_model.py and read by ml_predict and the metrics route; models/hf_cache holds the language-model weights; data/tmp holds each upload only until its request ends."),

        H2("5.6 Module Design"),
        P("The service tier has twelve modules, each with one responsibility; names beginning with an underscore are internal."),
        TAB("Modules of app/ and their public functions", ["Module", "Responsibility", "Functions"], [
            ["main.py", "FastAPI app, routes, upload guards, error handler, start-up seeding", "health, model_metrics, reviewer CRUD, import and export, analyze, list_analyses, get_analysis, export_analysis"],
            ["config.py", "Tunable settings from the environment and .env", "paths, ports, upload limit, model names, MATCH_WEIGHTS"],
            ["database.py, models.py, schemas.py", "Engine and session, ORM classes, Pydantic validation", "get_db, init_db, Reviewer, Analysis, ReviewerIn"],
            ["services/pipeline.py", "Orchestrates one analysis and applies filters", "run_analysis"],
            ["services/pdf_extract.py", "Text, title, sections, references, summary", "extract_pdf"],
            ["services/features.py", "Counts, keywords, lexicon hits, four structural signals", "extract_features"],
            ["services/ml_predict.py", "Lazy loading and prediction of the decision model", "artifacts_exist, predict_decision, load_metrics"],
            ["services/review_synthesis.py", "Deterministic review and 3-step language-model review", "deterministic_review, llm_review, review_quality"],
            ["services/llm_service.py", "Lazy, thread-safe loading of Qwen2.5 with a fallback model", "ensure_llm, generate, llm_status"],
            ["services/embeddings.py", "MiniLM embeddings with a TF-IDF fallback", "embed_texts, cosine, embedding_status"],
            ["services/literature.py", "OpenAlex retrieval and relevance ranking", "retrieve_literature, score_literature"],
            ["services/matching.py", "Profiles, overlaps, conflict check, score, explanation", "paper_profile, reviewer_profile, detect_conflict, match_reviewers"],
            ["services/export_service.py", "JSON and A4 PDF report", "analysis_to_json, analysis_to_pdf"],
            ["services/seed.py, textvec.py", "Six demo reviewers when empty; importable vectoriser class", "seed_if_empty, CombinedVectorizer"],
        ], widths=[1.6, 2.4, 2.3], size=9.5, align=["l", "l", "l"]),
        H3("5.6.1 Extraction and features"),
        P("extract_pdf reads each page with PyMuPDF, normalises whitespace, takes as title the first of the first 25 lines that is 12 to 220 characters long and does not end with a full stop, "
          "finds sections as short heading lines that match nine pattern groups, splits references after a References heading, and takes a summary from the summary or introduction. "
          "extract_features adds counts, the fifteen most frequent keywords, hits from a 21-term method lexicon and an 18-term topic list, and four signals (structure completeness, evidence "
          "coverage, method clarity, presentation) combined as 0.35, 0.25, 0.25 and 0.15 into the overall structural score. These weights are the team's heuristics and were not fitted to human judgements."),
        H3("5.6.2 Decision signal and review"),
        P("ml_predict transforms the title, summary and first 4,000 characters with the saved vectoriser and returns class probabilities, label and confidence, or 'model_unavailable'. The deterministic review "
          "always runs and turns the features into strengths, concerns, standing recommendations, a coverage view and page-anchored evidence; the novelty text always says novelty cannot be settled "
          "locally. llm_review optionally sends the first 6,000 characters to the local Qwen model in three steps (analysis, critique, synthesis; 512, 512 and 700 new tokens) with prompts that "
          "restrict it to the supplied text. llm_service loads the model once under a lock, tries the 1.5B model then the 0.5B one, runs on the CPU with greedy decoding and remembers a failed attempt."),
        H3("5.6.3 Literature, embeddings and matching"),
        P("retrieve_literature queries OpenAlex with the title and ranks works by cosine similarity to the query. embed_texts encodes the first 2,000 characters of each text with all-MiniLM-L6-v2, "
          "or, if it cannot load, with a 512-feature TF-IDF vectoriser fitted on the first batch and then reused, so its vocabulary is frozen by the first request. match_reviewers embeds the paper and "
          "every reviewer profile and computes cosine similarity, keyword overlap, method and topic overlap and availability, following the flowchart below."),
        dfig("match", 4.6, 3.7),
        H3("5.6.4 Conflict of interest"),
        P("detect_conflict searches the first 3,000 characters of the paper for any conflict term, the reviewer's full display name (a first name alone is not enough) or the affiliation string. A flagged "
          "reviewer has the penalty of 0.60 subtracted, which in practice moves them to the bottom. The method is simple and auditable; its limit is that it finds only literal strings."),
        H3("5.6.5 Pipeline filters and storage"),
        P("After scoring, run_analysis applies the filters (active only by default, minimum score, topic and method substrings), keeps five reviewers and builds the result; main.analyze stores it and "
          "warns if fewer than 50 words were extracted. Ports, the upload limit, model names, the literature count and the weights are read from the environment by config.py."),
        TAB("Configuration read by app/config.py", ["Setting", "Default", "Effect"], [
            ["PEERSCOPE_HOST, PEERSCOPE_PORT", f"127.0.0.1, {F.API_PORT}", "Where the API listens"],
            ["PEERSCOPE_MAX_UPLOAD_MB", str(F.UPLOAD_LIMIT_MB), "Largest accepted PDF"],
            ["PEERSCOPE_LLM_MODEL, PEERSCOPE_LLM_FALLBACK", "Qwen2.5-1.5B-Instruct, Qwen2.5-0.5B-Instruct", "Local language models"],
            ["PEERSCOPE_EMBED_MODEL", "all-MiniLM-L6-v2", "Sentence encoder"],
            ["PEERSCOPE_LITERATURE_COUNT, _TIMEOUT", "6, 8 s", "OpenAlex works requested and timeout"],
            ["PEERSCOPE_W_EXPERTISE, _KEYWORD, _METHOD, _AVAIL, _CONFLICT", "0.55, 0.20, 0.15, 0.10, 0.60", "Matching weights"],
        ], widths=[2.4, 2.0, 1.9], size=9.5, align=["l", "l", "l"]),

        H2("5.7 Scoring Design"),
        P("For a paper p and a reviewer r, with sim the cosine similarity (negative values set to zero), kw and me the keyword and method overlaps, av the availability and pen the conflict penalty:"),
        EQ(f"score(p, r) = 100 x clip( {w['expertise_similarity']} sim + {w['keyword_score']} kw + {w['method_score']} me + {w['availability_score']} av - {w['conflict_penalty']} pen , 0 , 1 )"),
        P("where av = clip(1 - current load / maximum load, 0, 1) and pen is 1 for a flagged reviewer and 0 otherwise. The result is Strong at 65 or more, Good at 45, Possible at 25 and Weak below. "
          f"The weights follow the structure of the base paper's affinity construction [{R['base']}] but were set by the team and not fitted; they are read from the environment so that an editor can tune them. "
          "The explanation sentence is built from the same values."),

        H2("5.8 User Interface Design"),
        P("The interface has eight routes: the landing page and, under /app, Dashboard, Analyze, Saved analysis, Reviewers, Model performance, History and About. Pages load lazily, an error boundary keeps "
          "one failure from blanking the others, and every asynchronous view has loading, empty and error states. The 'Depth Studio' kit supplies Sora, Inter and JetBrains Mono type, a dark theme with "
          "a light theme that follows the operating system, an emerald accent, a 248-pixel sidebar (a slide-in drawer on narrow screens) and a 64-pixel top bar. The result view shows four summary tiles "
          "and five tabs: Overview, Review, Literature, Reviewers, and Audit and export. A banner on the Dashboard and Model pages states that the decision model was trained on synthetic data."),
        PAIR([pshot("06_analyze_result_overview.png", "Analyze page after an analysis: summary tiles and the Overview tab."),
              pshot("13_model_performance.png", "Model performance page with the synthetic-data notice and confusion matrix.")], 2.6),

        H2("5.9 Key Design Decisions"),
        TAB("Design decisions and reasons", ["Decision", "Reason"], [
            ["Process PDFs locally; send only a title query out", "Review material is confidential and hosted tools raise manipulation risks [2], [27]"],
            ["Deterministic review always runs; language model optional", "A useful, honest result when the model cannot load or the machine is slow"],
            ["Linear weighted score with explicit availability and conflict terms", f"No labelled assignments exist; a linear score can be audited line by line [{R['base']}]"],
            ["MiniLM embeddings with a TF-IDF fallback", "Fast on a CPU, the encoder family of the base paper's baseline; the fallback works offline"],
            ["TF-IDF and logistic regression for the decision signal", "No real decision data and CPU only; fast to train and explain; output is a labelled demonstration"],
            ["SQLite with a JSON snapshot per analysis", "Single user, no server; a stored analysis must not change when the directory changes"],
            ["Functions over dictionaries; weights from the environment", "Testable stages, JSON-storable results, tuning without code changes"],
            ["No authentication; top five reviewers only", "Out of scope for a local tool (future work); a short list is what an editor needs"],
        ], widths=[2.8, 3.5], size=9.5, align=["l", "l"]),
        P("The coverage view in the Review tab uses a fixed value for the Novelty axis, because novelty cannot be measured from the paper alone, and the Model page shows a notice whenever the "
          "metrics file says the data were synthetic. The design errs on the side of showing what the system does not know."),
    ]
