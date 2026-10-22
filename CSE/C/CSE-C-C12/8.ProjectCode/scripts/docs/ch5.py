"""Chapter 5: System Design (SymptoTrackAI, implemented as the CareLens AI web application)."""

import glob
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R

_FILES = {"arch": "01_system_architecture.png", "flow": "02_high_level_workflow.png", "dfd0": "03_dfd_level0.png", "dfd1": "04_dfd_level1.png",
          "dfd2": "05_dfd_level2.png", "uml": "06_uml_class.png", "seq": "07_sequence_chat.png", "uc": "08_use_case.png", "er": "09_er_diagram.png",
          "flowchart": "10_flowchart_retrieval.png", "safety": "11_safety_decision_flow.png"}
_CAPS = {"arch": "Four-tier architecture of SymptoTrackAI (CareLens AI): React web app, FastAPI application, RAG modules and local data stores.",
         "flow": "High-level workflow of one symptom analysis (POST /api/chat).",
         "dfd0": "Context diagram (DFD level 0).", "dfd1": "DFD level 1: six processes and three data stores.",
         "dfd2": "DFD level 2: expansion of the analysis processes into their sub-processes.",
         "uml": "UML class diagram: ORM classes, schemas, routers and the RAG classes.",
         "seq": "Sequence diagram of the main flow: one symptom message from the browser to the stored answer.",
         "uc": "Use-case diagram of the visitor and the registered user.", "er": "Entity-relationship diagram of the SQLite database and the retrieval stores.",
         "flowchart": "Flowchart of the retrieval algorithm: expansion, dual retrieval, fusion, reranking, safety and generation.",
         "safety": "Decision flow of the safety layer and the answer filter."}


def _loc(*patterns):
    n = 0
    for pat in patterns:
        for p in glob.glob(os.path.join(F.CODE, pat), recursive=True):
            if "__pycache__" in p or "node_modules" in p or not os.path.isfile(p):
                continue
            with open(p, encoding="utf-8", errors="ignore") as fh:
                n += sum(1 for line in fh if line.strip())
    return n


def dfig(key, width=5.6, max_h=6.6):
    """Real diagram, width limited so that its height stays below max_h inches."""
    path = F.diag(_FILES[key])
    cap = _CAPS[key]
    return FIG(path, cap, F.shot_w(path, width, max_h))


def sfig(name, caption, width=5.6, max_h=5.0):
    path = F.shot(name)
    return FIG(path, caption, F.shot_w(path, width, max_h))


def blocks():
    return design_goals() + workflow() + dataflow() + uml() + database() + modules() + ui_design() + decisions() + quality()


