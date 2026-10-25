"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10)."""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .ch8 import OBJECTIVES, objective_rows

SHIPPED = F.SHIPPED


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def h(name, k):
    return F.hit(name, k)


# ------------------------------------------------------------------ document 9
def novelty_blocks():
    cm = F.CMP["4"]
    return [
        H2("2.1 What is new, and what is not"),
        P("This project does not propose a new retrieval or compression algorithm. TF-IDF [7], cosine similarity, extractive sentence selection and cloze questions are standard techniques, and the structure of retrieve, compress and generate is the one that the base paper [1] "
          "and the earlier work on retrieval-augmented generation [4] describe. What is new is the combination and the target: a platform that takes a student's own documents (syllabi, notes, question banks), turns them into a searchable repository, answers questions from them with the source shown, "
          "turns the same material into quizzes, and converts quiz results into a priority roadmap and a dashboard, all in one application that runs offline on a laptop. A second contribution is the evaluation, which measures how each stage behaves and reports the gaps."),
        H2("2.2 Difference from the base paper and the supporting papers"),
        TAB("The project against the base paper [1] and the two supporting papers [2], [3]", ["Dimension", "SAC-RAG [1]", "TutorLLM [2] and LLM assessment RAG [3]", "This project"],
            [["Problem", "Cheaper and more accurate RAG for multi-hop question answering", "Course-grounded tutoring: [2] adds knowledge tracing to RAG for learning recommendations; [3] applies RAG to assessment in higher education",
              "A student's own documents turned into grounded Q&A, quizzes, roadmap and dashboard"],
             ["Data", "HotpotQA, 2WikiMultiHopQA, MuSiQue", "Course material (see the papers)", "Documents uploaded by the user; evaluated on a six-subject notes corpus"],
             ["Retrieval", "Question-type routing: BM25 + dense + reranker, dense, or sub-question decomposition", "Retrieval over course content", "TF-IDF cosine over 180-word chunks (BM25 and dense measured as references)"],
             ["Compression", "LLM evidence extraction", "Not the focus", "Extractive sentence selection"],
             ["Generator", "gpt-5-mini", "LLM", "Offline extractive answer; optional Claude call, not measured"],
             ["Personalisation", "None", "Knowledge tracing [2]; assessment feedback [3]", "Quiz accuracy per topic mapped to High, Medium or Low priority"],
             ["Deliverable", "A method and an ablation study", "Methods; their evaluations are not used here", "A working web application, a test suite and an evaluation harness"]],
            widths=[0.9, 1.8, 2.0, 2.0], align=["l", "l", "l", "l"], size=9),
        P("The batch documents name SAC-RAG [1] as the base paper. The project adopts its structure and its vocabulary: retrieve, compress, generate, three question types and the measurement of tokens against quality. "
          "It does not implement the question classifier, the type-specific retrieval or the LLM compression of [1]. The supporting papers [2] and [3] were read for their problem setting (grounded tutoring and assessment) and not for numbers; "
          "none of their results is used in the evaluation."),
        H2("2.3 Mapping of ideas to the implementation"),
        TAB("Where each idea of the base paper stands in the code", ["Idea in [1]", "Status in the project", "Where"],
            [["Retrieve evidence from an external knowledge base", "Implemented (TF-IDF, per-user index)", "`utils/rag_engine.py`, `RAGEngine.retrieve`"],
             ["Lexical plus dense retrieval", "Not in the product; measured as a reference (Hit@4 " + f"{h('hybrid_bm25_dense', 4):.3f})", "`scripts/run_experiments.py`, `scripts/dense_baseline.py`"],
             ["Question classifier (fact, definition, reasoning)", "Not implemented; questions typed by hand to analyse results", "`scripts/eval_questions.py`"],
             ["Sub-question decomposition for reasoning questions", "Not implemented", "none"],
             ["Context compression before generation", "Partly: extractive sentence selection, " + f"{cm['token_reduction_pct']:.1f} % fewer words", "`RAGEngine._extractive_answer`"],
             ["Answer generation from the compressed context", "Extractive text, or Claude when a key is configured", "`generate_answer`, `_llm_answer`"],
             ["Ablation of each component", "Applied to this project: retriever, chunk size, k, compression, threshold", "`experiments/results.json`"]],
            widths=[2.4, 2.6, 1.9], align=["l", "l", "l"], size=9.5),
        H2("2.4 Standard components and project-specific elements"),
        TAB("Standard components and project-specific elements", ["Element", "Standard or project-specific", "Comment"],
            [["TF-IDF vectors, cosine similarity, BM25 [6], LSA [8]", "Standard", "scikit-learn [16] and a small BM25 implementation for the comparison"],
             ["Word-window chunking with overlap", "Standard", "180 words, 30 overlap; every evidence fragment of the corpus stays inside a chunk"],
             ["Heading rules for subject and unit, TF-IDF topics", "Project-specific", "Fast and offline; unit recall 36 of 36 for \"Unit n:\" headings, 0 of 5 for Roman-numeral headings"],
             ["Citation of file, passage number and match score with every answer", "Project-specific", "Displayed on the Ask screen as an expandable list"],
             ["Cloze quiz from TF-IDF terms of the student's own document", "Project-specific", f"{F.AUDIT['summary']['acceptable']} of {F.AUDIT['summary']['n']} reviewed questions acceptable"],
             ["Roadmap from per-topic quiz accuracy (50 and 80 thresholds)", "Project-specific", "Tested at the boundaries; no schedule or knowledge-tracing model"],
             ["Evaluation corpus, 72 questions, gold-evidence metric", "Project-specific", "Reproducible; pinned Wikipedia revisions"],
             ["FastAPI service over unchanged Flask-era modules, React interface", "Project-specific", "The same `utils/` code serves both interfaces"],
             ["Measured trade-offs: retriever, compression, abstention threshold", "New measurement", "Section 8.3 to 8.5 of the report"]],
            widths=[2.7, 1.3, 2.9], align=["l", "c", "l"], size=9.5),
    ]


