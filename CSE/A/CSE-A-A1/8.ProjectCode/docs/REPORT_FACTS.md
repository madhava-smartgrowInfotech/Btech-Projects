# REPORT FACTS - Adaptive Learning Intelligence Platform (CSE-A-A1)

Single source of truth for every document in this documentation run. All numbers come from files in this repository:
`experiments/results.json`, `experiments/api_latency.json`, `experiments/quiz_audit.json`,
`experiments/pytest_report.xml`, the scripts in `scripts/`, and the code itself. Nothing here is estimated.

Measured on 2026-10-25. Machine: Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, CPU only
(no GPU). Python 3.11.9, scikit-learn 1.5.1, NumPy 1.26.4, FastAPI 0.115.0, uvicorn 0.30.6, Flask 3.0.3,
Node 24.19, React 19, Vite 8. The machine was shared with other jobs; timings are medians of repeated runs.

---

## 1. Project identity

| Item | Value |
|---|---|
| Title | Adaptive Learning Intelligence Platform Using Educational Document Analysis and Personalized Learning Analytics |
| Short product name | Adaptive Learning Intelligence Platform (ALIP); UI brand "AdaptiveLearning" |
| Batch | CSE-A, Batch 01 (CSE-A-A1) |
| Domain | Artificial Intelligence, Learning Analytics, Retrieval-Augmented Generation (RAG) |
| Students | A DHANUSH (23K91A0501), ALE VIJAYALAXMI (23K91A0508), BURRI MALLIKARJUN (23K91A0549), ATRAGADA NAGATRIMURTHULU (23K91A0517) |
| Guide | RAGHAVENDRA (designation not given: keep placeholder) |
| College, department head, principal, academic year | not given: keep the template's square-bracket placeholders |
| Base paper | D. Zhang, H. Yu, J. Huo, M. Su, "SAC-RAG: Semantic Adaptive Context Compression for Retrieval-Augmented Generation," IEEE Access, vol. 14, pp. 117406-117418 (page range from the PDF footers), 2026, DOI 10.1109/ACCESS.2026.3718025 |
| Supporting papers (archived_base_papers/) | An LLM-Powered Assessment RAG for Higher Education (arXiv 2601.06141, 2026); TutorLLM: Customizing Learning Recommendations with Knowledge Tracing and RAG (arXiv 2502.15709, 2025) |
| Ports | backend 8301, frontend 5301 (original Flask interface on 5000) |

### Batch literature survey table (5-batch file `5.LITERATURE SURVEY.docx`)
1. SAC-RAG: Semantic Adaptive Context Compression for RAG - IEEE Access, 2026 (base paper)
2. Optimizing Retrieval-Augmented Generation of Medical Content for Spaced Repetition Learning - Proc. 17th Int. Conf. on Computer Supported Education, 2025
3. Automatic Teaching Platform on Vision Language Retrieval Augmented Generation - 2025 IEEE Integrated STEM Education Conference (ISEC), 2025
4. Democratizing Financial Education: An API-Driven Platform Powered by Retrieval-Augmented Generation - 2025 Int. Conf. on Education Technology and Computers (ICETC)
5. Student-designed educational resources for Lean: exploring ChatGPT and Retrieval-Augmented Generation - ZDM Mathematics Education, 2026

(Only titles, years and venues are known for items 2-5; no authors, DOIs or results. Do not invent any. Cite them in the
reference list with the data the batch file gives and mark "details not verified"; do not quote results from them.)

Gap stated in the batch documents: existing RAG work targets general question answering and context compression; none of the
surveyed systems combines document ingestion, syllabus-grounded tutoring and progress analytics for a student's own curriculum.

