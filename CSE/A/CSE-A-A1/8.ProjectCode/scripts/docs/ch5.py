"""Chapter 5: System Design. Also holds DIAGRAMS, the list used by 11. BLOCK DIAGRAMS ALL.docx."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB

# (key, title, file, caption, explanatory paragraph(s))
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of the Adaptive Learning Intelligence Platform: browser, FastAPI service, SQLite and the file store.",
     "The diagram has three columns. On the left is the browser, which runs the React 19 single-page application with its landing, login, register, upload, documents, ask, quiz, roadmap and dashboard "
     "pages. In the middle is the FastAPI service on port 8301. It applies two middleware layers (a CORS rule that admits only the front-end origin, and a signed session cookie named `alip_session` "
     "valid for seven days) and exposes 14 JSON endpoints under `/api`. Inside the service sit the two groups of logic: the `RAGEngine` that holds one TF-IDF index per user in memory, and the "
     "document analysis, quiz generator and roadmap rules. On the right are the stores: the SQLite file `instance/app.db` with five tables, and the uploaded originals under `uploads/<user id>/`. "
     "During development the Vite server on port 5301 proxies `/api` to port 8301, so the browser sees one origin. Two dashed paths are optional: the call to the Anthropic API, made only when "
     "`ANTHROPIC_API_KEY` is set, and the original Flask interface on port 5000, which imports the same `db.py` and `utils/` modules and therefore cannot drift from the new interface."),
    ("wf", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: ingest and analyse, ask, then practise and adapt.",
     "The workflow has three stages. In the first stage an uploaded file is parsed (pypdf for PDF, python-docx for DOCX, plain reading for TXT), cleaned, cut into 180-word chunks with a 30-word "
     "overlap, scanned for subject and unit headings, given up to twelve TF-IDF topics, and stored; storing triggers a rebuild of the user's TF-IDF index (unigrams and bigrams, English stop words). "
     "In the second stage a question is vectorised with the same index, the four most similar chunks are retrieved by cosine similarity, and either the key sentences are selected or, if a key is "
     "configured, the chunks are sent to the language model; the answer is shown together with the source passages. The dashed arrow shows that retrieval depends on the index built in the first stage. "
     "In the third stage five fill-in-the-blank questions are generated from a document, the server grades the submitted answers, accuracy per topic is computed and the thresholds below 50 and below 80 "
     "percent give High, Medium and Low priority, which update the roadmap and the dashboard."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Level 0 data flow diagram (context diagram).",
     "At level 0 the platform is one process. The student sends registration and login details, study files, questions and quiz answers, and receives the detected topics, cited answers, quizzes and scores, "
     "the roadmap and the dashboard. The only other external entity is the language-model provider: when enabled, the platform sends the question and the retrieved context and receives generated "
     "answer text. The dashed lines mark this flow as optional."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram with five processes and five data stores.",
     "Level 1 splits the platform into five processes. Process 1.0 authenticates the user against D1 (users). Process 2.0 analyses documents and writes the document row with its topics to D2 and the chunks "
     "to D3; the uploaded file is also written to disk. Process 3.0 answers questions by reading the user's chunks from D3 and writing the question, answer and source file names to D4 (queries). "
     "Process 4.0 reads the chunks of the chosen document from D3 to build questions and writes one result per question and topic to D5 (quiz_results). Process 5.0 builds the roadmap and the dashboard "
     "from the attempts in D5 and the counts in D2 and D4. The long line on the right edge shows that processes 4.0 and 5.0 reach stores that are drawn beside other processes."),
    ("dfd2d", "Data flow diagram, level 2: document analysis", "05_dfd_level2_documents.png",
     "Level 2 data flow diagram of process 2.0, analyse documents.",
     "Process 2.0 consists of six steps in a chain. 2.1 validates the file (extension must be pdf, docx or txt, size at most 16 MB, name made safe); a failure returns an error message to the student. "
     "2.2 saves the original file under `uploads/<user id>/`. 2.3 extracts the raw text. 2.4 collapses whitespace and cuts the text into overlapping chunks. 2.5 looks for subject and unit headings "
     "and ranks TF-IDF terms, giving at most twelve topics. 2.6 stores the document row with its topics in D2 and the chunks in D3, and rebuilds the user's in-memory TF-IDF index from all chunks."),
    ("dfd2r", "Data flow diagram, level 2: answering questions", "06_dfd_level2_rag.png",
     "Level 2 data flow diagram of process 3.0, answer questions.",
     "Process 3.0 is also a chain of six steps. 3.1 rejects an empty question with error 400. 3.2 obtains the user's index: the cached engine if present, otherwise the chunks are read from D3 and D2 "
     "and the index is built. 3.3 vectorises the question and scores every chunk by cosine similarity. 3.4 keeps the four best chunks with a score above zero. 3.5 composes the answer, either by "
     "selecting key sentences or by calling the optional language model (any failure falls back to the extractive answer). 3.6 stores the question, answer and source file names in D4 and "
     "returns the answer with the source passages, their passage numbers and match scores to the student."),
    ("class", "UML class diagram", "07_uml_class_diagram.png",
     "UML class diagram of the service modules and the five entities.",
     "The upper part shows the code modules drawn as classes. `ApiService` (the module `backend/main.py`) holds the FastAPI object and the dictionary of quizzes in progress, and offers one function per "
     "endpoint; it uses `RAGEngine`, `QuizGenerator` and `Database`, and the helper `TextExtraction`. `RAGEngine` has a vectorizer, a matrix, the chunk texts and their metadata, and the methods "
     "`build_index`, `retrieve`, `_extractive_answer`, `generate_answer` and `_llm_answer`. `TextExtraction`, `QuizGenerator` and `Database` are modules of functions. The lower part shows the five "
     "entities with their key attributes. A user has many documents, queries and quiz results; a document has many chunks. The same relationships appear in the ER diagram."),
    ("sequp", "Sequence diagram: upload", "08_sequence_upload.png",
     "Sequence diagram of uploading a study document.",
     "The student chooses a file and a subject in the browser, and the interface posts them as a multipart request to `/api/documents`. FastAPI identifies the user from the session cookie and checks the file "
     "type and size. It calls the extraction helpers to obtain plain text, then the topic and chunk functions, and inserts the document and chunks into SQLite. It then asks the `RAGEngine` for the user's "
     "engine, which reads the chunks joined with the document names and fits a new TF-IDF vectorizer. The response (status 201) carries the document, the number of topics and the number of chunks, which "
     "the interface turns into a toast and a list of topic chips."),
    ("seqask", "Sequence diagram: ask a question", "09_sequence_ask.png",
     "Sequence diagram of asking a question.",
     "The student types a question and sends it with Ctrl+Enter. FastAPI checks the session and rejects an empty question, then takes the cached engine or builds it (a read of the chunks happens only on a cache "
     "miss). `generate_answer` retrieves the four best chunks. The framed alternative shows the two answer paths: if an API key is configured, the context is sent to the language model; otherwise, and also when the call "
     "fails, the extractive method picks the highest-ranked sentences. The result is stored in the queries table and returned with the sources, which the interface shows as an answer bubble, a mode badge "
     "and a collapsible list of passages with their match scores."),
    ("uc", "Use case diagram", "10_use_case_diagram.png",
     "Use case diagram: one actor, eleven use cases and one optional external actor.",
     "The student is the only actor of the platform. The use cases are registering, logging in and out, uploading study material, browsing documents with their detected topics, deleting a document, asking a "
     "question, reviewing recent questions, taking a quiz, viewing the roadmap and viewing the dashboard. Asking a question can be extended by generating the answer with Claude, which involves the optional "
     "language-model provider; taking a quiz includes grading the answers and recording the topics. Every use case except registration and login needs an authenticated session, and the server answers 401 otherwise."),
    ("er", "Entity-relationship diagram", "11_er_diagram.png",
     "Entity-relationship diagram of the SQLite database.",
     "The database has five tables. `users` is the parent of `documents`, `queries` and `quiz_results` through the foreign key `user_id`; `documents` is the parent of `chunks` through `document_id`. All foreign keys "
     "cascade on delete and foreign-key checking is switched on, so deleting a document removes its chunks. `quiz_results` stores the subject and topic as text instead of referring to a document, so a roadmap "
     "survives deleting the document it came from. The topics of a document and the sources of a query are stored as JSON text."),
    ("flow", "Flowchart: answering a question", "12_flowchart_rag.png",
     "Flowchart of the core algorithm: retrieval and answer generation.",
     "The flowchart is the core algorithm of the platform. An empty question ends with error 400. Otherwise the user's index is taken from the cache or built from the stored chunks. The question is vectorised, "
     "cosine similarity is computed with every chunk, and the four best chunks with a score above zero are kept. If none remains, the fixed message \"No relevant content was found in your uploaded documents\" is "
     "returned. If an API key is configured, the question and chunks are sent to the language model with the instruction to answer using only the context; a successful call gives the answer, and a failure "
     "falls through to the extractive branch. The extractive branch splits the chunks into sentences longer than 20 characters, ranks them by TF-IDF cosine against the question, keeps the top four with a positive "
     "score (the first three sentences if none is positive) and joins them. In every case the question, answer and source file names are stored before the response is returned."),
    ("flowq", "Flowcharts: quiz generation and roadmap", "13_flowchart_quiz_roadmap.png",
     "Flowcharts of quiz generation (left) and the roadmap priority rule (right).",
     "Panel A shows quiz generation. The words of at least four letters of the document are ranked by TF-IDF and the top 40 kept; fewer than four terms means no quiz (HTTP 422). Sentences between 26 and 219 "
     "characters are shuffled; for each sentence the first term that is not used yet and occurs as a whole word is blanked at its first occurrence, three other terms become distractors, and the four options are "
     "shuffled. The loop stops after five questions or when sentences run out. Panel B shows the roadmap: quiz rows are grouped by topic, accuracy is 100 x correct / attempts, and topics below 50 percent are High, "
     "below 80 percent Medium and the rest Low; the list is sorted by priority and then by accuracy."),
]


def _dg(key):
    for k, t, f, c, x in DIAGRAMS:
        if k == key:
            return t, f, c, x
    raise KeyError(key)


def _fig_text(key, width=5.6, with_text=True):
    t, f, c, x = _dg(key)
    out = [FIG(F.diag(f), c, width)]
    if with_text:
        out.append(P(x))
    return out


ENDPOINTS = [
    ["GET", "/api/health", "{status, llm_enabled}", "-"],
    ["POST", "/api/auth/register", "In: username, password, interests. Out: message (201)", "400 empty, 409 duplicate"],
    ["POST", "/api/auth/login", "In: username, password. Out: id, username, interests; sets the session cookie", "401"],
    ["POST", "/api/auth/logout", "Clears the session", "-"],
    ["GET", "/api/auth/me", "Signed-in user, or null with HTTP 200 when nobody is signed in", "-"],
    ["GET", "/api/dashboard", "doc_count, query_count, quiz_attempts, performance[subject, accuracy, attempts], five latest documents", "401"],
    ["GET", "/api/documents", "Documents with topics and chunk_count, newest first", "401"],
    ["POST", "/api/documents", "In: multipart document and subject. Out: document, topics_count, chunks_count, warning (201)", "400 type, 413 over 16 MB"],
    ["DELETE", "/api/documents/{id}", "Deletes chunks, row and file; refreshes the index", "404"],
    ["POST", "/api/ask", "In: question. Out: answer, sources[text, score, doc_name, chunk_index], llm_enabled", "400 empty"],
    ["GET", "/api/ask/history", "The last ten questions with answer and source names", "401"],
    ["POST", "/api/quiz/generate", "In: doc_id. Out: five questions with options and topic (answers withheld)", "404, 422 too little text"],
    ["POST", "/api/quiz/submit", "In: answers (index or null per question). Out: correct, total, score_pct, per-question results", "409 no active quiz"],
    ["GET", "/api/roadmap", "Topics with subject, accuracy, attempts, priority, sorted weakest first", "401"],
]

MODULES = [
    ["backend/main.py", "430", "FastAPI application: 14 endpoints, Pydantic bodies, CORS, session middleware, helpers", "`ask`, `upload_document`, `quiz_submit`, `roadmap`"],
    ["app.py", "402", "Original Flask interface and the per-user index cache `_rag_cache`, `get_engine_for_user`", "`get_engine_for_user`"],
    ["db.py", "74", "SQLite connection, five-table schema, `init_db`, timestamp helper", "`get_db`, `SCHEMA`"],
    ["config.py", "15", "Secret key, database path, upload folder, allowed types, 16 MB limit, optional API key", "`Config`"],
    ["utils/text_extraction.py", "127", "Extraction for PDF, DOCX, TXT; cleaning; chunking; heading hints; TF-IDF topics", "`extract_text`, `chunk_text`, `extract_topics`"],
    ["utils/rag_engine.py", "120", "TF-IDF index, retrieval, extractive answer, optional Claude call", "`RAGEngine`"],
    ["utils/quiz_generator.py", "84", "Cloze question generation from TF-IDF terms", "`generate_quiz`"],
    ["frontend/src", "4,867", "Ten pages, interface kit, theme, motion, charts, API client and auth context", "`Ask.tsx`, `api.ts`, `AppShell.tsx`"],
    ["tests/", "631", "84 pytest tests with a temporary database", "`conftest.py`, `test_api.py`"],
    ["scripts/", "2,160", "Corpus builder, questions, experiments, API timing, screenshots, figures, diagrams", "`run_experiments.py`"],
    ["run.bat", "23", "Creates the virtual environment, installs packages, starts both servers", "-"],
]

PAGES = [
    ["Landing", "/", "Hero, how it works, example answer, statistics strip, light and dark theme switch"],
    ["Login, Register", "/login, /register", "Credential forms with validation messages; registered users are redirected to the app"],
    ["Dashboard", "/app", "Counters for documents, questions and quiz questions, subject-wise accuracy chart, recent documents"],
    ["Upload", "/app/upload", "File drop area, subject field, processing result with topic chips and a link to a quiz"],
    ["Documents", "/app/documents", "Searchable table with subject, topics, chunks, upload time, quiz and delete buttons"],
    ["Ask your notes", "/app/ask", "Question box, answer, mode badge, expandable sources with match score, last ten questions"],
    ["Quiz", "/app/quiz", "Document picker, five questions with four options, result with per-question review"],
    ["Study roadmap", "/app/roadmap", "Counters per priority, filter tabs, sortable table with accuracy bar and attempts"],
]


DB_COLS = [
    ["users", "id", "INTEGER, primary key", "Autoincrement identifier"],
    ["", "username", "TEXT, unique, not null", "Login name, trimmed"],
    ["", "password_hash", "TEXT, not null", "Werkzeug scrypt or PBKDF2 hash, never the password"],
    ["", "interests, created_at", "TEXT", "Free text from registration; UTC ISO timestamp"],
    ["documents", "id, user_id", "INTEGER, primary key; foreign key", "Document identifier; owner (ON DELETE CASCADE)"],
    ["", "filename, filepath", "TEXT, not null", "Secured file name; path under uploads/<user id>/"],
    ["", "subject, topics", "TEXT (topics: JSON list)", "Subject typed at upload (default 'General'); up to twelve hints and keywords"],
    ["", "uploaded_at", "TEXT, not null", "UTC ISO timestamp"],
    ["chunks", "id, document_id", "INTEGER, primary key; foreign key", "Chunk identifier; parent document (ON DELETE CASCADE)"],
    ["", "chunk_index, text", "INTEGER; TEXT, not null", "Passage number shown as the source; about 180 words"],
    ["queries", "id, user_id", "INTEGER, primary key; foreign key", "Question identifier; asking user"],
    ["", "question, answer, sources, created_at", "TEXT (sources: JSON list)", "As typed; answer returned; source file names; UTC ISO timestamp"],
    ["quiz_results", "id, user_id", "INTEGER, primary key; foreign key", "Result identifier; student"],
    ["", "subject, topic, correct, created_at", "TEXT; TEXT; INTEGER; TEXT", "Subject of the document; blanked term used as topic; 1 if correct, 0 if wrong or blank; UTC ISO timestamp"],
]

# chapter-5 blurbs: the full explanations stay in DIAGRAMS (used by the block-diagram document)
BRIEF = {
    "arch": "The browser runs the React application; the FastAPI service on port 8301 applies a CORS rule and a signed session cookie (`alip_session`, seven days) and exposes 14 JSON endpoints; "
            "the stores are `instance/app.db` and `uploads/<user id>/`. The Anthropic call and the original Flask interface (port 5000, same `db.py` and `utils/`) are optional paths.",
    "wf": "Ingestion (parse, clean, chunk, detect headings, topics, store and re-index), asking (vectorise, retrieve four chunks, select sentences or call the model, show sources) and practice "
          "(five cloze questions, server-side grading, accuracy per topic, priority thresholds at 50 and 80 percent).",
    "dfd0": "The platform is one process between the student and the optional language-model provider.",
    "dfd1": "Five processes (authenticate, analyse documents, answer questions, generate and grade quizzes, build roadmap and dashboard) read and write five stores: users, documents, chunks, queries and quiz_results.",
    "dfd2d": "Process 2.0 validates the file (type, 16 MB, safe name), saves it, extracts text, cleans and chunks it, detects headings and at most twelve topics, then stores rows and rebuilds the user's index.",
    "dfd2r": "Process 3.0 rejects an empty question, obtains the cached or freshly built index, scores chunks by cosine similarity, keeps the top four with score above zero, composes the answer "
            "(extractive, or the optional model with fallback) and logs the query.",
    "class": "`ApiService` uses `RAGEngine`, `TextExtraction`, `QuizGenerator` and `Database`; the five entities hold the same relationships as the ER diagram (a user has many documents, queries and quiz results; a document has many chunks).",
    "sequp": "The upload request passes the session and file checks, the extraction helpers produce text, topics and chunks, SQLite stores them and the user's TF-IDF engine is rebuilt before the 201 response.",
    "seqask": "The question reaches the cached engine, the four best chunks are retrieved, the answer comes from the model (if a key is configured) or from sentence selection (also on failure), and the result is stored and returned with sources.",
    "uc": "The student is the only actor; asking can be extended by the optional model, and taking a quiz includes grading. All use cases except registration and login need a session (HTTP 401 otherwise).",
    "er": "`users` parents `documents`, `queries` and `quiz_results`; `documents` parents `chunks`; all foreign keys cascade on delete. `quiz_results` keeps subject and topic as text, so a roadmap survives deleting its document.",
    "flow": "Empty question gives error 400; otherwise the index is taken from the cache or built, four chunks are retrieved, an empty result returns the fixed no-content message, and the answer is produced by the model or by sentence selection.",
    "flowq": "Quiz: top 40 TF-IDF terms, shuffled sentences of 26 to 219 characters, first unused whole-word term blanked, three distractors, five questions or until sentences run out. Roadmap: accuracy per topic, High below 50, Medium below 80, otherwise Low.",
}


def _fig_short(key, width):
    t, f, c, x = _dg(key)
    return [FIG(F.diag(f), c, width), P(BRIEF[key])]


def blocks():
    b = [H1("CHAPTER 5: SYSTEM DESIGN")]
    b += [H2("5.1 Design goals"),
          P("The design follows from the requirements of Chapter 4: answer from the student's own documents and show where the answer came from; run on one ordinary Windows PC "
            "without a graphics processor or a database server; keep each student's documents private; behave the same through the Flask pages and the JSON API; and stay simple enough to test end to end."),
          B("**One set of modules, two interfaces.** `backend/main.py` contains no retrieval, quiz or grading logic of its own; it imports `db.py`, `config.py`, `utils/*` and the index cache of `app.py`, so the two interfaces cannot disagree.",
            "**SQLite and a rebuilt index.** The data are small and written by one process, so SQLite gives transactions and cascading deletes with no installation, and the TF-IDF index (263 ms for 672 chunks) is rebuilt after each change instead of stored, so it is never stale.",
            "**Answers only from the notes.** The offline answerer selects sentences from the retrieved passages, so it cannot add words that are not in the notes; the optional model is told to use only the context. The correct quiz option stays on the server until grading.")]
    b += [H2("5.2 System architecture")] + _fig_short("arch", 5.4)
    b += [P("The contract between browser and server is narrow: JSON with a session cookie, allowed from `localhost:5301` and `127.0.0.1:5301` only. There is no message queue, vector database or background "
            f"worker; every request is synchronous, which is adequate at the measured median of {F.API['ask']['median_ms']:.1f} ms for an answer.")]
    b += [H2("5.3 High-level workflow")] + _fig_short("wf", 5.0)
    b += [H2("5.4 Data flow diagrams"), H3("5.4.1 Level 0")] + _fig_short("dfd0", 4.2)
    b += [H3("5.4.2 Level 1")] + _fig_short("dfd1", 5.0)
    b += [H3("5.4.3 Level 2: document analysis")] + _fig_short("dfd2d", 5.0)
    b += [H3("5.4.4 Level 2: answering questions")] + _fig_short("dfd2r", 5.0)
    b += [H2("5.5 UML diagrams"), H3("5.5.1 Class diagram")] + _fig_short("class", 5.4)
    b += [H3("5.5.2 Sequence diagrams")] + _fig_short("sequp", 4.4) + _fig_short("seqask", 4.4)
    b += [H3("5.5.3 Use case diagram")] + _fig_short("uc", 4.4)
    b += [H2("5.6 Database design"),
          P("The data model has five tables in `instance/app.db`, created by `db.init_db()` with `CREATE TABLE IF NOT EXISTS`. Foreign-key checking is enabled for every connection "
            "(`PRAGMA foreign_keys = ON`) and every foreign key cascades on delete. The table gives the columns as defined in `db.py`."),
          TAB("Tables and columns of the database", ["Table", "Columns", "Type and constraint", "Meaning"], DB_COLS, widths=[1.0, 1.7, 1.7, 2.3], align=["l", "l", "l", "l"], size=8.5)]
    b += _fig_short("er", 4.6)
    b += [P("Two choices in the schema have consequences. `quiz_results` records subject and topic as text, so a roadmap survives the deletion of a document, but a topic name such as \"data\" is shared by every "
            "document that yields it and its accuracy mixes attempts from all of them. And the original file is written to `uploads/<user id>/<secured name>`, so two uploads with the same name share one path: "
            "deleting one removes the file of the other while its chunks stay in the database. This is recorded by a test (Chapter 7) and listed among the limitations.")]
    b += [H2("5.7 Module design"),
          P("The retrieval and quiz logic is small: 331 lines in three files under `utils/`. The API layer is 430 lines, the original Flask application 402 lines with ten templates, and the React interface 4,867 lines of TypeScript."),
          TAB("Module breakdown", ["Module", "Lines", "Responsibility", "Key names"], MODULES, widths=[1.45, 0.55, 3.1, 1.6], align=["l", "c", "l", "l"], size=8.5),
          P("Dependencies run one way: the interfaces call `utils/` and `db.py`; `utils/` imports only scikit-learn, pypdf, python-docx and the standard library. `RAGEngine` receives chunk records as plain "
            "dictionaries, so the test suite exercises it without a database (nine tests).")]
    b += [H2("5.8 Algorithm design"), H3("5.8.1 Retrieval and answering")] + _fig_short("flow", 3.9)
    b += [P("Retrieval is lexical (TF-IDF with unigrams and bigrams) because it needs no model download, GPU or network and the index rebuilds in a fraction of a second [6], [7]. The cost is quality: "
            f"the shipped retriever reaches Hit@4 of {F.hit(F.SHIPPED, 4):.3f}, below BM25 ({F.hit('bm25', 4):.3f}) and a BM25 plus dense hybrid ({F.hit('hybrid_bm25_dense', 4):.3f}), the kinds of retriever "
            "used by the base paper [1], [5], [9]. The top_k is four so that the context stays near 720 words. The extractive answer guarantees that every word comes from the passages; the price is a loss of answer-key recall "
            f"from {F.CMP['4']['key_in_ctx']:.3f} in the passages to {F.CMP['4']['key_in_ans']:.3f} in the answer (Chapter 8). Unlike the base paper, there is no question classifier, sub-question "
            "decomposition, reranker or model-based compression [1], [11], [15].")]
    b += [H3("5.8.2 Quiz generation and roadmap")] + _fig_short("flowq", 5.4)
    b += [P("The quiz generator needs no language model, but only the first occurrence of a blanked term is removed, a distractor may fit the sentence as well, and a sentence may begin in the middle of a thought. "
            "The roadmap uses fixed thresholds of 50 and 80 percent on one signal, the share of correct answers per topic: a transparent rule, not a learner model such as knowledge tracing [17] used by tutoring systems [2].")]
    b += [H2("5.9 API design"),
          P("Request bodies are Pydantic models (`RegisterBody`, `LoginBody`, `AskBody`, `QuizGenerateBody`, `QuizSubmitBody`), so a missing or mistyped field is reported with status 422 before any code runs. "
            "Every route except health, register, login, logout and `me` depends on `current_user`, which answers 401 when the session has no user. Interactive documentation is generated at `/api/docs`."),
          TAB("Endpoints of `backend/main.py`", ["Method", "Path", "Request and response", "Errors"], ENDPOINTS, widths=[0.65, 1.55, 3.4, 1.1], align=["c", "l", "l", "l"], size=8.5),
          P("Errors use the standard `detail` field, which the front end turns into a sentence; a network failure produces \"Can't reach the server. Check that the backend is running on port 8301\". "
            "The client sends cookies with every request, and a 401 on a protected page sends the user to the login page and back after sign-in.")]
    b += [H2("5.10 User interface design"),
          P("The React interface follows the *Aurora Glass* design kit: translucent glass cards over a soft gradient backdrop, violet and cyan accents, a sidebar that becomes a drawer on small screens, and a light and a dark theme "
            "sharing one set of colour tokens (stored under `alip-theme`, defaulting to the system preference)."),
          TAB("Pages of the React application", ["Page", "Route", "Content"], PAGES, widths=[1.3, 1.2, 4.2], align=["l", "l", "l"], size=9),
          B("**States and feedback.** Every data page has loading, empty and error states, and a 401 redirects to login. Toasts confirm uploads (\"12 topics detected, 4 chunks indexed\"), quiz submissions and errors; a badge tells whether an answer came from the offline mode or from Claude.",
            "**Charts and layout.** Subject accuracy is a bar chart in three colours (below 50, 50 to 79, 80 and above). The layout was captured at 1440, 768 and 360 pixels in both themes with no console error and no horizontal overflow (Chapter 7), and every page is a lazy chunk (the largest, the landing page, is 18.5 kB before compression)."),
          PAIR([(F.shot("07_dashboard.png"), "Dashboard with counters, subject accuracy and recent documents."),
                (F.shot("09_ask.png"), "Ask your notes: answer, offline-mode badge and sources.")], 3.0),
          P("There is no administrator interface, teacher view, notification or revision calendar; these are listed as future work in Chapter 10.")]
    return b
