"""Chapter 6 content: methodology and software implementation."""
from __future__ import annotations

from doc_common import CHARTS, DIAG, EXP, POLICIES, RETR, ROOT
from rc_design import diagram


def src(path: str, start: int, end: int) -> str:
    """Real source lines (1-based, inclusive) from the project, so listings never drift from the code."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


def grab(path: str, marker: str, n: int) -> str:
    """`n` real source lines starting at the first line that contains `marker`."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if marker in line)
    return "\n".join(lines[i:i + n])


def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.paras(
        "PolicyLens turns an uploaded policy wording into four things: a searchable set of clauses, a Policy Card, cited answers and a "
        "claim plan. The method has two phases. **Preparation** runs once per document in a background worker: validate, parse, "
        "segment, index, extract the Policy Card and compute risks. **Use** runs on demand: retrieve clauses, generate a grounded answer "
        "or plan, and check it. The central idea, taken from the extract-then-generate structure of the base paper [1], is that the "
        "language model never reads the policy from memory: it is given only the clauses that retrieval selected, tagged so that every "
        "statement can be traced back, and everything it returns is checked afterwards.")
    d.table([["Step", "Method", "Output"],
             ["1 Validate", "PDF signature, size limit, encryption check, SHA-256 of the content", "Accepted document or a coded error"],
             ["2 Parse", "PyMuPDF lines with position and font; header/footer removal; column order; table rows", "Ordered lines per page"],
             ["3 Segment", "Rule-based clause starts and exclusion codes; heading path; 12-380 word chunks", "Clauses with page and highlight boxes"],
             ["4 Index", "BM25 Okapi; MiniLM embeddings in ChromaDB", "Keyword and vector indexes"],
             ["5 Policy Card", "One Gemini call with a JSON schema; quote location", "Card with source and verified flag per value"],
             ["6 Risks", "Rules on card numbers plus AI findings; de-duplication", "Risk highlights with severity"],
             ["7 Retrieve", "BM25 + dense, Reciprocal Rank Fusion, cross-encoder re-rank", "Top-7 clauses"],
             ["8 Generate", "Gemini with tagged clauses and a JSON schema", "Answer, claims, citations"],
             ["9 Check", "NLI entailment and number check; tag filtering", "Faithfulness score 0-100"],
             ["10 Claim / compare", "Calculated eligibility rules + Gemini; field-by-field table + trade-offs", "Verdict, checklist, estimate; comparison"]],
            "Pipeline of PolicyLens", widths=[0.16, 0.5, 0.34], font=9.5)


def sec_dataset(d):
    d.h2("Dataset")
    d.p("PolicyLens trains nothing, so it needs no training data. It works on whatever policy wording a user uploads. The repository ships "
        "two kinds of data: four sample policy wordings that make the product usable immediately, and an evaluation set written from "
        "them. Everything is small (about 4.7 MB), so the complete data is committed; no Kaggle or other dataset was used.")
    rows = [["Sample", "Insurer", "UIN", "Pages", "Words", "Clauses", "Layout", "Parse (s)"]]
    for n, ins, uin, pg, w, cl, lay, ps, *_ in POLICIES:
        rows.append([n, ins, uin, str(pg), f"{w:,}", str(cl), lay, f"{ps}"])
    rows.append(["**Total**", "", "", "**166**", "**73,001**", "**801**", "", ""])
    d.table(rows, "The four sample policy wordings", widths=[0.15, 0.2, 0.17, 0.06, 0.08, 0.08, 0.18, 0.08], font=8.5)
    d.p("**Source and licence.** The wordings are public documents that Indian insurers publish for prospective customers, downloaded from each "
        "insurer's official website and stored unmodified. Copyright remains with the insurers; the files are included only as sample "
        "input for demonstration and testing, and PolicyLens is not affiliated with or endorsed by any of them. **Why these four:** they "
        "cover the layouts a real product meets: two-column A4 with letter-spaced headings, small-page two-column with separately "
        "printed clause numbers, single column with `Def. N` numbering and ruled tables, and single column with multi-level numbering.")
    d.h3("Evaluation set")
    d.p("The evaluation set was written by hand from the four wordings; every expected answer was checked against the PDF and the "
        "evidence snippets are copied verbatim from the policy text.")
    d.table([["File", "Items", "Content"],
             ["qa.jsonl", "57", "51 answerable questions (Star 14, HDFC ERGO 13, Niva Bupa 12, Care 12 in total with 6 out-of-scope) in seven categories, each with evidence, pages and key facts"],
             ["qa_multilingual.jsonl", "5", "Hindi or Telugu questions (and one English question answered in Hindi)"],
             ["claims.jsonl", "14", "Claim scenarios with expected verdict: covered 5, partly covered 1, not covered 7, needs info 1"],
             ["cards.json", "52", "Hand-checked Policy Card values: UIN, insurer, waiting periods, pre/post-hospitalisation, free-look, room rent, bonus, deadlines"]],
            "Evaluation set (data/eval/)", widths=[0.22, 0.08, 0.7], font=9.5)
    d.p("**Split.** There is no training, so the whole set is a held-out test set. Nothing in it is used to fit any weight. It is used "
        "only to measure, and, as stated in the limitations, to choose a few pipeline settings and to find parser faults.")
    d.p("**Question categories** (51 answerable): benefits 15, waiting periods 14, claim process 8, exclusions 5, policy terms 4, room "
        "rent 3, sub-limits 2; plus 6 out-of-scope questions, for example \"Does this policy insure my house against fire?\".")


