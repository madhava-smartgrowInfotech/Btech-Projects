"""Chapters 3 and 4 content: feasibility study, existing and proposed system, requirements, platform, user role."""
from __future__ import annotations


def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.paras(
        "The project needs five technical capabilities: reading PDFs with complex layouts, retrieving clauses, generating grounded text, "
        "checking the generated text, and serving everything through a web application. Each was available without a GPU or a paid "
        "service.",
        "**PDF reading.** PyMuPDF returns every text line with its page, position and font, which is enough to rebuild reading order in "
        "two-column layouts, remove running headers and footers and locate highlight boxes. The four sample wordings (two-column A4, "
        "small-page two-column, single column with `Def. N` numbering, single column with multi-level numbering) parsed in 3.2 to 4.2 "
        "seconds each.",
        "**Retrieval.** BM25 needs no model; the MiniLM embedding model (91.6 MB), the MS MARCO cross-encoder (91.8 MB) and the NLI model "
        "(294.5 MB) are small enough to run on a CPU. On the development machine (12-thread Intel Core i5-12500, 15.7 GB of memory) BM25 "
        "answers in about 1 ms, dense search in about 11 ms and the cross-encoder re-rank in about 0.9 s.",
        "**Generation.** Google's Gemini models accept a whole 40 to 60 page wording in one request and return output that follows a "
        "JSON schema, which makes extraction and answers machine-checkable. A free tier is available for development. A fallback chain "
        "covers quota limits and overload.",
        "**Web application.** FastAPI, SQLAlchemy with SQLite, React and Vite are mature and run on a laptop. All of this was demonstrated "
        "in the built system: 25 backend tests pass and the web application builds without type errors.")
    d.p("The one technical risk is dependence on an external model service. It is reduced by the fallback chain, by a disk cache that "
        "avoids repeating identical requests, and by doing everything that can be done locally (retrieval, re-ranking, faithfulness, "
        "eligibility rules, risk rules) without the service.")


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.table([["Item", "Choice", "Cost"],
             ["Language model", "Gemini API, free tier (fallback chain of three models)", "No fee during development; quota-limited"],
             ["Local models", "all-MiniLM-L6-v2, ms-marco-MiniLM-L6-v2, nli-deberta-v3-xsmall (Apache-2.0)", "No licence fee; one-off download (about 478 MB)"],
             ["Software", "Python, FastAPI, SQLAlchemy, SQLite, ChromaDB, PyMuPDF, React, Vite, Tailwind CSS (open source)", "No licence fee"],
             ["Hardware", "An ordinary desktop or laptop; no GPU", "Existing machine"],
             ["Data", "Four public policy wordings downloaded from insurers' websites; hand-written evaluation set", "No fee; staff time only"],
             ["Hosting", "Runs locally; a server deployment was not costed", "Not measured"]],
            "Cost elements of the project", widths=[0.18, 0.5, 0.32], font=9.5)
    d.p("The running cost of the system is therefore dominated by the language-model service. A complete evaluation run needs about 80 "
        "Gemini requests, and each answer needs one. The application records the model, token counts and latency of every request in "
        "the `llm_calls` table and shows the totals on the dashboard, so the cost of a paid plan could be estimated from real usage. A "
        "monetary estimate was not made because the project ran on the free tier.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.bullets([
        "**Users.** A policyholder needs only a browser. Registration is by e-mail and password; a demo account with four processed sample policies lets a new user see every feature at once.",
        "**Setup.** `setup.bat` installs the dependencies, downloads the local models and prepares the sample data; `run.bat` starts the API and the web app and opens the browser; `stop.bat` stops them.",
        "**Everyday use.** Uploading a 40-page policy takes seconds to parse and index plus one model request for the Policy Card; a question is answered in a median of 4.3 seconds.",
        "**Maintenance.** All settings are in a documented `.env` file; the Gemini model names are configuration, not code; the evaluation can be re-run with one command to detect regressions.",
        "**Trust.** Every answer shows its sources on the original page and a faithfulness score, and the interface states that the insurer makes the final decision.",
    ])


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The build history in the project repository shows the phases below. The dates are taken from the commit log and the "
        "evaluation run names; the documentation phase is the present work.")
    d.table([["Phase", "Date (2026)", "Outcome"],
             ["Planning and prompts", "21 September", "Build plan (`docs/PLAN.md`), architecture and data model"],
             ["Project foundations", "21 September", "Backend skeleton, database models, authentication, PDF parsing and segmentation"],
             ["Retrieval and evaluation", "21 September", "BM25, dense index, fusion, re-ranking; evaluation harness and first run (eval-20260921-2353)"],
             ["Chat, claims, comparison", "21 September", "Answerer, faithfulness scorer, Claim Copilot, comparator, language service"],
             ["Web application", "21 September", "Landing page, dashboard, policy view, chat, claims, compare, model performance"],
             ["Fixes and tuning", "21-22 September", "Abstention rule, parent-context, exclusion-code clauses; runs eval-20260922-0008 and -0027"],
             ["Documentation and screens", "22 September, 15 October", "Product documents, real screenshots, diagrams, this report"]],
            "Project schedule from the repository history", widths=[0.26, 0.2, 0.54], font=9.5)
    d.p("The evaluation harness made the later phases fast: a full run takes about ten minutes, so each fix could be checked "
        "immediately. The schedule was feasible because every heavy component was an existing library or pre-trained model.")


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.table([["Advantages", "Constraints"],
             ["Runs on one laptop with no GPU and no licence fee", "Depends on an external model service and its free-tier quota"],
             ["Documents stay on the user's machine; only clauses are sent to the model", "Evaluated with the smallest model of the fallback chain"],
             ["Every answer is cited and scored; the system can decline", "Faithfulness score is a heuristic from a small NLI model"],
             ["Rules (waiting periods, co-payment, estimate) are calculated, not generated", "Text-layer, English wordings only; no OCR"],
             ["Repeatable evaluation and public Model performance page", "Small evaluation set; partly tuned on itself"],
             ["English, Hindi and Telugu questions and answers", "Translation quality limited (mixed-script line observed)"]],
            "Advantages and constraints of the project", widths=[0.5, 0.5], font=10)