### Batch objectives (`6.OBJECTIVES&PROBLEM STATEMENT.docx`) and their status in the product
| # | Objective | Status (measured / read from code) |
|---|---|---|
| 1 | Document ingestion that parses syllabi, notes, question banks and extracts subjects, units, topics | PARTLY. PDF/DOCX/TXT parsed (pypdf, python-docx). Subject/unit hints only for headings "Subject:", "Course:", "Unit N:", "Chapter N:" (Arabic numerals): unit recall 36/36 on the corpus, but 0/5 for "UNIT-I", "Unit I:", "Module 1:" and "1. Title". Topics = hints + TF-IDF keywords (max 12). DOCX tables ignored. Scanned PDFs give no text. |
| 2 | Vector embeddings for semantic (not keyword) search | NOT MET. The shipped retriever is TF-IDF + cosine (sparse lexical vectors), not learned embeddings. A dense BGE-small reference was measured only as an experiment (not in the product). |
| 3 | RAG QA that answers strictly from the uploaded material and cites the source | MET for extractive mode: 100 % of answer words come from the retrieved chunks, every answer lists source file + passage + match score. Weakness: 9/12 off-topic questions still got an answer (no relevance threshold). LLM mode (Claude) exists in code but was NOT measured (no API key). |
| 4 | Semantic context compression within the model context window | PARTLY. No learned/LLM compression like SAC-RAG. The extractive sentence selection step shrinks 720 words of retrieved context to about 90 words (87.5 % fewer words) but loses answer-key recall (0.861 -> 0.667). No question-type routing. |
| 5 | Personalised study roadmaps and revision schedules from coverage and performance | PARTLY. Roadmap = per-topic quiz accuracy bucketed High (<50) / Medium (50-79.9) / Low (>=80), sorted. No revision schedule / spaced repetition, no coverage model. Topics are single TF-IDF keywords (some generic: "using", "used", "normal"). |
| 6 | Dashboard with curriculum coverage, study velocity, engagement | PARTLY. Dashboard shows documents uploaded, questions asked, quiz questions attempted, subject-wise quiz accuracy bar chart, five recent documents. No coverage %, no study velocity over time. |

---

## 2. Architecture summary (from the code)

* **Frontend** (`frontend/`): React 19 + TypeScript + Vite 8 + Tailwind CSS 4, TanStack Query, axios, Recharts, framer-motion, GSAP, Lenis, Radix UI, sonner toasts.
  53 TS/TSX source files, 4,867 lines (+ 385 lines CSS). Pages: Landing, Login, Register, Upload, Documents, Ask, Quiz, Roadmap, Dashboard, NotFound.
  Light and dark themes (`alip-theme` in localStorage). `npm run build` (tsc --noEmit + vite build) succeeds in 8.7 s; largest chunks (gzip): index 121.5 kB, charts 111.4 kB, motion 102.3 kB, api 45.9 kB; every page is a lazy chunk under 20 kB raw.
* **Backend** (`backend/main.py`, 430 lines): FastAPI, 14 endpoints, signed session cookie `alip_session` (Starlette SessionMiddleware, SameSite=Lax, 7 days, https_only=False), CORS limited to http://localhost:5301 and 127.0.0.1:5301, Pydantic request bodies, Werkzeug password hashing and `secure_filename`.
* **Shared modules**: `db.py` (SQLite schema, 74 lines), `config.py`, `utils/text_extraction.py` (127), `utils/rag_engine.py` (120), `utils/quiz_generator.py` (84), `app.py` (402 lines, original Flask UI; also holds `get_engine_for_user` and the per-user in-memory index cache `_rag_cache`). Python application code total 1,252 lines in 9 files.
* **Storage**: SQLite `instance/app.db` (5 tables), uploaded originals in `uploads/<user_id>/`.
* **Optional LLM**: if `ANTHROPIC_API_KEY` is set, `RAGEngine._llm_answer` calls the Anthropic API (model string `claude-sonnet-4-6`, max_tokens 500, prompt: answer using ONLY the context); any exception falls back silently to the extractive answer. NOT measured.
* **Original Flask interface** (port 5000, Jinja templates, Bootstrap) still works and shares db.py and utils/.

### Endpoints (14)
| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | status + llm_enabled |
| POST | /api/auth/register | create user (201; 400 empty, 409 duplicate) |
| POST | /api/auth/login | session cookie (401 on failure) |
| POST | /api/auth/logout | clear session |
| GET | /api/auth/me | current user or null |
| GET | /api/dashboard | counts, subject accuracy, 5 latest documents |
| GET | /api/documents | list with chunk counts |
| POST | /api/documents | upload (multipart: document, subject); 400 type, 413 >16 MB |
| DELETE | /api/documents/{id} | delete document, chunks, file |
| POST | /api/ask | RAG answer + sources |
| GET | /api/ask/history | last 10 questions |
| POST | /api/quiz/generate | 5 cloze questions from one document (answers kept server-side) |
| POST | /api/quiz/submit | grade, store per-topic results |
| GET | /api/roadmap | topics with accuracy, attempts, priority |