def sec_preprocessing(d):
    d.h2("Preprocessing: Parsing and Segmentation")
    d.paras(
        "Preprocessing is the most domain-specific part of the system, because policy wordings are laid out for printing, not for "
        "machines. **Validation** rejects files that are not PDFs (the content must start with `%PDF`), are larger than the configured "
        "limit (25 MB by default), are password-protected, have no pages or have no text layer, and reuses a document that was already "
        "processed (by SHA-256 of the content).",
        "**Parsing** (`pdf_parser.py`) reads every line with its page, bounding box and font. It removes running headers and footers by "
        "finding lines that repeat across pages, detects two-column pages and restores the reading order, joins words that were "
        "letter-spaced in headings, merges fragments on the same baseline, and reads tables row by row. A page with no text layer "
        "raises an error that is shown as \"no readable text layer\".",
        "**Segmentation** (`segmenter.py`) turns the ordered lines into clauses. A new clause starts at a printed number (`4.2.1`), a "
        "definition (`Def. 5`), an IRDAI exclusion code (`Excl03`), a section heading or a bold or Roman heading. A list item that carries an "
        "exclusion code becomes its own clause whether the code opens the item (\"o. Maternity: Code - Excl18\") or closes it. Each clause "
        "keeps its heading path (for example *Exclusions > Standard exclusions*), its page range and the rectangles of its lines, so "
        "that the viewer can highlight it. Long clauses are split into chunks of at most 380 words and fragments shorter than 12 words are "
        "merged. The four samples produced 801 clauses.",
        "**Why not fixed-size chunks?** A citation must point at one rule. Fixed windows cut rules in half and join unrelated ones, and "
        "the survey [6] names segmentation as the bottleneck for multi-step questions. Clause-aware chunks also give the viewer exact "
        "highlight positions. The cost is that the segmenter is rule-based and had to be extended when a failure showed a new pattern, "
        "as the third evaluation run shows (Chapter 8).")