# =====================================================================================================================
def design_goals():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter turns the requirements of Chapter 4 into a design. It gives the architecture, the workflow of one symptom analysis, the data flow diagrams, the UML models, "
          "the database, the module design, the interface design and the reasons for the main design decisions. The project is named SymptoTrackAI; it is implemented as a web application called "
          f"{F.APP_NAME}, which is the name that appears in the code and on every screen, and the two names are used for the same system. Every diagram was drawn from the code in the repository "
          "(app/, scripts/ and frontend/) and each is listed again with a short explanation in the block-diagram document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. The first is **local-first operation**: symptoms are health data, so nothing is sent to an external service. The embedding model, the reranker and the generator run "
          "on the machine, and the consultations are stored in a local SQLite file. The second is **answers grounded in retrieved text**: the user is shown the knowledge-base records that "
          "the answer was built from, so that the basis of every answer can be inspected. The third is **graceful degradation**: if a model cannot be loaded the system still answers, "
          "using a simpler method, and the label on the answer says which method produced it. The fourth is **safety first**: a rule layer that is independent of the retrieval models raises an "
          "emergency or caution notice, and a permanent disclaimer states that the output is not a diagnosis. The fifth is **simplicity of operation**: one launcher, one configuration file, one database file."),
        P("The architecture has four tiers over a set of local stores. The presentation tier is a React single-page application served by the Vite development server on "
          f"port {F.WEB_PORT}. It has eight routes and a thin client module, lib/api.js, which calls the API through fetch and turns every failure into a message that is safe to show. "
          f"The application tier is a FastAPI service on port {F.API_PORT}; its routers (auth, chat, history, about and the legacy pages) are mounted in app/main.py. It validates input with Pydantic, "
          "opens a database session per request, calls the RAG tier and converts errors into JSON responses. The RAG tier, app/rag, holds the working classes; a single object, "
          "the Pipeline, orchestrates them for one query. The data tier is SQLite for the users and their consultations, a processed knowledge base in CSV and JSON, "
          "a FAISS index with its record list, a BM25 corpus file, and the Hugging Face cache that holds the three model weights."),
        dfig("arch", 5.8),
        P("No external service is used at run time. After the models have been downloaded once, the whole system works offline: if the embedding model cannot be loaded the "
          "retrieval uses TF-IDF vectors, if the reranker cannot be loaded the hybrid order is used, and if the generator cannot be loaded an evidence-based answer is composed from the retrieved records. "
          "The backend still serves the original server-rendered pages (templates/ and static/, written before the React interface) at the root of the API; they are not the product front door "
          "and are not described further."),
        TAB("Tiers, technologies and responsibilities", ["Tier", "Technology", "Responsibility"], [
            ["Presentation", "React 19, React Router 7, Vite 8, Recharts, Framer Motion, GSAP", "Landing, sign-in, assistant, history, detail and about pages; theme; loading, empty and error states"],
            ["Application", "FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, PyJWT, bcrypt", "Routes, input validation, authentication, per-user queries, error handling"],
            ["RAG", "sentence-transformers, FAISS, rank-bm25, Transformers, scikit-learn", "Query expansion, embeddings, dense and lexical search, fusion, reranking, generation, safety rules"],
            ["Data", "SQLite, CSV, JSON, FAISS index file, Hugging Face cache", "Users, consultations, knowledge base, indexes, model weights"],
        ], widths=[1.1, 2.6, 2.6], size=10, align=["l", "l", "l"]),
    ]


# =====================================================================================================================
def workflow():
    out = [
        H2("5.2 High-Level Workflow"),
        P("The workflow of the system is the workflow of one POST /api/chat request. It runs through a fixed sequence of stages. The route checks the sign-in cookie and the length of the message; "
          "the Pipeline normalises the text and builds a short hypothetical description from it; the combined text is embedded; FAISS returns the fifteen nearest records and BM25 the fifteen best lexical "
          "matches; the two score lists are normalised and fused; the cross-encoder rescores the fused candidates and the best five are kept; a separate rule layer checks the original message for emergency "
          "wording; the generator produces the answer text; the answer filter removes listed medication phrases; and the consultation is stored and returned to the interface, which shows the answer, "
          "the safety banner and one evidence card per retrieved record."),
        dfig("flow", 5.6),
        P("There are three degradation paths. If the sentence-transformer cannot be loaded, the embedding backend switches to a 384-feature TF-IDF vectoriser fitted on the knowledge base. If the cross-encoder "
          "cannot be loaded, the hybrid score is used as the rerank score. If the generator cannot be loaded, or fails on a query, Generator.generate returns the deterministic evidence-based answer and "
          "labels it evidence-fallback. If the knowledge base or the index is missing the route returns 503 with a message that names the missing file. In all cases the other stages are unaffected."),
        P("Offline, the knowledge base is prepared by scripts/prepare_data.py, which writes data/processed/knowledge_base.csv and .json; scripts/build_index.py embeds every record, writes the FAISS index and the BM25 "
          "corpus into data/index/, and scripts/seed_demo.py creates the demo account. run.bat runs the three scripts when their outputs are missing. The Pipeline also rebuilds the index itself on first use if the files are absent."),
        dfig("flowchart", 5.2, 7.0),
        P("The flowchart above shows the retrieval algorithm at the level of decisions: where the pipeline branches on the availability of a model, and where the safety layer and the answer filter are applied. "
          "The decision flow of the safety layer alone is shown below."),
        dfig("safety", 5.2, 5.6),
    ]
    return out