### Database (db.py)
`users(id, username UNIQUE, password_hash, interests, created_at)` 1-N `documents(id, user_id FK, filename, filepath, subject, topics JSON text, uploaded_at)` 1-N `chunks(id, document_id FK, chunk_index, text)`;
`users` 1-N `queries(id, user_id FK, question, answer, sources JSON text, created_at)`; `users` 1-N `quiz_results(id, user_id FK, subject, topic, correct 0/1, created_at)`.
All FKs ON DELETE CASCADE, `PRAGMA foreign_keys=ON`. quiz_results has no FK to documents (subject and topic stored as text).

### Algorithms (exact parameters in code)
* Text extraction: pypdf `PdfReader` page text; python-docx paragraphs; UTF-8 text. `clean_text` collapses spaces/tabs and 3+ newlines.
* Chunking: word windows, `chunk_size=180`, `overlap=30` (stride 150).
* Subject/unit hints: regexes `^subject\s*[:-]`, `^course\s*[:-]`, `^unit\s*\d+\s*[:-]`, `^chapter\s*\d+\s*[:-]`; de-duplicated, capped 15, each <120 characters.
* Topics: TF-IDF (unigram+bigram, English stop words, max 500 features) summed over sentences (>15 chars); hints first, then keywords; at most 12 topics.
* Retrieval: `TfidfVectorizer(stop_words="english", ngram_range=(1,2))` fit on the user's chunks; cosine similarity with the query; top_k=4, scores <=0 dropped. Index rebuilt after every upload/delete.
* Extractive answer: split retrieved chunks into sentences (>20 chars), TF-IDF vectorise [query + sentences], rank by cosine, keep top 4 with score >0 (fallback first 3 sentences; if no sentences, first 500 chars of the best chunk), join with spaces. No retrieved chunk -> "No relevant content was found in your uploaded documents ...".
* Quiz generator: TF-IDF of the whole document (words with 4+ letters), top 40 terms; sentences 26-219 characters shuffled; for each sentence the first unused term occurring as a whole word is blanked (first occurrence); 3 random other terms as distractors; options shuffled; 5 questions; unseeded `random`.
* Roadmap: per topic, accuracy = 100 x correct / attempts; High if <50, Medium if <80, else Low; sorted by (priority, accuracy).

---

## 3. Dataset facts (evaluation corpus built for this documentation run)

The product has no ML training set. To measure it, `scripts/fetch_corpus.py` builds a six-subject "notes" corpus from English Wikipedia
(CC BY-SA 4.0; each article pinned to a revision id in `experiments/corpus_manifest.json`; text kept out of git, rebuilt by the script).
Each subject is one file with `Subject: ...` and six `Unit n: <article>` sections (the layout the document analyser recognises). Math markup
(`{\displaystyle ...}`) is stripped; each article is capped at 3,200 words.

| File (subject) | Articles | Words | Chunks (180/30) |
|---|---|---|---|
| 01 Data Structures | Stack, Queue, Linked list, Binary search tree, Hash table, Heap | 15,072 | 101 |
| 02 Operating Systems | Deadlock, Scheduling, Memory paging, Semaphore, Virtual memory, Thread | 16,797 | 112 |
| 03 Database Systems | Database normalization, ACID, B-tree, Relational model, Database index, Concurrency control | 15,504 | 104 |
| 04 Computer Networks | TCP, DNS, OSI model, Routing, Network congestion, DHCP | 17,618 | 118 |
| 05 Machine Learning | Overfitting, Gradient descent, Decision tree learning, Naive Bayes, K-means, SVM | 18,346 | 123 |
| 06 Algorithms | Dijkstra, Merge sort, Quicksort, Binary search, Dynamic programming, BFS | 17,107 | 114 |
| **Total** | 36 articles | **100,444 words** | **672 chunks** (mean 179.2 words) |