def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.table([["Decision", "Chosen", "Alternatives considered", "Why"],
             ["Keyword retrieval", "BM25 Okapi (k1 = 1.4, b = 0.7) with insurance synonyms", "TF-IDF", "Policies are full of exact terms (\"cataract\", \"Excl02\", \"30 days\"); BM25 alone put the right clause in the top 5 for every question"],
             ["Dense retrieval", "all-MiniLM-L6-v2 + ChromaDB (cosine)", "Gemini embeddings", "Runs locally in about 10 ms, no quota; helps with paraphrases (\"glasses\" vs \"refractive error\")"],
             ["Combining retrievers", "Reciprocal Rank Fusion, k = 60", "Weighted score sum", "BM25 scores and cosine scores are not comparable; RRF needs no calibration [9]"],
             ["Ranking", "Cross-encoder ms-marco-MiniLM-L6-v2", "No re-ranking", "Reads the question and clause together; lifted rank-1 accuracy from 69% to 80% and MRR from 0.795 to 0.897"],
             ["Generator", "Gemini, JSON schema, low thinking, temperature 0.2", "Fine-tuned small model", "A whole wording fits in one request, structured output is checkable, Hindi/Telugu are good, free tier [17]"],
             ["Faithfulness", "nli-deberta-v3-xsmall + number check", "LLM-as-judge", "Independent of the writer, offline, no quota, deterministic [13], [14]"],
             ["Claim rules", "Calculated from the Policy Card", "Ask the model", "Months, ages and money must be exact; a failed waiting period must never read \"covered\""],
             ["Training", "None", "Fine-tune on policies", "The task is reading, not predicting; no labelled public set; wordings change every year"]],
            "Algorithm choices", widths=[0.15, 0.25, 0.18, 0.42], font=8.5)
    d.p("The retrieval choices were made by measurement. The table and figure below repeat the ablation reported in Chapter 8: no single method was best on every measure, "
        "and the combination of fusion and re-ranking gave the best ranking.")
    rows = [["Method", "hit@1", "hit@3", "hit@5", "MRR@10", "recall@5"]] + [[m, f"{a:.3f}", f"{b:.3f}", f"{c:.3f}", f"{e:.3f}", f"{f:.3f}"] for m, a, b, c, e, f, *_ in RETR]
    d.table(rows, "Retrieval ablation on 51 questions (run eval-20260922-0027)", widths=[0.34, 0.13, 0.13, 0.13, 0.14, 0.13], font=9.5, align=["l", "c", "c", "c", "c", "c"])
    d.figure(EXP / "retrieval_ablation.png", "Retrieval ablation: BM25, dense, hybrid and hybrid with re-rank", width=5.2)


def sec_math(d):
    d.h2("Mathematical Formulation")
    d.p("The formulas below are the ones implemented in the code; symbols are defined where they are used.")
    d.h3("Keyword score (BM25 Okapi)")
    d.p("For a query Q with terms q and a clause D, score(D, Q) = sum over q of IDF(q) * f(q, D) * (k1 + 1) / (f(q, D) + k1 * (1 - b + b * |D| / avgdl)), "
        "where f(q, D) is the frequency of q in D, |D| the length of D in tokens, avgdl the average clause length, k1 = 1.4 and b = 0.7 [8]. "
        "Queries are expanded with an insurance synonym list.")
    d.h3("Dense score")
    d.p("Each clause and each query is embedded by all-MiniLM-L6-v2 into a 384-dimensional vector; the dense score is the cosine similarity of "
        "the query vector and the clause vector, searched in ChromaDB [10], [11].")
    d.h3("Reciprocal Rank Fusion")
    d.p("Given the rankings r (BM25 and dense, for each query variant), the fused score of a clause d is RRF(d) = sum over r of w_r / (k + rank_r(d)) "
        "with k = 60 and w_r = 1 [9]. The pool for re-ranking is the fused top 20 plus the top 8 of each retriever, so that a clause found by only one "
        "method (for example an exact keyword match) still reaches the re-ranker.")
    d.h3("Re-ranking and the final score")
    d.p("The cross-encoder returns a relevance score s_ce(q, d) for each pool member. The final score is s(d) = s_ce(q, d) + 0.001 * 60 * RRF(d): "
        "the cross-encoder decides and the fused rank breaks ties. The best seven clauses are kept (TOP_K = 7).")
    d.h3("Abstention rule")
    d.p("Let s_max be the best final score and b_max the best BM25 score among the retrieved clauses. PolicyLens answers \"not covered in this policy\" "
        "without calling the model if there are no clauses or if s_max < 0.004 and b_max < 9.0. Neither value separates answerable from "
        "unanswerable questions on its own (answerable questions had re-rank scores as low as 0.0020 and BM25 scores as low as 7.1; out-of-scope "
        "questions reached 0.0029 and 7.3), but the pair did on the evaluation set.")
    d.h3("Faithfulness score")
    d.p("The model restates its answer as short claims c_1 ... c_n, each tagged with clauses. For each claim the cited clause text is cut into "
        "sentence and two-sentence windows w, the eight windows most similar to the claim are kept, and an NLI model gives the probability of "
        "entailment e(w, c) from the softmax of its logits. The support of a claim is support(c) = max( max_w e(w, c), 0.75 * overlap(c, text) if "
        "overlap(c, text) >= 0.8 ), multiplied by 0.5 if a number in the claim (dates and calendar years excluded) does not occur in the cited text. "
        "The answer's score is F = 100 * (1/n) * sum of support(c_i). The labels are well supported (F >= 80), partly supported (50 <= F < 80) "
        "and weakly supported (F < 50).")
    d.h3("Claim estimate")
    d.p("For an estimated bill C, a deductible dd, a sub-limit cap L that names the treatment (if any) and an applicable co-payment of p percent, "
        "the payable amount is P = min(max(0, C - dd), L), the co-payment is P * p / 100, the insurer pays P - P * p / 100, and the policyholder "
        "pays C minus that amount. The estimate is before non-payable items and before any room-rent proportionate deduction, and says so.")
    d.h3("Evaluation measures")
    d.p("hit@k is the share of questions with a relevant clause in the top k, where a clause is relevant if it contains one of the question's "
        "verbatim evidence snippets; MRR@10 is the mean of 1/rank of the first relevant clause (0 if none in the top 10); evidence recall@5 is "
        "the share of a question's evidence snippets found in the top 5. Answer accuracy is the share of answerable questions whose answer is not "
        "\"not in policy\" and contains every key fact; citation accuracy is the share whose cited clause contains the evidence or lies on an expected page; "
        "abstention accuracy is the share of out-of-scope questions declined. Claim accuracy is the share of scenarios with the expected verdict.")


