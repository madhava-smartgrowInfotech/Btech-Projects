"""Chapter 7: System Testing (SymptoTrackAI, implemented as CareLens AI). All numbers come from docs/metrics/*.json via facts."""

import json
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

SEC = json.load(open(os.path.join(F.METRICS_DIR, "security.json"), encoding="utf-8"))
SR = {r["id"]: r for r in SEC["rows"]}
SP, S2, S3, S4 = "S1_shipped_protocol_30", "S2_verbatim_leave_one_out_176", "S3_two_symptoms_leave_one_out_176", "S4_lay_language_60"
RS = F.RET["hybrid_rerank"]


def ok(x):
    return "Pass" if x else "Fail"


def _pytest_result():
    return ok(F.PYTEST_PASSED == F.PYTEST_TOTAL)


def _loc_tests():
    n = 0
    for fn in ("tests/test_carelens.py", "tests/__init__.py"):
        p = os.path.join(F.CODE, fn)
        if os.path.exists(p):
            n += sum(1 for l in open(p, encoding="utf-8") if l.strip())
    return n


def _st(stage):
    return F.LAT["stages_ms"][stage]


def blocks():
    pr = _pytest_result()
    sm = ok(F.SMOKE_PASSED == F.SMOKE_TOTAL)
    A = F.LAT["pipeline_answer_with_local_generator_ms"]
    Bk = F.LAT["pipeline_answer_fallback_only_ms"]
    fb, t5 = F.LAT_FB, F.LAT_T5
    sec_fail = SEC["failed"]
    s = F.SAF
    lit, par = s["by_group_pos"]["literal"], s["by_group_pos"]["paraphrase"]
    ordn, hard = s["by_group_neg"]["ordinary"], s["by_group_neg"]["hard"]
    flt = s["filter"]
    rel = F.REL
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing Strategy"),
          P(f"SymptoTrackAI, implemented as the {F.APP_NAME} application, was tested in six layers. Single functions (query expansion, fusion, safety rules, password hashing, the generator fallback) are tested in isolation; "
            "the API is tested in-process against the real application object with a real retrieval round trip; the whole stack, including the React web server and its proxy, is exercised by a smoke test that drives a running "
            "server over HTTP; security and input validation were probed with a script written for this report; the retrieval, relevance and safety components were **measured** on probe sets; and every screen was walked in a real browser while the "
            f"screenshots of Chapter 8 were captured. The automated tests live in tests/ ({_loc_tests()} non-blank lines) and scripts/smoke_test.py; the probes live in scripts/measure_metrics.py, scripts/measure_security.py and scripts/probe_data.py."),
          P("What the tests establish is that the code behaves as designed on the cases tried. They do not establish clinical correctness: the knowledge base is synthetic and no clinician reviewed an answer, so none of the results below says "
            "how the system would perform on real patients (Section 7.9)."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"], [
              ["Unit", "Query expansion, safety rules and filter, password hashing, fusion, generator fallback", "pytest, in-process", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests pass ({pr})"],
              ["Integration", "Registration, chat, history isolation, validation and a retrieval round trip", "pytest with FastAPI TestClient", f"Included in the {F.PYTEST_TOTAL} tests"],
              ["Functional (end to end)", "Health, proxy, sign-in, chat, emergency, history search, detail, delete, about, registration, logout", "scripts/smoke_test.py against the running servers", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks pass ({sm})"],
              ["Security and validation", "Sessions, tokens, cookie, input bounds, isolation between users", "scripts/measure_security.py", f"{SEC['passed']} of {SEC['n']} probes pass; {len(sec_fail)} findings"],
              ["Measured probes", "Retrieval configurations, relevance display, generator, safety rules, answer filter, latency", "scripts/measure_metrics.py", "Sections 7.6 and 7.7"],
              ["Browser walk", "Every screen, light and dark, with real answers; console, page and HTTP errors", "scripts/capture_docs_screens.py (Playwright, Chrome)", "All screens captured; no console error"],
          ], widths=[1.2, 2.3, 1.7, 1.1], size=9, align=["l", "l", "l", "l"])]

    # ------------------------------------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit Testing"),
          P(f"The repository contains {F.PYTEST_TOTAL} pytest functions. They are listed with what each asserts; none is a placeholder. No tests were added to the product for this report."),
          TAB("Automated pytest cases", ["ID", "Test function", "Input", "Assertions", "Result"], [
              ["T1", "test_normalize_and_expand", "'I have high fever, headache and body pain'", "Normalised text contains 'fever'; hypothetical text contains 'Medical symptom presentation'", pr],
              ["T2", "test_safety_emergency", "'severe chest pain and difficulty breathing'; 'I have a mild headache'", "First is flagged 'emergency'; second is 'routine' or 'caution'", pr],
              ["T3", "test_safety_filter_removes_dosage", "'take antibiotics daily'", "Output contains 'removed'", pr],
              ["T4", "test_password_hashing", "'Secret123'", "Hash differs from the password; correct password verifies; wrong one does not", pr],
              ["T5", "test_hybrid_fuse", "Two dense hits and one lexical hit", "The record found by both retrievers is ranked first", pr],
              ["T6", "test_generator_fallback", "Generator without a model, one evidence record", "Answer contains 'not a diagnosis'", pr],
              ["T7", "test_auth_and_history_isolation", "Two accounts; user 1 asks 'I have fever and cough'", "Chat returns 200; after switching to user 2, the consultation of user 1 gives 404", pr],
              ["T8", "test_api_validation", "'hi'; a 5000-character message", "Both rejected with 400 or 422", pr],
              ["T9", "test_retrieval_roundtrip", "'high fever, headache and body pain', top 3", "At least one evidence record and a top condition", pr],
          ], widths=[0.4, 1.7, 1.7, 2.2, 0.5], size=8.5, align=["c", "l", "l", "l", "c"]),
          P(f"The suite ran in {F.PYTEST_SECONDS:.0f} seconds, most of it model loading. Two tests (T5, T6) use hand-made inputs and test the logic only; T9 only checks that retrieval returns something, not that it is right, "
            "which is why correctness is measured separately in Section 7.6. A weakness of the suite is that T7 and T8 write their test users into the real database file (data/carelens.db), which is why the file is excluded from version control. "
            "The suite does not test the safety rules beyond one positive and one negative example, the relevance computation, the history search or the deletion route; those are covered by the smoke test and the probes.")]

    # ------------------------------------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration and Functional Testing"),
          P("scripts/smoke_test.py needs the backend on its port and the Vite server running. It talks to the application the way the browser does, through the web port and its /api proxy, with a cookie jar, and uses the demo account "
            "and one throw-away account. Its checks are grouped below; all of them pass."),
          TAB("Functional checks of the smoke test", ["Group", "Checks", "Expected", "Result"], [
              ["Availability", "Backend health on the API port; frontend serves the app; proxy reaches the API", "200 and the expected markers", sm],
              ["Access control", "History without sign-in; wrong password", "401 and 401 with 'Invalid'", sm],
              ["Session", "Demo login; the cookie is accepted by /api/auth/me", "200 and the demo e-mail", sm],
              ["Chat", "A fever query returns an answer and at least one evidence record with the card fields; the safety flag is a valid value", "200; disease, symptoms, description, guidance, severity and relevance present", sm],
              ["Emergency", "'severe chest pain and difficulty breathing'", "safety_flag = emergency", sm],
              ["Validation", "A one-character message", "422", sm],
              ["History", "The new consultation is listed; searching 'fever' returns only matching rows; the detail has its evidence", "200 and the expected rows", sm],
              ["Deletion", "Both test consultations are deleted; the deleted one then gives 404", "200, 200, 404", sm],
              ["About", "The metrics endpoint returns the stored figures and the knowledge-base size", "200 with top1_accuracy and kb_records", sm],
              ["Registration", "New account; duplicate e-mail; the new account's history is empty; logout clears the session", "200, 400, empty list, 401", sm],
          ], widths=[1.1, 2.9, 1.7, 0.6], size=9, align=["l", "l", "l", "c"]),
          P(f"The {F.SMOKE_TOTAL} checks pass. The smoke test uses the fallback or the model generator, whichever the backend loaded, and tests only the shape of the answer; it cannot notice that an answer is an echo of its prompt (Section 7.6.3)."),
          P("The browser itself was exercised by the capture script, which signs in through the real form, sends eight real questions (a routine one, a lay-language one, a caution case, an emergency and four more), opens the history, the search, "
            "a consultation and the deletion dialog, switches the theme and loads the pages at phone width. It records console errors, uncaught page errors and failed requests and exits with an error if it sees any; it saw none.")]

    # ------------------------------------------------------------------------------------------------ 7.4
    grp = {}
    for r in SEC["rows"]:
        grp.setdefault(r["id"][0], []).append(r)
    names = {"A": "Accounts and sessions", "T": "Token handling", "V": "Input validation", "I": "Isolation and storage"}

    def gcount(k):
        rr = grp[k]
        return f"{sum(x['pass'] for x in rr)} of {len(rr)}"

    _obs = {"A5": "Cookie sent without the Secure attribute", "A11": "401 on all 15 attempts; no 423 or 429", "T6": "Key equals the value written in app/config.py"}
    sec_rows = [[r["id"], r["check"], r["expected"], _obs.get(r["id"], str(r["observed"])), ok(r["pass"])] for r in SEC["rows"] if not r["pass"]]
    b += [H2("7.4 Security Testing"),
          P(f"{SEC['n']} black-box probes were run against the API in-process with a scratch database (scripts/measure_security.py; the full list is in docs/metrics/security.json). They test who can reach what, how tokens are checked, "
            f"how input is bounded, and whether one user can see another's data. {SEC['passed']} pass and {len(sec_fail)} fail; the failures are real weaknesses and are listed rather than hidden."),
          TAB("Security probes by group", ["Group", "Probes passed", "Examples of what was checked"], [
              [names["A"], gcount("A"), "No access without sign-in; httponly and SameSite cookie; duplicate e-mail 400; password of 5 characters rejected; malformed e-mail rejected; e-mail case-insensitive"],
              [names["T"], gcount("T"), "Valid token accepted; altered signature, foreign key, expired and unsigned (alg none) tokens and a token for a non-existent user all give 401"],
              [names["V"], gcount("V"), "Message length bounds 3 and 2000 (2 and 2001 rejected); missing or non-JSON body 422; markup stored verbatim as text; SQL meta-characters in the search harmless; a request for a prescription yields no dosage text"],
              [names["I"], gcount("I"), "Another user gets 404 on read and delete and sees an empty list; deletion works; history is closed after logout; stored password is a bcrypt hash"],
          ], widths=[1.5, 0.9, 3.9], size=9, align=["l", "c", "l"]),
          P("Authentication is sound where it was tested: tokens with a wrong signature, a different key, an expired time or no signature at all are refused, the cookie is not readable by page scripts, other users' consultations answer 404 (not 403), "
            "and passwords are stored as bcrypt hashes. The probes also found three weaknesses."),
          TAB("Security findings", ["ID", "Probe", "Expected", "Observed", "Result"], sec_rows, widths=[0.4, 2.0, 1.6, 1.6, 0.6], size=9, align=["c", "l", "l", "l", "c"]),
          B("**A5, no Secure flag:** the cookie would also be sent over plain HTTP; this matters only if the application is deployed behind HTTPS and would be fixed by setting secure=True for non-local hosts.",
            "**A11, no limit on failed sign-ins:** fifteen consecutive wrong passwords were all answered 401; there is no rate limit or lock-out, so a password could be guessed by repetition.",
            "**T6, default signing key:** unless CARELENS_SECRET_KEY is set, tokens are signed with the key written in app/config.py, which anyone with the source can use to forge a token. The application is meant for a single local machine, where this is a low risk, "
            "but it must be changed for any shared deployment."),
          P("Not tested: cross-site request forgery beyond the SameSite setting, denial of service by long-running requests, dependency vulnerabilities, the Docker deployment and transport security. No penetration test by a third party was done.")]

    # ------------------------------------------------------------------------------------------------ 7.5
    b += [H2("7.5 Validation and Edge Cases"),
          TAB("Edge cases tried on the chat route and their outcomes", ["Input", "Expected", "Observed"], [
              ["Message of 2 characters", "Rejected", f"{SR['V1']['observed']} (validation error)"],
              ["Three spaces", "Rejected", f"{SR['V2']['observed']} ('Please describe your symptoms.')"],
              ["Message of 3 characters", "Accepted", f"{SR['V3']['observed']}"],
              ["Message of 2000 characters", "Accepted", f"{SR['V4']['observed']}"],
              ["Message of 2001 characters", "Rejected", f"{SR['V5']['observed']}"],
              ["Body without a query / not JSON", "Rejected", f"{SR['V6']['observed']} / {SR['V7']['observed']}"],
              ["Markup in the message", "Stored as plain text", "Returned verbatim; the React interface renders text, not HTML"],
              ["Complaint outside the knowledge base (15 tried)", "Weak or no match", f"All {rel['out_kb_n']} still returned a top record shown as 'Strong match' (Section 7.6.2)"],
              ["Emergency in paraphrased words (12 tried)", "Emergency banner", f"None of {par['n']} flagged (Section 7.6.4)"],
              ["Negation or history mentioning an emergency word (10 tried)", "No emergency banner", f"{len(hard['false_emergency'])} of {hard['n']} wrongly flagged"],
          ], widths=[2.5, 1.4, 2.4], size=9, align=["l", "l", "l"]),
          P("The bounds and malformed-input cases behave as designed. The last three rows are the cases where the design does not hold, and they are the most important test results of this chapter: the system always answers, "
            "the displayed relevance does not tell the user when the knowledge base does not cover the complaint, and the safety rules depend on literal wording. Not tried: non-English text, emoji, extremely long single words, "
            "queries in a different script, and concurrent requests.")]

    # ------------------------------------------------------------------------------------------------ 7.6
    def cell(cfg, st, key="top1"):
        return f"{F.RET[cfg][st][key] * 100:.1f}"

    rows = [[F.RET[c]["label"], cell(c, SP), cell(c, S2), cell(c, S3), cell(c, S4)] for c in F.CFG_ORDER]
    b += [H2("7.6 Probe Measurements"),
          H3("7.6.1 Retrieval accuracy by configuration"),
          P(f"The retrieval configurations were compared on the four query sets of Section 6.2.3 (the table gives Top-1 accuracy in per cent, the share of queries whose first record is of the right condition). The shipped protocol column "
            f"leaves the held-out record in the index and is the protocol of the stored results/metrics.json; the other columns remove it. With {F.KB['records']} records, all sets are small, so the 95% interval of the shipped configuration is wide: "
            f"{F.ci('hybrid_rerank', S2)} on S2, {F.ci('hybrid_rerank', S3)} on S3 and {F.ci('hybrid_rerank', S4)} on S4."),
          TAB("Top-1 accuracy (%) by retrieval configuration", ["Configuration", "S1 shipped protocol (n=30)", "S2 verbatim, leave-one-out (n=176)", "S3 two symptoms (n=176)", "S4 lay language (n=60)"],
              rows, widths=[2.2, 1.0, 1.1, 1.0, 1.0], size=9, align=["l", "c", "c", "c", "c"]),
          FIG(F.fig("f02_ablation.png"), "Top-1 accuracy of the seven retrieval configurations on verbatim, two-symptom and lay-language queries.", 5.6),
          P(f"Four observations follow. First, the stored 100% figure is reproduced only by the shipped protocol, where the answer is in the index; removing the held-out record gives {F.pct(F.ret('hybrid_rerank', 'S1_leave_one_out_30'))} on the same 30 queries and the 100% is an upper bound for the wiring, as the About page itself says. "
            f"Second, lexical search alone is strong on this base ({cell('bm25', S2)}% on verbatim queries, {cell('bm25', S4)}% on lay queries), because queries and records share words; dense search alone is weaker on verbatim queries ({cell('dense', S2)}%) than on lay ones ({cell('dense', S4)}%), so each retriever covers the other's failures. "
            f"Third, the cross-encoder improves the fused order on lay and two-symptom queries ({cell('hybrid', S4)}% to {cell('hybrid_rerank', S4)}% and {cell('hybrid', S3)}% to {cell('hybrid_rerank', S3)}%). "
            f"Fourth, the rule-based HyDE-style expansion did not help: without it the shipped configuration scores {cell('hybrid_rerank_nohyde', S4)}% on lay queries and {cell('hybrid_rerank_nohyde', S2)}% on verbatim queries, against {cell('hybrid_rerank', S4)}% and {cell('hybrid_rerank', S2)}% with it. "
            f"With n = {F.RET['hybrid_rerank'][S4]['n']} the difference on lay queries is {RS[S4]['n_misses']} queries and lies inside the sampling interval, so the honest conclusion is that no benefit was shown. The offline mode (TF-IDF vectors, no reranker) drops to {cell('hybrid_tfidf', S4)}% on lay queries."),
          P("The two lay-language queries missed by the shipped configuration were 'my nose will not stop running and I have a slight cough, nothing serious' (Common Cold returned as Allergic Rhinitis) and 'a slow-rising fever for days, feeling weak, no appetite, abdominal pain' "
            "(Typhoid returned as Appendicitis). Both are confusions between conditions that share symptoms in the knowledge base. On two-symptom queries the misses are of the same kind: 'I have congestion and runny nose' retrieves Allergic Rhinitis for Common Cold, and 'I have fever and chills' retrieves Malaria for Pneumonia."),
          FIG(F.fig("f03_protocol_comparison.png"), "The shipped configuration under four protocols: the stored protocol is an upper bound.", 5.0),
          H3("7.6.2 Relevance display"),
          P(f"For all {rel['in_kb_n']} lay queries and all {rel['out_kb_n']} complaints outside the knowledge base (for example 'my tooth aches badly when I drink cold water' or 'lower back pain after lifting heavy boxes'), the best record is displayed with relevance 100% and the label 'Strong match'. "
            f"Through the real pipeline, {rel['out_kb_labels_via_pipeline_answer'].get('Strong match', 0)} of {rel['out_kb_n']} out-of-base complaints came out as 'Strong match'. The cause is the min-max rescaling of Section 6.3.5. "
            f"The raw cross-encoder score, which the interface discards, does separate the two groups: its mean is {rel['raw_rerank_in_kb']['mean']} for in-base queries (range {rel['raw_rerank_in_kb']['min']} to {rel['raw_rerank_in_kb']['max']}) and {rel['raw_rerank_out_kb']['mean']} for out-of-base ones (range {rel['raw_rerank_out_kb']['min']} to {rel['raw_rerank_out_kb']['max']}), "
            f"and the area under the ROC curve for telling them apart is {rel['auroc_in_vs_out_by_raw_rerank_score']:.2f} (raw hybrid score: {rel['auroc_in_vs_out_by_raw_hybrid_score']:.2f}). The information needed for an honest 'no match' exists and is not shown."),
          FIG(F.fig("f05_relevance_display.png"), "Raw cross-encoder score of the best record for in-base and out-of-base queries, against the displayed 100%.", 5.2),
          H3("7.6.3 Generated answers"),
          P(f"The local generator was run on {F.GEN['n']} queries. In {F.GEN['echo_answers']} of them ({F.pct(F.GEN['echo_rate'], 0)}) the 'answer' was the instruction and the retrieved context, unchanged, labelled {F.GEN['generator_label']}. "
            f"The installed Transformers {F.GEN['transformers_version']} no longer provides the task the code requests ({F.GEN['text2text_task_in_installed_transformers']}), so the code falls back to a task that, for a T5 model, returns its input. The requirements file asks only for transformers 4.38 or newer, so a fresh install picks up the version that breaks it. "
            f"The deterministic fallback, in contrast, named only conditions among the retrieved records in {F.GEN['fallback_names_only_retrieved_conditions']} of {F.GEN['n']} answers, which is guaranteed by its construction. Groundedness was not judged by a person or a model: the only check is this structural one, so the objective of grounded, cited answers is met in structure (the evidence cards) and not shown for the generated text."),
          H3("7.6.4 Safety rules"),
          P(f"The emergency layer was tested with {s['n_pos']} emergency descriptions and {s['n_neg']} non-emergency texts written by the team. {lit['n']} descriptions used the rules' own wording and {par['n']} used everyday paraphrases ('gasping for air', 'I do not want to live anymore', 'worst stomach pain of my life'). "
            f"The layer flagged {lit['detected']} of {lit['n']} literal descriptions and **{par['detected']} of {par['n']} paraphrases**; overall recall is {s['emergency_recall']:.3f} (95% interval {s['recall_ci'][0]:.2f} to {s['recall_ci'][1]:.2f}). The one literal miss was 'lips swollen and cannot breathe', because the rule expects 'swollen lips' first. "
            f"None of the paraphrases was flagged even as 'caution'. Among the non-emergency texts, all {ordn['n']} ordinary ones were routine, but {len(hard['false_emergency'])} of the {hard['n']} hard negatives (negation or history, such as 'I do not have difficulty breathing, only a blocked nose' and 'my grandmother had a stroke last year') raised an emergency banner "
            f"and {len(hard['caution'])} more raised a caution; precision is {s['emergency_precision']:.2f}."),
          FIG(F.fig("f06_safety_rules.png"), "Safety layer: recall on literal and paraphrased emergencies, and false alarms on ordinary and hard negative texts.", 5.2),
          P(f"The answer filter was tried on {flt['n']} sentences with medication instructions. It cleaned {flt['removed']} of them. Of the ten sentences that contained one of its five listed phrases it cleaned {flt['listed_removed']}: the detection ignores case but the replacement does not, so 'Take ibuprofen every six hours' and 'Dosage: one tablet daily' passed through unchanged; "
            "unlisted drugs ('Take paracetamol 500 mg every four hours', 'Take amoxicillin three times a day') were not touched at all. In normal operation the fallback answer is built from knowledge-base guidance that contains no dosages, so the filter rarely has anything to remove; it is not a reliable defence if a generator ever produces dosage text.")]

    # ------------------------------------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance Testing"),
          P(f"Performance was measured on one CPU-only PC ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, Windows 11, Python {F.ENV['python']}) with the models already loaded, on {F.LAT['n']} queries. "
            "The first request after start-up must load the models and the indexes, which took about a minute in the measurement script. The table gives the pipeline stages, each timed in its own pass."),
          TAB("Pipeline stage times (milliseconds, 30 queries, warm models)", ["Stage", "Mean", "Median", "95th percentile"],
              [[lab, f"{_st(k)['mean']:.2f}", f"{_st(k)['median']:.2f}", f"{_st(k)['p95']:.2f}"] for k, lab in (("expand", "Normalise and expand"), ("embed", "Embed query (MiniLM)"), ("faiss", "FAISS search"), ("bm25", "BM25 search"),
                                                                                                                  ("fuse", "Fusion"), ("rerank", "Cross-encoder rerank (15 pairs)"), ("safety", "Safety check"))],
              widths=[2.8, 1.1, 1.1, 1.3], size=10, align=["l", "c", "c", "c"]),
          P(f"The cross-encoder is the dominant stage at {_st('rerank')['mean']:.0f} ms on average; the embedding costs {_st('embed')['mean']:.0f} ms and everything else together under 5 ms. The whole pipeline call takes {Bk['mean']:.0f} ms on average (95th percentile {Bk['p95']:.0f} ms) "
            f"with the evidence-based answer and {A['mean']:.0f} ms ({A['p95']:.0f} ms) when the local generator is called; the model adds about {F.GEN['mean_generate_ms']:.0f} ms to produce, and here to return, its echo."),
          FIG(F.fig("f04_latency_stages.png"), "Time per pipeline stage and for the whole call, with and without the local generator.", 5.2),
          TAB("HTTP latency of POST /api/chat on 127.0.0.1 (30 requests, milliseconds)", ["Generator", "Mean", "Median", "95th percentile", "Maximum", "First request"], [
              ["Evidence-based fallback", f"{fb['chat_ms']['mean']:.0f}", f"{fb['chat_ms']['median']:.0f}", f"{fb['chat_ms']['p95']:.0f}", f"{fb['chat_ms']['max']:.0f}", f"{fb['chat_first_request_ms']:.0f}"],
              ["Flan-T5-small (default)", f"{t5['chat_ms']['mean']:.0f}", f"{t5['chat_ms']['median']:.0f}", f"{t5['chat_ms']['p95']:.0f}", f"{t5['chat_ms']['max']:.0f}", f"{t5['chat_first_request_ms']:.0f}"],
          ], widths=[1.9, 0.8, 0.8, 1.2, 0.9, 0.9], size=10, align=["l", "c", "c", "c", "c", "c"]),
          P(f"Through the HTTP layer a question is answered in about {fb['chat_ms']['mean'] / 1000:.1f} s with the fallback and {t5['chat_ms']['mean'] / 1000:.1f} s with the local generator. Other routes are quick: health about {fb['health_ms']['mean']:.0f} ms, listing the history about {fb['history_list_ms']['mean']:.0f} ms, and sign-in about {fb['login_ms']['mean']:.0f} ms, which is the deliberate cost of bcrypt. "
            "The measurements used 127.0.0.1 because the name localhost adds about two seconds per call on this machine through an IPv6 fallback; the browser, which goes through the Vite proxy, was not timed. "
            "Throughput under many simultaneous users was not tested: the pipeline holds one set of models in memory and runs on the CPU, so concurrent requests would queue."),
          FIG(F.fig("f08_api_latency.png"), "HTTP latency of the chat route with the two generator modes.", 4.8)]

    # ------------------------------------------------------------------------------------------------ 7.8
    b += [H2("7.8 User Acceptance"),
          P("No formal user acceptance test was carried out. No patient, clinician or other outside user used the application, and no usability or comprehension measure was collected. What exists is the team's own walk-through: the demo account was used to try the main flow, and the capture script confirmed that every page loads without a console error at desktop and phone width. "
            "A user study with the intended public, and a review of the answers by a clinician, are the two evaluations that would matter most and are listed as future work.")]

    # ------------------------------------------------------------------------------------------------ 7.9
    b += [H2("7.9 Summary and Limits of the Testing"),
          TAB("Summary of results", ["Area", "Result"], [
              ["Automated tests", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pytest and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass"],
              ["Security probes", f"{SEC['passed']} of {SEC['n']} pass; three weaknesses (no Secure flag, no sign-in rate limit, default signing key)"],
              ["Retrieval, lay-language probes", f"Top-1 {F.pct(F.ret('hybrid_rerank', S4))} for the shipped configuration (n = {RS[S4]['n']}, interval {F.ci('hybrid_rerank', S4)})"],
              ["Retrieval, two-symptom queries", f"Top-1 {F.pct(F.ret('hybrid_rerank', S3))} (n = {RS[S3]['n']})"],
              ["Relevance display", f"Top record always 100%; {rel['out_kb_labels_via_pipeline_answer'].get('Strong match', 0)} of {rel['out_kb_n']} out-of-base complaints shown as 'Strong match'"],
              ["Local generator", f"{F.GEN['echo_answers']} of {F.GEN['n']} answers are an echo of the prompt; fallback answers are structurally grounded"],
              ["Emergency rules", f"Recall {s['emergency_recall']:.2f}; paraphrases {par['detected']} of {par['n']}; {len(hard['false_emergency'])} of {hard['n']} hard negatives falsely flagged"],
              ["Latency (HTTP, CPU)", f"About {fb['chat_ms']['mean'] / 1000:.1f} s per question with the fallback, {t5['chat_ms']['mean'] / 1000:.1f} s with the local generator"],
          ], widths=[2.0, 4.3], size=10, align=["l", "l"]),
          P("The testing has clear limits. The knowledge base is synthetic and its records of one condition are near-duplicates, so retrieval accuracy on it is easy and says little about a real medical corpus. All probe sets are small and were written by the same team that wrote the system; "
            "the lay-language queries were not reviewed by a clinician; the emergency probes are examples, not a clinical test. The 95% intervals are wide. Groundedness was checked only structurally. No load, concurrency, accessibility-audit, long-run or clinical testing was done, "
            "and no user study. Results were measured once on a single machine and are not repeated runs, although the retrieval experiments are deterministic. The three defects found (prompt echo, always-100% relevance, literal safety rules) are documented rather than fixed in this work."),
          ]
    return b
