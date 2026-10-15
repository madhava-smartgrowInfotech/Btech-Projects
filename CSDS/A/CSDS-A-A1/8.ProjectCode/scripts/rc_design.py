"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry."""
from __future__ import annotations

from doc_common import DIAG

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of PolicyLens",
                     ["The diagram shows five layers. At the top is the user's browser: a policyholder, and any visitor to the public Model performance page. "
                      "Below it is the React web application, served by Vite on port 5101, which proxies every `/api` call to the backend. The backend is a FastAPI "
                      "application on port 8101. Its REST layer exposes authentication, users, policies, conversations, claims, comparisons, the dashboard, "
                      "evaluation and health endpoints, and passes work to eight services: the ingestion worker, the PDF parser and segmenter, the hybrid retriever, "
                      "the Policy Card extractor with the risk engine, the answerer, Claim Copilot with the eligibility rules, the comparator with the language service, "
                      "and the faithfulness scorer.",
                      "Every request to a language model goes through one Gemini client, which handles the JSON schema, the fallback chain, the pacing and the cache. "
                      "Three small models run locally on the CPU. Storage is local: SQLite for records, ChromaDB for the clause vectors, and plain files for PDFs, "
                      "page images and the response cache. The only external service is the Gemini API."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["The ten steps fall into two groups. Steps 1 to 6 (upload, parse, segment, index, Policy Card, risks) run once per policy in a background "
                  "worker whose status moves from queued to parsing, indexing, extracting and ready. Steps 7 to 10 (ask, Claim Copilot, compare, review) run on "
                  "demand against a ready policy. The note at the bottom states the central rule of the system: if the wording does not cover a question, the "
                  "assistant says so instead of guessing."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["At the highest level PolicyLens is one process with three external entities. The policyholder sends credentials, policy PDFs, questions, claim "
              "details and comparison and language choices, and receives Policy Cards, risks, cited answers with faithfulness scores, claim plans and "
              "comparisons. The Gemini API receives clauses with a JSON schema and returns structured JSON. The insurer's policy wording is the input document, "
              "supplied either by the user or as one of four sample wordings."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 splits PolicyLens into eight processes: authentication (1.0), upload, parse, segment and index (2.0), Policy Card and risk extraction (3.0), "
              "question answering (4.0), Claim Copilot (5.0), plan comparison (6.0), translation (7.0), and the dashboard with model performance (8.0). Nine "
              "data stores hold the users, the documents with their clauses and vector index, the cards and risk flags, the conversations and messages, the claim "
              "cases, the comparisons, the cached translations and the evaluation runs. Processes marked with an asterisk also exchange JSON with the Gemini API."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: Answer a question (process 4.0)",
             ["Process 4.0 is expanded into eight steps that follow the code of `answer_question()`: detect the script and translate a Hindi or Telugu question into "
              "an English search query (4.1), search BM25 and the vector index for 30 candidates each (4.2), fuse the rankings and re-rank them with the cross-encoder "
              "(4.3), and check whether anything relevant was found (4.4). If nothing was, the answer \"not covered in this policy\" is returned without a model call. "
              "Otherwise the rule or table context is added and the model is called (4.5), citations to clauses that were not retrieved are dropped (4.6), the "
              "faithfulness score is computed (4.7), and the message is stored and returned (4.8)."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["The policyholder can register or sign in, upload a policy or add the samples, view the Policy Card, review risks, search clauses, ask questions, "
                 "open a cited clause on its page, run Claim Copilot and tick its checklist, compare two plans, switch language and view the dashboard. A visitor "
                 "who has not signed in can view the Model performance page. The Gemini API is an external actor used by the use cases that generate text: "
                 "building the card, answering, claim planning, comparison and translation."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: asking a question and opening a citation",
                 ["The sequence shows the main flow. The user submits a question; the web app posts it to the API, which checks the token and the ownership of the "
                  "policy, translates the query if needed, retrieves the top clauses, and applies the abstention rule. If the model is called, the API sends the tagged "
                  "clauses and the JSON schema, receives the answer and its claims, asks the NLI scorer for the support score, stores the message and returns the answer "
                  "with its citations. When the user clicks a source chip the web app requests the page image, and the clause is highlighted on it."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram (12 tables)",
           ["Twelve tables are created by SQLAlchemy in SQLite. A user owns policies; a policy points to a document, which is shared by content hash so that "
            "the same PDF is processed once even if two users upload it. A document has many clauses and risk flags and at most one Policy Card. Conversations "
            "belong to a user and a policy and contain messages. Claim cases and comparisons belong to a user and reference policies. Translations are cached by "
            "a key built from the document and a content hash, and the `llm_calls` table logs every model request."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The upper part shows the domain entities with their main attributes and associations. The lower part shows the services and engine types with their "
             "key methods and constants: the answerer and its thresholds, the hybrid retriever, the faithfulness scorer, the Gemini client, the ingestion worker, the "
             "parser and segmenter, the extractor and risk engine, and the claim, eligibility and comparison services. Dotted arrows are dependencies; every AI "
             "request goes through the Gemini client."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core algorithm, answer_question()",
                  ["The flowchart follows the code of the answerer. After optional translation, BM25 and dense search each return 30 candidates; Reciprocal Rank "
                   "Fusion combines them; the pool of the fused top 20 plus each retriever's top 8 is re-ranked by the cross-encoder, and the top 7 are kept. The "
                   "decision diamond is the abstention rule. On the \"no\" path the rule or table that a retrieved fragment belongs to is added, Gemini is called "
                   "with a JSON schema, uncited tags are dropped, citations are built, and each claim is scored by the NLI model before the message is stored."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    d.figure(DIAG / fname, caption, width=width, max_h=5.5)
    for p in paras:
        d.p(p)


def sec_arch(d):
    d.h2("System Architecture")
    d.p("PolicyLens is a single-machine application: a React web app, a FastAPI backend, local storage and three CPU models, with the Gemini "
        "API as the only external service. The figure below shows the layers.")
    diagram(d, "architecture")
    d.p("The design follows four principles. **Ground everything in the document**: the only text the language model may use is the clauses "
        "that retrieval hands it, tagged so that each statement can be traced. **Check independently**: faithfulness, quote verification and "
        "eligibility rules are computed outside the model that wrote the text. **Keep the heavy work local**: retrieval, re-ranking and "
        "scoring run on the CPU, which keeps documents on the user's machine and saves quota. **Degrade gracefully**: with the Gemini key "
        "removed, upload, search and the document viewer still work.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams show how data moves through PolicyLens at three levels of detail.")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Three UML views describe the design: the use-case diagram (who does what), the class diagram (what the code contains) and the sequence "
        "diagram (how the main flow runs). The algorithm itself is shown as a flowchart in Chapter 6.")
    diagram(d, "usecase")
    diagram(d, "uml")
    diagram(d, "sequence")


def sec_database(d):
    d.h2("Database Design")
    d.p("The database is SQLite, created by SQLAlchemy 2. Large structured results (citations, the Policy Card, claim results) are stored as "
        "JSON columns, because they are read and written whole and are never queried field by field.")
    diagram(d, "er")
    d.table([["Table", "Purpose", "Key columns"],
             ["users", "Accounts", "email (unique), full_name, password_hash (bcrypt), language, theme"],
             ["documents", "One parsed PDF, shared by content hash", "sha256 (unique), file_name, page_count, insurer, product_name, uin, status, progress, parse_stats"],
             ["policies", "A document in one user's library", "owner_id, document_id, display_name, is_sample"],
             ["clauses", "Retrievable chunks of a document", "document_id, ordinal, clause_ref, heading, section_path, text, page_start/end, bboxes (JSON), word_count"],
             ["policy_cards", "Extracted card (one per document)", "document_id (unique), data (JSON with sources), summary, model, prompt_version, verified_ratio"],
             ["risk_flags", "Risk highlights", "document_id, title, category, severity, explanation, clause_ordinal, page, quote, source (rule/ai), rule_id"],
             ["conversations", "A chat about one policy", "user_id, policy_id, title"],
             ["messages", "Questions and answers", "conversation_id, role, content, content_en, language, status, citations, faithfulness (+detail), retrieval, timings, model"],
             ["claim_cases", "Claim Copilot checks", "user_id, policy_id, treatment, inputs, result, verdict, checklist_state, faithfulness"],
             ["comparisons", "Plan comparisons", "user_id, policy_a_id, policy_b_id, result, model"],
             ["translations", "Cached Hindi/Telugu translations", "source_type, source_key, language, content"],
             ["llm_calls", "Usage log of model requests", "user_id (SET NULL), purpose, model, input/output tokens, latency_ms, ok, cached"]],
            "Database tables", widths=[0.16, 0.26, 0.58], font=9)
    d.p("Deleting a user cascades to their policies, conversations, claim cases and comparisons. A document row uses `RESTRICT` from "
        "`policies`, so a shared document is never removed while a policy still points to it.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([["Module", "Code", "Responsibility"],
             ["REST API", "backend/app/api/", "Authentication, policies, chat, claims, comparisons, dashboard, evaluation; consistent {detail, code} errors"],
             ["Ingestion worker", "services/ingestion.py", "Runs parse, index and extract in a background thread; resumes unfinished work after a restart"],
             ["PDF parser", "services/pdf_parser.py", "Lines with page, position and font; removes running headers and footers; two-column reading order; joins letter-spaced headings; tables as rows; rejects scans"],
             ["Segmenter", "services/segmenter.py", "Clause starts (`4.2.1`, `Def. 5`, `Excl03`, headings); IRDAI exclusion-code items as separate clauses; heading path; chunks of 12-380 words with highlight boxes"],
             ["Hybrid retriever", "ml/retrieval/", "BM25 with insurance synonyms; MiniLM + ChromaDB; Reciprocal Rank Fusion; cross-encoder re-rank"],
             ["Extractor", "services/extractor.py", "One schema-constrained Gemini call; quote location to verify clause and page"],
             ["Risk engine", "services/risk_engine.py", "Rules on extracted numbers plus AI findings, de-duplicated, with severity"],
             ["Answerer", "services/answerer.py", "Retrieval, abstention rule, rule/table context, cited answer, tag filtering"],
             ["Faithfulness scorer", "ml/faithfulness.py", "NLI support of each claim against sentence windows of its cited clauses, number check"],
             ["Claim Copilot", "services/claim_copilot.py, eligibility.py", "Multi-query retrieval; calculated pre-checks and estimate; structured verdict, checklist and steps"],
             ["Comparator", "services/comparator.py", "Field-by-field table with better markers and AI trade-offs citing both policies"],
             ["Language service", "services/language.py", "Script detection; query translation; card and risk translation (cached)"],
             ["Gemini client", "services/gemini_client.py", "JSON-schema calls, fallback chain, cool-down, RPM pacing, disk cache, usage log"],
             ["Evaluation harness", "ml/", "Retrieval, answer, claim and extraction evaluations; metrics, plots, run folders"]],
            "Modules of PolicyLens", widths=[0.17, 0.25, 0.58], font=9)


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The web application has twelve pages: the landing page, sign-in and registration, the dashboard, My policies, the policy view "
        "(with tabs for the Policy Card, risks, the original document and clause search), Ask your policy, the four-step Claim Copilot "
        "wizard, Compare plans, Model performance, Settings and a not-found page. A sidebar on wide screens and a bottom bar on phones "
        "give access to the main sections.",
        "Design decisions follow from the purpose of the product. Every fact carries a **clause and page chip** that opens the original "
        "page with the clause highlighted, so that trust never rests on the interface alone. Every answer shows its **faithfulness badge**, "
        "the model that produced it and its response time. Verdicts and severities use colour together with a text label, so the meaning "
        "does not depend on colour. The interface is available in light and dark themes, and honours the reduced-motion setting. Screens "
        "are shown in Chapter 8 and Appendix C.")