Questions: 72 hand-written questions (`scripts/eval_questions.py`), 12 per subject, 24 each of three types matching the base paper's taxonomy (fact, definition, reasoning; typed by question wording).
Gold evidence = a sentence fragment copied from the corpus (verified to occur exactly once); a retrieved chunk is a hit when it contains it. Each evidence string lies wholly inside at least one chunk (72/72).
`answer_any` strings test the generated answer. 12 further off-topic questions (football, cooking, geography, ...) test abstention.
Split: no training; all 72 questions are test questions. Licence of the corpus text: CC BY-SA 4.0 (Wikipedia). The bundled demo file `sample_data/sample_notes_data_structures.txt` (619 words, 4 chunks) is the project's own and was used for the UI screens.

---

## 4. Measured results (experiments/results.json)

### 4.1 Retrieval, 672 chunks, 72 questions (Hit@k = gold evidence inside one of the top-k chunks; MRR@10)
| Retriever | Hit@1 | Hit@3 | Hit@4 | Hit@10 | MRR@10 |
|---|---|---|---|---|---|
| **TF-IDF 1-2 gram (shipped)** | 0.403 | 0.736 | 0.792 | 0.931 | 0.588 |
| TF-IDF unigram | 0.389 | 0.694 | 0.778 | 0.944 | 0.577 |
| BM25 (k1 1.5, b 0.75) | 0.500 | 0.792 | 0.833 | 0.944 | 0.659 |
| TF-IDF + LSA (200 dims) | 0.431 | 0.681 | 0.764 | 0.958 | 0.585 |
| BM25 + LSA (min-max, 0.5/0.5) | 0.500 | 0.819 | 0.833 | 0.944 | 0.658 |
| Dense BGE-small-en-v1.5 (quantised ONNX via fastembed, 384-d) | 0.431 | 0.750 | 0.778 | 0.917 | 0.588 |
| BM25 + dense (min-max, 0.5/0.5) | **0.556** | **0.833** | **0.889** | **0.958** | **0.709** |

Bootstrap 95 % CI of the shipped retriever (2,000 resamples): Hit@1 0.292-0.514, Hit@4 0.694-0.875, MRR@10 0.505-0.673. With 72 questions, differences of a few points between retrievers are within noise; the clear signals are BM25 > TF-IDF at Hit@1 and the hybrid being best.
Dense model: 52.3 s to embed 672 chunks on CPU, 4.4 ms per query (reference only, not shipped).

By question type for the shipped retriever (Hit@1 / Hit@4): fact 0.542 / 0.833; definition 0.292 / 0.833; reasoning 0.375 / 0.708. BM25: fact 0.667 / 0.958, definition 0.292 / 0.750, reasoning 0.542 / 0.792. BM25+dense: fact 0.625 / 0.958, definition 0.542 / 0.875, reasoning 0.500 / 0.833.

### 4.2 Chunk size (shipped TF-IDF; larger chunks mean fewer chunks and more words per hit, so compare with care)
| size/overlap | chunks | Hit@1 | Hit@4 | Hit@10 | MRR@10 | evidence intact |
|---|---|---|---|---|---|---|
| 60/15 | 2,233 | 0.306 | 0.611 | 0.694 | 0.446 | 70/72 |
| 100/20 | 1,257 | 0.417 | 0.708 | 0.903 | 0.568 | 72/72 |
| **180/30 (shipped)** | 672 | 0.403 | 0.792 | 0.931 | 0.588 | 72/72 |
| 300/50 | 404 | 0.556 | 0.847 | 0.986 | 0.688 | 72/72 |
| 450/75 | 269 | 0.486 | 0.944 | 1.000 | 0.677 | 72/72 |

### 4.3 Context compression (shipped retrieval + shipped extractive answer step), k = chunks retrieved
| k | words in retrieved context | words in answer | words removed | answer key in chunks | answer key in answer | evidence sentence in answer |
|---|---|---|---|---|---|---|
| 1 | 180 | 88.0 | 51.1 % | 0.625 | 0.514 | 0.361 |
| 2 | 360 | 94.4 | 73.8 % | 0.750 | 0.653 | 0.583 |
| **4 (default)** | 720 | 89.8 | **87.5 %** | **0.861** | **0.667** | 0.569 |
| 6 | 1,080 | 87.3 | 91.9 % | 0.944 | 0.764 | 0.639 |
| 8 | 1,438 | 84.2 | 94.1 % | 0.972 | 0.792 | 0.681 |

