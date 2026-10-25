"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB

SH = F.SHIPPED


def _chunks_row(key):
    r = F.CHUNKS[key]
    return [key, f"{r['chunks']:,}", f"{r['mean_words']:.0f}"]


def methodology_blocks():
    C = F.CORPUS
    shipped = F.RET[SH]
    b = []
    b += [H2("6.1 Overall methodology"),
          P("The platform is a document-analysis and retrieval pipeline followed by two small adaptive components, a quiz generator and a roadmap builder. The design follows the retrieve-then-generate idea of retrieval-augmented generation [4] and adopts from the base paper [1] "
            "the view that retrieval and context compression are separate stages whose joint effect on answer quality and context size must be measured. It does not adopt the base paper's learned components (an LLM question "
            "classifier, dense retrieval with a cross-encoder reranker, an LLM compressor), for the reasons given in Section 6.4. The steps are:"),
          N("**Ingest.** Accept a PDF, DOCX or TXT file of at most 16 MB, store the original under `uploads/<user id>/`, and extract plain text (Section 6.3).",
            "**Analyse.** Clean the text, detect subject and unit headings with regular expressions, and rank keywords by TF-IDF to obtain at most twelve topics per document.",
            "**Chunk and index.** Cut the text into windows of 180 words with an overlap of 30 words, store them in SQLite and rebuild the user's in-memory TF-IDF index.",
            "**Retrieve.** Vectorise the question, compute the cosine similarity with every chunk and keep the four best chunks with a positive score.",
            "**Answer.** Select the four sentences of the retrieved chunks that are most similar to the question (extractive mode), or, when an API key is configured, send the question and the chunks to an LLM with the instruction to use only the context.",
            "**Practise.** Build five fill-in-the-blank questions from a document, grade the submission on the server and store one result row per question.",
            "**Adapt.** Group the results by topic, compute the accuracy of each topic and label it High, Medium or Low priority."),
          P(f"To judge the pipeline, and not only to describe it, an experimental protocol was run on a six-subject corpus with {C['questions']} hand-written questions (Sections 6.2 and 6.6); it is the source of every number in Chapters 7 and 8.")]

    b += [H2("6.2 Dataset"),
          P("The product itself needs no training data: TF-IDF is fitted on the user's own documents at run time. The project therefore has no training, validation and test split in the machine-learning sense. Two document sets are used."),
          P("**Bundled sample notes.** `sample_data/sample_notes_data_structures.txt` is a 619-word note on data structures written for the project (a `Subject:` line, five `Unit n:` headings and a list of important questions; 4 chunks). It is used for the demonstration and most unit tests."),
          P("**Evaluation corpus.** To measure retrieval and answering at realistic volume, `scripts/fetch_corpus.py` builds six subject files from 36 English Wikipedia articles (CC BY-SA 4.0 [18]). Each file starts with `Subject: ...` and each article becomes a `Unit n: <title>` section, the layout that the document analyser recognises. "
            "Articles are pinned to revision identifiers in `experiments/corpus_manifest.json`, mathematical markup is removed and each is cut at 3,200 words, so the corpus can be rebuilt exactly. Wikipedia is better organised than typical lecture notes, which probably makes retrieval easier than on real material."),
          TAB("Evaluation corpus", ["File (subject)", "Articles", "Words", "Chunks (180/30)"],
              [[d["subject"], "6", f"{d['words']:,}", str(d["chunks"])] for d in C["documents"]]
              + [["Total", "36", f"{C['words']:,}", f"{C['chunks']:,}"]],
              widths=[2.4, 0.9, 1.2, 1.4], align=["l", "c", "r", "r"], size=10),
          P(f"**Questions.** Seventy-two questions were written by hand, twelve per subject and twenty-four for each of three types that follow the taxonomy of the base paper [1]: fact (When, Which, How many), definition (What is, Define) and reasoning (Why, How). "
            f"The type is assigned from the wording of the question. For each question the gold evidence is a sentence fragment copied from the corpus; a script confirms that every fragment occurs exactly once in its subject file, and that each lies wholly inside at least one chunk "
            f"({C['evidence_intact_in_a_chunk']} of {C['questions']}). A retrieved chunk counts as a hit when it contains the evidence after whitespace and case normalisation. Each question also carries one to three short answer strings, "
            f"used to test whether a generated answer contains the expected fact. In addition {C['off_topic_questions']} off-topic questions (sport, cooking, geography and similar) test whether the system refuses to answer when nothing relevant has been uploaded."),
          P("All seventy-two questions are test questions: nothing is trained and the shipped parameters were fixed before the questions were written; the sweeps of Chapter 8 are sensitivity analyses, not tuning. "
            "With 72 questions the confidence intervals are wide, so the bootstrap interval is stated wherever the shipped scores are quoted.")]

    b += [H2("6.3 Pre-processing"),
          P("`utils/text_extraction.py` holds all pre-processing. Each step is a small, separately tested function."),
          TAB("Pre-processing steps", ["Step", "Function", "Behaviour"],
              [["Text extraction", "`extract_text`", "PDF: `pypdf.PdfReader`, text of every page (a page that fails is skipped). DOCX: text of every paragraph (table cells are not read). TXT: UTF-8, undecodable bytes ignored. Any exception returns the string `[Could not extract text: ...]`."],
               ["Chunking", "`chunk_text`", "Splits on whitespace and forms windows of 180 words that advance by 150 words (overlap 30). The last window may be shorter."],
               ["Heading detection", "`detect_subject_hints`", "Four case-insensitive patterns: `Subject:`, `Course:`, `Unit <digits> :|-`, `Chapter <digits> :|-`. Hints longer than 120 characters are dropped, duplicates removed, at most 15 kept."],
               ["Topic extraction", "`extract_topics`", "TF-IDF (unigrams and bigrams, English stop words, at most 500 features) over the sentences longer than 15 characters; terms ranked by summed weight; headings first, keywords after; at most 12 topics."],
               ["File validation", "`allowed_file`", "The extension must be pdf, docx or txt (case-insensitive); the size must not exceed 16 MB."]],
              widths=[1.2, 1.4, 4.0], align=["l", "l", "l"], size=9.5),
          P(f"Chunking by word count is deliberately naive: a window can begin or end in the middle of a sentence. The overlap limits the damage for retrieval: with the shipped setting all {C['questions']} gold evidence fragments lie wholly inside at least one chunk, whereas with 60-word windows "
            f"{C['questions'] - F.CHUNKS['60/15']['evidence_intact']} are split. Heading detection recognises only Arabic numerals (`Unit 1:`, `Unit 1 -`, `Chapter 1:`); `UNIT-I`, `Unit I:`, `Module 1:` and `1. Title` are not found "
            f"({F.DOCAN['heading_formats']['Unit 1: Title']['units_found']} of {F.DOCAN['heading_formats']['Unit 1: Title']['of']} units for the first style, {F.DOCAN['heading_formats']['UNIT-I Title']['units_found']} of {F.DOCAN['heading_formats']['UNIT-I Title']['of']} for the second). "
            f"On the evaluation corpus all {sum(f['units_in_file'] for f in F.DOCAN['per_file'])} unit headings are found because the corpus uses the recognised layout.")]

    b += [H2("6.4 Algorithm choice and justification"),
          P("The project brief asks for semantic retrieval and context compression in the manner of the base paper [1]. The implemented algorithms are simpler, and the choice was made on four criteria: the system must run on an ordinary laptop with no GPU and no download; "
            "it must be free to run (no API cost); every answer must be traceable to a passage the student can read; and the code must be small enough for a four-student team to test completely. The table below lists each decision and the alternative that was not taken."),
          TAB("Algorithm decisions", ["Component", "Chosen", "Reason", "Not chosen and why"],
              [["Retrieval", "TF-IDF (1-2 grams) with cosine similarity, scikit-learn [16]", "Offline, no model download, fits in milliseconds, scores are inspectable (the interface shows the match score)", "Dense embeddings [5], [9]: need a model download and more memory; measured in Chapter 8 as a reference and not shipped. BM25 [6]: better in the measurements, not adopted in the product (Section 6.6)"],
               ["Answer", "Extractive: top four sentences by TF-IDF similarity to the question", "Cannot invent text; the answer is made only of the student's own sentences", "Abstractive generation: needs an LLM and a key. It exists as an optional branch (Anthropic API) but was not measured"],
               ["Compression", "The sentence selection itself", "Reduces the context shown or sent to the generator without a second model", "LLM compression as in SAC-RAG [1], LLMLingua [10], RECOMP [15]: cost, latency and a key"],
               ["Question types", "None: one strategy for every question", "Keeps the pipeline linear and easy to test", "Question-type routing as in SAC-RAG [1] and Adaptive-RAG [11]: needs a classifier; per-type results are only reported, not used"],
               ["Quiz", "Cloze questions on TF-IDF terms with random distractors from the same document", "Works offline on any document and needs no answer key", "LLM-written multiple-choice questions: cost and unverifiable quality"],
               ["Roadmap", "Per-topic accuracy with fixed thresholds 50 and 80", "Transparent rule a student can understand", "Knowledge tracing [17] as in TutorLLM [2]: needs response sequences and a trained model"]],
              widths=[0.9, 1.6, 2.0, 2.1], align=["l", "l", "l", "l"], size=9),
          P("Two of these choices are weaker than the stated objectives. Retrieval is lexical, so a question that shares no word with the passage cannot find it; the brief's phrase 'searched semantically rather than by keyword' is therefore not satisfied by the shipped code. "
            "And the compression is extractive and unconditioned on the question type, so it has no counterpart to the adaptive behaviour that is the main contribution of the base paper. These gaps are measured, not hidden, in Chapters 8 and 9."),
          P("The index is rebuilt from all of the user's chunks after every upload or deletion and is kept in a dictionary keyed by user, `_rag_cache`, inside the Python process. It is not persisted: after a restart it is rebuilt on the first question.")]

    b += [H2("6.5 Mathematical formulation"),
          H3("6.5.1 TF-IDF and cosine similarity"),
          P("Let the index contain n chunks and let df(t) be the number of chunks that contain term t, where a term is a unigram or bigram after stop-word removal. scikit-learn [16] uses the smoothed inverse document frequency and L2-normalised vectors:"),
          EQ("idf(t) = ln((1 + n) / (1 + df(t))) + 1;     w(t, d) = tf(t, d) x idf(t);     v_d = w(., d) / ||w(., d)||"),
          P("The query q is transformed with the same vocabulary and idf, giving v_q. Because both vectors have unit length, the cosine similarity is a dot product, and chunks are ranked by it:"),
          EQ("score(q, d) = cos(v_q, v_d) = v_q . v_d,     0 <= score <= 1"),
          P("The four chunks with the highest positive score form the retrieved set R. A term that is absent from the vocabulary does not contribute, so a question whose terms all fall outside the vocabulary has score zero for every chunk and returns no result."),
          H3("6.5.2 Extractive answer"),
          P("Let S be the sentences (longer than 20 characters) of the chunks in R. A second TF-IDF model is fitted on the list [q] + S, and the answer is made of the four sentences with the largest positive cosine similarity to q:"),
          EQ("answer(q) = join( top4{ s in S : cos(v_q, v_s) > 0 } )"),
          P("If no sentence scores above zero the first three sentences are returned; if there are none, the first 500 characters of the best chunk. The answer contains no word that is absent from R (verified in Chapter 8) and is about 90 words long whatever the question, because four sentences are always selected."),
          H3("6.5.3 Evaluation measures"),
          P("For question i let r_i be the rank of the first retrieved chunk that contains the gold evidence, or infinity if none of the first ten does. With N = 72 questions:"),
          EQ("Hit@k = (1 / N) x #{ i : r_i <= k };     MRR@10 = (1 / N) x sum_i (1 / r_i) with 1 / r_i = 0 if r_i > 10"),
          P("Answer-key recall is the share of questions whose generated answer (or retrieved context) contains at least one answer string; the word reduction is 1 minus the mean answer length over the mean context length. "
            "A 95 percent bootstrap interval (2,000 resamples, fixed seed) is given for the shipped retriever."),
          H3("6.5.4 Retrievers used for comparison"),
          P("To place the shipped retriever against the alternatives the base paper builds on, four more scorers were evaluated on the same chunks. BM25 [6] with k1 = 1.5 and b = 0.75 scores a chunk d by"),
          EQ("BM25(q, d) = sum over t in q of idf(t) x f(t, d) (k1 + 1) / ( f(t, d) + k1 (1 - b + b |d| / avgdl) ),     idf(t) = ln((n - df(t) + 0.5) / (df(t) + 0.5) + 1)"),
          P("LSA [8] projects the TF-IDF matrix to 200 dimensions (truncated SVD). The dense retriever embeds chunks and questions with BAAI/bge-small-en-v1.5 [9] (quantised ONNX model, 384 dimensions, fastembed, CPU). "
            "The hybrids add 0.5 times the min-max-normalised BM25 score to 0.5 times the normalised score of a second scorer, a simplified form of the fact-type retrieval of the base paper [1] without its cross-encoder reranking."),
          H3("6.5.5 Quiz generation and roadmap rule"),
          P("For a document with chunks C the quiz generator ranks terms of four or more letters by TF-IDF over the whole text and keeps the best 40. Sentences of 26 to 219 characters are shuffled; for each sentence the first term (in rank order) not yet used that occurs in it as a whole word is blanked at its first occurrence, "
            "three other terms are drawn at random as distractors, and the four options are shuffled; the process stops after five questions. The roadmap rule for a topic with a correct answers in m attempts is"),
          EQ("acc = 100 a / m;     priority = High if acc < 50;  Medium if 50 <= acc < 80;  Low otherwise")]

    b += [H2("6.6 Experiment configuration"),
          P(f"`scripts/run_experiments.py` runs the protocol on the project's own code (`utils.text_extraction`, `utils.rag_engine`, `utils.quiz_generator`) and writes `experiments/results.json`. Hardware and software were: {F.ENV['cpu']}, {F.ENV['ram']} RAM, {F.ENV['os']}, {F.ENV['gpu']}; "
            f"Python {F.ENV['python']}, scikit-learn {F.ENV['sklearn']}, NumPy {F.ENV['numpy']}. The machine was shared with other jobs, so timings are medians of repeated runs."),
          TAB("Experiment protocol", ["Experiment", "Configuration", "Measures"],
              [["Retriever comparison", "Seven retrievers (shipped TF-IDF, unigram TF-IDF, BM25, TF-IDF + LSA, BM25 + LSA, dense BGE-small, BM25 + dense) on the same 672 chunks, 72 questions", "Hit@1, 3, 4, 10, MRR@10, bootstrap interval, by question type"],
               ["Chunk size", "60/15, 100/20, 180/30 (shipped), 300/50 and 450/75 words, shipped retriever", "Chunks, evidence intact, Hit@k, MRR"],
               ["Compression", "Top k of 1, 2, 4, 6 and 8 chunks; shipped extractive answer step, offline mode", "Words in context and answer, answer-key recall, evidence retention, answer words found in context"],
               ["Abstention", "12 off-topic questions; top-1 score thresholds from 0 to 0.30", "Share of off-topic questions refused, share of in-scope questions still answered"],
               ["Document analysis", "Six corpus files; synthetic five-unit syllabus in seven heading styles", "Unit recall, topics per file, units found per style"],
               ["Quiz generation", "30 seeds x 6 files x 5 requested questions; manual review of 30 questions", "Yield, structural validity, ambiguity, answer repeated in the stem, reviewer label"]],
              widths=[1.3, 3.4, 1.9], align=["l", "l", "l"], size=9.5),
          P("The shipped design was fixed first and the other retrievers were compared afterwards; no product parameter changed after the measurements. The dense baseline needed a separate environment (ONNX runtime); the product's requirements are unchanged."),
          FIG(F.fig("fig_retrieval_methods.png"), "Retrieval quality of the seven retrievers evaluated on the same 672 chunks and 72 questions.", 5.6)]
    return b


