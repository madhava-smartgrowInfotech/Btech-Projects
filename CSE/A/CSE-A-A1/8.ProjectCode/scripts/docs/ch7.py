"""Chapter 7: System Testing."""

import json
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def _api_row(label, key):
    r = F.API[key]
    return [label, str(r["n"]), f"{r['median_ms']:.1f}", f"{r['p95_ms']:.1f}", f"{r['max_ms']:.1f}"]


def blocks():
    T = F.TESTS
    tf = F.TEST_FILES
    A = F.API
    up = [u["ms"] for u in A["uploads"]]
    A1 = json.load(open(os.path.join(F.EXP_DIR, "api_latency_run1.json"), encoding="utf-8"))
    up1 = [u["ms"] for u in A1["uploads"]]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    b += [H2("7.1 Testing strategy"),
          P("Before this documentation work the project contained a single end-to-end script, `scripts/smoke_test.py`, and no automated tests. The suite described here was written to measure the product as it is, not to confirm it: where the code has a limitation, a test records the current behaviour and the limitation is listed in Section 7.9 and in Chapter 9. "
            "The suite checks behaviour (does an upload create the right rows, is another user's document invisible, is a quiz graded on the server); retrieval and answer quality are measured on a corpus and reported in Chapter 8."),
          P(f"Testing has five layers: small functions tested directly with `pytest`; every API endpoint called through FastAPI's `TestClient` against a temporary SQLite database and upload folder (the suite never touches `instance/app.db`); a separate group of security tests; a scripted browser walk through the real interface; and response times measured on a running server. "
            f"The whole pytest run takes {T['seconds']:.1f} seconds on the development machine ({F.ENV['cpu']}, {F.ENV['ram']} RAM)."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"],
              [["Unit", "Text extraction, chunking, heading and topic detection, file-type check, retrieval engine, quiz generator", "`pytest`, direct import of `utils/`", f"{tf['test_text_extraction.py'] + tf['test_rag_engine.py'] + tf['test_quiz_generator.py']} tests pass"],
               ["Integration and functional", "Every endpoint: authentication, upload, documents, ask, quiz, roadmap, dashboard", "`pytest`, `TestClient`, temporary database", f"{tf['test_api.py']} tests pass"],
               ["Security", "Hashing, injection strings, path traversal, cookie flags, tampered cookie, CORS, isolation between users", "`pytest`", f"{tf['test_security.py']} tests pass"],
               ["End-to-end smoke test", "Register, login, upload, ask, quiz, roadmap, dashboard, delete, logout against the running API", "`scripts/smoke_test.py`", f"{F.SMOKE_TOTAL} of {F.SMOKE_TOTAL} checks pass"],
               ["Front end", "Type check, production build, console errors and layout overflow on 1440, 768 and 360 pixel screens, light and dark", "`npm run build`, Playwright", "Build succeeds; console clean"],
               ["Performance", "Response time of each endpoint; retrieval time against index size", "`scripts/measure_api.py`, `scripts/run_experiments.py`", "Measured (Section 7.8)"]],
              widths=[1.3, 2.7, 1.6, 1.0], align=["l", "l", "l", "c"], size=9),
          P(f"In total **{T['tests']} pytest tests ran: {T['tests'] - T['failures'] - T['errors'] - T['skipped']} passed, {T['failures']} failed, {T['errors']} errored and {T['skipped']} were skipped**, and all {F.SMOKE_TOTAL} smoke checks passed. "
            "Line coverage was not measured, so no coverage figure is claimed. The first run exposed one error, in the test itself (the expected length of the last chunk of a 500-word text was 80 instead of 50); the code under test was correct.")]

    b += [H2("7.2 Unit testing"),
          P("The unit tests import the real modules and mock only the LLM call. Text files are created in a temporary folder, Word files with `python-docx`, and PDF files by a small helper that writes a minimal valid one-page PDF, with or without a text layer, so that no binary fixture is stored."),
          TAB("Unit test cases (tests/test_text_extraction.py, test_rag_engine.py, test_quiz_generator.py)", ["ID", "Test function", "Checks", "Result"],
              [["U1", "test_extract_txt, test_extract_docx_paragraphs, test_extract_pdf_text_layer", "Text is recovered from TXT, DOCX paragraphs and a PDF with a text layer", "Pass"],
               ["U2", "test_extract_docx_ignores_table_cells", "Known limitation: text inside Word tables is not extracted", "Pass (records the limitation)"],
               ["U3", "test_extract_pdf_without_text_layer_is_empty, test_extract_corrupt_pdf_does_not_raise", "A scan-like PDF gives empty text; a corrupt PDF gives `[Could not extract text ...]` and no exception", "Pass"],
               ["U5", "test_chunk_text_size_and_overlap", "500 words give windows of 180, 180, 180 and 50 words; the last 30 words of one window open the next", "Pass"],
               ["U7", "test_detect_subject_hints_standard_headings, _deduplicates_and_caps", "Subject, course, unit and chapter headings are found; duplicates removed; at most 15 returned", "Pass"],
               ["U8", "test_detect_subject_hints_roman_numerals_not_recognised", "Known limitation: `UNIT-I`, `Unit I:` and `Module 1:` give no hints", "Pass (records the limitation)"],
               ["U9", "test_extract_topics_prefers_hints_then_keywords, _short_text_falls_back", "The sample notes give 12 topics starting with the subject; a tiny text gives none", "Pass"],
               ["U11", "test_retrieves_the_right_chunk, test_scores_are_sorted_descending", "The LIFO chunk is ranked first for a LIFO question; scores are positive, at most 1 and sorted", "Pass"],
               ["U12", "test_empty_index_returns_nothing, test_query_without_shared_terms_has_no_results", "No index or no shared term returns an empty list and the message `No relevant content ...`", "Pass"],
               ["U14", "test_extractive_answer_is_taken_from_retrieved_text", "Every word of the answer occurs in the retrieved chunks", "Pass"],
               ["U16", "test_quiz_has_requested_number_and_valid_structure, test_terms_are_not_reused_within_one_quiz", "Five questions, four distinct options, answer index consistent, each term used once", "Pass"],
               ["U17", "test_too_little_text_returns_empty", "Fewer than four candidate terms gives no quiz", "Pass"]],
              widths=[0.4, 2.4, 3.0, 0.9], align=["c", "l", "l", "c"], size=8.5),
          P("Together the unit tests cover every public function of `utils/text_extraction.py`, `utils/rag_engine.py` and `utils/quiz_generator.py`. The LLM call itself (`_llm_answer`) is not exercised against the real service.")]

    b += [H2("7.3 Integration testing"),
          P(f"The {tf['test_api.py']} API tests (`tests/test_api.py`) run the real FastAPI application, the real SQLite schema and the real pipeline in one process, with a fresh user per test so that tests do not depend on one another. "
            "They check the contract between the layers: rows created by an upload are visible through the documents list and the dashboard, the index rebuilt after an upload or deletion changes what a question can find, and quiz results written at submission appear in the roadmap and the subject chart."),
          TAB("Integration test cases (tests/test_api.py)", ["ID", "Test function", "Scenario and expected result", "Result"],
              [["I1", "test_register_login_me_logout", "Register, log in, read the user, log out; `me` returns null afterwards", "Pass"],
               ["I2", "test_upload_txt_creates_document_topics_and_chunks", "The sample notes give 4 chunks and 12 topics; the list shows the chunk count and hides the file path", "Pass"],
               ["I3", "test_ask_answers_from_the_upload_with_sources_and_history", "The LIFO question returns an answer containing `Last In First Out`, the source file name, and an entry in the history", "Pass"],
               ["I4", "test_deleting_a_document_removes_it_from_answers", "After deletion the same question has no sources", "Pass"],
               ["I6", "test_quiz_flow_grades_and_feeds_roadmap_and_dashboard", "Five questions without answer keys; an empty submission scores 0; the roadmap has five High rows; the dashboard counts one document and five attempts", "Pass"],
               ["I7", "test_quiz_submit_with_correct_answers_scores_100", "Submitting the stored answer indexes scores 100 percent and every roadmap row becomes Low", "Pass"],
               ["I9", "test_upload_docx", "A Word file is accepted and indexed", "Pass"]],
              widths=[0.4, 2.5, 3.1, 0.7], align=["c", "l", "l", "c"], size=8.5)]

    b += [H2("7.4 Functional testing"),
          P("Functional tests express the requirements as observable behaviour of the running API. Several apply to the three user stories that matter most: upload and analyse, ask with a cited answer, and practise with a roadmap."),
          TAB("Functional test cases", ["ID", "Requirement", "Test function", "Result"],
              [["F1", "Only PDF, DOCX and TXT files are accepted", "test_upload_rejects_unsupported_type", "Pass"],
               ["F2", "Files above 16 MB are refused", "test_upload_rejects_files_over_16_mb (an 18 MB body gives 413)", "Pass"],
               ["F3", "A document with no extractable text is accepted with a warning and no chunks", "test_upload_empty_text_gives_warning", "Pass"],
               ["F5", "A question must contain text", "test_ask_requires_text", "Pass"],
               ["F7", "A quiz cannot be submitted twice or without being generated", "test_quiz_cannot_be_submitted_twice, test_quiz_submit_without_active_quiz_conflicts (409)", "Pass"],
               ["F8", "A document with too little text cannot produce a quiz", "test_quiz_on_tiny_document_is_refused (422)", "Pass"],
               ["F10", "A new user sees a zero dashboard", "test_dashboard_for_new_user_is_zero", "Pass"]],
              widths=[0.4, 2.8, 2.9, 0.6], align=["c", "l", "l", "c"], size=9)]

    b += [H2("7.5 Validation and edge cases"),
          P("The roadmap rule is the only piece of adaptive logic and was tested at its boundaries. `test_roadmap_priority_thresholds` is parametrised with ten combinations and passes for all of them: 0/1, 1/3 and 49/100 give High; 1/2, 2/4, 7/9 and 79/100 give Medium; 4/5, 80/100 and 5/5 give Low. "
            "`test_roadmap_is_sorted_high_first_then_by_accuracy` checks the order of the list."),
          P("Edge cases outside the unit tests were measured on the corpus and are reported in Chapter 8: heading styles that are not recognised, off-topic questions that still receive an answer, and quiz questions that repeat their own answer. They are not defects of the code against its specification; "
            "they are cases where the behaviour falls short of what the objectives ask for.")]

    b += [H2("7.6 Security testing"),
          P(f"The {tf['test_security.py']} tests of `tests/test_security.py`, together with the nine parametrised authentication checks of `test_api.py`, were written from a list of ordinary web risks."),
          TAB("Security test cases", ["ID", "Risk", "Test function", "Observed behaviour"],
              [["S1", "Unauthenticated access", "test_protected_routes_need_login (9 routes)", "401 on every protected route"],
               ["S2", "Password disclosure", "test_passwords_are_stored_hashed", "Stored value is a scrypt or pbkdf2 hash that does not contain the password"],
               ["S3", "SQL injection", "test_sql_injection_in_login_and_register_is_inert, test_sql_injection_in_question_is_stored_literally", "Login with `' OR '1'='1' --` fails; the string is stored as text; tables remain"],
               ["S4", "Path traversal", "test_path_traversal_in_filename_stays_inside_user_folder, test_filename_with_only_dots_is_rejected", "`../../evil.txt` becomes `evil.txt` inside the user's folder; `..` is rejected"],
               ["S6", "Session cookie", "test_session_cookie_flags", "HttpOnly and SameSite Lax present; Secure absent (recorded limitation)"],
               ["S8", "Cross-site scripting", "test_script_in_subject_is_returned_as_plain_json_text", "A script tag in a subject is stored verbatim and returned as JSON, so React escapes it"],
               ["S10", "Access to other users' data", "test_users_cannot_see_or_delete_each_others_documents", "Another user's documents are not listed, deletion and quiz return 404, and the search finds no source"],
               ["S11", "File-name collision", "test_known_limitation_same_filename_shares_one_file_on_disk", "Two uploads of one name share a path; deleting one removes the file of the other (documented)"]],
              widths=[0.4, 1.4, 2.7, 2.1], align=["c", "l", "l", "l"], size=8.5),
          P("These tests establish that the common attacks do not succeed. They do not amount to a penetration test: rate limiting, CSRF protection, TLS and secret management are absent from the design and were not tested, and no external scanner was used.")]

    b += [H2("7.7 End-to-end smoke test and browser run"),
          P(f"`scripts/smoke_test.py` drives a running backend with the standard library and checks {F.SMOKE_TOTAL} points in order, from health and anonymous rejection through registration, login, upload, question, quiz, roadmap and dashboard to deletion and logout; all {F.SMOKE_TOTAL} pass against the scratch backend used for the measurements."),
          P("`npm run build` runs the TypeScript compiler and the production bundler without errors. `scripts/capture_screens.py --rich --responsive` then drives the real interface in Chrome through Playwright (five uploads, four questions, eight quizzes, every page in light and dark themes at 1440, 768 and 360 pixels) "
            "and records console errors, page errors, failed requests and horizontal overflow; the final run reported none. This checks stability and layout, not usability.")]

    b += [H2("7.8 Performance testing"),
          P(f"Latency was measured against a running backend on 127.0.0.1 (the host name `localhost` added about two seconds per call on this machine through an IPv6 fallback) with one user whose six corpus files ({F.API['total_chunks_indexed']} chunks) were indexed. Each endpoint was called "
            f"{F.API['runs_per_endpoint']} times. The table gives the second of two runs; the first run agreed on every median."),
          TAB("HTTP response time (milliseconds)", ["Endpoint", "Calls", "Median", "95th percentile", "Maximum"],
              [_api_row("GET /api/health", "health"), _api_row("POST /api/auth/login (password hashing)", "login"), _api_row("GET /api/dashboard", "dashboard"),
               _api_row("GET /api/documents", "documents_list"), _api_row("GET /api/ask/history", "history"), _api_row("GET /api/roadmap", "roadmap"),
               _api_row("POST /api/ask", "ask"), _api_row("POST /api/quiz/generate", "quiz_generate"), _api_row("POST /api/quiz/submit", "quiz_submit")],
              widths=[2.8, 0.6, 0.8, 1.2, 1.0], align=["l", "c", "r", "r", "r"], size=9.5),
          P(f"Most endpoints answer within a few milliseconds and a question within about {A['ask']['median_ms']:.0f} ms. Login takes about {A['login']['median_ms']:.0f} ms because the password hash is computed on purpose. "
            f"Quiz submission has a normal median of {A['quiz_submit']['median_ms']:.1f} ms but a 95th percentile of {A['quiz_submit']['p95_ms']:,.0f} ms: one or two of the {A['runs_per_endpoint']} calls in each run took one to two seconds. "
            "The call writes five rows and commits to SQLite; slow commits are the likely explanation, but the cause was not isolated and the outliers are reported as measured."),
          P(f"Uploading is the slow path because each upload re-indexes all of the user's chunks: one file of 88 to 110 kB took between {min(up):.0f} and {max(up):.0f} ms in the tabulated run and {min(up1):.0f} to {max(up1):.0f} ms in the earlier run, and deleting a document with re-indexing took {A['delete']:.0f} and {A1['delete']:.0f} ms. "
            "The spread comes from load of other jobs on the shared machine, so these figures are an order of magnitude only."),
          TAB("Retrieval time against index size (in-process, 72 queries)", ["Chunks in index", "Words", "Index build (ms)", "Retrieve, median / p95 (ms)", "Retrieve + extractive answer, median / p95 (ms)"],
              [[f"{s['chunks']:,}", f"{s['words']:,}", f"{s['index_build_ms']:.0f}", f"{s['retrieve_ms_median']:.1f} / {s['retrieve_ms_p95']:.1f}", f"{s['answer_ms_median']:.1f} / {s['answer_ms_p95']:.1f}"] for s in F.SCALE],
              widths=[1.1, 1.0, 1.1, 1.6, 1.8], align=["r", "r", "r", "c", "c"], size=9.5),
          P("Retrieval time grows roughly in proportion to the number of chunks, because the query is compared with every chunk; one student's notes are served in tens of milliseconds. The dense reference needed "
            f"{F.DENSE['embed_chunks_s']:.0f} seconds to embed the {F.CORPUS['chunks']} chunks and {F.DENSE['embed_query_ms_each']:.1f} ms per query on the same CPU, which is why it is kept outside the product."),
          FIG(F.fig("fig_api_latency.png"), "Median and 95th-percentile response time of the API endpoints (logarithmic scale).", 4.8)]

    b += [H2("7.9 Behaviours observed rather than asserted"),
          P("The following findings come from the experiments of Chapter 8 and from the characterisation tests. None is a failed test; each is a gap between behaviour and objective, repeated in the limitations of Chapter 9."),
          B(f"**Off-topic questions are answered.** {F.ABS['off_topic_answered_by_shipped']} of {F.ABS['n_off_topic']} questions unrelated to the notes still received an extractive answer, because the engine refuses only when no query term overlaps any chunk. The 'strictly from the uploaded material' objective is satisfied for what is returned (every answer word comes from the chunks) but not for whether it should be returned.",
            f"**Heading styles.** `UNIT-I`, `Unit I:`, `Module 1:` and `1. Title` yield no hints ({F.DOCAN['heading_formats']['UNIT-I Title']['units_found']} of {F.DOCAN['heading_formats']['UNIT-I Title']['of']} units), so a syllabus in those styles gets keyword topics only.",
            f"**Quiz quality.** Every generated question is structurally valid, but in {F.pct(F.QUIZ['answer_repeated_in_stem_rate'])} of 900 the answer term still appears in the question and in {F.pct(F.QUIZ['ambiguous_rate'])} another option appears there too; a manual review of 30 questions rated {F.AUDIT['summary']['acceptable']} acceptable, {F.AUDIT['summary']['ambiguous']} ambiguous and {F.AUDIT['summary']['poor']} poor.",
            "**Process-local state.** The index cache and the active-quiz dictionary live in one Python process; two server workers would not share them, and a restart discards an open quiz. This was not tested because it needs a multi-process deployment.",
            "**Roadmap topics.** Topics are single TF-IDF keywords, so some are generic words, and a keyword shared by two subjects merges their results.")]

    b += [H2("7.10 User acceptance"),
          P("**No user study was carried out.** No student other than the project team used the system, so no satisfaction, usability or learning-gain result exists and none is claimed. What was done is a scripted acceptance walk-through against the six objectives of the project, executed by `capture_screens.py` with real uploads in the real interface. "
            "The script plays a student who answers a chosen number of quiz questions correctly by selecting the option that restores the sentence from the notes and a wrong option for the rest. The resulting accuracies (Data Structures 85 percent, Algorithms 80, Operating Systems 60, Database Systems 30) are therefore simulated and demonstrate the roadmap logic, not the learning of a real student."),
          TAB("Acceptance walk-through against the objectives", ["No.", "Objective", "Evidence in the walk-through", "Verdict"],
              [["1", "Ingest syllabi, notes and question banks and extract subjects, units and topics", "Five documents uploaded; topics shown as chips (12 per file); heading hints found for `Subject:` and `Unit n:` layouts only", "Partly met"],
               ["2", "Store content so that it can be searched semantically", "Content stored as chunks and searched by TF-IDF; no embeddings in the product", "Not met"],
               ["3", "Answer strictly from the material and cite the source", "Answers made of the student's own sentences, with file, passage number and match score; off-topic questions are not refused", "Mostly met"],
               ["4", "Compress retrieved context within the model's limit", "Extractive sentence selection shortens the context; not learned and not question-aware", "Partly met"],
               ["5", "Generate personalised roadmaps and revision schedules", "Roadmap ranks topics by quiz accuracy; no schedule", "Partly met"],
               ["6", "Show coverage, study velocity and engagement on a dashboard", "Counts of documents, questions and quiz attempts and a subject accuracy chart; no coverage or velocity", "Partly met"]],
              widths=[0.4, 2.2, 3.1, 0.9], align=["c", "l", "l", "c"], size=9)]

    b += [H2("7.11 The limits of the testing done"),
          B("**No user study and no real student documents.** The corpus is Wikipedia text; real notes, scanned syllabi and tables inside documents were not measured.",
            "**Scanned PDFs.** A PDF without a text layer is handled gracefully (empty text, warning), but optical character recognition is outside the system and was not tried.",
            "**LLM mode.** No API key was available, so the optional Claude branch was tested only with the call mocked. Its answer quality, cost and latency are unknown.",
            "**Scale and concurrency.** All timings are for one user on one machine that was shared with other jobs. Concurrent users, long-running sessions and multi-process deployment were not tested.",
            f"**Statistical power.** The retrieval measurements use {F.CORPUS['questions']} questions; the 95 percent bootstrap interval for the shipped retriever's Hit@4 is {F.RET_CI['hit4'][0]:.3f} to {F.RET_CI['hit4'][1]:.3f}, so differences of a few points between retrievers are within noise.",
            "**Accessibility and cross-browser.** Only Chrome was driven; no screen-reader or colour-contrast audit was done.")]
    return b
