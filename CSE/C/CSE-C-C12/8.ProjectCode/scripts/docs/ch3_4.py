"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R

_E = F.ENV
_ST = F.LAT["stages_ms"]


def blocks():
    return chapter3() + chapter4()


def report3():
    return chapter3()


def report4():
    return chapter4()


def _s(x):
    return f"{x / 1000:.1f} s"


# =====================================================================================================================
def chapter3():
    fb, t5 = F.LAT_FB["chat_ms"], F.LAT_T5["chat_ms"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P(f"The feasibility of {F.PRODUCT} was settled partly by analysis and partly by building the system and measuring it. Where a question could not be settled with the data available to the team, "
          "the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risks were whether a retrieval pipeline with three neural models could run on an ordinary computer without a GPU, whether it would answer fast enough to feel interactive, and whether "
          f"every part could be built from free software. The development machine is a desktop with a {_E['cpu']} and {_E['ram_gb']} GB of RAM, running Windows 11."),
        TAB("Technical feasibility checks", ["Question", "Measurement", "Verdict"], [
            ["Can all models run on a CPU?", f"Embedding model, cross-encoder and Flan-T5-small load and run under Python {_E['python']} and torch {_E['torch']} on the machine above", "Feasible"],
            ["Is retrieval fast enough?",
             f"FAISS search {_ST['faiss']['mean']} ms, BM25 {_ST['bm25']['mean']} ms, query embedding {_ST['embed']['mean']:.0f} ms (mean over {F.LAT['n']} queries); the cross-encoder over {F.CANDIDATE_K} candidates is the slowest stage at {_ST['rerank']['mean']:.0f} ms",
             "Feasible"],
            ["Is the whole request interactive?",
             f"`POST /api/chat` over HTTP: mean {fb['mean']:.0f} ms with the evidence-based answer, {t5['mean']:.0f} ms with the Flan-T5 generator (p95 {t5['p95']:.0f} ms)", "Feasible"],
            ["Does it work offline?", "TF-IDF vectors, hybrid order and a template answer replace the three models; top-1 on everyday-language probes falls to "
             f"{F.pct(F.RET['hybrid_tfidf']['S4_lay_language_60']['top1'])} from {F.pct(F.SHIP['S4_lay_language_60']['top1'])}", "Feasible with lower quality"],
            ["Is the generator useful?", f"With transformers {_E['transformers']} the local generator returned its prompt in {F.GEN['echo_answers']} of {F.GEN['n']} answers", "Not feasible as installed"],
            ["Can accounts and history be built simply?", "SQLAlchemy and SQLite, bcrypt, signed cookies; automated tests pass", "Feasible"],
        ], widths=[1.8, 3.4, 1.1], size=9.5, align=["l", "l", "l"]),
        P("The generator row is a finding, not a plan: it was discovered while measuring and is discussed in Chapter 8. The system remains usable because the evidence-based answer does not need the model."),

        H2("3.2 Economic Feasibility"),
        P("The project needs no purchased software or paid service. Every component is open source, the models are downloaded once and then run locally, and symptom text is never sent to a "
          "third party, so there is no per-query fee. The hardware is an ordinary desktop already owned by the team; no GPU is needed."),
        TAB("Cost elements", ["Element", "Cost", "Note"], [
            ["Languages, frameworks, libraries", "No licence fee", "Python, FastAPI, SQLAlchemy, React, Vite, FAISS, rank-bm25, scikit-learn, PyTorch, Transformers"],
            ["Models", "No licence fee", "all-MiniLM-L6-v2, ms-marco-MiniLM-L-6-v2, Flan-T5-small, downloaded once"],
            ["Hosting and database", "None", "Runs on the user's own machine; SQLite file"],
            ["Hardware", "Existing PC", "About 4 GB free disk for models and dependencies (HOW_TO_RUN.md)"],
            ["Per-query cost", "None", "No external API is called for symptom data"],
            ["Effort", "Student time", "Four students over one academic project cycle; not priced"],
        ], widths=[2.0, 1.2, 3.1], size=9.5, align=["l", "l", "l"]),
        P("The principal hidden cost is validation: a real deployment would need clinicians to review the knowledge base, which this project did not have and did not cost."),

        H2("3.3 Operational Feasibility"),
        P("Operation is simple. A person double-clicks `run.bat`, which creates the Python environment, installs dependencies, prepares the knowledge base and starts the backend and the web interface; a "
          "Docker route is also provided. Users need only a browser. They register or use the demo account, type symptoms and read the answer. Day-to-day upkeep is limited to updating the knowledge-base table and "
          "rebuilding the index with two scripts. The risk is behavioural: a reader may over-trust a confident-looking answer, so the interface repeats that the result is not a diagnosis and shows an emergency "
          "notice when the rules fire."),

        H2("3.4 Schedule Feasibility"),
        P("The work was organised in five phases. The dates in the table are the file dates of the repository; the project calendar itself was not recorded."),
        TAB("Phases of the work", ["Phase", "Work", "Evidence"], [
            ["1. Study", "Base paper, literature survey, objectives", "Batch documents 2 to 6"],
            ["2. Backend and pipeline", "Knowledge base, indexes, retrieval, safety, accounts, history API, tests", "app/, scripts/, tests/ (first complete version dated 10 Sep 2026)"],
            ["3. Web interface", "React and Vite interface replacing the server-rendered pages", "frontend/ (22 Oct 2026)"],
            ["4. Measurement", "Ablation, probes, safety and latency scripts", "scripts/measure_metrics.py, docs/metrics/"],
            ["5. Documentation", "Diagrams, decks, report, paper", "docs/, batch documents"],
        ], widths=[1.4, 2.8, 2.1], size=9.5, align=["l", "l", "l"]),

        H2("3.5 Advantages and Constraints"),
        B("**Advantages:** answers come only from retrieved records; the system is private and free to run; each model-dependent stage has an offline fallback; every consultation is traceable to evidence cards.",
          f"**Constraints:** the knowledge base is synthetic ({F.KB['records']} records); no clinical review; English only; one cross-encoder call per query dominates the time; the installed generator does not work; no longitudinal analysis."),
    ]