def application_blocks():
    b = []
    b += [H2("6.7 Application architecture"),
          P("A request travels from a React page, through the Vite development proxy (port 5301 to 8301), to the FastAPI application in `backend/main.py`. The module does not reimplement the pipeline: it imports `db.py`, `config.py` and `utils/*` and "
            "the index cache from the original Flask module `app.py` (`import app as legacy`), so both interfaces use identical logic and the same SQLite file. Middleware adds CORS for the two frontend origins and a signed session cookie."),
          P("Document upload is the longest path. After validating the extension and size, the handler writes the file, extracts and cleans the text, derives the topics, cuts the chunks, inserts one `documents` row and one `chunks` row per window, "
            "and calls `get_engine_for_user`, which reads all of the user's chunks and fits a new TF-IDF model. A question then needs only the cached engine (`legacy._rag_cache`): it calls `generate_answer(question, api_key)` and logs the exchange in `queries`."),
          P(f"Rebuilding the index after each upload keeps the code simple and the index consistent, but its cost grows with the user's total number of chunks: uploading the six corpus files one by one took between "
            f"{min(u['ms'] for u in F.API['uploads']):.0f} and {max(u['ms'] for u in F.API['uploads']):.0f} ms per file in the measured run (Chapter 7). Retrieval itself takes a median of {F.SCALE[0]['retrieve_ms_median']:.1f} ms at {F.SCALE[0]['chunks']} chunks and "
            f"{F.SCALE[-1]['retrieve_ms_median']:.1f} ms at {F.SCALE[-1]['chunks']:,} chunks, so one student's notes are served comfortably; the design is not meant for shared collections of many users in one process."),
          P("The quiz endpoints keep the generated questions, including the correct answer index, in a Python dictionary `_active_quizzes` keyed by user, so that the browser never receives the answers before grading. This state lives in the process: a restart or a second worker loses it, "
            "and the next submission then receives HTTP 409. The Flask interface keeps the same data in its cookie session instead."),
          P("The roadmap is computed on every request from the `quiz_results` rows, grouped by topic and compared with the thresholds 50 and 80; nothing is cached."),
          P("Grouping is by topic string only, so two subjects that produce the same keyword (for example 'data' in Data Structures and in Database Systems) share one roadmap row, and the subject shown is the one of the latest result.")]

    ep = [["GET", "/api/health", "Status and whether an LLM key is configured", "200"],
          ["POST", "/api/auth/register", "Create a user from username, password, interests", "201; 400 empty field; 409 duplicate"],
          ["POST", "/api/auth/login", "Check the password hash and set the session cookie", "200; 401"],
          ["POST", "/api/auth/logout", "Clear the session", "200"],
          ["GET", "/api/auth/me", "Current user, or null when signed out", "200"],
          ["GET", "/api/dashboard", "Counts, accuracy per subject, five latest documents", "200; 401"],
          ["GET", "/api/documents", "Documents with chunk counts", "200; 401"],
          ["POST", "/api/documents", "Upload a file (multipart: document, subject)", "201; 400 type; 413 over 16 MB; 401"],
          ["DELETE", "/api/documents/{id}", "Delete document, chunks and file; rebuild the index", "200; 404"],
          ["POST", "/api/ask", "Answer a question with sources", "200; 400 empty; 401"],
          ["GET", "/api/ask/history", "The ten latest questions", "200; 401"],
          ["POST", "/api/quiz/generate", "Five cloze questions from one document (answers withheld)", "200; 404; 422 too little text"],
          ["POST", "/api/quiz/submit", "Grade the active quiz and store results", "200; 409 no active quiz"],
          ["GET", "/api/roadmap", "Topics with accuracy, attempts and priority", "200; 401"]]
    b += [H2("6.8 API design"),
          P("The API has fourteen JSON endpoints under `/api`. Request bodies are Pydantic models (`RegisterBody`, `LoginBody`, `AskBody`, `QuizGenerateBody`, `QuizSubmitBody`); the upload is multipart. Errors use FastAPI's `{\"detail\": ...}` form, which the React client shows as a message."),
          TAB("API endpoints", ["Method", "Path", "Purpose", "Status codes"], ep, widths=[0.7, 1.7, 2.8, 1.5], align=["c", "l", "l", "l"], size=9),
          P("Authentication is a signed cookie (`alip_session`, seven days, SameSite Lax) set by login; every endpoint except health, register, login, logout and `me` returns 401 without it, which the test suite checks for nine routes. "
            "Passwords are hashed with Werkzeug before storage. The sample screens of Chapter 8 show the API in use.")]

    b += [H2("6.9 Security and error handling"),
          P("Security was tested as a feature (Chapter 7). The table lists the situations that are handled."),
          TAB("Input validation and errors", ["Situation", "Behaviour", "HTTP"],
              [["Empty username or password at registration", "Rejected with a message", "400"],
               ["Wrong password or unknown user", "Same message for both, so existence of a user is not revealed", "401"],
               ["Protected route without a valid session (including a tampered cookie)", "Rejected; the cookie signature is checked", "401"],
               ["Extension other than pdf, docx, txt (including `notes.txt.exe`)", "Rejected before anything is stored", "400"],
               ["Filename with path parts (`../../evil.txt`) or only dots", "`secure_filename` keeps the file inside the user's folder; a name that reduces to nothing is rejected", "201 / 400"],
               ["Corrupt PDF or file without text", "No exception; zero chunks and a warning in the response", "201"],
               ["Another user's document id (delete, quiz)", "Reported as not found; documents and sources of one user never appear for another", "404"],
               ["SQL-injection text in names or questions", "Parameterised queries; the text is stored literally", "200 / 401"],
               ["Foreign browser origin", "No CORS header is returned", "-"]],
              widths=[2.7, 3.0, 0.9], align=["l", "l", "c"], size=9.5),
          P("The posture is that of a local teaching prototype. The session cookie is not marked Secure and the server is plain HTTP, so credentials travel unencrypted without a TLS proxy; there is no rate limiting, account lock-out, password-strength rule or CSRF token (SameSite Lax is the only mitigation); "
            "the signing secret defaults to a development value if `SECRET_KEY` is not set; and the upload body is read fully into memory before the size check. Two uploads of the same file name by one user share one path on disk, so deleting one removes the file the other still lists "
            "(its chunks remain, so questions are unaffected); this is a recorded limitation with a test that asserts the current behaviour."),
          P("The optional LLM branch falls back silently to the extractive answer on any exception; only the badge in the answer card tells the student which mode produced the answer.")]

    b += [H2("6.10 Installation and execution"),
          TAB("Software environment used for this work", ["Component", "Version"],
              [["Operating system / hardware", f"{F.ENV['os']}; {F.ENV['cpu']}; {F.ENV['ram']} RAM; {F.ENV['gpu']}"],
               ["Python and packages", f"Python {F.ENV['python']}; scikit-learn {F.ENV['sklearn']}; numpy {F.ENV['numpy']}; pypdf {F.ENV['pypdf']}; python-docx {F.ENV['python-docx']}"],
               ["Back end", f"FastAPI {F.ENV['fastapi']}; uvicorn {F.ENV['uvicorn']}; Flask {F.ENV['flask']} (original interface); SQLite (Python standard library)"],
               ["Front end", f"Node {F.ENV['node']}; React {F.ENV['react']}; Vite {F.ENV['vite']}; Tailwind CSS {F.ENV['tailwind']}; TanStack Query, axios, Recharts, framer-motion, GSAP"]],
              widths=[1.8, 4.8], align=["l", "l"], size=10),
          P("**One-command start.** Python 3.11 or newer and Node.js 20 or newer are required. Running `run.bat` in `8.ProjectCode` (i) creates the virtual environment `venv` and installs `backend/requirements.txt` on the first run, "
            "(ii) runs `npm install` in `frontend/` if `node_modules` is missing, and (iii) opens two windows, one for `uvicorn backend.main:app --host 127.0.0.1 --port 8301` and one for `npm run dev` (Vite on 5301). "
            "The SQLite database `instance/app.db` is created on first use; no model has to be trained because the index is built from the user's own uploads. Ports and the cookie-signing secret are read from `.env` (copied from `.env.example`); "
            "setting `ANTHROPIC_API_KEY` there, and installing the `anthropic` package, enables Claude-written answers."),
          CODE("python -m venv venv\n"
               "venv\\Scripts\\python -m pip install -r backend\\requirements.txt\n"
               "venv\\Scripts\\python -m uvicorn backend.main:app --port 8301     # API, docs at /api/docs\n"
               "cd frontend && npm install && npm run dev                          # http://localhost:5301\n"
               "venv\\Scripts\\python app.py                                        # original Flask UI, port 5000", 8.5),
          P(f"Checks: `python -m pytest -q` ({F.TESTS['tests']} tests) and `python scripts/smoke_test.py` ({F.SMOKE_TOTAL} checks). `scripts/capture_screens.py --rich --responsive` records the screens with Playwright; `scripts/fetch_corpus.py`, `run_experiments.py` and `measure_api.py` reproduce the experiments, and `serve_scratch.py` runs the backend on a throw-away database. "
            "A demonstration account (`demo`, password `Demo@1234`) exists in the project's own database.")]
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
