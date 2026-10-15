"""Chapter 7 content: system testing."""
from __future__ import annotations

from doc_common import TESTS


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        "PolicyLens is checked at four levels: automated backend tests, a production build of the web application, a measured evaluation "
        "of the AI pipeline, and a scripted end-to-end walk-through of the demo scenario in a real browser. The levels answer different "
        "questions. The backend tests ask whether the code behaves as designed, deterministically and without the network. The build "
        "asks whether the web application type-checks and bundles. The evaluation asks whether the AI pipeline is accurate. The "
        "walk-through asks whether a person can use the product from start to finish.",
        "Because the language model is an external service whose output varies, the automated tests never call it. Where an AI step is "
        "needed, a stand-in returns a schema-valid response, so that the rest of the pipeline (retrieval, citation filtering, "
        "faithfulness scoring, persistence) runs for real. The tests use an isolated temporary data folder, a synthetic two-page policy "
        "generated deterministically by `tests/fixtures.py`, and the real local models.")


def sec_unit(d):
    d.h2("Unit Testing")
    d.table([["Test file", "Tests", "What it checks"],
             ["test_units.py", "6", "Reciprocal Rank Fusion; tokeniser and synonym expansion; fuzzy quote matching; risk rules and de-duplication of AI findings; waiting-period checks; co-payment and cost estimate with a sub-limit"],
             ["test_faithfulness.py", "3", "Supported claims score high; wrong numbers and uncited claims score low; no claims means no score"],
             ["test_parser.py", "3", "Header removal, clause references (`2.1`, `3.1`, `Excl01`, `Excl02`), pages, highlight boxes, heading path, UIN detection; exclusion-coded list items become clauses whether the code opens, closes or wraps onto the next line; scanned PDFs rejected"]],
            "Unit tests", widths=[0.22, 0.08, 0.7], font=9.5)
    d.p("These twelve tests cover the pure logic of the system: ranking, parsing, scoring and the rules that must be exact. They run in a "
        "few seconds and caught real faults while the parser was extended for exclusion codes.")