def sec_model_training(d):
    d.h2("Models and Training Configuration")
    d.p("PolicyLens does not train a model. It combines pre-trained models, each chosen for one job, with rules that check their output. "
        "The tuned quantities are pipeline settings, each chosen by measurement on the evaluation set.")
    d.table([["Role", "Model", "Runs", "Size"],
             ["Generation, card, claim, comparison, translation", "Gemini: gemini-3.8-flash, then gemini-3.6-flash, then gemini-3.5-flash-lite", "Google API", "-"],
             ["Dense retrieval", "sentence-transformers/all-MiniLM-L6-v2 (384-d)", "CPU", "91.6 MB"],
             ["Re-ranking", "cross-encoder/ms-marco-MiniLM-L6-v2", "CPU", "91.8 MB"],
             ["Faithfulness", "cross-encoder/nli-deberta-v3-xsmall", "CPU", "294.5 MB"],
             ["Keyword retrieval", "BM25 Okapi (rank-bm25), k1 = 1.4, b = 0.7", "CPU", "-"],
             ["Vector store", "ChromaDB, persistent, cosine", "CPU", "-"]],
            "Models used", widths=[0.28, 0.5, 0.1, 0.12], font=9.5)
    d.table([["Setting", "Value", "Chosen because"],
             ["Clause size", "12-380 words", "A citation points at one rule; long clauses are split at sub-items"],
             ["Candidates per retriever", "30", "Lets fusion see clauses ranked well by only one retriever, keeping search under 20 ms"],
             ["Fusion", "RRF, k = 60", "Standard; no score scaling needed"],
             ["Re-rank pool", "fused top 20 + top 8 of each retriever", "The extra 8 recovered questions where one retriever alone found the clause"],
             ["Clauses given to Gemini", "top 7 + up to 4 governing rules or governed tables", "Waiting-period lists and sub-limit tables are separate chunks from the rule that gives them meaning"],
             ["Abstention", "re-rank < 0.004 and best BM25 < 9.0", "Separates the 6 out-of-scope from the 51 answerable questions"],
             ["Temperature", "0.2 (answers), 0.1 (Policy Card)", "Stable, repeatable wording"],
             ["Gemini fallback", "3 models, 10-minute cool-down, RPM 10", "Free-tier quota and overload"]],
            "Pipeline settings", widths=[0.24, 0.3, 0.46], font=9.5)
    d.p("**Why there is no training.** The task is reading, not predicting; every answer must come from the user's own wording. There is "
        "no public set of policy questions with clause-level answers for Indian health policies, so the hand-built set is small and is used "
        "only to measure. And wordings change every year, whereas retrieval over the uploaded document keeps working without retraining. "
        "Consequently there are no training curves, no epochs and no learning rate; the corresponding evidence is the evaluation in Chapter 8.")