At k=4: answers contain only words from the retrieved chunks (answer_words_in_context = 1.0; 100 % of answers fully grounded). Given the retrieval hit (57 of 72 questions), the answer contains the key 0.825 and the evidence sentence 0.719 of the time.
By type at k=4 (key in chunks -> key in answer): fact 0.917 -> 0.792; definition 0.917 -> 0.500; reasoning 0.750 -> 0.708. Compression cost at k=4: -19.4 points of answer-key recall for 87.5 % fewer words.
Base paper for contrast (different data and an LLM compressor): token consumption reduced 38-58 % at a 1-2 point EM drop.

### 4.4 Abstention (relevance threshold) - the shipped engine has none
* Shipped behaviour: refuses only if no query term overlaps any chunk. 9 of 12 off-topic questions received an answer, 3 refused (25 % correct abstention).
* Top-1 cosine score: in-scope mean 0.320, median 0.317, min 0.102, 10th percentile 0.212; off-topic mean 0.107, median 0.092, max 0.357.
* Threshold sweep (in-scope answered / off-topic refused): 0.10 -> 1.000 / 0.583; 0.12 -> 0.986 / 0.750; 0.15 -> 0.958 / 0.833; 0.20 -> 0.903 / 0.833; 0.25 -> 0.681 / 0.833; 0.30 -> 0.514 / 0.917. A threshold near 0.12-0.15 would refuse 75-83 % of off-topic questions at a 1-4 % cost in answered in-scope questions (suggested, not implemented).

### 4.5 Document analysis
* Heading detection on the corpus: 36/36 "Unit n:" headings and 6/6 "Subject:" lines found; every file yields the maximum 12 topics (7 hints + 5 TF-IDF keywords, e.g. "data", "node", "search", "unit").
* Heading formats on a synthetic five-unit syllabus: "Unit 1: Title" 5/5, "Unit 1 - Title" 5/5, "Chapter 1: Title" 5/5; "UNIT-I Title" 0/5, "Unit I: Title" 0/5, "Module 1: Title" 0/5, "1. Title" 0/5.
* Parsing (tests): TXT, DOCX paragraphs and text-layer PDF extracted; DOCX table text lost; PDF without a text layer gives empty text (upload returns a warning, 0 chunks); corrupt PDF returns "[Could not extract text ...]" without raising.

### 4.6 Quiz generation (30 seeds x 6 files x 5 requested = 900 questions)
* Yield 900/900 (1.0); every question structurally valid (4 distinct options, answer index consistent) = 1.000.
* Another option also appears inside the question stem (ambiguity risk): 85/900 = 9.4 %. The answer term itself is still visible in the stem (the first occurrence is blanked, later ones are not): 164/900 = 18.2 %.
* Manual review of 30 questions (seed 0, first 5 per file, `experiments/quiz_audit.json`): 17 acceptable (56.7 %), 5 ambiguous, 8 poor (leaked answer, formula/code fragment or sentence needing context). Single reviewer, subjective.
* Generation time (in process): median 15.7 ms, p95 19.9 ms. The 619-word sample notes always give 5 questions (30 seeds).

### 4.7 Latency and scaling
In-process (retriever only, 72 queries, median / p95 ms) by index size: 672 chunks 2.5 / 3.9 (retrieve), 5.8 / 8.1 (retrieve + extractive answer), index build 263 ms; 1,344 chunks 4.7 / 6.8 and 8.1 / 12.5, build 379 ms; 2,688 chunks 9.8 / 12.2 and 13.1 / 16.2, build 528 ms; 5,376 chunks (about 963k words) 19.4 / 24.4 and 23.0 / 30.2, build 974 ms. Retrieval time grows about linearly with the number of chunks.

HTTP API on 127.0.0.1, one user, 672 chunks indexed, 30 calls each (median / p95 ms, second run; first run in brackets): health 2.0 / 2.8; login 127.6 / 137.0 (password hashing); dashboard 4.2 / 5.8 [3.8 / 46.0]; documents list 5.8 / 6.9; roadmap 7.0 / 10.0; ask 29.5 / 35.3 [31.9 / 501]; ask history 4.1 / 10.6; quiz generate 23.1 / 28.2; quiz submit 24.5 / 2,172 [24.2 / 1,012] (1-2 slow SQLite commits per 30 calls, cause not isolated).
Upload of one 88-110 KB file, which re-indexes all of the user's chunks: 119-2,501 ms across two runs (first file 120 / 2,501 ms; with 672 chunks indexed 811 / 1,072 ms); delete with re-index 248-683 ms. The spread comes from machine load.