def contribution_blocks():
    cm = F.CMP["4"]
    return [
        P("The contributions, in the order in which the evidence supports them, are:"),
        N("**An integrated learning platform for a student's own material.** One application ingests PDF, DOCX and TXT files, builds a knowledge repository with detected subjects, units and topics, answers questions from it with the source file, passage and match score, "
          "generates quizzes from the same documents and turns the results into a priority roadmap and a dashboard. It runs on one CPU-only PC with one command (`run.bat`).",
          f"**Grounded question answering that works offline.** The extractive mode returns only sentences of the notes (answer words found in the retrieved chunks: 100 %) at a median of {F.API['ask']['median_ms']:.0f} ms per question over 672 chunks; an optional Claude call is used when a key is configured, with a silent fall-back to the extractive answer.",
          "**A web interface and API designed for study use.** Fourteen JSON endpoints, per-user data isolation, a React interface with light and dark themes that is usable at 360 pixels, and a document, quiz and roadmap workflow that needs no training of models.",
          f"**A reproducible evaluation of every stage.** A pinned six-subject corpus of {F.CORPUS['words']:,} words, 72 typed questions with gold evidence, scripts for retrieval, compression, abstention, document analysis, quiz quality and latency, and {F.TESTS['tests']} automated tests, all regenerated by commands listed in Appendix B.",
          f"**Measured guidance for the next version.** BM25 plus dense retrieval raises Hit@4 from {h(SHIPPED, 4):.3f} to {h('hybrid_bm25_dense', 4):.3f}; a relevance threshold of 0.12 to 0.15 would refuse 75 to 83 % of off-topic questions at a 1 to 4 % cost; "
          f"extractive compression removes {cm['token_reduction_pct']:.1f} % of the words but lowers answer-key recall by {100 * (cm['key_in_ctx'] - cm['key_in_ans']):.1f} points.",
          "**An honest account of what is not achieved.** The semantic embeddings, learned compression, revision schedule and coverage analytics named in the objectives are reported as gaps, with the evidence for each."),
    ]