# =====================================================================================================================
def dataflow():
    return [
        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
        P("At the context level the system is one process with two neighbours. The user sends registration and sign-in details, symptom descriptions, history searches and deletion requests, and receives "
          "the grounded answer, the evidence cards, the safety notice, the stored history and the evaluation figures. The Hugging Face Hub is contacted only on the first run, to download the embedding, "
          "reranker and generator weights into the local cache; after that no external system exchanges data with the application."),
        dfig("dfd0", 5.4),
        H3("5.3.2 Level 1: main processes"),
        P("Level 1 divides the system into seven processes and four stores. Process 1.0 guards the processes that act on a user's data (2.0, 4.0 and 5.0). The developer appears as a second actor because "
          "process 7.0, which builds the knowledge base and the indexes, is run once from the scripts before the application is used. The table gives the data that enter and leave each process."),
        TAB("Level 1 processes and their data", ["No.", "Process", "Inputs", "Outputs", "Stores"], [
            ["1.0", "Authenticate user", "E-mail, password, session cookie", "Session cookie, user id, validation errors", "D1 (read, write)"],
            ["2.0", "Retrieve evidence", "Symptom text", "Top-5 records with relevance", "D2 (read)"],
            ["3.0", "Generate and screen answer", "Original text, top-5 records", "Answer text, safety flag and message, evidence cards", "-"],
            ["4.0", "Store consultation", "Result of 3.0, user id", "New consultation row", "D3 (write)"],
            ["5.0", "Manage history", "Search text, consultation id, delete request, user id", "History list, detail, deletion result", "D3 (read, delete)"],
            ["6.0", "Report metrics", "Metrics request", "Stored metrics and knowledge-base size", "D4 (read), D2 (size)"],
            ["7.0", "Build knowledge base and index", "Condition table in prepare_data.py", "Knowledge-base files, FAISS and BM25 indexes", "D2 (write)"],
        ], widths=[0.5, 1.5, 1.7, 1.9, 0.9], size=9.5, align=["c", "l", "l", "l", "l"]),
        dfig("dfd1", 5.4, 6.0),
        P("The stores are D1, the users table; D2, the knowledge base with its FAISS and BM25 indexes; D3, the consultations table; and D4, the stored metrics file results/metrics.json. Process 5.0 also serves the "
          "history search, the detail view and the deletion, all of which are restricted to the signed-in user's own rows."),
        H3("5.3.3 Level 2: the analysis processes"),
        P("Level 2 expands processes 2.0 and 3.0 into the steps of Pipeline.answer. Each step takes the output of the previous one; the original message is passed unchanged to the safety check."),
        TAB("Level 2 sub-processes", ["No.", "Sub-process", "Module and function", "Data read"], [
            ["2.1", "Normalise and expand", "query_expansion.normalize_query, expand_query_hyde", "Symptom text"],
            ["2.2", "Embed query", "embeddings.EmbeddingBackend.encode", "all-MiniLM-L6-v2 weights"],
            ["2.3", "Semantic search", "faiss_store.FaissStore.search", "data/index/faiss.index"],
            ["2.4", "Lexical search", "bm25_store.BM25Store.search", "data/index/bm25.json"],
            ["2.5", "Fuse (0.65 / 0.35)", "hybrid_retriever.fuse", "Two lists of 15 hits"],
            ["2.6", "Cross-encoder rerank", "reranker.Reranker.rerank", "Cross-encoder weights"],
            ["3.1", "Grounded answer", "generator.Generator.generate", "Flan-T5 weights, or the fallback"],
            ["3.2", "Safety check and filter", "safety.check_safety, apply_safety_filter", "Original text; answer text"],
        ], widths=[0.5, 1.8, 2.5, 1.5], size=9.5, align=["c", "l", "l", "l"]),
        dfig("dfd2", 5.6),
    ]