### 4.8 Testing
* `pytest` suite (`tests/`, 6 files, 631 lines): **84 tests, 84 passed, 0 failed, 15.2 s** (test_api 45 incl. parametrised, test_text_extraction 15, test_security 11, test_rag_engine 9, test_quiz_generator 4). Uses a temporary database and upload folder.
* `scripts/smoke_test.py` (API end to end against a running server): **24 checks, all passed**.
* `npm run build`: TypeScript type check + production build succeed. Playwright run (`capture_screens.py --rich --responsive`): console clean - no console errors, page errors or failed requests on desktop, 768 px and 360 px, light and dark; no horizontal overflow.
* Security checks covered by tests: unauthenticated access to 9 protected routes returns 401; password stored as scrypt/pbkdf2 hash; SQL-injection strings stored literally and login with them fails; path traversal in filename ("../../evil.txt") saved as "evil.txt" inside the user's folder; ".exe" and double-extension files rejected; session cookie HttpOnly + SameSite=Lax (not Secure); tampered cookie rejected; CORS answers only the frontend origin; one user cannot list, delete, quiz on or search another user's documents.
* Characterised limitations (tests assert the current behaviour): (a) two uploads with the same file name share one file path, deleting one removes the file of the other (chunks stay in the database); (b) DOCX tables are not read; (c) "UNIT-I" style headings not recognised; (d) session cookie not Secure (local deployment).
* Not tested: LLM mode (no API key), concurrent users, multi-process deployment (quiz state `_active_quizzes` and index cache are process-local), scanned PDFs with OCR, real student syllabi, accessibility audit, a user study.

### 4.9 Findings the report must state plainly
1. The shipped retriever is lexical TF-IDF. BM25 beats it at Hit@1 (0.500 vs 0.403) and BM25 + dense is best (Hit@4 0.889), so the "semantic" retrieval of objective 2 is not achieved by the shipped code; the base paper's dense + BM25 + rerank pipeline is better supported than the product's.
2. No question-type classifier, adaptive retrieval or LLM compression from SAC-RAG is implemented. The only compression is extractive sentence selection: 87.5 % fewer words, answer-key recall falls from 0.861 to 0.667 (base paper: 38-58 % fewer tokens for 1-2 points of EM, with an LLM and different data).
3. Definition questions are the weak case for extractive answers (key present in the chunks 0.917 but in the answer only 0.500): the answer picks sentences that overlap the question's words, not the defining sentence.
4. No relevance threshold: 75 % of off-topic questions still get an (irrelevant) extracted answer. This undermines "answers strictly from the uploaded material".
5. Quiz questions are cloze questions on TF-IDF terms; only 17/30 reviewed questions were acceptable; roadmap topics are single keywords, some generic.
6. The roadmap/dashboard adapt to quiz accuracy only; there is no knowledge-tracing model, schedule or coverage tracking.
7. Datasets differ from the base paper (it uses HotpotQA, 2WikiMultiHopQA, MuSiQue with 1,000 questions each, gpt-5-mini, Recall@10, EM, F1); results here are on a 72-question notes corpus with no LLM, so numbers are not comparable, only the trade-off pattern is.

---

## 5. Base paper reference numbers (verified from the PDF text)
* SAC-RAG: LLM question classifier (Fact / Definition / Reasoning; 92.0 % accuracy on 300 manually labelled questions), type-specific retrieval (Fact: BM25 + dense with BGE cross-encoder rerank, top 10; Definition: dense only, top 8; Reasoning: LLM sub-question decomposition + parallel retrieval + rerank), unified LLM context compression, generation.
* Evaluation: HotpotQA, 2WikiMultiHopQA, MuSiQue; 1,000 questions each; four settings (Naive, Compress, Adaptive, SAC-RAG); metrics EM, F1, Recall@10, tokens; gpt-5-mini, temperature 0; Milvus (1,536-d), MongoDB, rank_bm25, bge-reranker-base.
* Headline: adaptive retrieval raises HotpotQA EM 0.560 -> 0.611 and Recall@10 0.787 -> 0.880; compression cuts tokens 38-58 % for 1-2 points of EM; reasoning EM 0.455 -> 0.577 after compression on HotpotQA; SAC-RAG average tokens 1,087-1,918 vs 2,407-3,111 for Adaptive RAG; latency about 27.8 s vs 9.6 s per instance (Naive) on HotpotQA because of extra LLM calls. F1 74.0 (HotpotQA), 66.4 (2Wiki), 40.3 (MuSiQue).

