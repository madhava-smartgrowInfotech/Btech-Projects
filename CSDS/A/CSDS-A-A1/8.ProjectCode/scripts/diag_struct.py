"""ER, UML class, use-case and sequence diagrams for PolicyLens (drawn from backend/app/models, services and api)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


# --------------------------------------------------------------------------- ER
def _table(c, x, top, w, name, cols, fc=BLUE_L):
    h = 4.2 + 2.55 * len(cols)
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=1.2)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=fc, bold=True, fs=7.4, r=1.2)
    for i, col in enumerate(cols):
        c.text(x + 1.2, y + h - 6.0 - 2.55 * i, col, fs=5.9, ha="left")
    return {"x": x, "y": y, "w": w, "h": h}


def er(out):
    c = Canvas(10.4, 7.9)
    W = 22.5
    R1, R2, R3 = 77, 49, 22
    _table(c, 2, R1, W, "users", ["PK id", "email (unique)", "full_name", "password_hash", "language, theme", "created_at"], BLUE_L)
    _table(c, 28.5, R1, W, "policies", ["PK id", "FK owner_id -> users", "FK document_id -> documents", "display_name", "is_sample", "created_at"], BLUE_L)
    _table(c, 55, R1, W, "documents", ["PK id", "sha256 (unique)", "file_name, page_count", "insurer, product_name, uin", "status, progress, error", "parse_stats (JSON)", "is_sample, sample_slug"], AMBER_L)
    _table(c, 81.5, R1, 20.5, "clauses", ["PK id", "FK document_id", "ordinal, clause_ref", "heading, section_path", "text, word_count", "page_start, page_end", "bboxes (JSON)"], AMBER_L)
    _table(c, 2, R2, W, "conversations", ["PK id", "FK user_id -> users", "FK policy_id -> policies", "title", "created_at, updated_at"], GREEN_L)
    _table(c, 28.5, R2, W, "messages", ["PK id", "FK conversation_id", "role, language, status", "content, content_en", "citations (JSON)", "faithfulness (+detail)", "retrieval, timings, model"], GREEN_L)
    _table(c, 55, R2, W, "policy_cards", ["PK id", "FK document_id (unique)", "data (JSON, sourced)", "summary (JSON)", "model, prompt_version", "verified_ratio"], AMBER_L)
    _table(c, 81.5, R2, 20.5, "risk_flags", ["PK id", "FK document_id", "title, category", "severity, source", "clause_ordinal, page", "quote, rule_id"], AMBER_L)
    _table(c, 2, R3, W, "claim_cases", ["PK id", "FK user_id, FK policy_id", "treatment, inputs (JSON)", "result (JSON), verdict", "checklist_state (JSON)", "faithfulness, model"], ROSE_L)
    _table(c, 28.5, R3, W, "comparisons", ["PK id", "FK user_id", "FK policy_a_id, policy_b_id", "result (JSON), model", "total_ms, language"], ROSE_L)
    _table(c, 55, R3, W, "translations", ["PK id", "source_type (card | risks)", "source_key (doc id:hash)", "language", "content (JSON), model"], GREY_L)
    _table(c, 81.5, R3, 20.5, "llm_calls", ["PK id", "FK user_id (SET NULL)", "purpose, model", "input/output tokens", "latency_ms, ok, cached"], GREY_L)

    def card(a, b, la="1", lb="N", fs=7):
        c.text(a[0], a[1], la, fs=fs, bold=True, color=INDIGO)
        c.text(b[0], b[1], lb, fs=fs, bold=True, color=INDIGO)

    c.line((24.5, 67), (28.5, 67)); card((25.6, 68.4), (27.4, 68.4))                    # users - policies
    c.line((51, 67), (55, 67)); card((52.2, 68.4), (53.9, 68.4), "N", "1")              # policies - documents
    c.line((77.5, 67), (81.5, 67)); card((78.6, 68.4), (80.4, 68.4))                    # documents - clauses
    c.line((66, 54.95), (66, 49)); card((67.3, 53.6), (67.3, 50.4), "1", "1")           # documents - policy_cards
    c.path([(72, 54.95), (72, 52), (91.7, 52), (91.7, 49)], head=False); card((73.2, 53.5), (93.0, 50.4))  # documents - risk_flags
    c.line((13.2, 57.5), (13.2, 49)); card((14.5, 56.2), (14.5, 50.4))                  # users - conversations
    c.line((24.5, 40), (28.5, 40)); card((25.6, 41.4), (27.4, 41.4))                    # conversations - messages
    c.path([(33, 57.5), (33, 53.5), (19, 53.5), (19, 49)], head=False); card((34.3, 55.8), (20.3, 50.4))   # policies - conversations
    c.path([(2, 70), (0.9, 70), (0.9, 12), (2, 12)], head=False); card((1.9, 71.2), (1.6, 13.4))           # users - claim_cases
    c.path([(28.5, 62), (26.4, 62), (26.4, 14), (24.5, 14)], head=False, ls="--"); card((27.2, 63.3), (25.5, 15.3))  # policies - claim_cases
    c.line((26.4, 10), (28.5, 10), ls="--"); card((26.9, 11.4), (27.9, 8.6), "1", "N")  # policies - comparisons (a, b)
    c.text(52, 0.9, "Every user-owned table references users.id (ON DELETE CASCADE); llm_calls uses SET NULL. Deleting a policy cascades to its conversations, claim checks and comparisons.", fs=6.4, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- UML
def _cls(c, x, top, w, name, attrs, methods, head=BLUE_L):
    n = max(len(attrs), 1) + max(len(methods), 1)
    h = 4.2 + 2.5 * n + 1.6
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=0.8, lw=1.1)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=head, bold=True, fs=7.0, r=0.8)
    ya = y + h - 6.0
    for a in attrs:
        c.text(x + 1.0, ya, a, fs=5.6, ha="left")
        ya -= 2.5
    if not attrs:
        ya -= 2.5
    c.line((x, ya + 1.2), (x + w, ya + 1.2), lw=0.8)
    ya -= 0.2
    for m in methods:
        c.text(x + 1.0, ya, m, fs=5.6, ha="left", italic=True)
        ya -= 2.5
    return {"x": x, "y": y, "w": w, "h": h, "top": top}


def uml(out):
    c = Canvas(10.4, 9.8)
    c.zone(1, 50, 102, 47, "Domain model (SQLAlchemy entities)", fc="#f4f5fb")
    T1, T2 = 90, 69
    U = _cls(c, 2.5, T1, 16, "User", ["id, email, full_name", "password_hash", "language, theme"], [])
    P = _cls(c, 21.5, T1, 16, "Policy", ["id, display_name", "is_sample", "owner_id, document_id"], [])
    D = _cls(c, 40.5, T1, 19, "Document", ["id, sha256, file_name", "page_count, insurer, uin", "status, progress", "parse_stats"], [])
    K = _cls(c, 62, T1, 18, "Clause", ["ordinal, clause_ref", "heading, section_path", "text, page_start/end", "bboxes"], [])
    PC = _cls(c, 83, T1, 18, "PolicyCard", ["data (sourced values)", "summary, model", "verified_ratio"], [])
    CV = _cls(c, 2.5, T2, 16, "Conversation", ["id, title", "user_id, policy_id"], [])
    M = _cls(c, 21.5, T2, 19, "Message", ["role, content, status", "citations, faithfulness", "timings, model"], [])
    R = _cls(c, 43, T2, 16, "RiskFlag", ["title, category", "severity, source", "clause_ordinal, page"], [])
    CC = _cls(c, 62, T2, 18, "ClaimCase", ["treatment, inputs", "result, verdict", "checklist_state"], [])
    CP = _cls(c, 83, T2, 18, "Comparison", ["policy_a_id, policy_b_id", "result, model"], [])
    mid = lambda b: b["y"] + b["h"] / 2
    c.arrow((18.5, mid(U)), (21.5, mid(P)), head=False, label="1..*", loff=(0, 1.6), fs=6)
    c.arrow((37.5, mid(P)), (40.5, mid(P)), head=False, label="*..1", loff=(0, 1.6), fs=6)
    c.arrow((59.5, mid(D)), (62, mid(D)), head=False, label="1..*", loff=(0, 1.6), fs=6)
    c.path([(50, T1), (50, T1 + 2.6), (92, T1 + 2.6), (92, T1)], head=False, label="1..1", loff=(0, 1.4), fs=6)
    c.arrow((50, D["y"]), (50, T2), head=False, label="1..*", loff=(3, 0), fs=6)
    c.arrow((10.5, U["y"]), (10.5, T2), head=False, label="1..*", loff=(3, 0), fs=6)
    c.arrow((18.5, T2 - 8), (21.5, T2 - 8), head=False, label="1..*", loff=(0, 1.6), fs=6)
    c.text(52, 52.2, "ClaimCase and Comparison also reference users.id and policies.id (see the ER diagram).", fs=6.2, italic=True)

    c.zone(1, 1, 102, 45, "Services and engine types (backend/app/services, backend/app/ml)", fc="#f1f9f5")
    S1, S2 = 41, 20
    A = _cls(c, 2.5, S1, 28, "Answerer", ["TOP_K = 7", "ABSTAIN_BELOW = 0.004, KEYWORD_FLOOR = 9.0"], ["answer_question(doc, q, lang, history)", "with_parent_context()"], head=GREEN_L)
    H = _cls(c, 34, S1, 22, "HybridRetriever", ["CANDIDATES = 30, RERANK_POOL = 20"], ["retrieve(doc, query, k, mode)", "bm25_index.search()", "dense_index.search()"], head=GREEN_L)
    F = _cls(c, 60, S1, 20, "FaithfulnessScorer", ["NLI DeBERTa (CPU)"], ["score_claims(claims, texts)", "label_for(score)"], head=GREEN_L)
    G = _cls(c, 84, S1, 17.5, "GeminiClient", ["fallback chain, cool-down", "RPM pacing, disk cache"], ["generate_json(prompt, schema)", "probe_models()"], head=AMBER_L)
    I = _cls(c, 2.5, S2, 22, "IngestionWorker", ["queue, status, progress"], ["enqueue(doc)", "process(job)", "resume_unfinished()"], head=INDIGO_L)
    S = _cls(c, 28, S2, 22, "PdfParser / Segmenter", ["Line, ParsedPdf, Chunk"], ["parse_pdf(path)", "segment(parsed)", "find_uin()"], head=INDIGO_L)
    X = _cls(c, 53.5, S2, 22, "Extractor / RiskEngine", ["PolicyCardExtraction"], ["run_extraction(doc)", "rule_risks(card)", "build_risks()"], head=INDIGO_L)
    E = _cls(c, 79, S2, 22.5, "ClaimCopilot / Eligibility / Comparator", ["ClaimPlan, TradeOff"], ["run_claim_copilot()", "pre_checks(card, treatment, inputs)", "compare(card_a, card_b)"], head=INDIGO_L)
    mid = lambda b: b["y"] + b["h"] / 2
    c.arrow((30.5, mid(A) + 3), (34, mid(A) + 3), label="uses", loff=(0, 1.6), fs=6)
    c.path([(16, A["y"]), (16, 23.6), (70, 23.6), (70, F["y"])], label="uses", loff=(0, 1.3), fs=6, ls=":")
    c.path([(10, A["y"]), (10, 22.4), (92, 22.4), (92, G["y"])], label="uses", loff=(0, 1.3), fs=6, ls=":")
    c.arrow((25, mid(I)), (28, mid(I)), label="calls", loff=(0, 1.6), fs=6)
    c.arrow((50, mid(S)), (53.5, mid(S)), label="text", loff=(0, 1.6), fs=6)
    c.text(52, 2.4, "Extractor, ClaimCopilot, Comparator, Answerer and the language service send every AI request through GeminiClient.", fs=6.2, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- use case
def usecase(out):
    c = Canvas(10.4, 8.4)
    c.zone(23, 1.5, 60, 81, "PolicyLens", fc="#fbfbff")

    def actor(x, y, label):
        c.ax.plot([x], [y + 6.2], "o", ms=7, mfc="white", mec="#1b2238")
        c.line((x, y + 5.4), (x, y + 2.4)); c.line((x - 2.6, y + 4.2), (x + 2.6, y + 4.2))
        c.line((x, y + 2.4), (x - 2.2, y)); c.line((x, y + 2.4), (x + 2.2, y))
        c.text(x, y - 2.4, label, fs=7.6, bold=True)

    actor(10, 38, "Policyholder")
    actor(94, 38, "Google Gemini API")
    actor(94, 6, "Visitor (no login)")
    cases = ["Register / sign in", "Upload policy PDF or add sample policies", "View Policy Card (values with clause + page)", "Review risk highlights",
             "Search clauses (BM25 / dense / hybrid)", "Ask a question, get a cited answer", "Open the cited clause on the policy page",
             "Run Claim Copilot, tick the checklist", "Compare two plans", "Switch language (en / hi / te)", "View dashboard", "View model performance"]
    ys = []
    for i, t in enumerate(cases):
        y = 75 - i * 6.1
        c.ellipse(53, y, 33, 5.0, t, fs=6.6)
        ys.append(y)
    for i, y in enumerate(ys):
        if i == 11:
            c.line((91.5, 11), (69.5, y))
        else:
            c.line((14.5, 43), (36.5, y))
    for i in (1, 2, 5, 7, 8, 9):
        c.line((91.5, 43), (69.5, ys[i]), ls="--")
    c.text(53, 83.0, "Solid: user action.  Dashed: the use case calls the Gemini API (Policy Card, answer, claim plan, comparison, translation).", fs=6.2, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- sequence
def sequence(out):
    c = Canvas(10.4, 7.8)
    names = [("User", 7), ("Web app\n(React)", 22), ("API\n(FastAPI)", 38), ("Hybrid\nretriever", 54), ("Gemini\nAPI", 69), ("NLI\nscorer", 83), ("SQLite", 96)]
    top, bot = 73, 1.5
    for n, x in names:
        c.box(x - 6, top, 12, 5.2, n, fc=INDIGO_L, ec=INDIGO, fs=7, bold=True)
        c.line((x, top), (x, bot), color="#9aa5ba", ls="--", lw=0.9)
    X = dict((n.split("\n")[0], x) for n, x in names)
    y = 69.5

    def msg(a, b, text, dy=3.5, dashed=False, self_=False):
        nonlocal y
        xa, xb = X[a], X[b]
        if self_:
            c.path([(xa, y), (xa + 6, y), (xa + 6, y - 2.4), (xa, y - 2.4)], label=None)
            c.text(xa + 7, y - 1.2, text, fs=6.4, ha="left")
            y -= 5.4
            return
        c.arrow((xa, y), (xb, y), ls="--" if dashed else "-", label=text, fs=6.3, loff=(0, 1.5))
        y -= dy

    msg("User", "Web app", "1  type question, press Enter")
    msg("Web app", "API", "2  POST /conversations/{id}/messages {question, language}")
    msg("API", "API", "3  check JWT, owner of policy; load history", self_=True)
    msg("API", "Gemini", "4  hi/te query -> English search query (cached)")
    msg("Gemini", "API", "English query", dashed=True, dy=3.3)
    msg("API", "Hybrid", "5  retrieve(): BM25 + dense -> RRF -> re-rank, top 7")
    msg("Hybrid", "API", "clauses with scores", dashed=True, dy=3.3)
    msg("API", "API", "6  abstain if re-rank < 0.004 and BM25 < 9.0", self_=True)
    msg("API", "Gemini", "7  prompt: tagged clauses + question + JSON schema")
    msg("Gemini", "API", "answer, claims[], follow-ups", dashed=True, dy=3.3)
    msg("API", "NLI", "8  score_claims(claims, cited clause text)")
    msg("NLI", "API", "support 0-100", dashed=True, dy=3.3)
    msg("API", "SQLite", "9  save message (citations, faithfulness, timings)")
    msg("API", "Web app", "10  201 answer + citations + score", dashed=True)
    msg("Web app", "User", "11  render answer, source chips, faithfulness badge", dashed=True)
    msg("User", "Web app", "12  click a source chip")
    msg("Web app", "API", "13  GET /policies/{id}/pages/{n}  (+ clause boxes)")
    msg("API", "Web app", "page PNG; highlight drawn over the clause", dashed=True)
    c.save(out)