# ------------------------------------------------------------------ document 10
def scope_blocks():
    return [
        H2("1.1 In scope"),
        P("The scope is what the delivered system does and was tested to do. Each item exists in the code base and has the evidence named in the last column."),
        TAB("Features in scope", ["No.", "Feature", "Where", "Evidence"],
            [["1", "Registration, login, logout and a signed session cookie; users see only their own data", "`/api/auth/*`, `current_user`", "Security tests; cross-user test"],
             ["2", "Upload of PDF, DOCX and TXT files up to 16 MB with a subject label", "`POST /api/documents`", "Upload tests; latency in Section 8.8"],
             ["3", "Text extraction, cleaning, 180-word chunking, subject and unit hints, up to 12 topics", "`utils/text_extraction.py`", "15 extraction tests; Section 8.6"],
             ["4", "Per-user TF-IDF index and retrieval of the top four chunks", "`utils/rag_engine.py`", "Section 8.3"],
             ["5", "Answer from the notes with sources, history of the last ten questions", "`POST /api/ask`, `GET /api/ask/history`", "Sections 8.4, 8.5, 8.11"],
             ["6", "Five-question cloze quiz per document, server-side grading, results stored per topic", "`/api/quiz/*`", "Section 8.7; API tests"],
             ["7", "Priority roadmap from quiz accuracy per topic", "`GET /api/roadmap`", "Boundary tests; screen in Section 8.2"],
             ["8", "Dashboard with counts, subject-wise accuracy and recent documents", "`GET /api/dashboard`", "Screen in Section 8.2"],
             ["9", "React interface, light and dark themes, responsive layout; original Flask interface", "`frontend/`, `app.py`", "Build and Playwright checks"],
             ["10", "Optional Claude answers when `ANTHROPIC_API_KEY` is set", "`RAGEngine._llm_answer`", "Fall-back tested with a stub; real calls not measured"]],
            widths=[0.4, 2.9, 1.9, 1.5], align=["c", "l", "l", "l"], size=9),
        H2("1.2 Out of scope"),
        B("**Semantic (embedding) retrieval in the product.** Dense retrieval was measured only as a reference experiment.",
          "**Question classification, adaptive retrieval and learned compression** of the base paper [1].",
          "**Revision schedules and spaced repetition**, knowledge tracing [17], curriculum coverage and study velocity.",
          "**OCR of scanned documents, handwriting, images and formulas.**",
          "**Grading of free-text answers**; quizzes are four-option fill-in-the-blank only.",
          "**Teacher or administrator roles**, shared classes, sharing of documents between students.",
          "**Cloud deployment, HTTPS, e-mail and mobile applications.**",
          "**Content moderation, plagiarism checks and fairness or accessibility audits.**")]


def assumption_blocks():
    return [
        P("The system and its evaluation rest on the following assumptions. Where an assumption is doubtful it is repeated as a limitation."),
        N("A student uploads documents whose text can be extracted: PDF with a text layer, DOCX paragraphs or plain text, in English.",
          "The questions a student asks use words that also occur in the notes; the retriever is lexical.",
          "Subject and unit headings follow the patterns \"Subject:\", \"Course:\", \"Unit n:\" or \"Chapter n:\" with an Arabic numeral.",
          "One user works on one PC on localhost; the backend trusts the frontend origin `http://localhost:5301`.",
          "A quiz term (a TF-IDF keyword of the document) is a meaningful topic of revision.",
          "The evaluation corpus of Wikipedia articles is a fair stand-in for lecture notes. This is an assumption: it was not tested on real notes.",
          "Medians of timings on a shared i5 PC describe the order of magnitude of a laptop deployment."),
    ]