# =====================================================================================================================
def uml():
    return [
        H2("5.4 UML Diagrams"),
        H3("5.4.1 Class diagram"),
        P("The class diagram shows the classes of the system. Two are persistent: User and Consultation, the SQLAlchemy classes that map to the two tables, joined by a one-to-many relationship with "
          "cascade delete. The Pydantic schemas (RegisterRequest, LoginRequest, ChatRequest, EvidenceItem, ChatResponse) state the limits of every input and the shape of the output. "
          "The routers are thin: each function validates, calls one collaborator and returns a dictionary. The Pipeline owns one object of each RAG class: EmbeddingBackend, FaissStore, BM25Store, Reranker "
          "and Generator. Safety is a module of two functions rather than a class, and hybrid_retriever is a module with the single function fuse."),
        dfig("uml", 5.8, 7.0),
        H3("5.4.2 Sequence diagram"),
        P("The sequence diagram follows one symptom message. The browser posts the text to /api/chat; the route resolves the user from the cookie, calls Pipeline.answer and then stores a Consultation row "
          "before it returns the response. Inside the Pipeline the order of calls is expansion, embedding, FAISS, BM25, fusion, reranking, safety check, generation and filtering. The interface then "
          "adds the answer to the conversation, shows a confirmation toast and reloads the list of recent consultations."),
        dfig("seq", 5.6, 6.6),
        H3("5.4.3 Use-case diagram"),
        P("Two human actors use the system. A visitor who is not signed in can open the landing page, register and sign in with an own or the demo account. A registered user can in addition describe symptoms, "
          "read the grounded answer and its evidence cards, see the emergency or caution banner (part of reading the answer), see the recent consultations, search the history, open a consultation, delete it, "
          "view the About page with the measured metrics, and sign out or switch the theme. The local models (MiniLM, the reranker and Flan-T5) take part as a system actor in reading the answer. "
          "Every use case from UC4 onwards needs a valid session cookie. The table below lists the use cases with their pre-conditions."),
        dfig("uc", 5.4, 5.6),
        TAB("Use cases", ["No.", "Use case", "Actor", "Pre-condition", "Main result"], [
            ["UC1", "Open landing page", "Visitor", "-", "Product pitch and links to register or the demo login"],
            ["UC2", "Register an account", "Visitor", "E-mail not yet used; password of 6 to 128 characters", "Account created and signed in"],
            ["UC3", "Sign in (own or demo account)", "Visitor", "Account exists", "Session cookie set; redirect to the assistant"],
            ["UC4", "Describe symptoms in everyday language", "User", "Signed in; 3 to 2000 characters", "Consultation saved"],
            ["UC5", "Read grounded answer and evidence cards", "User", "UC4 completed", "Answer text and five evidence cards"],
            ["UC6", "See emergency or caution banner", "User", "Message matches a rule", "Red or amber banner at the top of the answer"],
            ["UC7", "See recent consultations", "User", "Signed in", "Last five consultations beside the chat"],
            ["UC8", "Search consultation history", "User", "Signed in", "Own consultations (latest 200), filtered by symptom or condition"],
            ["UC9", "Open consultation detail", "User", "Consultation belongs to the user", "Stored question, answer and evidence"],
            ["UC10", "Delete a consultation", "User", "Confirmation accepted", "Row removed"],
            ["UC11", "View About page and measured metrics", "User", "Signed in or not", "Pipeline description and the stored evaluation figures"],
            ["UC12", "Sign out, switch theme", "User", "Signed in", "Cookie cleared; theme stored in the browser"],
        ], widths=[0.5, 1.9, 0.7, 1.7, 1.7], size=9, align=["c", "l", "l", "l", "l"]),
    ]


