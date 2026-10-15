"""Chapters 9 and 10, implementation decisions, references and appendices."""
from __future__ import annotations

from doc_common import CHARTS, REFERENCES, SHOTS
from rc_method import grab, src
from rc_results import extra_block


def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.table([["Decision", "Why"],
             ["Local embeddings, re-ranker and NLI model", "No API quota, deterministic, offline; the faithfulness check is independent of the model that wrote the answer"],
             ["Hybrid retrieval with a pool that always includes each retriever's top 8", "Keyword search is precise for exclusion codes and medical terms; embeddings handle paraphrase; the re-ranker puts the best clause first"],
             ["Schema-constrained JSON from Gemini", "Predictable structure, no fragile text parsing; every value carries its clause tag and quote"],
             ["Quote verification of Policy Card values", "A value whose quote cannot be found in the text is shown as unverified rather than silently trusted"],
             ["Clause-aware segmentation instead of fixed windows", "A citation must point at one rule and be highlighted on the original page"],
             ["Rules calculate waiting periods, co-payments and the estimate", "Months, ages and money must be exact; the model cannot overrule a failed waiting period"],
             ["Abstain on two scores, not one", "Neither the re-rank score nor the BM25 score separates answerable from out-of-scope questions alone"],
             ["Server-rendered page images for the viewer", "Exact highlight positions from the parser and no PDF library in the browser"],
             ["Fallback chain and cool-down for Gemini", "Free-tier models can be overloaded or out of quota; the app keeps answering and shows which model answered"],
             ["Response cache keyed by content hash", "Re-running the evaluation or re-importing a known PDF does not spend quota twice; a button bypasses the cache"],
             ["Documents shared by SHA-256", "The same PDF is processed once even if two users upload it"],
             ["SQLite and ChromaDB, no server to run", "One-machine installation by a student or a policyholder"],
             ["Background ingestion worker with resume", "Upload returns at once; unfinished work is resumed after a restart"],
             ["No training", "The task is reading, not predicting; no labelled public data; wordings change every year"]],
            "Implementation decisions", widths=[0.4, 0.6], font=9.5)


def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project built PolicyLens, an AI assistant that explains a health-insurance policy from the policyholder's own wording. "
        "A PDF is parsed into numbered clauses with page positions; a Policy Card lists the key terms with the clause and page that "
        "support each value; a hybrid retriever (BM25, MiniLM embeddings, Reciprocal Rank Fusion and a cross-encoder) finds the clauses "
        "relevant to a question; Gemini writes a plain-language answer from those clauses only; and an independent NLI model scores how "
        "well each answer is supported. The assistant says \"not covered in this policy\" when the wording is silent, guides claims with "
        "calculated eligibility pre-checks, a document checklist and a cost estimate, compares two policies, and works in English, "
        "Hindi and Telugu.",
        "The system was evaluated on a hand-built set drawn from four real policy wordings: 57 questions, 14 claim scenarios and 52 Policy "
        "Card values. The relevant clause was in the top five for 51 of 51 answerable questions, all 51 answers were correct and correctly "
        "cited, 6 of 6 out-of-scope questions were declined with no false abstentions, 14 of 14 claim verdicts were correct, 51 of 52 card "
        "values were correct, the mean faithfulness score was 87.0 and the median answer time was 4.3 seconds. Twenty-five automated tests pass.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p("Each of the six objectives was met: key attributes are extracted automatically into a verified Policy Card (51 of 52 values correct); a RAG "
        "pipeline retrieves the relevant clauses (hit@5 of 100%); answers are in plain language, grounded and cited (accuracy and citation "
        "accuracy 100%); claim support provides pre-checks, a checklist, steps and an estimate (14 of 14 verdicts); risks and trade-offs support "
        "plan comparison; and answer accuracy, faithfulness and response time were measured. The sixth objective is met with the limits stated "
        "below: the evaluation set is small and was partly used for tuning, and no user study was carried out.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([
        "**Keywords matter most in policy text.** BM25 alone found the relevant clause in the top five for every question; embeddings alone found it for 80%.",
        "**Re-ranking decides the top of the list.** Adding the cross-encoder raised hit@1 from 0.686 to 0.804 and MRR@10 from 0.795 to 0.897.",
        "**Structure beats chunks.** The largest accuracy gain across the three runs (answer accuracy 88.2% to 100%) came from segmentation and context fixes, not from a better model.",
        "**Two scores are needed to know when to abstain.** Neither the re-rank score nor the BM25 score separated answerable from out-of-scope questions alone; together they did.",
        "**A small model was enough on this set.** Every result was obtained with the smallest model in the fallback chain, `gemini-3.5-flash-lite`, because retrieval and rules do much of the work.",
        "**Faithfulness scores are a prompt, not a verdict.** Three correct answers scored below 50 and one question scored 99.0 and 37.9 in two runs; the score must be shown together with the sources.",
    ])
    d.figure(CHARTS / "improvement_runs.png", "Improvement across the three evaluation runs", width=4.8)


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets([
        "**Policyholders** who want to understand what they bought, check a planned claim before filing it, or compare two policies.",
        "**Insurance advisers and customer-service teams** who need a fast, cited answer to a wording question.",
        "**Hospitals' insurance desks** preparing claim documents (the checklist and steps are generated from the policy).",
        "**Regulators and consumer groups** reviewing how clearly policy wordings state waiting periods, sub-limits and exclusions (the risk highlights surface them).",
        "**Teaching** retrieval-augmented generation with a real, checkable evaluation.",
    ])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "The evaluation set is small (51 answerable questions, four policies, 14 claim scenarios) and the abstention thresholds and parser fixes were tuned on it; results on unseen policies are not yet known.",
        "All results are from the smallest Gemini model in the chain; larger models were not measured.",
        "The faithfulness score is a heuristic; the translation of the Policy Card into Telugu contained one mixed-script line.",
        "Plan variants (for example the seven variants in one HDFC ERGO wording) are not yet selectable, so one card value is ambiguous.",
        "Text-layer English PDFs only; no OCR.",
        "No user study, no load or security testing.",
        "No numeric comparison with the base paper is possible, because it summarises Turkish court rulings and reports ROUGE.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "Evaluate on a fresh, larger question set from policy wordings not used in development, with independent annotators.",
        "Re-run the evaluation with the larger Gemini models and report the difference.",
        "Let the user select the plan variant on the Policy Card and use it in answers and claim checks.",
        "Improve the faithfulness scorer, for example with a larger NLI model or by giving the scorer the clause heading only for inclusion lists.",
        "Check translation quality automatically (script detection per line) and retry a line that mixes scripts.",
        "Fix the dashboard tile layout at 1440 px and repeat the accessibility checks.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "OCR for scanned policy documents.",
        "Upload and parsing of non-English wordings and more languages for answers.",
        "Claim document upload with a check against the generated checklist; reminders for claim deadlines.",
        "Policy renewal comparison: a changed wording against last year's.",
        "Hospital network look-up for cashless claims; voice input for questions.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets([
        "Replace SQLite and the local vector store with a server database and a hosted vector store for many users.",
        "Run the three local models in a separate worker service, and queue ingestion with a job system.",
        "Serve over HTTPS with a generated signing secret, rate limiting and a security review before any shared deployment.",
        "Add monitoring of model quota, latency and the faithfulness distribution; keep the evaluation as a regression test in continuous integration.",
        "Measure load and concurrency, which were not tested here.",
    ])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "Compare clause-aware segmentation with learned segmentation and with graph-structured retrieval [5] on insurance wordings.",
        "Calibrate the faithfulness score against human judgement and learn the abstention rule from data instead of two thresholds.",
        "Study how often retrieval-grounded answers still contain a false statement, as in [2], on health-insurance wordings with a larger panel of expert answers.",
        "Evaluate whether policyholders make better decisions with the assistant: a user study with real wordings.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{ref}", align="left", size=11, line=1.2, space_after=4)
        p.paragraph_format.left_indent = __import__("docx").shared.Inches(0.45)
        p.paragraph_format.first_line_indent = __import__("docx").shared.Inches(-0.45)