def limitation_blocks():
    sh = F.RET[SHIPPED]
    return [
        P("Each limitation is stated with its measured consequence and with what would address it. The identifiers L1 to L13 are used in the other chapters."),
        TAB("Limitations", ["ID", "Limitation", "Consequence (measured)", "What would address it"],
            [["L1", "Retrieval is lexical TF-IDF, not semantic", f"Hit@1 {h(SHIPPED, 1):.3f}, Hit@4 {h(SHIPPED, 4):.3f}; BM25 Hit@1 {h('bm25', 1):.3f}; BM25 + dense Hit@4 {h('hybrid_bm25_dense', 4):.3f}", "BM25 plus dense hybrid (Section 10.1)"],
             ["L2", "No relevance threshold", "9 of 12 off-topic questions answered with unrelated sentences", "Refuse when the top-1 score is below about 0.12 to 0.15"],
             ["L3", "Extractive answer is a fixed ~90 words and favours sentences that repeat the question", f"Answer-key recall {F.CMP['4']['key_in_ctx']:.3f} in chunks, {F.CMP['4']['key_in_ans']:.3f} in the answer; definitions {F.CMP['by_type_k4']['definition']['key_in_ans']:.3f}", "Answer-aware sentence selection or an LLM compressor"],
             ["L4", "SAC-RAG components (question classifier, type-specific retrieval, LLM compression) are not implemented", "Objective 4 only partly met", "Add a rule-based or LLM classifier and route retrieval by type"],
             ["L5", "Heading detection is limited; DOCX tables and scans are not read", "Roman-numeral, \"Module n\" and numbered headings found 0 of 5; table text lost; scans give no chunks", "More heading patterns, table extraction, OCR"],
             ["L6", "Two uploads with the same file name share one file on disk", "Deleting one document removes the file of the other (rows stay)", "Store files under unique names (document id)"],
             ["L7", "Quiz questions are cloze sentences on TF-IDF terms", f"{F.AUDIT['summary']['acceptable']} of 30 acceptable; answer term still visible in {F.pct(F.QUIZ['answer_repeated_in_stem_rate'])} of questions", "Sentence quality filters; blank every occurrence; better distractors"],
             ["L8", "Roadmap topics are single keywords and are keyed by topic name only", "Generic topics (\"using\", \"normal\"); the same keyword in two subjects is merged", "Use units or noun phrases as topics; key by subject and topic"],
             ["L9", "Roadmap and dashboard use quiz accuracy only", "No revision schedule, coverage or study velocity (objectives 5 and 6 partly met)", "Knowledge tracing [17], spaced repetition, coverage tracking"],
             ["L10", "Security suited to local use only", "Cookie not Secure, default secret key if `.env` is missing, no rate limiting or CSRF token, only the frontend origin is allowed by CORS", "HTTPS, secret from the environment, rate limits, CSRF protection"],
             ["L11", "State is process-local and the index is rebuilt after each upload", f"Index rebuild {F.SCALE[0]['index_build_ms']:.0f} ms at 672 chunks and {F.SCALE[-1]['index_build_ms']:.0f} ms at 5,376; active quiz and cache lost on restart", "Persist quiz state and indexes; incremental indexing"],
             ["L12", "The evaluation corpus and question set are small and not from students", f"95 % interval of Hit@4 {F.RET_CI['hit4'][0]:.3f} to {F.RET_CI['hit4'][1]:.3f}", "Collect real notes and student questions"],
             ["L13", "Screenshots use scripted quiz answers", "Dashboard and roadmap scores illustrate the screens only", "A user study"]],
            widths=[0.4, 2.1, 2.4, 1.9], align=["c", "l", "l", "l"], size=8.5),
        P("The limitations are not equally serious. L1 to L3 affect the quality of every answer and are the first to address; L5 and L7 affect the usefulness of the knowledge repository and the quiz; L10 matters only if the application is exposed beyond a local machine."),
    ]