# =====================================================================================================================
def chapter4():
    s4 = F.SHIP["S4_lay_language_60"]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the situation the system replaces, the system that was built, and the requirements that it was built against. Each requirement has an identifier that the testing "
          "and results chapters refer to."),

        H2("4.1 Existing System and Its Limitations"),
        P("Today a person with a symptom typically uses a web search engine, a symptom-checker website or a general chatbot, and sometimes the system described in the base paper's literature."),
        TAB("Existing approaches and their limitations", ["Approach", "Limitation"], [
            ["General web search", "Returns generic, alarming or unrelated pages; no memory of earlier symptoms; no link between a person's description and one source"],
            ["General chatbot", "Answers from broad public training data, can hallucinate, gives no source for a statement, and sends the text to an external service"],
            ["Learned medical chatbots (Section 2.3.1)", "Predict from trained parameters; answers are not tied to a retrievable record"],
            ["Base-paper framework", f"Embedding retrieval and stored history, but no lexical retrieval, reranking, safety escalation or reported measurements [{R['base']}]"],
            ["Paper or phone notes", "Symptoms recorded as isolated events; progression is never visible"],
        ], widths=[2.0, 4.3], size=9.5, align=["l", "l"]),

        H2("4.2 Proposed System and Its Advantages"),
        P(f"{F.PRODUCT}, implemented as {F.APP_NAME}, is a local web application. A user signs in, describes symptoms in everyday language and receives the matching medical information together with the "
          "records it rests on, a relevance indicator, an emergency or caution notice where the rules apply, and a standing disclaimer. Each consultation is stored in the user's private history."),
        B("**Grounded:** the answer is assembled from the retrieved records, with evidence cards for each.",
          f"**Robust retrieval:** dense and lexical search, fusion and reranking; {F.pct(s4['top1'])} top-1 on {s4['n']} everyday-language probes on the synthetic base.",
          "**Safe by design:** ten emergency rules, six caution keywords, a permanent disclaimer and a filter for medication instructions - with the known gaps reported in Chapter 8.",
          "**Private:** local models, local SQLite, per-user history isolation, deletion supported.",
          "**Degrades gracefully:** each model has an offline alternative."),

        H2("4.3 Functional Requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Where implemented"], [
            ["FR-1", "A visitor can register with an email and a password of 6 to 128 characters; a duplicate email is refused", "routes/auth.py"],
            ["FR-2", "A user can sign in and out; the session is a signed cookie valid for 24 hours", "routes/auth.py, auth.py"],
            ["FR-3", "The user can submit symptom text of 3 to 2,000 characters", "schemas.py, routes/chat.py"],
            ["FR-4", "The system normalises the text and builds an expanded query", "rag/query_expansion.py"],
            ["FR-5", f"The system retrieves {F.CANDIDATE_K} candidates by dense and lexical search, fuses them and reranks to {F.TOP_K}", "rag/pipeline.py and its stores"],
            ["FR-6", "Each answer lists evidence cards: record id, symptoms, description, guidance, severity, red flags, relevance", "routes/chat.py"],
            ["FR-7", "An answer is generated from the evidence (Flan-T5 or deterministic fallback) and filtered for medication instructions", "rag/generator.py, rag/safety.py"],
            ["FR-8", "The system flags emergency or caution wording and always shows a disclaimer", "rag/safety.py"],
            ["FR-9", "Every consultation is stored with query, answer, evidence, score, flag and time", "models.py, routes/chat.py"],
            ["FR-10", "The user can list (latest 200) and search their consultations", "routes/history.py"],
            ["FR-11", "The user can open one consultation in detail", "routes/history.py"],
            ["FR-12", "The user can delete a consultation, after a confirmation", "routes/history.py, frontend"],
            ["FR-13", "A user cannot read or delete another user's consultation (404)", "routes/history.py"],
            ["FR-14", "An About page shows the pipeline and the evaluation file with its caveat", "routes/about.py, About page"],
            ["FR-15", "The interface supports light and dark themes and phone-width screens", "frontend/"],
            ["FR-16", "A demo account exists so the product can be explored", "demo.py"],
        ], widths=[0.6, 4.1, 1.6], size=9.5, align=["c", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements", ["ID", "Requirement", "How it is met or measured"], [
            ["NFR-1 Performance", "A request should finish in about a second on a CPU", f"Measured: mean {F.LAT_FB['chat_ms']['mean']:.0f} ms (fallback answer), {F.LAT_T5['chat_ms']['mean']:.0f} ms (Flan-T5 path)"],
            ["NFR-2 Privacy", "Symptom text stays on the machine", "Local models and SQLite; no external call for symptom data"],
            ["NFR-3 Security", "Passwords hashed, sessions signed, histories isolated", "bcrypt, HS256 JWT in an httponly cookie, per-user queries; tests"],
            ["NFR-4 Reliability", "The system answers when a model is missing", "Fallbacks for embeddings, reranking and generation"],
            ["NFR-5 Safety", "Emergencies are flagged; no dosage advice", "Rule layer and answer filter; recall measured in Chapter 8"],
            ["NFR-6 Usability", "Plain language, examples, clear errors", "React interface with example prompts, toasts and empty states"],
            ["NFR-7 Portability", "Runs on Windows 10/11 with one command", "run.bat; Docker option; ports in .env"],
            ["NFR-8 Maintainability", "Settings and data are replaceable", "Environment-variable settings; knowledge base built by script"],
        ], widths=[1.3, 2.3, 2.7], size=9.5, align=["l", "l", "l"]),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Item", "Tested configuration"], [
            ["Processor", _E["cpu"]],
            ["Memory", f"{_E['ram_gb']} GB RAM"],
            ["Graphics", "None needed; all models run on the CPU"],
            ["Disk", "About 4 GB free for dependencies and downloaded models"],
            ["Network", "Needed once to download models and packages; not needed afterwards"],
        ], widths=[1.6, 4.7], size=10, align=["l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software", ["Layer", "Software and version"], [
            ["Operating system", "Windows 11 Pro (tested); Linux and macOS with the manual steps"],
            ["Language", f"Python {_E['python']}; Node.js 18 or newer (24.19 used)"],
            ["Backend", f"FastAPI {_E['fastapi']}, Uvicorn, SQLAlchemy {_E['sqlalchemy']} (SQLite), Pydantic 2, bcrypt, PyJWT"],
            ["Retrieval", f"sentence-transformers {_E['sentence_transformers']}, FAISS {_E['faiss']} (CPU), rank-bm25, scikit-learn {_E['scikit_learn']}"],
            ["Models", f"{_E['embedding_model']}; {_E['reranker_model']}; {_E['generator_model']}"],
            ["Deep learning", f"torch {_E['torch']}, transformers {_E['transformers']}"],
            ["Frontend", "React 19, Vite 8, react-router 7, Recharts 3; Chrome, Edge or Firefox"],
            ["Test and measurement", "pytest, matplotlib, Playwright (screens)"],
        ], widths=[1.6, 4.7], size=9.5, align=["l", "l"]),

        H2("4.7 Data Requirements"),
        P(f"Three kinds of data are handled. The knowledge base is a table of {F.KB['records']} records with identifier, condition, symptoms, description, guidance, severity, red flags and source. "
          "The user data are an account (email and password hash) and a list of consultations. The index files hold the embedding vectors and the BM25 corpus. The knowledge base is regenerated by "
          "`prepare_data.py` and the indexes by `build_index.py`."),

        H2("4.8 User Roles"),
        P("The product has one role in the running system, the registered user, whose data are isolated from all others. A demo account is a normal user. The people around the product have other roles:"),
        TAB("Roles", ["Role", "Goal", "Main screens or tools"], [
            ["Visitor", "See what the product does and create an account", "Landing, Register, Sign in"],
            ["Registered user", "Describe symptoms, read information, review and delete history", "Symptom assistant, History, About"],
            ["Maintainer", "Edit the knowledge base, rebuild indexes, run tests", "scripts/, tests/, .env"],
        ], widths=[1.4, 2.8, 2.1], size=10, align=["l", "l", "l"]),

        H2("4.9 Constraints and Assumptions"),
        P("The knowledge base is synthetic and English; the system gives information and not diagnosis; the cross-encoder dominates response time; the secret key has a development default that must be changed "
          "before any real deployment; and there is a single SQLite file and no administrator role. Users are assumed to write in English and to act on an emergency notice."),

        H2("4.10 Requirements Against Objectives"),
        TAB("Objectives and the requirements that serve them", ["Objective", "Requirements"], [
            ["1. Curated knowledge base indexed for retrieval", "FR-5, Section 4.7"],
            ["2. Natural-language symptoms with query expansion", "FR-3, FR-4"],
            ["3. Hybrid retrieval with neural reranking", "FR-5, NFR-1"],
            ["4. Grounded responses citing the retrieved source", "FR-6, FR-7"],
            ["5. Track symptoms over time", "FR-9, FR-10, FR-11 (storage only; no trend requirement was implemented)"],
            ["6. Evaluate relevance, groundedness and response time", "NFR-1, NFR-5; Chapters 7 and 8"],
        ], widths=[3.4, 2.9], size=9.5, align=["l", "l"]),
    ]