def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.paras(
        "Today a policyholder who wants to understand a health policy has four options. They can read the policy wording, which is "
        "long and technical. They can ask an agent or call a helpline, which is slow and depends on the person who answers. They can use "
        "a comparison website, which compares premiums and headline benefits. Or they can ask a general-purpose chatbot, which answers "
        "from broad training data instead of their own wording. Claim filing offers no guided pre-check.")
    d.table([["Limitation of the existing system", "Consequence"],
             ["Policy wording is technical and lengthy", "Key exclusions, waiting periods and conditions are easily missed"],
             ["Agent and helpline answers are slow and inconsistent", "Depends on human availability; generic answers"],
             ["General chatbots are not grounded in the policy", "Can hallucinate coverage details [16]"],
             ["No tool extracts key attributes automatically", "Deductibles, limits and waiting periods must be found by hand"],
             ["No guided claim pre-check", "Delays and rejections from missing eligibility information and documents"],
             ["Answers carry no clause references", "The user cannot verify what they are told"]],
            "Limitations of the existing system", widths=[0.5, 0.5], font=10)


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.p("PolicyLens answers strictly from the user's own policy wording. A person uploads a PDF; the system parses it into numbered "
        "clauses, builds a Policy Card, flags risks, answers questions with citations and a faithfulness score, checks planned claims and "
        "compares two policies, in English, Hindi or Telugu.")
    d.table([["Feature", "What it does", "Advantage over the existing system"],
             ["F1 Policy upload and parsing", "PDF to numbered clauses with pages and highlight positions", "The wording becomes searchable and citable"],
             ["F2 Policy Card", "Sum insured, deductible, co-pay, room rent, waiting periods, sub-limits, exclusions, deadlines, each linked to its clause", "Key terms in one place, with proof"],
             ["F3 Clause-grounded chat", "Plain-language answers citing clause and page; says \"not covered in this policy\" instead of guessing", "No unsupported answers"],
             ["F4 Hybrid retrieval", "BM25 + MiniLM embeddings, fused and re-ranked", "Finds the right clause for exact terms and for paraphrases"],
             ["F5 Claim Copilot", "Verdict, calculated checks, cost estimate, documents, steps", "Guidance before filing"],
             ["F6 Plan comparison", "Two policies side by side with trade-offs", "Compares exclusions and conditions, not only premiums"],
             ["F7 Risk highlights", "Waiting-period, sub-limit, co-pay and room-rent traps by severity", "Surfaces the fine print"],
             ["F8 Multilingual answers", "English, Hindi, Telugu", "Accessible to more users"],
             ["F9 Faithfulness score", "NLI score of each answer against its cited text", "Shows how far to trust each answer"]],
            "Features of PolicyLens", widths=[0.22, 0.45, 0.33], font=9.5)


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([["ID", "Requirement", "Satisfied by"],
             ["FR1", "The user shall register, sign in and change language, theme and password", "Auth and users API; Settings page"],
             ["FR2", "The user shall upload a PDF policy wording or add sample policies; scanned, encrypted, oversize and duplicate files shall be refused with a clear message", "POST /policies, /policies/samples"],
             ["FR3", "The system shall parse the wording into numbered clauses with page numbers and highlight positions", "pdf_parser, segmenter"],
             ["FR4", "The system shall build a Policy Card whose values link to their clause and page and are marked verified or not", "extractor"],
             ["FR5", "The system shall flag risks by severity from rules and from the model, without duplicates", "risk_engine"],
             ["FR6", "The user shall search the clauses by keyword, semantics or hybrid", "POST /policies/{id}/search"],
             ["FR7", "The user shall ask questions and receive cited answers, a faithfulness score and follow-up questions; unanswerable questions shall be declined", "answerer, faithfulness"],
             ["FR8", "The user shall open any cited clause on the original page with the clause highlighted", "page_renderer, viewer"],
             ["FR9", "The user shall run a claim check and receive a verdict, pre-checks, documents, steps and an estimate; checklist ticks shall be saved", "claim_copilot, eligibility"],
             ["FR10", "The user shall compare two policies", "comparator"],
             ["FR11", "Questions and answers shall work in English, Hindi and Telugu; the card and risks shall be translatable", "language service"],
             ["FR12", "The user shall see a dashboard of their activity and a public page of measured model performance", "dashboard, evaluation API"]],
            "Functional requirements", widths=[0.08, 0.64, 0.28], font=9.5)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "How it is met / measured"],
             ["NFR1 Accuracy", "Answers shall be correct and cited", "Answer accuracy 51/51, citation accuracy 100% on the evaluation set"],
             ["NFR2 Faithfulness", "Each answer shall carry a support score", "Mean 87.0; shown on every answer"],
             ["NFR3 Response time", "A typical answer shall arrive within seconds", "Median 4.3 s, 95th percentile 18.2 s (live Gemini)"],
             ["NFR4 Security", "Passwords hashed, tokens signed, data owner-only", "bcrypt, JWT (24 h), owner checks tested in test_policy_flow.py"],
             ["NFR5 Privacy", "Documents stay local", "Only retrieved clauses and the question go to the model API"],
             ["NFR6 Reliability", "The service shall survive model overload and restarts", "Fallback chain, cool-down, cache, resumable ingestion"],
             ["NFR7 Usability", "Plain language, no horizontal scroll on phones, light/dark themes", "Checked at 360 px and 1440 px (see testing)"],
             ["NFR8 Portability", "Runs on Windows 10/11 with Python 3.11 and Node LTS", "setup.bat, run.bat, stop.bat"],
             ["NFR9 Maintainability", "Configuration outside the code; tests", "`.env`; 25 backend tests; strict TypeScript"],
             ["NFR10 Reproducibility", "The evaluation shall be repeatable", "ml/run_all.py; three runs kept in experiments/"]],
            "Non-functional requirements", widths=[0.2, 0.38, 0.42], font=9.5)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.table([["Item", "Requirement"],
             ["Machine used for development and measurement", "12th Gen Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, no discrete GPU, Windows 11 Pro"],
             ["Disk", "About 2.5 GB for the virtual environment, node_modules and model weights (project plan); the data folder is about 4.7 MB"],
             ["Minimum machine", "Not measured; the system was run only on the machine above"],
             ["Operating system", "Windows 10 or 11 (batch scripts); the Python and Node code is portable"],
             ["Python and Node", "Python 3.11 (3.11.9 used); Node.js LTS"],
             ["Backend libraries", "FastAPI >= 0.115, Uvicorn, Pydantic >= 2.7, SQLAlchemy >= 2.0, PyJWT, passlib + bcrypt 4.0.1, google-genai >= 1.0, chromadb >= 1.0, rank-bm25, PyMuPDF >= 1.24, sentence-transformers >= 3.0, torch >= 2.3, numpy, pandas, matplotlib, scikit-learn, pytest, httpx"],
             ["Web libraries", "React 18.3, Vite, TypeScript, Tailwind CSS, shadcn/ui (Radix), React Router 7, TanStack Query 5, Axios, Recharts 3, Framer Motion, GSAP, Lenis"],
             ["External service", "Google Gemini API key (free tier): a key is the only credential needed"],
             ["Browser", "A current Chrome or Edge (used for all captures); other browsers were not tested"]],
            "Hardware and software requirements", widths=[0.28, 0.72], font=9.5)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.paras(
        "PolicyLens has one authenticated role, the **policyholder**. Every policy, conversation, claim check and comparison belongs to "
        "the user who created it and is visible only to that user; this is enforced in the API and covered by a test. Two things need "
        "no sign-in: the landing page and the **Model performance** page, which shows the public evaluation figures. A demo account "
        "(`demo@policylens.app`) is seeded with the four sample policies.",
        "**Constraints.** The wording must be a PDF with a text layer, in English, up to the configured upload size. A claim check needs "
        "a Policy Card, so it is available only after a policy is processed. The faithfulness score and the claim verdict are aids; "
        "the insurer makes the final decision on any claim, and the interface says so.")