def sec_app_arch(d):
    d.h2("Application Architecture")
    d.paras(
        "The backend is organised in layers: routers in `api/` validate input and enforce ownership; services in `services/` and `ml/` hold "
        "the logic; models in `models/` map to tables; schemas in `schemas/` define request and response types with Pydantic v2; `core/` "
        "holds configuration, the database session, error types, logging and security. A background thread (the ingestion worker) takes "
        "jobs from a queue so that upload returns immediately; the web app polls `/policies/{id}/status` every two seconds until the "
        "status is `ready`.",
        "The frontend is a single-page React application in TypeScript. React Router provides the routes with lazy-loaded pages; TanStack "
        "Query caches server data and drives the polling; Axios attaches the JWT; Tailwind CSS and shadcn/ui components provide the styling; "
        "Recharts draws the dashboard and the Model performance charts. The viewer shows page images that the backend renders with the "
        "highlight rectangles supplied by the parser, so the browser needs no PDF library.")


def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Reciprocal Rank Fusion")
    d.p("The fusion function is eleven lines. It adds 1/(k + rank) for each list in which an item appears and sorts by the total.")
    d.code(src("backend/app/ml/retrieval/fusion.py", 8, 15), "reciprocal_rank_fusion() in ml/retrieval/fusion.py")
    d.h3("The abstention rule and the call to the model")
    d.p("In `answer_question()`, after retrieval, the answerer checks the two scores. Only if the rule does not fire is the model called.")
    d.code(grab("backend/app/services/answerer.py", "if not retrieved or (result.best_score", 5), "Abstention check in services/answerer.py")
    d.h3("Dropping citations that were not retrieved")
    d.p("The model can only cite clauses it was given. Any tag that does not belong to a retrieved clause is removed from the text, and "
        "unknown ordinals are discarded from the claims, so a citation can never point to something the system did not show.")
    d.code(grab("backend/app/services/answerer.py", "# Keep only citations", 13), "Citation filtering in services/answerer.py")
    d.h3("Faithfulness: support of a claim")
    d.p("The support of each claim is the best entailment over the evidence windows, with a lexical backstop for near-verbatim restatements "
        "and a penalty when a number is not found in the cited text.")
    d.code(grab("backend/app/ml/faithfulness.py", "claim_numbers = _numbers(claim.text)", 9), "Claim support in ml/faithfulness.py")
    d.h3("Calculated claim estimate")
    d.p("The estimate is plain arithmetic on the Policy Card values, not model output.")
    d.code(grab("backend/app/services/eligibility.py", "cost = inputs.get(\"estimated_cost\")", 12), "Cost estimate in services/eligibility.py")