def not_measured_blocks():
    return [
        P("Some behaviours could not be measured within the project. They are listed so that no reader assumes a result that does not exist."),
        B("**The Claude answer mode.** No API key was available. The code path is tested only with a stub that fails or returns a fixed string; answer quality, cost and latency of real calls are unknown.",
          "**Concurrent users and long sessions.** One simulated user was used for latency; behaviour with several users, a multi-process server or a large number of documents beyond 5,376 chunks was not measured.",
          "**Scanned documents.** The behaviour on a PDF without a text layer was tested (no text, a warning); recognition of the text by OCR does not exist and was not measured.",
          "**Real student material.** No real syllabus, lecture note or question bank was used; the corpus is Wikipedia text.",
          "**Learning outcomes.** Whether the quizzes and the roadmap improve a student's results is unknown; no user study, survey or controlled trial was made.",
          "**Answer correctness judged by people.** Answers were scored by the presence of a key string, not by human raters; exact match and F1 against reference answers were not computed.",
          "**Accessibility.** Keyboard operation and contrast were considered in the design but no audit with assistive technology was done.",
          "**Cause of rare slow database commits.** Quiz submission showed 1 to 2 second outliers in one or two of 30 calls; the cause was not isolated."),
    ]


# ------------------------------------------------------------------ document 12
def walkthrough_blocks():
    return [
        H2("3.1 Chunking: `chunk_text`"),
        P("The notes are split into overlapping windows of words. The window of 180 words is long enough to hold a definition together with its example and short enough that four of them (about 720 words) fit in a prompt; the overlap of 30 words keeps a sentence "
          "that crosses a boundary whole in at least one chunk. With this setting every one of the 72 evidence fragments of the evaluation lies inside at least one chunk, whereas windows of 60 words cut two of them."),
        CODE(src("utils/text_extraction.py", 58, 73), 9),
        H2("3.2 Index and retrieval: `RAGEngine`"),
        P("The engine fits a TF-IDF vectoriser with unigrams and bigrams and English stop words on the chunks of one user, and scores a query by cosine similarity with every chunk. Chunks with a score of zero are dropped, which is the only form of abstention. "
          "The matrix is sparse, so the cost of a query grows linearly with the number of chunks (2.5 ms at 672 chunks, 19.4 ms at 5,376)."),
        CODE(src("utils/rag_engine.py", 26, 57), 9),
        H2("3.3 The extractive answer"),
        P("When no language-model key is configured the answer is made of the sentences of the retrieved chunks that are closest to the question. The sentences are re-vectorised together with the question, ranked by cosine similarity and the best four with a positive score are joined. "
          "The result contains only words of the notes, which is why answers are grounded by construction; it also explains why the answer is always about 90 words and why a sentence that repeats the question's words can outrank the defining sentence."),
        CODE(src("utils/rag_engine.py", 59, 101), 9),
        H2("3.4 The ask endpoint"),
        P("The endpoint checks the session, rejects an empty question, reuses the cached engine of the user or builds one from the database, asks it for an answer and stores the question, the answer and the source file names. "
          "The sources returned to the browser carry the chunk text, the file name, the passage index and the score."),
        CODE(src("backend/main.py", 297, 321), 9),
        H2("3.5 Quiz generation"),
        P("The top 40 TF-IDF terms of the whole document are the candidate answers. Shuffled sentences of 26 to 219 characters are scanned, and the first term that occurs in a sentence as a whole word and has not been used becomes the blank. "
          "Three other terms are the distractors. Because the terms come from the document itself the quiz needs no external resource, but the sentence is not checked for self-containment, which explains the poor questions in the review."),
        CODE(src("utils/quiz_generator.py", 26, 84), 8.5),
        H2("3.6 The roadmap"),
        P("Quiz results are stored one row per question with the topic (the blanked term) and a 0 or 1. The roadmap groups the rows by topic, computes accuracy and maps it to a priority. "
          "The rule is deliberately simple and explainable: below 50 % is High, below 80 % is Medium. It is keyed by topic only, so the same keyword in two subjects shares one entry."),
        CODE(src("backend/main.py", 400, 430), 8.5),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions, the alternatives that were considered, the reason and what the evaluation later showed."),
        TAB("Implementation decisions", ["Decision", "Alternative", "Reason", "What the measurements showed"],
            [["TF-IDF with cosine similarity for retrieval", "Dense embeddings, BM25", "No model download, no GPU, runs offline in seconds, easy to explain in a viva", f"Adequate (Hit@4 {h(SHIPPED, 4):.3f}) but BM25 and BM25 + dense are better ({h('bm25', 4):.3f}, {h('hybrid_bm25_dense', 4):.3f})"],
             ["Word-window chunks of 180 words, 30 overlap", "Sentences, paragraphs, 60 to 450 words", "Keeps definitions with examples; fits four chunks into a context", "Keeps all 72 evidence fragments intact; larger chunks score higher but pass on more words"],
             ["Extractive answer by default, Claude optional", "A language model only", "Zero cost and no network; no hallucination in the default mode", "100 % of answer words come from the notes; key recall falls by 19 points against the chunks"],
             ["Top four chunks", "More chunks", "Balance between coverage and length", f"Hit@3 {h(SHIPPED, 3):.3f}, Hit@4 {h(SHIPPED, 4):.3f}, Hit@10 {h(SHIPPED, 10):.3f}"],
             ["SQLite and files on disk", "Server database", "Zero set-up for a student project", "Median endpoint latency 4 to 30 ms; rare commit stalls of 1 to 2 s"],
             ["Per-user in-memory index, rebuilt after each change", "Persistent or incremental index", "Simple and always consistent", f"Rebuild {F.SCALE[0]['index_build_ms']:.0f} ms at 672 chunks, {F.SCALE[-1]['index_build_ms']:.0f} ms at 5,376"],
             ["Quiz answers kept on the server until grading", "Send answers to the browser", "Prevents reading the answers from the network tab", "Tested: generate responses contain no answer index"],
             ["Cloze questions from TF-IDF terms", "Language-model generated questions", "Offline and deterministic in structure", f"{F.AUDIT['summary']['acceptable']} of 30 acceptable; needs quality filters"],
             ["Roadmap thresholds 50 and 80", "Learned model", "Transparent rule that a student can read", "Boundary behaviour tested; topics too coarse"],
             ["FastAPI layer over the existing modules, React interface", "Rewrite the logic", "No retrieval, quiz or grading code duplicated; the Flask interface still works", "The same 84 tests cover the shared code"],
             ["Signed session cookie, Werkzeug password hashing", "Tokens in local storage", "Simple, HttpOnly, no password in clear text", "Hashes verified by test; cookie not Secure (local use)"],
             ["Scripts that measure everything", "One-off manual checks", "Numbers in the report are regenerated by commands", "Results in `experiments/*.json` feed the documents"]],
            widths=[1.7, 1.3, 1.9, 1.9], align=["l", "l", "l", "l"], size=8.5),
    ]


