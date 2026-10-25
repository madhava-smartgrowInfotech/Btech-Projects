"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis)."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB


def blocks():
    return chapter3() + chapter4()


def chapter3():
    E = F.ENV
    api = F.API
    sc = F.SCALE
    ask_ms = api["ask"]["median_ms"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built, whether it is worth building and whether it can be used. This chapter answers the three questions for the "
          "Adaptive Learning Intelligence Platform from what was built and measured, and adds a plan of the work. No monetary figures are given: the project had no budget line, "
          "and an invented estimate would be decoration rather than evidence."),

        H2("3.1 Technical Feasibility"),
        P("The technology is mature, free and runs on an ordinary desktop. The system was built, tested and measured on one machine: " + E["cpu"] + ", " + E["ram"] + " of memory, " + E["os"] +
          ", with no graphics processor. The table lists each component with its measured version and the evidence that it is sufficient."),
        TAB("Technical feasibility by component", ["Component", "Technology (version used)", "Evidence that it is feasible"],
            [["Document parsing", f"pypdf {E['pypdf']}, python-docx {E['python-docx']}", "PDF text layers, DOCX paragraphs and plain text are extracted; a corrupt PDF is reported without raising an error (unit tests)"],
             ["Retrieval", f"scikit-learn {E['sklearn']}, numpy {E['numpy']}", f"TF-IDF index of {F.CORPUS['chunks']} chunks ({F.CORPUS['words']:,} words) is built in {sc[0]['index_build_ms']:.0f} ms and answers a query in {sc[0]['retrieve_ms_median']:.1f} ms (median)"],
             ["Quiz and roadmap", "Python standard library, scikit-learn", f"A five-question quiz is generated in {F.QUIZ['gen_ms_median']:.1f} ms (median, in process); the roadmap rules are plain arithmetic"],
             ["Serving API", f"FastAPI {E['fastapi']}, uvicorn {E['uvicorn']}, Flask {E['flask']}", f"/api/ask answers in {ask_ms:.1f} ms (median) over HTTP on localhost with {F.CORPUS['chunks']} chunks indexed"],
             ["Storage", "SQLite (Python standard library)", "Five tables, no server process, foreign keys with cascading deletes"],
             ["Web interface", f"React {E['react']}, Vite {E['vite']}, Tailwind {E['tailwind']}, Node {E['node']}", "Production build (type check and bundle) completes in 8.7 s; ten pages, each a separate lazy chunk below 20 kB"]],
            widths=[1.3, 2.1, 3.3], align=["l", "l", "l"], size=9.5),
        P("Three technical risks were found. First, the retrieval index is not stored: it is rebuilt in memory from the chunk table after every upload or deletion, which keeps it consistent with the "
          f"database but costs more as the text grows ({sc[0]['chunks']} chunks take {sc[0]['index_build_ms']:.0f} ms, {sc[3]['chunks']:,} chunks take {sc[3]['index_build_ms']:.0f} ms): acceptable for one student's notes, "
          "not for a shared index of a whole institution. Second, the per-user index cache and the active quiz live in the memory of one server process, so several worker processes would need a shared store. "
          "Third, the offline answerer returns sentences from the notes rather than composing text; the optional Claude integration was implemented but not measured because no API key was available."),
        P("Data is the other constraint. Real student notes require the consent of their owners and none were available, so the measurements use a six-subject corpus of "
          f"{len(F.CORPUS['documents'])} files built from public encyclopaedia articles [18] (Chapter 8); the screenshots use the bundled sample notes plus four of those files."),

        H2("3.2 Economic Feasibility"),
        P("The system consumes almost nothing that has to be bought. Every component is free and open source, no graphics processor is needed, and the evaluation corpus of about 100,000 words "
          "fits in a few hundred kilobytes of SQLite rows."),
        TAB("Cost items", ["Item", "Requirement", "Observation from this work"],
            [["Hardware", "One ordinary PC or small server, CPU only", "All measurements on a desktop with a 6-core processor and 15.7 GB of memory; smaller machines were not tested"],
             ["Software and data", "No licences; students' own documents", "All libraries are open source; the evaluation corpus is freely licensed (CC BY-SA 4.0)"],
             ["Language model", "Optional", "Used only when ANTHROPIC_API_KEY is set and paid per use by the provider; every answer in this report is from the offline mode"],
             ["Effort", "Students and a guide", f"{F.LOC['application (9 Python files)']:,} lines of Python and {F.LOC['frontend (53 TS/TSX files)']:,} lines of TypeScript, protected by {F.TESTS['tests']} automated tests"]],
            widths=[1.3, 2.0, 3.4], align=["l", "l", "l"], size=9.5),
        P("The benefit is qualitative: a student saves the time of searching scattered files and receives an answer that names its file and passage. Whether this improves learning outcomes was not measured; "
          "there was no user study and the report does not claim it."),

        H2("3.3 Operational Feasibility"),
        P("The users are students, and the system asks them to do four things they already do: upload notes, ask questions, practise and read a summary. There is one user role and no administrator, so no operational staff are needed."),
        B("**Setup and learning curve.** `run.bat` creates the virtual environment, installs the packages and starts both servers; a demo account is documented in the README. The sidebar has six entries and every page has loading, empty and error states in plain language.",
          "**Device fit and offline use.** The layout was captured without console errors at 1440, 768 and 360 px in light and dark themes. Answers work without a network or an API key; a badge reads \"Offline mode: key sentences from your notes\".",
          "**Limits.** There is no password reset, no e-mail and no administrator view; a forgotten password cannot be recovered."),

        H2("3.4 Schedule Feasibility"),
        P("The plan of work is given as phases with indicative week numbers. It is a plan, not a record: the repository history holds no dated milestones for each phase, and none are claimed."),
        TAB("Plan of work (indicative weeks)", ["Phase", "Weeks", "Work", "Output"],
            [["1", "1 - 2", "Problem identification, reading of the base paper [1] and related work, objectives", "Abstract, introduction, literature survey, objectives"],
             ["2", "3 - 6", "Document extraction, chunking, topic detection, TF-IDF retrieval, quiz and roadmap rules, Flask pages", "Working original application on SQLite"],
             ["3", "7 - 9", "FastAPI layer over the same modules, React interface with light and dark themes", "Ports 8301 and 5301, 14 endpoints, ten pages"],
             ["4", "10 - 11", "Test suite, evaluation corpus and questions, retrieval, compression and latency measurements", f"{F.TESTS['tests']} tests, experiments/results.json"],
             ["5", "12", "Screenshots, diagrams, decks, report and paper", "Submission documents"]],
            widths=[0.5, 0.7, 3.5, 2.0], align=["c", "c", "l", "l"], size=9.5),

        H2("3.5 Legal, Ethical and Data Feasibility"),
        B("**Licences and data.** All libraries are open source. The evaluation corpus is English Wikipedia text under CC BY-SA 4.0 [18], each article pinned to a revision in `experiments/corpus_manifest.json`.",
          "**Personal data.** Passwords are stored as salted hashes (scrypt or PBKDF2 through Werkzeug). Notes, questions and quiz results are stored unencrypted, and there is no retention policy or account deletion.",
          "**Copyright and third parties.** A student may upload copyrighted textbooks; documents are private to their owner (covered by tests) but there is no copyright check. If the optional language model is enabled, the question and passages are sent to an external provider; the default is off."),

        H2("3.6 Risk Analysis"),
        TAB("Risks and mitigation", ["Risk", "Likelihood and impact", "Mitigation, or remaining gap"],
            [["Answer drawn from an irrelevant passage", "High for off-topic questions; 9 of 12 were still answered", "Source file, passage and match score shown with every answer; a score threshold of about 0.12 to 0.15 is proposed, not implemented"],
             ["Retrieval misses the right passage", f"Hit@4 is {F.hit(F.SHIPPED, 4):.3f}: about one question in five fails", "Compared with BM25 and dense retrieval; hybrid retrieval proposed as future work"],
             ["Poor quiz questions", f"Only {F.AUDIT['summary']['acceptable']} of {F.AUDIT['summary']['n']} reviewed questions were acceptable", "Quiz is a practice aid; the review shows the correct term"],
             ["No extractable text (scan); data loss; single-process state", "Medium; medium; low for a demo", "Upload warns and returns zero chunks (no OCR); one SQLite file, no backup feature; a shared cache would be needed for deployment"]],
            widths=[1.9, 2.0, 2.8], align=["l", "l", "l"], size=9.5),

        H2("3.7 Advantages and Constraints"),
        TAB("Advantages and constraints of the proposed system", ["Advantages", "Constraints"],
            [["Free, open-source stack; no GPU needed", "Lexical TF-IDF retrieval, not learned embeddings"],
             ["Answers cite the file, passage and match score", "No relevance threshold: off-topic questions still receive an extract"],
             ["Works offline; optional Claude mode", "Claude mode not measured"],
             ["Per-user private repository", "Single role, no administrator, no password reset"],
             [f"{F.TESTS['tests']} automated tests and a {F.SMOKE_TOTAL}-check API smoke test", "Headings recognised only as \"Subject:\", \"Course:\", \"Unit N:\", \"Chapter N:\""],
             ["Responsive light and dark interface", "No spaced-repetition schedule or coverage tracking"]],
            widths=[3.35, 3.35], align=["l", "l"], size=10),
        P("**Conclusion of the study.** The system is technically, economically and operationally feasible as a prototype that students run on their own machine "
          f"(median answer time {ask_ms:.0f} ms, {F.TESTS['tests']} tests passing). The legal position is feasible with caveats: notes are stored unencrypted and the copyright of uploads is not checked. "
          "A shared deployment would be feasible only after the process-local state is externalised, the index is cached rather than rebuilt, a relevance threshold is added and a data-protection policy is written."),
    ]