def sec_api(d):
    d.h2("API Design")
    d.p("The API is REST over JSON under `/api`, with 42 route handlers. Interactive documentation (Swagger UI) is served at `/docs`. All "
        "endpoints except health, registration, login and the evaluation endpoints require `Authorization: Bearer <token>`. Errors are always "
        "`{\"detail\": \"readable message\", \"code\": \"machine_code\"}`.")
    d.table([["Group", "Endpoints"],
             ["Health", "GET /health"],
             ["Auth and user", "POST /auth/register, POST /auth/login, GET /auth/me, PATCH /users/me, POST /users/me/password, GET /users/languages"],
             ["Policies", "GET/POST /policies, POST /policies/samples, GET/PATCH/DELETE /policies/{id}, GET /policies/{id}/status, /file, /pages, /pages/{n}, /clauses, /clauses/{ordinal}, /card, /risks, POST /policies/{id}/extract, POST /policies/{id}/search"],
             ["Chat", "POST/GET /conversations, GET/DELETE /conversations/{id}, POST /conversations/{id}/messages"],
             ["Claims", "POST/GET /claims, GET/DELETE /claims/{id}, PATCH /claims/{id}/checklist"],
             ["Compare", "POST/GET /comparisons, GET/DELETE /comparisons/{id}"],
             ["Dashboard and evaluation", "GET /dashboard/summary; GET /evaluation/latest, /evaluation/runs, /evaluation/runs/{run}, /evaluation/runs/{run}/plots/{file}"]],
            "API endpoints", widths=[0.2, 0.8], font=9)
    d.p("**Example: ask a question.** `POST /api/conversations/{id}/messages` with the body below returns the stored question and the answer "
        "with its citations, faithfulness score, retrieval trace and timings; the `status` is `answered`, `partial` or `not_in_policy`.")
    d.code('{"question": "Is cataract surgery covered and after how long?", "language": "en"}', "Request body")
    d.p("**Example: Claim Copilot.** `POST /api/claims` needs only `policy_id` and `treatment`; the other fields sharpen the result.")
    d.code('{"policy_id": 4, "treatment": "Knee replacement", "hospitalization_type": "planned", "claim_mode": "cashless",\n'
           ' "policy_start_date": "2023-10-01", "insured_age": 64, "pre_existing": "no", "estimated_cost": 350000, "language": "en"}', "Request body")
    d.p("The response contains the verdict (`covered`, `partly_covered`, `not_covered`, `needs_info`), the reasons with their clauses, the "
        "pre-checks (`pass`, `fail`, `warning`, `unknown`), the document checklist, the claim steps, the estimate and the timings.")


def sec_security(d):
    d.h2("Security and Error Handling")
    d.bullets([
        "**Passwords** are hashed with bcrypt; a password needs at least eight characters with a letter and a number; login is case-insensitive on the e-mail address.",
        "**Tokens.** A signed JWT (HS256, PyJWT) with a 24-hour expiry (`JWT_EXPIRE_MINUTES`, default 1440). The signing secret is generated by `setup.bat` in `.env`; if it is missing the code falls back to a development default, which must be replaced for any shared deployment.",
        "**Ownership.** Every policy, conversation, claim check and comparison is tied to its owner and returned only to that user; this is covered by `test_policy_flow.py`.",
        "**Uploads** are validated before they are stored: PDF signature, size limit (25 MB by default), encryption, page count and duplicate hash.",
        "**Secrets** (the Gemini key, the JWT secret) live in `.env`, which is excluded from version control; the API never returns them.",
        "**CORS** is limited to the configured origins (the web app on port 5101).",
        "**Error handling.** Application errors carry a code and a readable message; validation errors return 422 with details; unexpected errors are logged and returned as a generic message. AI errors are mapped to `ai_quota` (429), `ai_unavailable` (503) or `ai_not_configured` (503), and the web app turns them into plain messages.",
        "**Model-output safety.** Output is constrained by a JSON schema, citations are filtered to retrieved clauses, and rule-based checks cannot be overruled by the model. Text inside an uploaded PDF is passed to the model, so a deliberately crafted document could try to instruct it; this was not tested (see Chapter 7).",
    ])


def sec_install(d):
    d.h2("Installation and Execution")
    d.p("The full guide is `docs/03_HOW_TO_RUN.md` and Appendix B. In short, on Windows 10 or 11 with Python 3.11 and Node.js LTS:")
    d.table([["Step", "Command", "What it does"],
             ["1", "setup.bat", "Checks Python and Node, creates the virtual environment, installs packages, creates `.env`, downloads the three local models (about 480 MB), installs the web packages, creates the database, the demo account and the four sample policies, and builds their index"],
             ["2", "edit `.env`", "Paste the free Gemini API key after `GEMINI_API_KEY=`"],
             ["3", "run.bat", "Starts the API (port 8101) and the web app (port 5101) and opens http://localhost:5101"],
             ["4", "demo@policylens.app / Demo@12345", "Sign in to the demo account with four ready sample policies"],
             ["5", "stop.bat", "Stops both servers"],
             ["6", "venv\\Scripts\\python ml\\run_all.py", "Re-runs the full evaluation (about 10 minutes, about 80 Gemini requests)"]],
            "Installation and execution", widths=[0.07, 0.33, 0.6], font=9)