# =====================================================================================================================
def database():
    return [
        H2("5.5 Database Design"),
        P("The application database is a single SQLite file, data/carelens.db, accessed through SQLAlchemy. It has two tables created by init_db at start-up. SQLite was chosen because it needs no "
          "server, stores all data in one file that the user can see and delete, and is sufficient for one machine and a few accounts. The knowledge base and its indexes are not in the database: they are "
          "read-only files that are loaded into memory by the Pipeline."),
        dfig("er", 5.2, 5.4),
        TAB("Table users", ["Column", "Type", "Constraint", "Meaning"], [
            ["id", "Integer", "Primary key, indexed", "User identifier"],
            ["email", "String(255)", "Unique, indexed, not null", "Sign-in name, stored in lower case"],
            ["password_hash", "String(255)", "Not null", "bcrypt hash of the password"],
            ["created_at", "DateTime", "Default: current UTC time", "Registration time"],
        ], widths=[1.3, 1.2, 1.9, 2.0], size=10, align=["l", "l", "l", "l"]),
        TAB("Table consultations", ["Column", "Type", "Constraint", "Meaning"], [
            ["id", "Integer", "Primary key, indexed", "Consultation identifier"],
            ["user_id", "Integer", "Foreign key to users.id, indexed, not null", "Owner; every query filters on it"],
            ["symptom_query", "Text", "Not null", "The message as typed (3 to 2000 characters)"],
            ["generated_response", "Text", "Not null", "Answer text, with the emergency notice prepended when flagged"],
            ["top_condition", "String(255)", "Default empty", "Condition of the best-ranked record"],
            ["retrieved_evidence", "Text", "Default '[]'", "JSON list of the five evidence records with relevance"],
            ["retrieval_score", "Float", "Default 0.0", "Displayed relevance of the best record (0 to 1)"],
            ["safety_flag", "String(50)", "Default 'routine'", "routine, caution or emergency"],
            ["created_at", "DateTime", "Default: current UTC time", "Time of the consultation"],
        ], widths=[1.4, 1.0, 2.2, 1.8], size=9.5, align=["l", "l", "l", "l"]),
        P("One user has many consultations (relationship with cascade 'all, delete-orphan'). The evidence is kept as a JSON string in one column rather than in a third table: a consultation is written once and "
          "read whole, so a join would add complexity without a benefit, and the stored evidence stays exactly as it was shown even if the knowledge base is rebuilt later. The cost is that the evidence "
          "cannot be queried with SQL; the history search is therefore done in Python on the latest 200 rows, over the question text and the top condition only."),
        P("The knowledge base is held in data/processed/knowledge_base.json and .csv with ten fields per record."),
        TAB("Knowledge-base record", ["Field", "Content"], [
            ["record_id", "REC-0001 and so on"], ["disease", "Condition name"], ["symptoms", "Comma-separated, lower-case symptom list of this record"],
            ["description", "One-sentence description (shared by all records of a condition)"], ["guidance", "Self-care and when-to-seek-care text (shared by condition)"],
            ["severity", "low, moderate, high or emergency"], ["red_flags", "Warning signs that call for urgent care"],
            ["source, source_type", "Provenance label; every record carries source_type = synthetic"],
            ["retrieval_text", "'Disease: ... Symptoms: ... Description: ... Guidance: ...' - the text that is embedded and indexed"],
        ], widths=[1.6, 4.7], size=10, align=["l", "l"]),
    ]