# ------------------------------------------------------------------ document 15 / chapters 9 and 10
def conclusion_blocks():
    cm = F.CMP["4"]
    sh = F.RET[SHIPPED]
    return [
        H2("9.1 Summary"),
        P("The Adaptive Learning Intelligence Platform lets a student upload syllabi, notes and question banks, analyses them into a searchable repository with detected subjects, units and topics, answers questions from the notes with the source shown, generates quizzes from the same documents "
          "and turns quiz accuracy into a priority roadmap and a dashboard. It is delivered as a FastAPI service with a React interface and, unchanged, as the original Flask application, and it runs offline on one CPU-only PC. "
          "The project follows the structure of the base paper [1] (retrieve, compress, generate) with simpler components, and the evaluation in this report measures how far those components go."),
        H2("9.2 Objectives achieved"),
        P("Of the six objectives, one was met in the offline mode (grounded answers with sources), one was not met (semantic embeddings) and four were met in part. The table gives the status and the basis of each."),
        TAB("Objectives and their status", ["No.", "Objective", "Status", "Basis"], objective_rows(), widths=[0.4, 2.2, 0.9, 3.2], align=["c", "l", "c", "l"], size=9),
        H2("9.3 Key findings"),
        N(f"The shipped retriever is lexical. It finds the evidence in the top four chunks for {F.pct(h(SHIPPED, 4))} of 72 questions and ranks it first for {F.pct(h(SHIPPED, 1))}. BM25 reaches {h('bm25', 1):.3f} at rank one, and BM25 plus a dense model reaches Hit@4 {h('hybrid_bm25_dense', 4):.3f}; "
          "the semantic retrieval of objective 2 is therefore not delivered, and the dense and hybrid retrieval of [1] is better supported than the product's.",
          f"None of the SAC-RAG components (question classifier, adaptive retrieval, LLM compression) is implemented. The only compression is extractive sentence selection, which removes {cm['token_reduction_pct']:.1f} % of the words and lowers answer-key recall from {cm['key_in_ctx']:.3f} to {cm['key_in_ans']:.3f}; "
          "[1] reports 38 to 58 % fewer tokens for one to two points of exact match, with a language model and different data.",
          f"Definition questions are the weak case for extractive answers: the key is in the retrieved chunks for {F.CMP['by_type_k4']['definition']['key_in_ctx']:.3f} of them and in the answer for {F.CMP['by_type_k4']['definition']['key_in_ans']:.3f}. The answer favours sentences that repeat the question's words, not the defining sentence.",
          "There is no relevance threshold: 9 of 12 off-topic questions received an unrelated answer. A threshold near 0.12 to 0.15 would refuse 75 to 83 % of them at a cost of 1 to 4 % of in-scope questions.",
          f"The quiz and roadmap work end to end but their content is shallow: {F.AUDIT['summary']['acceptable']} of 30 reviewed questions were acceptable, the answer term is visible in the question in {F.pct(F.QUIZ['answer_repeated_in_stem_rate'])} of 900 generated questions, and roadmap topics are single keywords.",
          "The roadmap and dashboard adapt only to quiz accuracy; there is no knowledge-tracing model, revision schedule, coverage or study-velocity measure.",
          f"The software is sound for its purpose: {F.TESTS['tests']} of {F.TESTS['tests']} automated tests and {F.SMOKE_TOTAL} of {F.SMOKE_TOTAL} smoke checks pass, endpoints answer in 4 to 30 ms (login 128 ms), and hostile inputs are refused or stored as plain text. "
          "These results are on a Wikipedia corpus of 72 questions with an extractive answerer; they are not comparable with the datasets of the base paper."),
        H2("9.4 Practical applications"),
        P("The platform can serve as a personal study assistant that keeps a semester's notes in one searchable place and shows the source of every answer, as a revision planner whose ranked weak topics tell a student what to revise first "
          "(once topics are made more meaningful), and as a teaching case for the whole cycle of ingestion, retrieval, answering, quiz generation and honest measurement. With BM25 plus dense retrieval, a relevance threshold and real syllabi it could serve a class (Chapter 10)."),
        H2("9.5 Known limitations and lessons"),
        P("The platform was evaluated on encyclopaedic text and not on student notes; answers were scored by key strings and not by people; the Claude mode was not measured. Retrieval is lexical, definitions are answered poorly, off-topic questions are answered, "
          "Roman-numeral headings, DOCX tables and scans are not handled, quiz questions are of uneven quality, and security is suited to local use (limitations L1 to L13 in the scope and limitations document). "
          "Two lessons follow. Each stage must be measured separately: the screens looked convincing, but retrieval ranks the evidence first in only two of five questions and the answer step then drops the key in about one case in six. "
          "And grounding is not relevance: an answer made only of sentences from the notes can still answer a different question, so a relevance check is a separate requirement. With 72 questions the interval of Hit@4 is about 0.18 wide, "
          "so small differences between retrievers must not be reported as improvements."),
    ]