def appendix_a(d):
    d.p("The listings below are extracted from the source files when this report is built, so they match the code that produced the results.")
    d.h2("Hybrid Retrieval")
    d.code(src("backend/app/ml/retrieval/hybrid.py", 55, 134), "retrieve() in ml/retrieval/hybrid.py")
    d.h2("Faithfulness Scoring")
    d.code(grab("backend/app/ml/faithfulness.py", "def score_claims", 62), "score_claims() in ml/faithfulness.py")
    d.h2("Co-payment Rule")
    d.code(grab("backend/app/services/eligibility.py", "def copay_applies", 22), "copay_applies() in services/eligibility.py")
    d.h2("Password Hashing and Tokens")
    d.code(src("backend/app/core/security.py", 16, 34), "hash_password(), verify_password() and create_access_token() in core/security.py")


def appendix_b(d):
    d.h2("Installation Guide")
    d.numbered([
        "Install Python 3.11 (tick Add python.exe to PATH) and Node.js LTS on Windows 10 or 11.",
        "Open the project folder (it contains `setup.bat`, `run.bat`, `backend` and `frontend`) and run `setup.bat`. It creates the virtual environment, installs the packages, creates `.env`, downloads the three local models (about 480 MB), installs the web packages, creates the database, the demo account and the four sample policies, and builds their index. This takes about 15 minutes, mostly downloads.",
        "Get a free Gemini API key at https://aistudio.google.com/apikey, open `.env` and paste it after `GEMINI_API_KEY=`.",
        "Optional: run `venv\\Scripts\\python scripts\\check_gemini.py` to send three tiny test requests.",
        "Run `run.bat`. It starts the API on port 8101 and the web app on port 5101 and opens http://localhost:5101.",
        "Sign in with `demo@policylens.app` and `Demo@12345`, or register a new account.",
        "Stop with `stop.bat`. `scripts\\reset.bat` resets the data.",
    ])
    d.h2("User Guide")
    d.table([["Task", "How"],
             ["Upload a policy", "My policies, then Upload policy; choose a PDF with selectable text; watch the status move from queued to ready; or press Sample policies to add the four samples"],
             ["Read the Policy Card", "Open the policy; the Policy Card tab lists the values; every chip \"Clause - page\" opens the original page with the clause highlighted"],
             ["See the risks", "Risks tab; filter by severity"],
             ["Search the wording", "Clause search tab; choose BM25, dense, hybrid or hybrid with re-rank"],
             ["Ask a question", "Ask this policy (or Ask your policy); type a question or press a suggestion; open a source chip to see the page; the badge shows the faithfulness score"],
             ["Change the language", "Settings, or the language menu in the chat, or on the card; the source quotes stay in English"],
             ["Check a claim", "Claim Copilot: choose the policy, the treatment, the details (start date, age, pre-existing disease, estimated bill), then Review; tick the checklist as documents are collected"],
             ["Compare two policies", "Compare plans: choose Policy A and Policy B and the language, then Compare"],
             ["See measured quality", "Model performance (no sign-in needed)"]],
            "User guide", widths=[0.25, 0.75], font=10)
    d.p("PolicyLens explains policy wordings; the insurer makes the final decision on any claim.")


def appendix_c(d):
    d.p("Additional captures of the running application (15 October 2026).")
    extra_block(d)