# =====================================================================================================================
def modules():
    loc_app = _loc("app/*.py", "app/rag/*.py", "app/routes/*.py")
    loc_fe = _loc("frontend/src/**/*.jsx", "frontend/src/**/*.js")
    return [
        H2("5.6 Module Design"),
        P(f"The backend has {loc_app} non-blank lines of Python in 24 files; the React interface has {loc_fe} lines of JavaScript and JSX. The table lists every backend module with its one responsibility."),
        TAB("Backend modules", ["Module", "Responsibility", "Main interface"], [
            ["main.py", "Creates the app, mounts the static files and routers, creates tables and the demo user at start-up, health route", "app, GET /api/health"],
            ["config.py", "All settings, each overridable by a CARELENS_* environment variable", "settings"],
            ["database.py", "Engine, session factory, init_db", "get_db, init_db"],
            ["models.py", "ORM classes User and Consultation", "User, Consultation"],
            ["schemas.py", "Pydantic request and response models with length limits", "ChatRequest and others"],
            ["auth.py", "bcrypt hashing and JWT creation and decoding", "hash_password, verify_password, create_token, decode_token"],
            ["demo.py", "Creates the demo account if missing", "ensure_demo_user"],
            ["routes/auth.py", "Register, login, logout, me; require_user dependency (cookie or Bearer token)", "/api/auth/*"],
            ["routes/chat.py", "Validates, runs the Pipeline, stores the consultation, maps errors to 400, 503 and 500", "POST /api/chat"],
            ["routes/history.py", "List with search, get one, delete; every query filtered by user_id", "/api/history"],
            ["routes/about.py", "Serves results/metrics.json with the knowledge-base size", "GET /api/about/metrics"],
            ["routes/pages.py", "Legacy server-rendered pages", "/, /login, /dashboard ..."],
            ["rag/pipeline.py", "Lazy singleton that loads the models and indexes and runs the whole flow", "get_pipeline, Pipeline.answer, rebuild"],
            ["rag/query_expansion.py", "Normalisation and the hypothetical-description template", "normalize_query, expand_query_hyde"],
            ["rag/embeddings.py", "Sentence-transformer encoder with a TF-IDF fallback", "EmbeddingBackend.encode"],
            ["rag/faiss_store.py", "Flat inner-product index: build, save, load, search", "FaissStore"],
            ["rag/bm25_store.py", "BM25 index over the same records", "BM25Store"],
            ["rag/hybrid_retriever.py", "Min-max normalised weighted fusion", "fuse"],
            ["rag/reranker.py", "Cross-encoder rescoring and relevance normalisation", "Reranker.rerank"],
            ["rag/generator.py", "Flan-T5 generation and the evidence-based fallback", "Generator.generate"],
            ["rag/safety.py", "Emergency and caution rules, medication-phrase filter", "check_safety, apply_safety_filter"],
        ], widths=[1.5, 3.3, 1.5], size=9, align=["l", "l", "l"]),
        P("Three design points follow from the table. First, the Pipeline is a lazy singleton: the three models take about a minute to load, so they are loaded on the first chat request and reused afterwards, "
          "which keeps start-up of the server immediate and the health route always available. Second, each RAG class hides one replaceable choice: swapping the vector store, the encoder or the generator means "
          "changing one file. Third, the safety module has no dependency on the retrieval classes, so a failure of any model cannot disable it."),
        H3("5.6.1 The RAG classes in detail"),
        P("**EmbeddingBackend** tries to load the sentence-transformer when it is created and records its mode, 'sentence-transformer' or 'tfidf'. In the first mode encode returns unit-length 384-dimensional vectors. "
          "In the second it fits, or re-uses, a TF-IDF vectoriser with at most 384 features and English stop words, pads or truncates the matrix to 384 columns and normalises the rows, so that the rest of the code does not need to know which mode is active. "
          "When the index is loaded from disk in TF-IDF mode, the vectoriser is refitted on the stored records."),
        P("**FaissStore** wraps a flat inner-product index. build adds the vectors and saves the index to data/index/faiss.index together with the record list in records.json; load restores both and returns false if either is missing, "
          "which makes the Pipeline rebuild; search returns up to k tuples of (score, record, position). **BM25Store** lower-cases the retrieval text, keeps alphanumeric tokens and builds a BM25Okapi model; it saves the records and the tokenised corpus as JSON "
          "so that the model can be rebuilt on load. Both stores index the same record list in the same order, which is what allows the fusion step to match their hits by position."),
        P("**Reranker** loads the cross-encoder when created. rerank scores every (query, retrieval text) pair, sorts by score, rescales the scores of all candidates to the 0 to 1 relevance and returns the best k. If the model is unavailable, "
          "or if prediction fails, the hybrid score takes the place of the cross-encoder score. **Generator** loads a text-to-text pipeline, builds the prompt of Section 6.3.6, and returns a pair of the answer and a label that says which method produced it: "
          "the model's name or 'evidence-fallback'. **Pipeline** creates one of each, ensures that the indexes exist, and exposes answer(raw_query, top_k), which returns one dictionary with the answer, the evidence list, the safety flag and message, the relevance label, the score, the generator label and the expansion that was used."),
        TAB("Data passed between the stages", ["Stage output", "Structure"], [
            ["Expansion", "{normalized, hypothetical, combined} - three strings"],
            ["Dense and lexical hits", "List of (score, record, position) tuples, at most 15 each"],
            ["Fused candidate", "{idx, record, sem, lex, hybrid} - sorted by the hybrid score, at most 15"],
            ["Reranked candidate", "The fused dictionary plus rerank (raw score) and relevance (0 to 1), at most 5"],
            ["Evidence item", "{record_id, disease, symptoms, description, guidance, severity, red_flags, relevance, hybrid, rerank}; the route removes hybrid and rerank before sending"],
            ["Safety result", "{flag, message} with flag routine, caution or emergency"],
            ["Pipeline result", "{answer, top_condition, evidence, safety_flag, safety_message, relevance_label, retrieval_score, generated_by, expanded}"],
        ], widths=[1.7, 4.6], size=9.5, align=["l", "l"]),
    ]