---

## 6. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted, real app, scratch database)
Captured by `python scripts/capture_screens.py --rich --responsive` against a scratch backend (`scripts/serve_scratch.py`); user `student_1792896764`; five documents uploaded (the bundled sample notes + four corpus files: Data Structures, Operating Systems, Database Systems, Algorithms), four questions asked, eight quizzes taken (40 quiz questions). Quiz answers were scripted to simulate a student with different mastery per subject (the script picks the option that restores the sentence from the notes for k of 5 questions): accuracy Data Structures 85 % (20 questions), Algorithms 80 % (5), Operating Systems 60 % (5), Database Systems 30 % (10). Roadmap on the final run: 30 topics, 9 High, 2 Medium, 19 Low.

| File | Screen |
|---|---|
| 01_landing-light.png / 02_landing-dark.png | Landing page (hero, how it works, example answer, stats) light and dark |
| 03_login.png, 04_register.png | Login and registration (register form filled) |
| 05_upload-ready.png | Upload page with the sample notes selected and subject "Data Structures" |
| 06_upload-done.png | "Document processed": 12 topics detected, 4 chunks indexed, topic chips; toast |
| 07_dashboard.png | Dashboard: 5 documents, 4 questions, 40 quiz questions; subject accuracy bars (green/amber/red); recent documents |
| 08_documents.png | Knowledge repository: documents, subjects, detected topics, chunk counts (101/104/112/114/4), quiz and delete buttons |
| 09_ask.png | Ask your notes: "What is a deadlock?" answered from 02_Operating_Systems.txt passage 8 (match 0.46), "Offline mode: key sentences from your notes" badge, recent questions panel, expandable sources |
| 10_quiz-picker.png | Quiz: choose a document |
| 11_quiz-taking.png | Quiz in progress: fill-in-the-blank questions with four options |
| 12_quiz-result.png | Result: 80 % (4 of 5), per-question review with the correct term and topic |
| 13_roadmap.png | Roadmap: High 9 / Medium 2 / Low 19, filter tabs, sortable table with topic, subject, accuracy bar, attempts |
| 14_dashboard-dark.png | Dashboard in dark mode |
| 15_mobile-dashboard.png (360x780), 16_mobile-ask.png (360x780), 17_tablet-roadmap.png (768x1024), 18_mobile-roadmap-dark.png (360x780) | Responsive layouts |

Observation visible on screen 13: roadmap topics are single TF-IDF keywords; several are generic (e.g. "using", "used", "normal", "elements").

---

## 7. Diagrams (`docs/diagrams/`, PNG 150 dpi, drawn with matplotlib from the code) and figures (`docs/figures/`)
Diagrams: 01 system architecture; 02 high-level workflow; 03 DFD level 0; 04 DFD level 1; 05 DFD level 2 (process 2.0 document analysis); 06 DFD level 2 (process 3.0 RAG answering); 07 UML class diagram; 08 sequence (upload); 09 sequence (ask); 10 use-case diagram; 11 ER diagram; 12 flowchart of the core algorithm (answering a question); 13 flowcharts of quiz generation and roadmap priority.
Result figures: fig_retrieval_methods, fig_hit_at_k, fig_by_type, fig_chunk_size, fig_compression, fig_abstention, fig_scaling, fig_api_latency, fig_heading_formats, fig_quiz_quality.

## 8. Reproduce
```
python scripts/fetch_corpus.py                       # corpus (Wikipedia, pinned revisions)
python scripts/eval_questions.py                     # verifies the 72 evidence strings
venv\Scripts\python scripts\run_experiments.py       # experiments/results.json (21 s)
<fastembed venv>\python scripts\dense_baseline.py    # optional dense reference
venv\Scripts\python scripts\serve_scratch.py --data <dir> --port 8301   # scratch backend
venv\Scripts\python scripts\measure_api.py           # experiments/api_latency.json
venv\Scripts\python -m pytest -q                     # 84 tests
python scripts/capture_screens.py --rich --responsive
python scripts/make_figures.py ; python scripts/make_diagrams.py
```
