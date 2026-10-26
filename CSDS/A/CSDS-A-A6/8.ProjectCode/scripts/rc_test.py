"""Chapter 7 content: system testing (ClauseGuard). Counts come from 8.ProjectCode/tests and the runs recorded in docs/REPORT_FACTS.md."""
from __future__ import annotations

from doc_common import CHARTS, metrics

AP = metrics("api")
RU = metrics("rules")
PA = metrics("parity")
CO = metrics("corpus")


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        "ClauseGuard is checked at five levels: automated tests of the backend, measurement of the classifier and the rule engine on labelled clause sets, a run of the non-API "
        "pipeline over the whole CUAD corpus, measured API response times, and a walk-through of the finished product in a real browser with real uploads. The levels answer different "
        "questions. The automated tests ask whether the code behaves as designed, deterministically and without any external service. The labelled sets ask how accurate the "
        "classifier and the rules are. The corpus run asks whether the pipeline survives 510 real contracts of very different shapes. The latency run asks whether the product is responsive, "
        "and the browser walk-through asks whether a person can go from sign-up to a readable report.",
        "The backend suite is written with pytest and FastAPI's test client and lives in `8.ProjectCode/tests`. The Gemini service is the only external dependency of the product, so the "
        "suite replaces it with two deterministic stubs: a fake embedding derived from a hash of the text, and a fake JSON answer for explanations and summaries. Every API test runs against a "
        "throw-away SQLite file created in a temporary directory and a small synthetic centroid matrix, so the tests never touch `data/app.db` and never use API quota. The rule engine, the "
        "segmenter, the complexity score, the clause graph, the vector store, the JWT and password code and the HTTP routes run for real in every test. **The suite contains 73 test cases: 68 pass and 5 "
        "are expected failures (xfail)** that assert the behaviour a better implementation should have and fail today, so that known gaps are reported rather than hidden. The full run takes about 8 seconds.",
        "Because Gemini is stubbed, the suite cannot say anything about the quality of the generated explanations, the safer wording or the summaries, nor about the real classification accuracy. "
        "Those are covered by the measurements of Chapter 8 and by the three real uploads described under functional testing.")


def sec_unit(d):
    d.h2("Unit Testing")
    d.table([["File", "Cases", "What it checks"],
             ["test_rules_graph.py", "26 (22 pass, 4 xfail)", "The eight rules and their severities; each rule fires on its textbook clause; five ordinary clauses raise no flag; case-insensitive matching; several rules on one clause; "
                                                             "the shipped 40-clause set scores false positives 0 and recall 0.941; the three risky combinations, a combination spread over different clauses, a partial combination, two combinations "
                                                             "at once, and the graph JSON (nodes, pairwise edges)"],
             ["test_complexity_parsing.py", "21", "Syllable counter; Flesch score bounded and ordered; legalese density; cross-references; a dense contract scores harder than a plain one; the eight grade boundaries "
                                                  "(0, 19.9, 20, 39.9, 40, 59.9, 60, 80); numbered headings, paragraph fallback, dropped fragments, page numbers, text before the first heading; DOCX and PDF extraction; "
                                                  "unsupported file type; vector store round trip and cosine"],
             ["test_classification.py", "6", "Confident embedding hit makes no model call; close top two below 0.60 triggers the tie-break; a failing tie-break falls back to the embedding label; "
                                             "a category outside the candidates is rejected; the 'Other / Unclassified' floor below 0.35"]],
            "Unit-level tests (53)", widths=[0.24, 0.17, 0.59], font=9)
    d.p("These 53 cases cover the pure logic that must be exact: the regular expressions, the arithmetic of the complexity score, the segmenter and the decision rules of the classifier. "
        "The grade-boundary test is worth a note: it replaces the four component functions so that each difficulty equals the target score, and then checks that the weights sum to one and that "
        "scores of 19.9 and 20, 39.9 and 40, 59.9 and 60 fall on opposite sides of the A/B, B/C and C/D cut-offs.")
    d.table([["ID", "Case", "Expected", "Result"],
             ["U1", "Textbook clause for each of the 8 rules", "The matching rule id is returned", "Pass (8 of 8)"],
             ["U2", "Ordinary clauses (notice termination, payment term, governing law, licence grant, insurance)", "No flag", "Pass (5 of 5)"],
             ["U3", "Shipped 40-clause set", "0 false positives, recall 0.941", "Pass"],
             ["U4", "Three rule ids across four clauses", "Combination termination + no-refund + penalty with clause ids 1, 3, 4", "Pass"],
             ["U5", "Text before the first numbered heading", "Dropped (3 clauses kept, parties line lost)", "Pass; documents a limitation"],
             ["U6", "Keyword-free paraphrases (3 cases)", "Rule should fire", "xfail: rule misses the paraphrase"],
             ["U7", "Fair capped liquidated damages", "No flag desired", "xfail: penalty rule fires"],
             ["U8", "Top-1 below 0.35 on 10-dimensional centroids", "Label 'Other / Unclassified'", "Pass"]],
            "Selected unit test cases", widths=[0.07, 0.38, 0.33, 0.22], font=9)


