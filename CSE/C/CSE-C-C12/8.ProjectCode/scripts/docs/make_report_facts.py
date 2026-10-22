"""Write docs/REPORT_FACTS.md from docs/metrics/*.json (run after scripts/measure_metrics.py):  python -m scripts.docs.make_report_facts"""
import os

from . import facts as F

R = F.RET
LAB = {c: R[c]["label"] for c in F.CFG_ORDER}
SETN = {"S1_shipped_protocol_30": "S1 shipped protocol (30; held-out record still indexed)", "S1_leave_one_out_30": "S1 leave-one-out (30)",
        "S2_verbatim_leave_one_out_176": "S2 verbatim, leave-one-out (176)", "S3_two_symptoms_leave_one_out_176": "S3 two random symptoms, leave-one-out (176)",
        "S4_lay_language_60": "S4 lay-language probes (60)"}


def main():
    L = []
    w = L.append
    w("# REPORT_FACTS - SymptoTrackAI (CSE-C-C12)\n")
    w("Everything in the documents must agree with this file. Numbers come from `docs/metrics/*.json` (measured on 2026-10-22 by `scripts/measure_metrics.py`, "
      "`scripts/measure_latency.py`, pytest and `scripts/smoke_test.py`); nothing here is estimated.\n")
    w("## 1. Identity\n")
    w(f"- Project title: **{F.FULL_TITLE}**. The application is implemented, and shown on screen, as **{F.APP_NAME}** (name in the code); the documents call the project SymptoTrackAI and name CareLens AI as the implemented web application.")
    w(f"- Batch {F.BATCH_NO} ({F.SECTION}); guide {F.GUIDE}; students: " + "; ".join(f"{n} ({r})" for n, r in F.STUDENTS) + ".")
    w(f"- Base paper: {F.BASE_PAPER}  It reports **no numbers** (qualitative 'experimental observations'; one example: constipation + stomach ache + high fever + swollen lymph nodes -> Typhoid). "
      "It uses a 'Sequence-NQ transformer' + FAISS + RAG over a symptom-disease knowledge base, with registration/login and a stored consultation history.")
    w(f"- Ports: backend {F.API_PORT}, frontend {F.WEB_PORT}. Demo login `{F.DEMO_LOGIN[0]}` / `{F.DEMO_LOGIN[1]}`.\n")
    w("## 2. Architecture (from the code)\n")
    w("`symptoms -> normalise -> HyDE-style template expansion -> MiniLM embedding -> FAISS (IndexFlatIP, 384-d) + BM25 (rank-bm25) -> min-max fusion 0.65/0.35 (top 15) -> MS-MARCO MiniLM cross-encoder rerank (top 5) -> grounded generation (Flan-T5-small, or evidence-based fallback) -> regex safety layer + answer filter -> UI + SQLite`")
    w("- Backend: FastAPI + Uvicorn, SQLAlchemy/SQLite (`users`, `consultations`), bcrypt, PyJWT HS256 (httponly cookie `carelens_token`, 1440 min), Pydantic v2. "
      f"Frontend: React 19 + Vite 8 (kit V2 'Neo Brutal Grid'), react-router 7, recharts. Legacy Jinja pages remain served by the backend (`/`, `/login`, `/dashboard` ...).")
    w(f"- Models (all local, CPU): `{F.ENV['embedding_model']}` (384-d), `{F.ENV['reranker_model']}`, `{F.ENV['generator_model']}` (77 M parameters class, T5-small family); fallbacks: TF-IDF (384 features) for embeddings, hybrid order without rerank, evidence-based template answer.")
    w(f"- Config: candidate pool {F.CANDIDATE_K}, top-k {F.TOP_K}, weights {F.FUSION_WEIGHTS}, query max 2000 chars (min 3), token life 1440 min.")
    w("- Relevance display: `relevance = (rerank - min)/(max - min)` over the 15 candidates, so the **top record is always 1.00**; labels Strong >= 0.66, Moderate >= 0.33, Weak.")
    w("- Safety: 10 emergency regex rules, 6 caution keywords (`chest pain, breathing, bleeding, pregnant, infant, newborn`), permanent disclaimer, answer filter with 5 banned phrases (case-sensitive replace).")
    w("- Code size (non-blank lines): backend app 800 (24 files), legacy templates/static 159, React frontend 2,820 JS/JSX + 580 CSS, scripts 453, tests 60.\n")
    w("## 3. Endpoints\n")
    for row in [("GET", "/api/health", "no"), ("POST", "/api/auth/register", "no"), ("POST", "/api/auth/login", "no"), ("POST", "/api/auth/logout", "no"), ("GET", "/api/auth/me", "cookie"),
                ("POST", "/api/chat", "yes"), ("GET", "/api/history?search=", "yes"), ("GET", "/api/history/{id}", "yes"), ("DELETE", "/api/history/{id}", "yes"), ("GET", "/api/about/metrics", "no (reads results/metrics.json + KB size)")]:
        w(f"- `{row[0]} {row[1]}` - auth: {row[2]}")
    w("\nTables: `users(id, email unique, password_hash, created_at)`; `consultations(id, user_id FK, symptom_query, generated_response, top_condition, retrieved_evidence JSON text, retrieval_score, safety_flag, created_at)`; one user has many consultations (cascade delete).\n")
    k = F.KB
    w("## 4. Knowledge base and data\n")
    w(f"- {k['records']} records, {k['conditions']} conditions ({', '.join(f'{c} {n}' for c, n in k['records_per_condition'].items())}); severity: {k['severity']}; "
      f"{k['mean_symptoms_per_record']} symptoms per record (range {k['min_symptoms']}-{k['max_symptoms']}); symptom vocabulary {k['symptom_vocabulary']}; **{k['distinct_description_guidance_pairs']} distinct description/guidance pairs** (one per condition, shared by all of its records).")
    w("- Source: `scripts/prepare_data.py` builds records from a hand-written table of 30 conditions with 6 random symptom-subset variants each (seed 42, de-duplicated). `source_type = synthetic` ('CareLens AI curated local knowledge (synthetic fallback)'). **No public dataset, no clinical validation, no licence issue (written by the team).**")
    w("- The shipped `results/metrics.json` (served on the About page): n=30, Top-1 = Top-3 = F1 = MRR = 1.0, mean latency 245 ms. It evaluates held-out records that are **still in the index** with the query = the record's own symptom list, so it is an upper bound for wiring, not an accuracy claim (the About page says so).\n")
    w("## 5. Retrieval results (top-1 condition accuracy; Wilson 95% CI for the shipped configuration)\n")
    for s in F.SETS:
        w(f"### {SETN[s]}\n")
        w("| Configuration | Top-1 | Top-3 | Top-5 | MRR@5 | distinct conditions in top 5 |\n|---|---|---|---|---|---|")
        for c in F.CFG_ORDER:
            x = R[c][s]
            w(f"| {LAB[c]} | {x['top1']:.4f} | {x['top3']:.4f} | {x['top5']:.4f} | {x['mrr5']:.4f} | {x['mean_distinct_conditions_in_top5']} |")
        w(f"\nShipped configuration Top-1 95% CI: {F.ci('hybrid_rerank', s)}; misses: {R['hybrid_rerank'][s]['n_misses']}.\n")
    w("Per-query timing is not in these tables because embeddings are cached across query sets in the measurement script; use section 9 for latency.\n")
    w("Notes: 'Top-3' counts the first three retrieved *records*; because a condition has 4-6 near-identical records, the five evidence cards usually show one or two conditions "
      f"(mean distinct conditions in top 5: {R['hybrid_rerank']['S4_lay_language_60']['mean_distinct_conditions_in_top5']} on S4), so the 'possible conditions' list is not a differential diagnosis. "
      "S4 queries were written by the authors in everyday language (2 per condition); they are not clinician-validated. Leave-one-out removes only the held-out record; its sibling records remain.\n")
    w("Misses of the shipped configuration on S4: " + "; ".join(f"'{m['query']}' ({m['truth']} -> {m['predicted']})" for m in R['hybrid_rerank']['S4_lay_language_60']['misses']) + ".\n")
    rel = F.REL
    w("## 6. Displayed relevance versus what the model knows\n")
    w(f"- 60 in-KB lay queries and {rel['out_kb_n']} out-of-KB complaints (tooth ache, sprained ankle, back pain ...): the top record has displayed relevance 1.00 in **all** of them; all {rel['out_kb_n']} out-of-KB queries are shown as 'Strong match' (also via `pipeline.answer`: {rel['out_kb_labels_via_pipeline_answer']}).")
    w(f"- The raw cross-encoder score does separate them: in-KB mean {rel['raw_rerank_in_kb']['mean']} (min {rel['raw_rerank_in_kb']['min']}, max {rel['raw_rerank_in_kb']['max']}) vs out-of-KB mean {rel['raw_rerank_out_kb']['mean']} (min {rel['raw_rerank_out_kb']['min']}, max {rel['raw_rerank_out_kb']['max']}); "
      f"AUROC in-KB vs out-of-KB = {rel['auroc_in_vs_out_by_raw_rerank_score']} (raw rerank) and {rel['auroc_in_vs_out_by_raw_hybrid_score']} (raw hybrid). The information exists but the min-max normalisation hides it.\n")
    g = F.GEN
    w("## 7. Generation\n")
    w(f"- Installed transformers {g['transformers_version']}: task `text2text-generation` is **{g['text2text_task_in_installed_transformers']}** (removed from transformers 5), so `Generator` falls back to `text-generation`, which for T5 returns the prompt unchanged: "
      f"**{g['echo_answers']}/{g['n']} answers ({g['echo_rate']*100:.0f}%) are an echo of the prompt** (instruction + retrieved context), labelled `local-generator:google/flan-t5-small`. Mean generation time {g['mean_generate_ms']} ms.")
    w(f"- Evidence-based fallback (offline mode, `CARELENS_GENERATOR_MODEL` unavailable): deterministic text built from the retrieved records, {g['mean_fallback_ms']} ms; in {g['fallback_names_only_retrieved_conditions']}/{g['n']} answers every named condition is one of the retrieved records (by construction).")
    w("- Consequence: groundedness holds structurally (nothing is generated beyond the retrieved text) but answers are not synthesised, do not cite per statement, and there is no human or model groundedness judgement.\n")
    s = F.SAF
    w("## 8. Safety layer (author-written probes, not clinical validation)\n")
    w(f"- Emergency flag on {s['n_pos']} emergency descriptions: {s['true_emergency']} detected, recall {s['emergency_recall']} (Wilson {s['recall_ci']}); literal wording {s['by_group_pos']['literal']['detected']}/{s['by_group_pos']['literal']['n']}, "
      f"**paraphrased wording {s['by_group_pos']['paraphrase']['detected']}/{s['by_group_pos']['paraphrase']['n']}** (none flagged, not even as caution).")
    w(f"- On {s['n_neg']} non-emergency texts: 20 ordinary -> 0 false alarms; 10 hard negatives (negation or history) -> {len(s['by_group_neg']['hard']['false_emergency'])} false emergencies, {len(s['by_group_neg']['hard']['caution'])} caution flags (precision {s['emergency_precision']}).")
    f = s["filter"]
    w(f"- Answer filter: {f['removed']}/{f['n']} test sentences cleaned; for the 5 listed phrases {f['listed_removed']}/{f['n_listed_phrases']} cases (case-sensitive replace misses 'Take ibuprofen', 'Dosage:', 'Prescribe'); unlisted drugs (paracetamol, amoxicillin) pass through.\n")
    w("## 9. Latency (CPU only, i5-12500, 15.7 GB, warm models, 30 queries)\n")
    st = F.LAT["stages_ms"]
    w("| Stage | mean ms | median | p95 |\n|---|---|---|---|")
    for k2 in ("expand", "embed", "faiss", "bm25", "fuse", "rerank", "safety"):
        w(f"| {k2} | {st[k2]['mean']} | {st[k2]['median']} | {st[k2]['p95']} |")
    a, b = F.LAT["pipeline_answer_with_local_generator_ms"], F.LAT["pipeline_answer_fallback_only_ms"]
    w(f"\n- `pipeline.answer` in-process: with local generator mean {a['mean']} ms (p95 {a['p95']}); fallback only mean {b['mean']} ms (p95 {b['p95']}). The cross-encoder (15 query-record pairs, mean {st['rerank']['mean']} ms when timed alone) is the dominant stage; the stages were timed in separate passes, so they do not add up exactly to the totals.")
    for lab, d in (("fallback generator", F.LAT_FB), ("Flan-T5 generator", F.LAT_T5)):
        w(f"- `POST /api/chat` over HTTP on 127.0.0.1, {lab}: mean {d['chat_ms']['mean']} ms, median {d['chat_ms']['median']}, p95 {d['chat_ms']['p95']}, first request {d['chat_first_request_ms']} ms; login ~{d['login_ms']['mean']} ms (bcrypt); history list ~{d['history_list_ms']['mean']} ms; health ~{d['health_ms']['mean']} ms.")
    w("- Model load at first request ~62 s (cold start in the measurement script; embedding + reranker + generator).\n")
    w("## 10. Tests\n")
    w(f"- pytest: {F.PYTEST_PASSED}/{F.PYTEST_TOTAL} passed in {F.PYTEST_SECONDS} s (normalise/expand, safety emergency, safety filter, password hashing, fuse, generator fallback, auth + history isolation, API validation, retrieval round trip).")
    w(f"- `scripts/smoke_test.py` (end-to-end via the Vite proxy): {F.SMOKE_PASSED}/{F.SMOKE_TOTAL} checks passed.")
    sec = F._load(os.path.join(F.METRICS_DIR, "security.json"))
    if sec:
        w(f"- `scripts/measure_security.py` (in-process TestClient, scratch DB): {sec['passed']}/{sec['n']} black-box probes passed; failed: {', '.join(sec['failed'])} "
          "(no Secure cookie flag, no sign-in rate limit, default JWT signing key in use). Details in `docs/metrics/security.json`.")
    w("- Not done: load/concurrency test, browser accessibility audit, user study, clinical review, security penetration test.\n")
    w("## 11. Screenshot inventory (`docs/screenshots/`, 1440x900 unless noted, captured by `scripts/capture_docs_screens.py` on 2026-10-22 with the real running app)\n")
    for fn in sorted(os.listdir(F.SHOTS)):
        w(f"- `{fn}`")
    w("\nScreens 07, 08, 18, 19, 20 and the history/detail screens were captured with the evidence-based fallback generator (backend started with an unavailable generator model; the supported offline mode). "
      "`21_assistant_generator_echo.png` was captured with the default Flan-T5 generator and shows the prompt echo (defect). The About page shows the shipped 100% figures with the app's own synthetic-data caveat.\n")
    w("## 12. Objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx) versus outcome\n")
    w("1. Curated knowledge base indexed for retrieval - **achieved with a synthetic 176-record, 30-condition base** (FAISS flat index + BM25 index); not clinically curated.")
    w("2. NL symptoms with query expansion - **achieved**; expansion is a rule-based template (not an LLM HyDE) and measured effect is neutral-to-negative (no-HyDE variant scores as high or higher).")
    w("3. Hybrid retrieval with neural reranking - **achieved and measured** (hybrid + cross-encoder top-1 0.967 on S4, 0.881 on S3).")
    w("4. Grounded responses citing the retrieved source for every statement - **partly**: answers are built from retrieved records and each is shown with evidence cards (record id, symptoms, guidance), but there is no per-statement citation and the local generator path echoes its prompt.")
    w("5. Track reported symptoms over time to reveal progression and trends - **not achieved beyond storage**: consultations are saved, searchable, viewable and deletable; there is no trend, timeline or progression analysis.")
    w("6. Evaluate retrieval relevance, groundedness and response time - **retrieval and time measured; groundedness only checked structurally** (no judge).\n")
    w("## 13. Defects found while measuring (documented, not fixed)\n")
    w("1. Local generator returns its own prompt (transformers 5 removed `text2text-generation`).")
    w("2. Displayed relevance is relative: top record always 100%, out-of-KB complaints still 'Strong match'.")
    w("3. Safety rules miss paraphrased emergencies (0/12) and fire on negations/history (6/10 hard negatives); answer filter replace is case-sensitive.")
    w("4. Shipped `results/metrics.json` evaluates records that are in the index (100% is an upper bound).")
    w("5. Evidence cards show near-duplicate records of the same condition, not a differential.")
    w("6. Symptom-trend tracking is not implemented.")
    w("7. `tests/test_auth_and_history_isolation` writes users into the real `data/carelens.db` (the file is git-ignored).")
    out = os.path.join(F.DOCS, "REPORT_FACTS.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