def quality():
    return [
        H2("5.9 Quality Attributes and Design Constraints"),
        P("The design was judged against five quality attributes, each with the measure that was actually used and the constraint that limits it."),
        TAB("Quality attributes", ["Attribute", "How the design addresses it", "Constraint or open point"], [
            ["Privacy", "Local models, local SQLite file, no analytics, no external calls after the first model download, per-user filtering of every query", "Data are not encrypted at rest; the signing key is a default value unless changed"],
            ["Safety", "Rule layer independent of retrieval, permanent disclaimer, emergency banner above the answer, medication-phrase filter", "Rules are literal; they do not understand paraphrase or negation"],
            ["Reliability", "Three degradation paths; 503 and 500 mapped to readable messages; retry button in the interface", "A model that loads but misbehaves (the generator echo) is not detected"],
            ["Performance", "Models loaded once; exact search over a small index; stages timed separately", "The cross-encoder on a CPU dominates the response time; no concurrency design"],
            ["Maintainability", "One module per replaceable choice; settings in one file with environment overrides; no global state besides the Pipeline singleton", "The test suite is small; behaviour of the safety and history code is mostly covered by the smoke test and probes"],
            ["Portability", "Windows launcher, manual steps for other systems, Docker images for the API and the web server", "Tested only on Windows 11"],
        ], widths=[1.1, 3.0, 2.2], size=9, align=["l", "l", "l"]),
        P("Two constraints shaped many choices. The hardware is an ordinary laptop or desktop without a GPU, which ruled out a large generator and made the small Flan-T5 and the six-layer cross-encoder the practical choices. "
          "The knowledge base is small and written by the team, which made an exact flat index sufficient and made the retrieval question easy; a real clinical corpus of thousands of passages would need the structure that the base paper and the ClinicBot "
          f"system [{R['clinicbot']}] describe, such as sectioned guidelines with provenance, and would justify an approximate index."),
    ]


# =====================================================================================================================
def ui_design():
    out = [
        H2("5.7 User Interface Design"),
        P("The interface is a React single-page application built on a neo-brutalist component kit (thick borders, a grid background, a lime accent, Archivo Black headings and IBM Plex text). "
          "Routes are code-split with lazy loading. Signed-in pages are rendered in a shell with a side navigation that becomes a drawer on narrow screens; the public pages use a top bar. "
          "A guard component sends a visitor who is not signed in to the sign-in page and returns them to the page they asked for afterwards, and the sign-in and registration pages redirect a signed-in user to the assistant."),
        TAB("Routes and screens", ["Route", "Screen", "What it offers"], [
            ["/", "Landing", "Product pitch, how it works in steps, facts ticker, links to register or try the demo login"],
            ["/login, /register", "Sign in, Create account", "Forms with inline errors and a show-password control"],
            ["/assistant", "Symptom assistant", "Chat log, four example chips, text area (Enter sends), safety banners, answer, evidence cards, five recent consultations"],
            ["/history", "Consultations", "Search box, sortable table with condition, safety badge, relevance and date, view and delete with confirmation"],
            ["/history/:id", "Consultation detail", "Stored question, answer and evidence cards; delete"],
            ["/about", "About and metrics", "The seven pipeline stages, the stored evaluation figures and the caveat that they come from synthetic data"],
            ["*", "Not found", "Message and link home"],
        ], widths=[1.3, 1.4, 3.6], size=9.5, align=["l", "l", "l"]),
        P("Four design rules were applied. **Safety is never decorative**: an emergency notice is a full-width red alert above the answer, a caution notice is amber, and the line 'Not a diagnosis. In an emergency "
          "call your local emergency number' sits permanently under the text box. **Evidence is visible**: each answer is followed by cards that show the record's typical symptoms, description, guidance, severity badge, "
          "'seek urgent care if' warning signs and a relevance bar, whose tooltip states that it is similarity to a record and not a medical probability. **Every state is designed**: loading skeletons, empty states, "
          "error states with a retry button, toasts for success, and a typing indicator while the answer is computed. **Accessibility basics are in place**: the conversation is an aria-live log, controls have labels, "
          "dialogs trap focus and close with Escape, the theme (light or dark) is stored in the browser, and animations respect the reduced-motion setting."),
    ]
    if F.REPORT:
        out.append(PAIR([(F.shot("07_assistant_answer.png"), "Assistant screen with an answer and the recent-consultations panel."),
                         (F.shot("09_history.png"), "History screen with search, safety badges and relevance.")], 3.0))
    else:
        out += [sfig("20_assistant_evidence.png", "Evidence cards under an answer: symptoms, description, guidance, severity, urgent-care warning and relevance.", 5.4, 4.2),
                sfig("09_history.png", "History screen with search, safety badges and relevance.", 5.4, 4.2)]
    out.append(P("Screens captured from the running application are shown with their analysis in Chapter 8."))
    return out