def sec_integration(d):
    d.h2("Integration Testing")
    d.p("The remaining 20 cases call the application through its HTTP interface with FastAPI's test client, so that routing, JWT authentication, validation, the database and the whole "
        "upload pipeline are exercised together with stubbed Gemini answers.")
    d.table([["Area", "Cases", "What is checked"],
             ["Health, registration, log-in", "8", "Health endpoint reports status ok and port 8106; register then log in; duplicate e-mail gives 400; five-character password, invalid e-mail and missing password give 422; wrong password and unknown user give 401; the stored password hash starts with the bcrypt marker and differs from the password"],
             ["Tokens", "2", "Missing token is refused; a garbage token, an expired token and a token signed with another secret give 401; a token whose user no longer exists gives 401 'User not found'"],
             ["Upload pipeline", "7", "A DOCX with five numbered clauses gives five clause rows, three flagged, a grade, a summary and the combination termination + no-refund + penalty; report, list, clause detail and graph (5 nodes, 3 edges, 1 combination); wrong extension gives 400; empty text gives 400; no key gives 503; a Gemini failure gives 502 and the temporary file is removed; a failed upload leaves no contract row; malformed JSON from Gemini should give 502 but gives 400 (expected failure)"],
             ["Ownership", "2", "Another user gets 404 for the report, the graph and a clause of someone else's contract and sees an empty list; unknown contract and unknown clause give 404"],
             ["Evaluation endpoint", "1", "`/api/eval/metrics` returns the metrics file with `available` true and 40 predatory examples"]],
            "Integration tests (20, one of them an expected failure)", widths=[0.2, 0.08, 0.72], font=9)
    d.table([["Group", "Cases", "Passed", "Expected failures"],
             ["Rules and graph (unit)", "26", "22", "4"],
             ["Complexity, parsing, vector store (unit)", "21", "21", "0"],
             ["Classification (unit)", "6", "6", "0"],
             ["API (integration)", "20", "19", "1"],
             ["**Total**", "**73**", "**68**", "**5**"]],
            "Backend test inventory (pytest 9.1.1, 26 October 2026)", widths=[0.46, 0.14, 0.17, 0.23], font=10, align=["l", "c", "c", "c"])
    d.p("The React front end is exercised only by the browser walk-through described under functional testing; there are no automated front-end tests.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("The functional tests follow the golden path of the product and were run against the live application on 26 October 2026 in Chrome at 1440 x 900, driven by Playwright, with the real Gemini "
        "service. A demonstration user was registered through the sign-up page and three contracts were uploaded through the upload page: an invented one-sided freelance agreement (DOCX), an "
        "invented fair consulting agreement (DOCX) and a real supply agreement from the CUAD corpus typeset to a ten-page PDF. For the demonstration, the backend ran with the text model "
        "`gemini-3.1-flash-lite`, because the default `gemini-flash-latest` had exhausted its free-tier quota of 20 requests per day and timed out. The screenshots in Chapter 8 are the captures made during this run.")
    d.table([["No.", "Requirement", "Test performed", "Observed"],
             ["F1", "Register and sign in", "Sign up as a new user; the app opens the upload page", "Pass"],
             ["F2", "Reject a wrong file type", "Select a .txt file on the upload page", "Pass: the page shows 'Only PDF and DOCX files are supported' and keeps the button disabled"],
             ["F3", "Analyse a one-sided DOCX", "Upload freelance_services_agreement.docx (11 clauses)", "Pass: 8 flags, one for each rule, 3 combinations, grade B (23.3); 113.6 s"],
             ["F4", "Analyse a fair DOCX", "Upload balanced_consulting_agreement.docx (8 clauses)", "Pass: 0 flags, no combination, grade A (13.7); 15.5 s"],
             ["F5", "Analyse a real PDF", "Upload supply_agreement_cuad.pdf (10 pages)", "Pass: 11 clauses, 1 flag (unilateral termination), no combination, grade C (53.8); 54.6 s"],
             ["F6", "Open a flagged clause", "Open clauses 2, 4 and 5 of the freelance contract", "Pass: reason, quoted provision and safer wording shown with the rule's severity"],
             ["F7", "Show the clause graph", "Open the graph of the freelance contract", "Pass: 11 nodes, three combination explanations"],
             ["F8", "List contracts", "Open My contracts", "Pass: three rows with grade, flag count and upload time"],
             ["F9", "Show the evaluation", "Open the Evaluation page after a 9 s wait for the counters", "Pass: precision 100 %, recall 94 %, F1 97 %, CUAD top-1 79 %, top-3 98 %"],
             ["F10", "Protected route", "Open an /app page without a token", "Not executed in the browser; covered by the API tests"]],
            "Functional test cases (live walk-through)", widths=[0.07, 0.22, 0.31, 0.4], font=8.5)
    d.p("Every executed step passed. Two observations qualify the result. First, the grade of the one-sided contract is B because the complexity score measures wording, not fairness. "
        "Second, the labels in the clause table are plausible for about half of the clauses (5 of 11 for the freelance contract and 4 of 8 for the fair contract in the author's reading), a figure "
        "that is indicative only and is discussed in Chapter 8.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Security testing is limited to the automated tests and a review of the code. The tests confirm that a missing, malformed, expired or forged token is refused with 401 (a token signed with another secret "
        "and an expired token were both generated in the test); that a token for a deleted user is refused; that passwords shorter than six characters and invalid e-mail addresses are refused with 422; "
        "that a wrong password and an unknown user give the same 401 message; that duplicate e-mail addresses are refused; that passwords are stored as bcrypt hashes; that another user cannot read a "
        "contract, its graph or its clauses (404, not 403, so the existence of the contract is not revealed); and that the temporary upload file is removed even when the pipeline fails.")
    d.table([["ID", "Attack or misuse", "Expected", "Result"],
             ["S1", "Request without a token", "Refused (403 from the bearer scheme)", "Pass"],
             ["S2", "Garbage bearer token", "401", "Pass"],
             ["S3", "Expired token (exp in the past)", "401", "Pass"],
             ["S4", "Token signed with a different secret", "401", "Pass"],
             ["S5", "Valid token of a deleted user", "401 'User not found'", "Pass"],
             ["S6", "Read another user's contract, graph and clause", "404", "Pass"],
             ["S7", "Password stored in clear text", "Hash differs and starts with the bcrypt marker", "Pass"],
             ["S8", "Upload of a .txt file", "400", "Pass"]],
            "Security test cases", widths=[0.07, 0.4, 0.33, 0.2], font=9.5)
    d.p("**Findings from the review.** The CORS policy allows every origin; the JWT secret falls back to a default string when the environment does not define it; there is no rate limiting; the token "
        "lifetime is 24 hours with no revocation; the upload route trusts the file extension rather than the file content; and the contract text is sent to an external service (Gemini), which is a "
        "confidentiality consideration for real contracts. **Not tested:** penetration testing, HTTPS deployment, cross-site scripting in the front end, malicious PDF or DOCX files, and denial of service through large uploads.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.table([["Case", "Behaviour observed", "Result"],
             ["Upload with extension .txt", "HTTP 400 'Only PDF and DOCX files are supported.' (test and browser)", "Pass"],
             ["DOCX containing only 'Hi'", "HTTP 400 'No readable clauses were found in this document.'", "Pass"],
             ["Scanned PDF without a text layer", "Expected to give the same 400, because no text is extracted and no OCR is attempted (read from the code; not run)", "By design; documented"],
             ["Gemini failure or quota during the pipeline", "HTTP 502 with the Gemini message; nothing stored; temporary file removed; the browser shows the error", "Pass"],
             ["Gemini returns malformed JSON", "`json.JSONDecodeError` is a `ValueError`, so the route answers HTTP 400 (blaming the file) instead of 502", "Defect found (xfail)"],
             ["No API key configured", "HTTP 503 'GEMINI_API_KEY is not configured'", "Pass"],
             ["Text before the first numbered heading (title, parties)", "Silently dropped when the page has two or more headings", "Limitation (U5)"],
             ["Headings other than '1.' or 'Section 1' (Article I, roman numerals)", "Not recognised; the paragraph fallback merges blocks of about 400 characters; 84 of 510 CUAD contracts give fewer than 5 clauses", "Limitation"],
             ["Clause that runs across a page break (PDF)", "Split in two because pages are segmented separately", "Limitation"],
             ["PDF line breaks inside a pattern", "Rules that use `.{0,N}` miss: 6 of 8 rules found in the PDF against 8 of 8 in the DOCX with identical text", "Defect found"],
             ["Phrase 'shall not be entitled to any refund'", "Missed: the pattern expects 'not entitled' without 'be'", "Defect found (probe set)"],
             ["Top-1 similarity of every clause", "Between 0.657 and 0.849 on 240 spans, so the 0.60 tie-break and 0.35 'Unclassified' tests never act", "Defect found"]],
            "Validation and edge cases", widths=[0.34, 0.46, 0.2], font=9)
    d.p("Four of the five expected failures in the suite correspond to defects of the rule engine that the independent probe set exposed: three keyword-free paraphrases (a post-termination "
        "covenant worded without 'non-compete', 'fees once paid cannot be returned', and 'liability ... shall be unlimited') are missed, and fair capped liquidated damages are flagged as a penalty. The fifth was found by reading the code and confirmed by a test: when Gemini returns malformed JSON, the parser raises `json.JSONDecodeError`, which is a subclass of `ValueError`, so the upload route maps it to HTTP 400 ('bad request') instead of 502 ('bad gateway') and the user is told that the file is at fault. They are kept as "
        "tests of the desired behaviour, so that improving the rules turns them into passes.")
    d.figure(CHARTS / "10_format_parity.png", "One contract in three input forms: eight of eight rules fire on the DOCX, six of eight on the PDF, and eight of eight again when whitespace is collapsed before matching", width=3.6)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Response times were measured against the live server on the same machine over 127.0.0.1 (an Intel Core i5-12500 with 12 threads, 15.7 GB of memory, no GPU used, Windows 11) while other jobs were "
        "running, so the figures are indicative rather than a benchmark. The address 127.0.0.1 is used because the name `localhost` adds about two seconds per call on this machine through an IPv6 fallback. "
        "Endpoints that do not call Gemini were repeated 30 times (10 for the bcrypt and error cases), using the contract of the freelance upload (11 clauses).")
    ep = AP["endpoints"]
    rows = [["Request", "Runs", "Median (ms)", "95th percentile (ms)", "Max (ms)"]]
    for k, v in ep.items():
        rows.append([k.replace("/api", ""), str(v["n"]), f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    d.table(rows, "API response times without Gemini (live server)", widths=[0.46, 0.08, 0.15, 0.17, 0.14], font=9, align=["l", "c", "c", "c", "c"])
    up = AP["uploads"]
    d.p(f"The three upload requests include real Gemini calls and are dominated by them: **{up['balanced']['seconds']} s** for the fair contract (8 embeddings and 1 summary), **{up['cuad_pdf']['seconds']} s** for the real "
        f"supply agreement (11 embeddings, 1 explanation and 1 summary) and **{up['freelance']['seconds']} s** for the one-sided contract (11 embeddings, 8 explanations and 1 summary). An embedding call took about 0.7 s while the "
        "evaluation vectors were cached, and, by subtraction, a text call roughly 10 to 25 s with the lite model used for the demonstration, so the upload time grows with the number of flags. The browser's upload request has a "
        "180 s timeout (`timeout: 180000` in `frontend/src/lib/api.js`); a contract with about 14 flags would exceed it even though the server would finish and store the result. By contrast, every read endpoint answers in "
        "under 20 ms at the median, the report in 9.3 ms, and the bcrypt-based log-in and registration take about 255 to 265 ms by design.")
    d.p(f"The non-API part of the pipeline (segmentation, eight regular expressions, combinations and the complexity score) processed all {CO['contracts']} CUAD contracts ({CO['clauses_total']:,} clauses) in "
        f"{CO['total_seconds']} s, which is {CO['mean_seconds_per_contract'] * 1000:.0f} ms per contract, so the local code is not a bottleneck. Embeddings of the 500 training spans and 240 held-out spans were cached in about 7 minutes (about 0.6 s per call, with a few rate-limit retries).")
    d.figure(CHARTS / "08_latency.png", "Measured response times: endpoints without Gemini (log scale, median and 95th percentile) and the three real uploads against the 180 s browser timeout", width=6.0)
    d.p("**Not measured:** concurrent users, memory use under load, behaviour with a large database, the front end's load time, and other hardware.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user-acceptance test was carried out and no lawyer or signatory reviewed the output. What was done is a functional acceptance run by the project team: three uploads through the real interface "
        "(see Functional Testing), which show that the intended flow works from sign-up to a clause-level report with reasons, quoted provisions and safer wording. It does not show that real users find the report "
        "understandable or that its legal reasoning is correct. The generated reasons cite Indian statutes (for example Section 74 of the Indian Contract Act, 1872 for the penalty and Section 27 for the non-compete) and "
        "read plausibly, but nobody qualified in law has checked them, and the safer wording sometimes keeps a restriction (the proposed replacement for the three-year non-compete still forbids soliciting clients for six months). "
        "A review of a sample of outputs by practising lawyers and a pilot with freelancers who read their own contracts are the most important next steps.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "The automated tests stub Gemini, so they say nothing about the quality of the generated explanations, safer wording and summaries, and nothing about real embedding quality.",
        "The 40-clause set that produced the published 100 % precision and 94 % recall was written by the author of the rules; on 40 independently phrased clauses the same rules reach precision 0.786 and recall 0.458 (Chapter 8). The probe set was also written by a project member after reading the rule patterns, so it is independent of the wording of the shipped set but not of the project.",
        "The CUAD classification test uses 240 annotation spans of about 290 characters, not whole clauses of about 1,160 characters, and the split is by span text, not by contract (192 of 240 spans share a contract with a training span; the contract-disjoint score is 0.800, so the effect is small).",
        "The CUAD cross-check of the rules is a proxy only, because CUAD categories such as 'Uncapped Liability' are not defined as predatory.",
        "No Indian contracts were available: CUAD contains US filings, the sample contracts are invented, and only the real supply agreement is a real document (a contract for work at a Canadian university, analysed under a prompt that assumes Indian law).",
        "No browser automation suite, no load or concurrency test, no penetration test and no user study were carried out; all timings come from one machine that was running other jobs.",
    ])