def sec_integration(d):
    d.h2("Integration Testing")
    d.table([["Test file", "Tests", "What it checks"],
             ["test_auth.py", "6", "Health endpoint; register, duplicate e-mail, case-insensitive login, bad credentials, missing and invalid token; password rules; language and password changes; the demo account is seeded"],
             ["test_policy_flow.py", "7", "Upload validation; full processing of an uploaded PDF; clause list; hybrid search in all four modes returns the cataract clause first; page image and original PDF; owner-only access; chat answer with citation filtering (a citation to a clause that was not retrieved is removed) and faithfulness; abstention; Claim Copilot with checklist ticks; dashboard; delete"]],
            "Integration tests", widths=[0.22, 0.08, 0.7], font=9.5)
    rows = [["File", "Tests"]] + [[f, str(n)] for f, n in TESTS] + [["**Total**", "**25 passed** (about 15 s)"]]
    d.table(rows, "Backend test inventory (pytest, 15 October 2026)", widths=[0.6, 0.4], font=10)
    d.p("The web application is checked by `npm run build`, which runs the TypeScript compiler in strict mode and the Vite production "
        "build. On 15 October 2026 it completed with no type errors.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("The functional tests follow the demo scenario of the project, run against the live application with live Gemini calls on "
        "15 October 2026 using the demo account and the four sample policies. The observed results are those recorded during the run "
        "and shown in the screenshots of Chapter 8.")
    d.table([["No.", "Test", "Expected", "Observed"],
             ["F1", "Sign in with the demo account", "Dashboard opens", "Pass"],
             ["F2", "Open My policies", "Four ready sample policies", "Pass: four policies, all ready"],
             ["F3", "Open the Policy Card of the Star Health policy", "Values with clause and page chips; verified share shown", "Pass: 91% of values verified in the text"],
             ["F4", "Ask \"Is cataract surgery covered and after how long?\"", "Covered after the 24-month specified-disease wait; citations; faithfulness", "Pass: answered, citations Clause 2 p. 10 and Clause Excl02 p. 28, faithfulness 88, 6.2 s"],
             ["F5", "Ask \"Does this policy insure my house against fire?\"", "Declines without a model call", "Pass: \"Not covered in this policy document\", 1.7 s"],
             ["F6", "Ask a room-rent question in Hindi (HDFC ERGO)", "Hindi answer with citations; Show in English", "Pass: answered in Hindi with 4 citations, faithfulness 91.5"],
             ["F7", "Claim Copilot: knee replacement, cover from 2023-10-01, age 64, Rs. 3,50,000", "Partly covered: waiting periods complete, 20% co-payment", "Pass: partly covered; 36 months of cover; estimate shown"],
             ["F8", "Claim Copilot: same treatment, cover from 2026-04-01, age 45", "Not covered: waiting period incomplete", "Pass: not covered"],
             ["F9", "Compare Star Health with HDFC ERGO Optima Secure", "Side-by-side table, trade-offs, choose-A/B-if", "Pass: 21-row table"],
             ["F10", "Open a cited clause", "Original page with the clause highlighted", "Pass"],
             ["F11", "Switch the card to Telugu", "Translated card", "Pass with a defect: one line contains Bengali/Gurmukhi script"],
             ["F12", "Dark theme and 390 px phone layout", "Readable, no horizontal scroll", "Pass (captured)"]],
            "Functional test cases", widths=[0.07, 0.33, 0.28, 0.32], font=8.5)


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Security testing in this project is limited to the automated tests and the code review of the validation paths. The tests "
        "confirm that a missing or invalid token is refused, that passwords below the rule are rejected, that a duplicate e-mail is "
        "refused, that login with a wrong password fails with a generic message, and that one user cannot read another user's policy, "
        "conversation, claim check or comparison. Upload validation (PDF signature, size, encryption, empty or damaged files) is covered by the "
        "upload tests. **Not tested:** penetration testing, rate limiting, HTTPS deployment, and resistance to a PDF that contains "
        "instructions aimed at the language model (prompt injection). The mitigations that exist (schema-constrained output, citation "
        "filtering, calculated rules that the model cannot overrule) were not attacked.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.table([["Case", "Behaviour"],
             ["Scanned PDF without a text layer", "Rejected with \"no readable text layer\" (test_parser.py)"],
             ["Not a PDF, oversize, encrypted, empty or damaged file", "Rejected with a coded message (`not_pdf`, `too_large`, `encrypted`, `bad_pdf`)"],
             ["Same PDF uploaded twice", "Processed once (SHA-256); the second upload reuses the document or returns `duplicate_policy`"],
             ["Question outside the policy", "\"Not covered in this policy\" without a model call; 6 of 6 out-of-scope questions"],
             ["Model cites a clause that was not retrieved", "The tag is removed (test_policy_flow.py)"],
             ["Gemini model out of quota or overloaded", "Falls back to the next model; the answer shows which model produced it"],
             ["No Gemini key", "Upload, search and the viewer work; the Policy Card explains how to add a key"],
             ["Claim for a treatment in the waiting period", "Calculated check fails; the verdict can never be \"covered\""],
             ["Plan with several variants (HDFC ERGO)", "Known limitation: the card reports the Optima Secure figure; variant selection not implemented"],
             ["Hindi or Telugu question", "Translated for search; the answer is in the requested script (5 of 5)"]],
            "Validation and edge cases", widths=[0.4, 0.6], font=9.5)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Performance was measured on the development machine (12-thread Intel Core i5-12500, 15.7 GB RAM, no GPU) with live Gemini calls. "
        "The figures come from the evaluation run eval-20260922-0027 and from the live run of 15 October 2026.")
    d.table([["Measurement", "Result"],
             ["Retrieval, 51 queries, median (p95)", "BM25 1.1 ms (32.2); dense 10.7 ms (15.7); hybrid 11.0 ms (16.6); hybrid + re-rank 878.9 ms (995.5)"],
             ["Answer, all 62 questions, median / p95 / max", "4.34 s / 18.18 s / 24.77 s"],
             ["Answer stages, median (p95)", "retrieval 0.86 s (1.83); Gemini 2.53 s (17.16); faithfulness 0.83 s (1.72)"],
             ["Claim check, 4 timed live calls", "mean 13.8 s, median 12.3 s, p95 22.8 s"],
             ["Parsing a policy wording", "3.2 s (24 pages) to 4.2 s (53 pages)"],
             ["Live run, 15 October 2026", "cataract answer 6.2 s; co-payment answer 5.6 s; abstained question 1.7 s; Hindi answer 10.0 s; claim check 14.2 s"],
             ["Web build", "Vite production build 7.6 s; type check passes"]],
            "Performance measurements", widths=[0.36, 0.64], font=9.5)
    d.p("The long tail of the answer time comes from the fallback chain: when the primary models report quota or overload, the request moves "
        "to the next model and that wait is included in the figure. **Not measured:** concurrent users, memory use under load, other "
        "hardware.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user-acceptance test with real policyholders was carried out. The usability claims in this report rest on the scripted demo "
        "scenario, on captures of every screen at 1440 px and 390 px, and on the project's own checks (no horizontal scrolling at "
        "phone width, no console errors, reduced-motion support). A pilot in which policyholders upload their own wordings and "
        "rate the answers is the most important piece of future work.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "The 25 automated tests use a synthetic two-page policy and a stand-in for the language model; they do not test answer quality, which is measured separately.",
        "The evaluation set is small (51 answerable questions, 14 claim scenarios, 52 card values, four policies) and was used to tune the abstention thresholds and parser, so its results are optimistic.",
        "All results come from the smallest model in the fallback chain, `gemini-3.5-flash-lite`, because the larger models' free quota was exhausted; results with the larger models were not measured.",
        "No load, concurrency, security or penetration testing; one machine; one browser family (Chrome).",
        "No user study with real policyholders.",
    ])
