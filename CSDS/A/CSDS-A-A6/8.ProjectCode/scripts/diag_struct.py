"""ER, UML class, use-case and sequence diagrams for ClauseGuard (from backend/app/db.py, schemas.py, routes and services)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas


def table(c, x, y, w, title, cols, fs=6.2, row=3.7, fc=INDIGO_L):
    """ER table box: header + one line per column (name  type). (x, y) = top-left."""
    h = 5.2 + row * len(cols)
    c.rect(x, y - h, w, h, fc="white", ec=INK, lw=1.2)
    c.rect(x, y - 5.2, w, 5.2, fc=fc, ec=INK, lw=1.2)
    c.text(x + w / 2, y - 2.6, title, fs=7.4, bold=True)
    for i, (n, t, k) in enumerate(cols):
        yy = y - 5.2 - row * (i + 0.5)
        c.text(x + 1.5, yy, (k + " " if k else "") + n, fs=fs, ha="left", bold=bool(k))
        c.text(x + w - 1.5, yy, t, fs=fs, ha="right", color="#4a5570")
    return {"x": x, "y": y - h, "w": w, "h": h}


def er(out):
    c = Canvas(10.4, 7.4)
    c.text(52, 71, "ER diagram - SQLite (SQLAlchemy models in backend/app/db.py)", fs=10.5, bold=True)
    R = 2.9
    table(c, 2, 66, 22, "users", [("id", "int", "PK"), ("email", "varchar(255), unique", ""), ("password_hash", "varchar(255)", ""), ("created_at", "datetime", "")], row=R)
    table(c, 29, 66, 28, "contracts", [("id", "int", "PK"), ("user_id", "int", "FK"), ("filename", "varchar(500)", ""), ("contract_type_guess", "varchar(100)", ""),
                                       ("uploaded_at", "datetime", ""), ("complexity_grade / _score", "varchar(2) / float", ""),
                                       ("readability_score, legalese_density", "float", ""), ("cross_reference_count, avg_sentence_length", "int / float", ""),
                                       ("plain_summary", "text", ""), ("key_obligations, combo_flags", "text (JSON)", "")], row=R)
    table(c, 62, 66, 36, "clauses", [("id", "int", "PK"), ("contract_id", "int", "FK"), ("index_in_doc", "int", ""), ("page_number", "int", ""), ("text", "text", ""),
                                     ("clause_type", "varchar(100)", ""), ("classification_confidence", "float", ""),
                                     ("classification_method", "varchar(20)", ""), ("embedding", "blob (float32 x 3,072)", "")], row=R)
    table(c, 62, 28, 36, "flags", [("id", "int", "PK"), ("clause_id", "int", "FK"), ("rule_id", "varchar(100)", ""), ("rule_label", "varchar(200)", ""),
                                   ("severity", "varchar(20): low / medium / high", ""), ("reason, provision, safer_wording", "text", "")], row=R)
    c.arrow((24, 58), (29, 58), head=False, lw=1.4)
    c.text(25, 60.5, "1", fs=7, bold=True); c.text(28, 60.5, "N", fs=7, bold=True); c.text(26.5, 55.6, "owns", fs=6.4, italic=True)
    c.arrow((57, 58), (62, 58), head=False, lw=1.4)
    c.text(58, 60.5, "1", fs=7, bold=True); c.text(61, 60.5, "N", fs=7, bold=True); c.text(59.5, 55.6, "contains", fs=6.4, italic=True)
    c.arrow((80, 34.6), (80, 28), head=False, lw=1.4)
    c.text(78, 33.4, "1", fs=7, bold=True); c.text(78, 29.3, "N", fs=7, bold=True); c.text(84.5, 31.3, "raises", fs=6.4, italic=True)
    c.box(2, 12, 54, 12, "Cascade: deleting a user deletes contracts, clauses and flags (relationship cascade = all, delete-orphan).\n"
                         "combo_flags (JSON on contracts) stores the risky combinations: combo_id, reason, rule_ids, clause_ids.\n"
                         "There is no table for the clause graph: it is rebuilt from clauses and flags on each request.", fc=GREY_L, fs=6.3, align="left", pad=1.5)
    c.text(52, 3.5, "4 tables, 3 foreign keys (user_id, contract_id, clause_id). Rules and combinations are constants in code, not rows.", fs=6.3, italic=True)
    c.save(out)


def cls(c, x, y, w, name, attrs, ops, fc=INDIGO_L, fs=5.5, row=2.5):
    h = 4.4 + row * (len(attrs) + len(ops)) + 1.2
    c.rect(x, y - h, w, h, fc="white", ec=INK, lw=1.1)
    c.rect(x, y - 4.4, w, 4.4, fc=fc, ec=INK, lw=1.1)
    c.text(x + w / 2, y - 2.2, name, fs=6.8, bold=True)
    yy = y - 4.4
    for a in attrs:
        yy -= row
        c.text(x + 1, yy + row / 2, a, fs=fs, ha="left")
    if attrs and ops:
        c.line((x, yy - 0.3), (x + w, yy - 0.3), lw=0.8)
    for o in ops:
        yy -= row
        c.text(x + 1, yy + row / 2 - 0.3, o, fs=fs, ha="left")
    return {"x": x, "y": y - h, "w": w, "h": h}


def uml(out):
    c = Canvas(10.4, 11.0)
    c.text(52, 107, "UML class diagram - persistent entities, rule model and services", fs=10, bold=True)
    cls(c, 1.5, 103, 21, "User", ["id: int", "email: str", "password_hash: str", "created_at: datetime"], [])
    cls(c, 27, 103, 28, "Contract", ["id, user_id: int", "filename: str", "complexity_grade: str", "complexity_score: float", "readability_score, legalese_density",
                                     "cross_reference_count: int", "avg_sentence_length: float", "plain_summary: str", "key_obligations, combo_flags: JSON"],
        ["combo_flags_list() -> list", "key_obligations_list() -> list"])
    cls(c, 60, 103, 28, "Clause", ["id, contract_id: int", "index_in_doc, page_number: int", "text: str", "clause_type: str", "classification_confidence: float",
                                   "classification_method: str", "embedding: bytes"], [])
    cls(c, 60, 78, 28, "Flag", ["id, clause_id: int", "rule_id, rule_label: str", "severity: str", "reason, provision: str", "safer_wording: str"], [])
    cls(c, 27, 65, 28, "Rule (dataclass)", ["id, label: str", "severity: str", "legal_basis: str", "pattern: re.Pattern"], ["RULES: list[Rule] (8)", "detect_flags(text) -> list[Rule]"], fc=AMBER_L)
    cls(c, 1.5, 65, 21, "ParsedPage", ["text: str", "page_number: int"], ["extract_pages(path, type)", "split_into_clauses(pages)"], fc=GREEN_L)
    cls(c, 1.5, 46, 22, "Classification", ["SAMPLE_PATH, CENTROID_CACHE", "TIE_BREAK_MARGIN = 0.03"], ["build_or_load_centroids()", "classify_clause(text)", "_tie_break(text, cands)"], fc=GREEN_L)
    cls(c, 26, 46, 22, "RiskGraph (graph.py)", ["RISKY_COMBOS (3)"], ["detect_risky_combinations()", "build_clause_graph()", "graph_to_json()"], fc=GREEN_L)
    cls(c, 51, 46, 22, "Complexity", ["LEGALESE_TERMS", "CROSS_REF_RE"], ["flesch_reading_ease()", "legalese_density()", "score_contract()"], fc=GREEN_L)
    cls(c, 76, 46, 22, "Explain", [], ["explain_flag(text, rule)", "summarize_contract(...)"], fc=GREEN_L)
    cls(c, 1.5, 24, 22, "GeminiClient", [], ["embed_text(text, task)", "generate_json(prompt)", "generate_text(prompt)"], fc=ROSE_L)
    cls(c, 26, 24, 22, "VectorStore", [], ["to_blob(), from_blob()", "cosine_similarity_matrix()", "top_k_similar()"], fc=GREEN_L)
    cls(c, 51, 24, 22, "Pipeline", [], ["process_upload(session, user_id,", "   path, filename, type) -> Contract"], fc=INDIGO_L)
    cls(c, 76, 24, 22, "Routers + auth", [], ["POST /auth/register, /login", "POST /contracts/upload", "GET /contracts, /{id}, /clauses, /graph", "GET /eval/metrics"], fc=BLUE_L)
    # associations (1 to many)
    c.arrow((22.5, 96), (27, 96), head=False); c.text(24.7, 97.6, "1..*", fs=5.6)
    c.arrow((55, 96), (60, 96), head=False); c.text(57.5, 97.6, "1..*", fs=5.6)
    c.arrow((74, 78), (74, 78 + 0.01), head=False)
    c.path([(74, 80.9), (74, 78)], head=False); c.text(76.5, 79.5, "1..*", fs=5.6)
    c.arrow((55, 63), (60, 63), ls="--", label="produces", loff=(0, 1.6), fs=5.4)
    c.arrow((12, 49.5), (12, 46.3), ls="--"); c.text(16, 48, "feeds", fs=5.4)
    # pipeline dependencies (dashed)
    c.text(52, 5.5, "Pipeline orchestrates ParsedPage, Classification, Rule, RiskGraph, Complexity and Explain; Classification and Explain call GeminiClient;", fs=6.0, italic=True)
    c.text(52, 2.7, "VectorStore does the cosine maths. Solid lines: association; dashed: dependency. Entities are SQLAlchemy models; Rule is a plain dataclass.", fs=6.0, italic=True)
    c.save(out)


def usecase(out):
    c = Canvas(10.4, 7.4)
    c.text(52, 71.5, "Use-case diagram", fs=10.5, bold=True)
    c.zone(25, 6, 52, 62, "ClauseGuard")
    cases = [("UC1 Register / log in", 51, 59.5), ("UC2 Upload contract\n(PDF / DOCX)", 51, 50.5), ("UC3 View complexity grade\nand plain summary", 51, 41.5),
             ("UC4 Open flagged clause:\nreason, quote, safer wording", 51, 32.5), ("UC5 View clause graph and\nrisky combinations", 51, 23.5), ("UC6 List my contracts", 33, 14), ("UC7 View evaluation results", 69, 14)]
    for t, x, y in cases:
        c.ellipse(x, y, 22 if x == 51 else 17, 7.2, t, fc=INDIGO_L, ec=INDIGO, fs=6.2)
    c.ellipse(51, 11, 0.1, 0.1, "", fc="white", ec="white")
    c.box(2, 40, 17, 9, "Signatory\n(registered user)", fc=BLUE_L, fs=7.0, bold=True)
    c.box(2, 18, 17, 8, "Visitor\n(not signed in)", fc=GREY_L, fs=7.0, bold=True)
    c.box(83, 46, 16, 9, "Google Gemini\n(secondary actor)", fc=ROSE_L, ec="#c98a8a", fs=6.8, bold=True)
    c.box(83, 18, 16, 8, "Evaluator\n(runs ml/eval.py)", fc=GREEN_L, fs=6.8, bold=True)
    for t, x, y in cases[:6]:
        pass
    for (x, y) in [(40, 59.5), (40, 50.5), (40, 41.5), (40, 32.5), (40, 23.5), (28, 14.6)]:
        c.line((19, 44.5), (x, y), lw=0.9)
    c.line((19, 22), (40, 59.5), lw=0.9)
    c.line((19, 22), (60, 14.6), lw=0.9, ls="-")
    c.line((62, 50.5), (83, 50.5), lw=0.9, ls="--")
    c.line((62, 32.5), (83, 49), lw=0.9, ls="--")
    c.line((62, 41.5), (83, 48), lw=0.9, ls="--")
    c.line((77.5, 14.6), (83, 20), lw=0.9)
    c.text(72, 52.2, "<<include>> classify, explain", fs=5.8, italic=True)
    c.text(52, 2.6, "UC2-UC6 need a valid JWT and operate only on the caller's own contracts; UC7 and the landing page are public. Gemini supplies embeddings, explanations and summaries.", fs=6.2, italic=True)
    c.save(out)


def sequence(out):
    c = Canvas(10.4, 11.8)
    c.text(52, 114.5, "Sequence diagram - uploading a contract and reading the report", fs=10, bold=True)
    names = [("Signatory", 7), ("React app", 22), ("FastAPI\nroute", 37), ("pipeline /\nservices", 52), ("Gemini\nAPI", 67), ("SQLite", 82), ("Filesystem", 95)]
    for n, x in names:
        c.box(x - 6, 105, 12, 5.5, n, fc=BLUE_L if x < 30 else INDIGO_L if x < 60 else ROSE_L if x == 67 else GREY_L, fs=6.2, bold=True)
        c.line((x, 105), (x, 3), ls="--", lw=0.8, color="#9aa5ba")
    y = [101.5]

    def msg(a, b, t, ret=False, ls="-"):
        if a == b:
            c.text(a + 2, y[0], t, fs=5.7, ha="left", italic=True)
        else:
            c.arrow((a, y[0]), (b, y[0]), ls="--" if ret else ls, label=t, loff=(0, 1.7), fs=5.7)
        y[0] -= 4.0

    msg(7, 22, "choose file, press Analyse")
    msg(22, 37, "POST /api/contracts/upload (Bearer JWT, multipart)")
    msg(37, 82, "decode JWT, load user (401 if invalid)")
    msg(37, 95, "write temp file (uuid + extension)")
    msg(37, 52, "process_upload(session, user, file)")
    msg(52, 95, "extract_pages, split_into_clauses")
    c.box(47, y[0] - 1.8, 28, 4.6, "loop: for each clause", fc=AMBER_L, ec="#c9a45a", fs=5.8)
    y[0] -= 6.0
    msg(52, 67, "embed_text(clause)")
    msg(67, 52, "3,072-d vector", ret=True)
    msg(52, 67, "tie-break prompt (only if close and < 0.60)", ls="--")
    msg(52, 52, "detect_flags(text): 8 regex rules")
    msg(52, 67, "explain_flag(text, rule) for each hit")
    msg(67, 52, "reason, provision, safer wording", ret=True)
    msg(52, 82, "flush Clause and Flag rows")
    c.box(47, y[0] - 1.8, 28, 4.6, "end loop", fc=AMBER_L, ec="#c9a45a", fs=5.8)
    y[0] -= 6.0
    msg(52, 52, "combinations + complexity score (local)")
    msg(52, 67, "summarize_contract(excerpts, flags)")
    msg(67, 52, "plain_summary, key_obligations", ret=True)
    msg(52, 82, "commit Contract")
    msg(37, 95, "delete temp file")
    msg(37, 22, "200 ContractReportResponse", ret=True)
    msg(22, 7, "show /app/contracts/{id}", ret=True)
    msg(22, 37, "GET /contracts/{id}/clauses/{cid}, /graph")
    msg(37, 82, "read clause + flags (owner check, else 404)")
    msg(37, 22, "ClauseResponse / graph JSON", ret=True)
    c.save(out)