# =====================================================================================================================
def decisions():
    return [
        H2("5.8 Design Decisions and Their Reasons"),
        P("Each decision below was made while the system was built, with the alternative that was not taken and the consequence that has since been observed."),
        TAB("Design decisions", ["Decision", "Alternative", "Reason", "Observed consequence"], [
            ["Run every model locally", "Hosted LLM API", "Symptom text is health data; no cost, key or internet needed", "First request takes about a minute to load models; CPU generation is slow"],
            ["Hybrid dense + lexical retrieval", "Dense only", "Symptom words are short and exact; BM25 catches literal matches, the encoder catches paraphrase", f"Hybrid {F.pct(F.ret('hybrid','S4_lay_language_60'),0)} vs dense {F.pct(F.ret('dense','S4_lay_language_60'),0)} on lay probes; BM25 alone {F.pct(F.ret('bm25','S4_lay_language_60'),0)}"],
            ["Cross-encoder reranking of 15 candidates", "Return the fused order", "A cross-encoder reads query and record together and is more precise", f"Top-1 on lay probes {F.pct(F.ret('hybrid_rerank','S4_lay_language_60'),1)} vs {F.pct(F.ret('hybrid','S4_lay_language_60'),1)}; reranking is the slowest stage"],
            ["Rule-based HyDE-style template", "LLM-written hypothetical document", "No second model call and no latency; deterministic", f"No measured gain: top-1 without it {F.pct(F.ret('hybrid_rerank_nohyde','S4_lay_language_60'),1)} on lay probes"],
            ["Min-max fusion with weights 0.65/0.35", "Reciprocal rank fusion", "Keeps score magnitudes; weights are configurable", "Weights were not tuned on data"],
            ["Relevance = min-max of rerank scores", "Raw cross-encoder score or probability", "Gives the user a simple 0 to 100% bar", "The best record is always 100%, even for complaints outside the knowledge base (Chapter 8)"],
            ["Answer from retrieved records, with a deterministic fallback", "Free generation", "Nothing may be said that is not in the evidence", "Fallback text is repetitive; the local generator path echoes its prompt in the tested environment"],
            ["Regex safety layer separate from retrieval", "Classifier or LLM triage", "Transparent, instant, cannot be disabled by a model failure", "Misses paraphrased emergencies and fires on negations (Chapter 7)"],
            ["Evidence stored as JSON text", "Separate evidence table", "Written once and read whole; keeps what was shown", "Not searchable with SQL"],
            ["JWT in an httponly cookie, Bearer also accepted", "Token in local storage", "Not readable by page scripts", "No Secure flag and a default signing key (Chapter 7)"],
            ["SQLite", "PostgreSQL", "Single file, no server", "Suited to one machine, not to many users"],
            ["Vite dev server proxies /api", "Cross-origin requests with CORS", "Same origin, so the cookie works without CORS configuration", "Docker uses nginx for the same purpose"],
        ], widths=[1.4, 1.2, 1.8, 1.9], size=8.5, align=["l", "l", "l", "l"]),
    ]