def future_blocks():
    return [
        H2("10.1 Improvements to retrieval and answering"),
        B(f"**Replace TF-IDF with BM25 or a BM25 plus dense hybrid.** In the experiments BM25 raised Hit@1 from {h(SHIPPED, 1):.3f} to {h('bm25', 1):.3f}, and the hybrid raised Hit@4 from {h(SHIPPED, 4):.3f} to {h('hybrid_bm25_dense', 4):.3f} with a small quantised model [9] that embeds a query in {F.DENSE['embed_query_ms_each']} ms on the CPU. "
          "The cost is a one-time embedding of each upload (52 s for 672 chunks on this PC) and one more model to ship.",
          "**Add a relevance threshold.** Refuse to answer when the best score is below a value between 0.12 and 0.15, and say so on the Ask screen. The measured effect is 75 to 83 % of off-topic questions refused for a 1 to 4 % cost; the value should be re-tuned on real notes.",
          "**Select the answer sentence with the answer in mind.** Mix question similarity with position in the chunk so that the defining sentence is favoured; this targets the drop of definition answers from 0.917 to 0.500 key recall.",
          "**Question-type routing in the style of [1] and [11].** Classify a question as fact, definition or reasoning by rules and route facts to BM25, definitions to dense retrieval and reasoning questions to decomposition; the by-type results show different best retrievers for each type.",
          "**LLM compression and generation.** Use a language model to extract evidence [10], [15] and write the answer from it when a key is available, and measure it on the same 72 questions to see whether the loss of answer-key recall disappears."),
        H2("10.2 Improvements to document analysis"),
        B("**More heading patterns.** Recognise \"UNIT-I\", \"Unit I:\", \"Module 1\" and numbered lists; this closes the 0 of 5 results of Section 8.6.",
          "**Read DOCX tables and slides**, which hold many syllabi, and add OCR for scanned pages, which currently give no text and a warning.",
          "**Unique file names.** Store each upload under its document identifier so that two files with the same name cannot share a path (limitation L6).",
          "**Better topics.** Use units, section headings or noun phrases instead of single TF-IDF keywords and remove generic words; this makes the roadmap meaningful."),
        H2("10.3 Improvements to quizzes, roadmap and dashboard"),
        B("**Cloze quality filters.** Blank every occurrence of the term, reject sentences that start mid-clause or contain formulas or code, and choose distractors of similar frequency; the review accepted 17 of 30 questions today.",
          "**Knowledge tracing and spaced repetition.** Replace the two fixed thresholds by a model of mastery per topic over time, as in [2] and [17], and schedule revisions; this addresses objective 5.",
          "**Coverage and study velocity.** Track which units of a document have been asked about or quizzed and show progress over time on the dashboard (objective 6).",
          "**Key the roadmap by subject and topic**, so that the same word in two subjects is not merged."),
        H2("10.4 Scalability, security and deployment"),
        B("**Per-subject retrieval.** Let the student restrict a question to one subject or document, removing cross-subject distractors.",
          f"**Persistent and incremental indexes.** Rebuilding the whole index after each upload took {F.SCALE[0]['index_build_ms']:.0f} ms at 672 chunks and {F.SCALE[-1]['index_build_ms']:.0f} ms at 5,376; an incremental index and stored quiz state also remove the dependence on one process.",
          "**HTTPS, a secret from the environment, a Secure cookie, rate limiting and CSRF protection** before the application is reachable from a network.",
          "**Continuous testing.** Run the 84 tests and the experiments script in a pipeline and add browser tests."),
        H2("10.5 Further research and evaluation"),
        B("**Collect real notes and student questions** and repeat the evaluation, with human judgement of correctness and usefulness and exact match or F1 against reference answers.",
          "**A user study** to learn whether the quizzes and the roadmap change how students revise.",
          "**Measure the Claude mode** and compare cost, latency and quality with the extractive mode on the same questions.",
          "**Study abstention and compression jointly**: whether a relevance threshold plus answer-aware compression restores the quality that extractive selection loses."),
        H2("10.6 Suggested order"),
        P("A sensible order is: first the relevance threshold, unique file names, more heading patterns and a subject-keyed roadmap (days); then BM25 or hybrid retrieval and answer-aware sentence selection; then cloze filters, better topics and coverage tracking; "
          "then the measured Claude mode, question-type routing and LLM compression, which realise the structure of the base paper [1]; and last knowledge tracing, spaced repetition, accounts, HTTPS and a pilot with real notes and a user study."),
    ]


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