def chapter4():
    E = F.ENV
    api = F.API
    t = F.TESTS
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter analyses the problem as it stands, states what the proposed system must do and how well, and lists the hardware, software and people involved. "
          "Requirement identifiers (FR for functional, NR for non-functional) are used again in Chapters 5 and 7."),

        H2("4.1 Existing System and its Limitations"),
        P("Each semester brings a student six to eight subjects, and the material (syllabi, timetables, lecture notes, question banks) is spread over many PDF and word-processor files. "
          "Conventional e-learning portals store and list these files but do not read what is inside. A general chat assistant explains concepts, yet answers from public text rather than the student's "
          "own syllabus and may state a wrong answer with confidence when it is not grounded in a source [4]."),
        P("The base paper [1] proposes SAC-RAG, which classifies a question as fact, definition or reasoning, retrieves differently for each type and compresses the retrieved text with a language model; "
          "it is evaluated on three multi-hop question-answering benchmarks [13], not on educational documents. Tutoring work combines retrieval with learner modelling [2] or assessment [3], but none of the "
          "works in the batch literature table combines document ingestion, syllabus-grounded answers and progress analytics for a student's own curriculum."),
        TAB("Limitations of the existing situation", ["No.", "Limitation", "Consequence for the student"],
            [["L1", "Files are stored but their content is not analysed", "Subjects, units and topics must be found by hand"],
             ["L2", "Keyword search inside one PDF only", "A question needs several files opened one by one"],
             ["L3", "General chatbots answer from public text", "Answers may not match the syllabus and carry no source"],
             ["L4", "Recommendations are identical for every learner", "Prior performance and behaviour are ignored"],
             ["L5", "No single view of what has been studied or understood", "Weak topics are noticed late"],
             ["L6", "Practice questions are written by hand", "Little practice on one's own material"]],
            widths=[0.5, 2.9, 3.3], align=["c", "l", "l"], size=10),

        H2("4.2 Proposed System and its Advantages"),
        P("The proposed system is a web platform in which a student uploads PDF, DOCX or TXT files. It extracts the text, splits it into overlapping passages of 180 words (30 words "
          "of overlap), detects subject and unit headings, derives up to twelve TF-IDF topics per document and stores everything in a private repository. A question is answered by "
          "retrieving the four most similar passages (TF-IDF, cosine similarity), selecting the key sentences and listing the source file, passage number and match score. Five fill-in-the-blank "
          "questions can be generated from any document; graded answers feed a roadmap that ranks topics from weakest to strongest and a dashboard of uploads, questions and accuracy per subject."),
        TAB("Advantages over the existing situation", ["Limitation", "Feature of the proposed system", "Evidence in this work"],
            [["L1, L2", "Upload analysis and a searchable repository", f"All {F.DOCAN['per_file'][0]['units_in_file'] * 6} unit headings of the corpus found; hit@4 of {F.hit(F.SHIPPED, 4):.3f} on 72 questions"],
             ["L3", "Answers built only from the student's passages, with source and score", "Every word of the offline answer comes from the retrieved passages (measured: 100 %)"],
             ["L4, L5", "Quiz results per topic drive the roadmap and dashboard", f"{F.TESTS['tests']} tests including ten priority-threshold cases"],
             ["L6", "Automatic cloze questions", f"{F.QUIZ['generated']} of {F.QUIZ['requested']} requested questions generated, all structurally valid"]],
            widths=[0.9, 2.9, 2.9], align=["c", "l", "l"], size=9.5),
        P("The proposed system does not claim to reproduce SAC-RAG. It has no question-type classifier, no learned embeddings, no cross-encoder reranking and no language-model compression: "
          "its retrieval is lexical and its only compression is the selection of sentences. These differences are measured in Chapter 8 and listed as limitations in Chapter 9."),

        H2("4.3 Functional Requirements"),
        P("The table lists each functional requirement, the endpoint or page that implements it and the test evidence (files in `tests/`; final run "
          f"{t['tests']} tests, {t['failures']} failed, {t['seconds']:.1f} s; plus the {F.SMOKE_TOTAL}-check API smoke test)."),
        TAB("Functional requirements", ["ID", "Requirement", "Implemented by", "Evidence"],
            [["FR1", "Register with a username and password; reject empty and duplicate names", "POST /api/auth/register; Register page", "test_register_validation, test_duplicate_username_rejected"],
             ["FR2", "Log in and out with a session; reject wrong passwords; protect every data route", "POST /api/auth/login, /logout, GET /me", "test_register_login_me_logout, wrong-password test, 9 protected-route cases"],
             ["FR3", "Upload PDF, DOCX or TXT up to 16 MB with an optional subject; reject other types", "POST /api/documents; Upload page", "upload, DOCX, unsupported-type and 16 MB tests"],
             ["FR4", "Extract text, split into 180-word chunks with 30 overlap, detect headings, derive up to 12 topics", "utils/text_extraction.py", "15 tests in test_text_extraction.py"],
             ["FR5", "List documents with topics and chunk counts; delete a document with its chunks and file", "GET, DELETE /api/documents", "delete test, user-isolation test"],
             ["FR6", "Answer from the user's own passages and show source file, passage number and score", "POST /api/ask; Ask page", "ask-with-sources test, 9 tests in test_rag_engine.py"],
             ["FR7", "Keep the last ten questions", "GET /api/ask/history", "test_history_is_capped_at_ten"],
             ["FR8", "Generate five cloze questions from a document, keeping answers on the server", "POST /api/quiz/generate", "4 tests in test_quiz_generator.py, quiz-flow test"],
             ["FR9", "Grade a submitted quiz once and store per-topic results", "POST /api/quiz/submit", "100-percent-score and no-double-submit tests"],
             ["FR10", "Rank topics High (<50 %), Medium (<80 %), Low by accuracy", "GET /api/roadmap; Roadmap page", "10 threshold cases, sort-order test"],
             ["FR11", "Show counts, accuracy per subject, five recent documents", "GET /api/dashboard; Dashboard page", "new-user dashboard test, quiz-flow test"],
             ["FR12", "Optional Claude answers when ANTHROPIC_API_KEY is set, with fallback to offline answers", "RAGEngine._llm_answer", "two mocked tests (live mode not measured)"],
             ["FR13", "Light and dark theme, responsive layout from 360 px", "frontend theme tokens", "Playwright capture: console clean, no horizontal overflow"]],
            widths=[0.45, 2.45, 1.75, 2.05], align=["c", "l", "l", "l"], size=8.5),

        H2("4.4 Non-functional Requirements"),
        TAB("Non-functional requirements", ["ID", "Requirement", "Target", "Measured or verified"],
            [["NR1", "Response time of question answering", "Under one second", f"/api/ask median {api['ask']['median_ms']:.1f} ms, p95 {api['ask']['p95_ms']:.1f} ms with {F.CORPUS['chunks']} chunks"],
             ["NR2", "Response time of data pages", "Under 100 ms", f"dashboard {api['dashboard']['median_ms']:.1f} ms, documents {api['documents_list']['median_ms']:.1f} ms, roadmap {api['roadmap']['median_ms']:.1f} ms (median)"],
             ["NR3", "Scalability of retrieval", "Roughly linear", f"{F.SCALE[0]['retrieve_ms_median']:.1f} ms at {F.SCALE[0]['chunks']} chunks, {F.SCALE[3]['retrieve_ms_median']:.1f} ms at {F.SCALE[3]['chunks']:,}"],
             ["NR4", "Password protection", "Salted hash", "test_passwords_are_stored_hashed"],
             ["NR5", "Session security", "HttpOnly, SameSite, signed", "HttpOnly, SameSite=Lax verified; not Secure (local use); tampered cookie rejected"],
             ["NR6", "Isolation between users", "No cross-user access", "Tests on list, delete, quiz and ask across two users"],
             ["NR7", "Input safety", "No injection or traversal", "SQL-injection strings stored literally; \"../../evil.txt\" saved as evil.txt in the user folder"],
             ["NR8", "Offline operation", "No external service", "All measurements taken without an API key"],
             ["NR9", "Portability", "Windows, CPU only, one command", "run.bat; measured on Windows 11 with no GPU"],
             ["NR10", "Maintainability", "Automated tests", f"{t['tests']} pytest tests in about {t['seconds']:.0f} s; {F.SMOKE_TOTAL}-check smoke test; type-checked front end"],
             ["NR11", "Usability", "Clear states and errors", "Loading, empty and error states on every data page"]],
            widths=[0.5, 1.9, 1.5, 2.8], align=["c", "l", "l", "l"], size=8.5),
        P(f"Login takes about {api['login']['median_ms']:.0f} ms because the password hash is deliberately slow. `quiz_submit` has a median of {api['quiz_submit']['median_ms']:.1f} ms but showed "
          "outliers of one to two seconds on one or two of every thirty calls, attributed to SQLite commits on the shared test machine but not isolated further."),

        H2("4.5 Data Requirements"),
        B("**Inputs and storage.** PDF with a text layer, DOCX (paragraph text only) or UTF-8 text, up to 16 MB, with an optional subject; headings \"Subject:\", \"Course:\", \"Unit N:\" or \"Chapter N:\" (Arabic numerals) are recognised. "
          "One row per user, document, chunk, question and quiz answer is kept in SQLite (Section 5.6), and the original file under `uploads/<user id>/`.",
          f"**Evaluation data.** {len(F.CORPUS['documents'])} notes files, {F.CORPUS['words']:,} words and {F.CORPUS['chunks']} chunks built from 36 encyclopaedia articles [18], 72 hand-written questions (24 each of fact, definition and reasoning) with gold evidence sentences, and 12 off-topic questions. "
          "The demonstration file `sample_data/sample_notes_data_structures.txt` has 619 words and four chunks, and always yields a five-question quiz."),

        H2("4.6 Hardware Requirements"),
        B(f"**Used for development and measurement:** {E['cpu']}, {E['ram']} of memory, {E['gpu']}, local SSD; screens checked at 1440 x 900, 768 and 360 px.",
          "**Required:** any modern 64-bit CPU (weaker processors were not tested), enough memory to hold the index (5,376 chunks, about 960,000 words, were indexed in the scaling experiment), "
          "space for uploads (16 MB each at most) and the SQLite file, and a browser window from 360 px wide. No graphics processor."),

        H2("4.7 Software Requirements"),
        TAB("Software", ["Layer", "Software", "Version"],
            [["Platform", "Windows 11 Pro; Python; SQLite", f"Python {E['python']}; SQLite bundled; Python code is portable"],
             ["Retrieval, quiz, parsing", "scikit-learn, numpy, pypdf, python-docx", f"{E['sklearn']}, {E['numpy']}, {E['pypdf']}, {E['python-docx']}"],
             ["Interfaces", "Flask, Werkzeug; FastAPI, uvicorn, python-multipart, itsdangerous", f"{E['flask']}, 3.0.3; {E['fastapi']}, {E['uvicorn']}, 0.0.9, 2.2.0"],
             ["Front end", "Node, React, Vite, Tailwind CSS", f"{E['node']}, {E['react']}, {E['vite']}, {E['tailwind']}"],
             ["Testing", "pytest, httpx, Playwright with Chrome", "8.3.3, 0.27.2, 1.44.0"],
             ["Optional", "anthropic package and API key", "Not used for any reported measurement"]],
            widths=[1.5, 3.2, 2.0], align=["l", "l", "l"], size=10),

        H2("4.8 User Roles"),
        P("There is one role: the student. A registered user has a private space containing documents, questions, quizzes and roadmap. There is no administrator, no teacher view and no "
          "public sharing. The boundary is enforced in the server: every query that reads or changes documents, chunks, questions or quiz results is filtered by the identifier of the logged-in user."),

        H2("4.9 Constraints and Assumptions"),
        B("The user's files contain extractable text: scanned images are not read (no OCR) and DOCX tables are ignored. Questions are in English and the stop-word list is English.",
          "The notes of one user fit in memory and the index is rebuilt after every upload or deletion; the server runs as one process, so the quiz in progress and the index cache are not shared between workers.",
          "The system is used on localhost or a trusted network (cookies are not marked Secure), and quiz accuracy is the only signal of mastery: there is no timing, repeated-attempt model or revision schedule."),

        H2("4.10 Analysis Summary"),
        TAB("Traceability of the batch objectives", ["Objective", "Requirements", "Status in the built system"],
            [["1. Ingest syllabi, notes and question banks; extract subjects, units, topics", "FR3, FR4, FR5", "Partly met: three file types; headings only in four formats; at most 12 topics"],
             ["2. Store as vector embeddings for semantic search", "(not a requirement of the design)", "Not met: TF-IDF sparse vectors; dense retrieval measured only as an experiment"],
             ["3. Answer strictly from the material and cite the source", "FR6, FR7, FR12", "Met for the offline mode (every answer word is from the passages); no relevance threshold"],
             ["4. Compress the context within the model window", "FR6", "Partly met: sentence selection removes 87.5 % of the words, with a loss of answer-key recall"],
             ["5. Personalised roadmaps and revision schedules", "FR8, FR9, FR10", "Partly met: priority roadmap from quiz accuracy; no revision schedule"],
             ["6. Dashboard of coverage, velocity and engagement", "FR11", "Partly met: counts and subject accuracy; no coverage or velocity"]],
            widths=[2.6, 1.3, 2.8], align=["l", "c", "l"], size=9.5),
        P("The analysis leads to a design with three parts: an ingestion pipeline that turns files into chunks and topics, a retrieval and answering engine over a per-user index, and a practice loop "
          "that turns quiz results into a roadmap. Every functional requirement has at least one automated check. The requirements implied by the batch objectives but not met by the design "
          "(semantic embeddings, model-based compression, revision schedules, coverage and velocity metrics) are carried to Chapters 9 and 10 as limitations and future work."),
    ]
