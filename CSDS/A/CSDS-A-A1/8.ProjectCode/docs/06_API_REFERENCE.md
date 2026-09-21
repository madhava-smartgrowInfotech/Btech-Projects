# API reference

Base URL: `http://localhost:8101/api`. Interactive documentation (Swagger UI) with every schema: **http://localhost:8101/docs**.

- **Authentication:** `Authorization: Bearer <access_token>` on every endpoint except health, register, login and evaluation.
- **Errors:** always JSON `{"detail": "readable message", "code": "machine_code"}`; validation errors (422) add `errors[]`.
- **Common codes:** `unauthorized` / `token_invalid` (401), `not_found` (404), `email_taken` / `duplicate_policy` (409), `busy` (409, policy still processing), `ai_quota` (429, Gemini free-tier limit), `ai_unavailable` (503, Gemini busy), `ai_not_configured` (503, no key).

---

## Health

### `GET /health`
```json
{
  "status": "ok", "version": "1.0.0", "database": "ok",
  "vector_store": {"status": "ok", "collection": "clauses_minilm", "vectors": 801},
  "local_models": {"embedder": {"model": "sentence-transformers/all-MiniLM-L6-v2", "downloaded": true, "loaded": true, "load_ms": 6884}, "...": {}},
  "ingestion": {"running": true, "queued": 0, "current": null},
  "gemini": {"configured": true, "model": "gemini-3.8-flash", "fallback_models": ["gemini-3.6-flash", "gemini-3.5-flash-lite"],
             "availability": {"gemini-3.8-flash": "cooling down", "gemini-3.6-flash": "available", "gemini-3.5-flash-lite": "available"}},
  "embedding_provider": "local", "languages": ["en", "hi", "te"]
}
```

---

## Auth and account

### `POST /auth/register`
```json
{"full_name": "Priya Sharma", "email": "priya@example.com", "password": "Secret123"}
```
`201` ->
```json
{"access_token": "eyJ...", "token_type": "bearer", "expires_at": "2026-09-22T23:30:00Z",
 "user": {"id": 5, "email": "priya@example.com", "full_name": "Priya Sharma", "language": "en", "theme": "system", "created_at": "..."}}
```
Password: at least 8 characters with a letter and a number. `409 email_taken` if the email exists.

### `POST /auth/login`
`{"email": "demo@policylens.app", "password": "Demo@12345"}` -> same shape as register. `401 bad_credentials`.

### `GET /auth/me` -> the user object.

### `PATCH /users/me`
`{"language": "hi"}` or `{"full_name": "..."}` or `{"theme": "dark"}` -> updated user. Languages: `en`, `hi`, `te`.

### `POST /users/me/password`
`{"current_password": "...", "new_password": "..."}` -> `204`.

### `GET /users/languages` -> `[{"code": "en", "name": "English"}, {"code": "hi", "name": "Hindi"}, {"code": "te", "name": "Telugu"}]`

---

## Policies

### `GET /policies`
```json
[{
  "id": 4, "display_name": "Family Health Optima (Star Health)", "is_sample": true, "created_at": "...",
  "document": {"id": 4, "file_name": "star-health-family-health-optima.pdf", "size_bytes": 1272345, "page_count": 44,
               "insurer": "Star Health and Allied Insurance Company Limited", "product_name": "Family Health Optima Insurance Plan",
               "uin": "SHAHLIP26046V092526", "status": "ready", "status_detail": null, "progress": 100,
               "error": null, "extraction_error": null, "is_sample": true, "processed_at": "..."},
  "has_card": true, "clause_count": 219, "risk_counts": {"high": 4, "medium": 7},
  "highlights": {"sum_insured": "Rs. 1,00,000 to Rs. 25,00,000", "pre_existing_wait": "36 months", "specific_wait": "24 months"}
}]
```

### `POST /policies` (multipart/form-data)
Fields: `file` (PDF, up to `MAX_UPLOAD_MB`), optional `display_name`. `201` -> policy (status `queued`, or `ready` if the same PDF was processed before). Errors: `not_pdf`, `too_large` (413), `encrypted`, `bad_pdf`, `duplicate_policy` (409).

Processing statuses: `queued -> parsing -> indexing -> extracting -> ready` or `failed`.

### `POST /policies/samples` -> adds the sample policies to your library (`400 samples_present` if all are there).
### `GET /policies/{id}` -> policy. `PATCH /policies/{id}` `{"display_name": "..."}`. `DELETE /policies/{id}` -> `204`.
### `GET /policies/{id}/status`
```json
{"id": 9, "status": "extracting", "status_detail": "Building the Policy Card and risk highlights with AI", "progress": 65,
 "error": null, "extraction_error": null, "has_card": false}
```

### `GET /policies/{id}/file` -> the original PDF (`application/pdf`, inline).
### `GET /policies/{id}/pages` -> `[{"number": 1, "width": 595.0, "height": 842.0}, ...]` (PDF points).
### `GET /policies/{id}/pages/{n}?scale=1.5` -> PNG of page *n* (scale 0.5-3.0, cached).

### `GET /policies/{id}/clauses?page=28`
```json
[{"id": 1140, "ordinal": 141, "clause_ref": "Excl02", "heading": "Specified disease / procedure waiting period",
  "section_path": "III EXCLUSIONS > STANDARD EXCLUSIONS", "text": "2. Specified disease / procedure waiting period - Code Excl 02 a. Expenses ...",
  "page_start": 28, "page_end": 29, "bboxes": [{"page": 28, "x0": 307.1, "y0": 560.2, "x1": 553.0, "y1": 790.5}],
  "label": "Clause Excl02 - Specified disease / procedure waiting period"}]
```
### `GET /policies/{id}/clauses/{ordinal}` -> one clause.

### `GET /policies/{id}/card?lang=en|hi|te`
```json
{
  "policy_id": 4, "document_id": 4, "language": "en", "model": "gemini-3.5-flash-lite", "prompt_version": "card-v4",
  "created_at": "...", "verified_ratio": 1.0, "translated": false,
  "data": {
    "insurer": "Star Health and Allied Insurance Company Limited", "product_name": "Family Health Optima Insurance Plan",
    "uin": "SHAHLIP26046V092526", "policy_type": "Family floater",
    "sum_insured": {"value": "Rs. 1,00,000 to Rs. 25,00,000", "number": 100000, "unit": "INR", "found": true,
                    "quote": "...", "clause_ordinal": 70, "clause_ref": null, "clause_label": "C70", "page": 10, "verified": true},
    "waiting_periods": {"initial": {"value": "30 days", "...": "..."}, "pre_existing": {"value": "36 months", "...": "..."},
                        "specific_diseases": {"value": "24 months", "...": "..."}, "maternity": {"...": "..."}},
    "specific_disease_examples": ["Cataract", "Joint Replacement / Arthroplasty", "..."],
    "sub_limits": [{"name": "Cataract", "value": "...", "page": 10, "...": "..."}],
    "key_exclusions": [], "co_payment_conditions": [], "claim_timelines": {}, "...": "..."
  },
  "summary": {"overview": "...", "best_for": ["..."], "watch_outs": ["..."], "next_actions": ["..."]},
  "labels": {"fields": {"sum_insured": "Sum insured", "...": "..."}, "waiting_periods": {}, "claim_timelines": {}}
}
```
Non-English requests translate the text values (cached); quotes stay in English. `409 card_pending` while processing, `404 card_missing` with the reason if extraction failed.

### `POST /policies/{id}/extract` -> starts a fresh Gemini extraction (bypasses the cache); returns the status object.

### `GET /policies/{id}/risks?lang=en`
```json
[{"id": 31, "title": "Pre-existing diseases covered only after 3 years", "category": "waiting_period", "severity": "high",
  "explanation": "Any illness you had before buying the policy is not covered until ...", "clause_ordinal": 140,
  "clause_label": "Clause Excl01 - ...", "page": 28, "quote": "Expenses related to ...", "source": "rule"}]
```

### `POST /policies/{id}/search`
`{"query": "cataract waiting period", "mode": "hybrid_rerank", "k": 8}` - modes `bm25`, `dense`, `hybrid`, `hybrid_rerank`.
```json
{"query": "...", "mode": "hybrid_rerank", "timings_ms": {"bm25": 28, "dense": 115, "fusion": 0, "rerank": 737},
 "items": [{"score": 0.32, "bm25": 21.4, "bm25_rank": 1, "dense": 0.61, "dense_rank": 2, "rrf": 0.0325, "rerank": 0.32,
            "clause": {"ordinal": 141, "clause_ref": "Excl02", "label": "...", "page_start": 28, "text": "...", "bboxes": []}}]}
```

---

## Chat

### `POST /conversations` `{"policy_id": 4}` -> `201` conversation.
### `GET /conversations?policy_id=4` -> list. `GET /conversations/{id}` -> conversation with `messages[]`. `DELETE /conversations/{id}` -> `204`.

### `POST /conversations/{id}/messages`
Request: `{"question": "Is cataract surgery covered and after how long?", "language": "en"}` (language optional - defaults to the user's setting).

Response:
```json
{
  "question": {"id": 71, "role": "user", "content": "Is cataract surgery covered and after how long?", "...": "..."},
  "answer": {
    "id": 72, "role": "assistant", "status": "answered", "language": "en", "model": "gemini-3.5-flash-lite",
    "content": "Yes, cataract surgery is covered ... waiting period of 24 months ... [C141] ...",
    "content_en": "...",
    "citations": [{"ordinal": 141, "tag": "C141", "clause_ref": "Excl02", "label": "Clause Excl02 - ...", "page": 28,
                   "page_end": 29, "quote": "...", "bboxes": [{"page": 28, "x0": 307.1, "y0": 560.2, "x1": 553.0, "y1": 790.5}]}],
    "faithfulness": 96.9,
    "faithfulness_detail": {"score": 96.9, "label": "well_supported",
                            "claims": [{"text": "...", "clauses": [141], "support": 0.97, "numbers_ok": true, "note": null}]},
    "retrieval": {"query": "...", "items": [{"ordinal": 141, "bm25_rank": 1, "dense_rank": 2, "rerank": 0.32}],
                  "follow_ups": ["..."]},
    "timings": {"translate_ms": 0, "retrieval_ms": 1059, "generation_ms": 2100, "faithfulness_ms": 1782, "total_ms": 4941},
    "total_ms": 4941
  },
  "follow_ups": ["What is the specific limit for cataract surgery?"]
}
```
`status` is `answered`, `partial` or `not_in_policy`. Citation tags `[C141]` in `content` refer to `citations[].ordinal`.

---

## Claim Copilot

### `POST /claims`
```json
{"policy_id": 4, "treatment": "Knee replacement", "hospitalization_type": "planned", "claim_mode": "cashless",
 "policy_start_date": "2023-09-01", "insured_age": 64, "pre_existing": "no", "estimated_cost": 350000,
 "room_type": "not_sure", "notes": null, "language": "en"}
```
Only `policy_id` and `treatment` are required. `201` ->
```json
{"id": 12, "policy_id": 4, "policy_name": "...", "treatment": "Knee replacement", "verdict": "partly_covered",
 "result": {
   "verdict": "partly_covered", "verdict_summary": "...", "verdict_summary_en": "...",
   "reasons": [{"text": "...", "text_en": "...", "policy_fact_en": "...", "clauses": [{"ordinal": 141, "label": "...", "page": 28}]}],
   "prechecks": [{"check": "Specific disease/procedure waiting period", "status": "pass", "detail": "...", "source": "rule",
                  "clause_ordinal": 141, "page": 28}],
   "documents": [{"id": "d0", "item": "Pre-authorisation form", "why": "...", "clauses": []}],
   "steps": [{"title": "Contact the helpline", "detail": "...", "timeline": "Before admission", "clauses": []}],
   "cost_notes": ["..."],
   "estimate": {"estimated_cost": 350000, "deductible": 0, "co_payment_percent": 20, "co_payment_amount": 70000,
                "insurer_pays": 280000, "you_pay": 70000, "notes": ["..."]},
   "matched_specific_disease": "Joint Replacement / Arthroplasty",
   "citations": [], "faithfulness": {"score": 87.1, "label": "well_supported", "claims": []},
   "timings": {"retrieval_ms": 6100, "generation_ms": 4800, "faithfulness_ms": 900, "total_ms": 11800}, "model": "..."},
 "checklist_state": {}, "language": "en", "faithfulness": 87.1, "total_ms": 11800, "created_at": "..."}
```
Verdicts: `covered`, `partly_covered`, `not_covered`, `needs_info`. Pre-check statuses: `pass`, `fail`, `warning`, `unknown`.

### `GET /claims`, `GET /claims/{id}`, `DELETE /claims/{id}`
### `PATCH /claims/{id}/checklist` `{"item_id": "d0", "done": true}` -> the updated claim check.

---

## Compare

### `POST /comparisons` `{"policy_a_id": 4, "policy_b_id": 5, "language": "en"}`
```json
{"id": 3, "policy_a_name": "...", "policy_b_name": "...", "language": "en", "model": "...", "total_ms": 3300,
 "result": {
   "rows": [{"key": "co_payment", "label": "Co-payment", "better": "b",
             "a": {"value": "20% ... age 61 and above", "found": true, "clause_ordinal": 111, "page": 21, "verified": true},
             "b": {"value": "Not specified in this policy", "found": false}}],
   "risk_counts": {"a": {"high": 4, "medium": 7}, "b": {"high": 1, "medium": 3}},
   "overall": "...", "choose_a_if": ["..."], "choose_b_if": ["..."],
   "trade_offs": [{"topic": "Room rent", "policy_a": "...", "policy_b": "...", "better": "B", "why": "...",
                   "tags": [{"policy": "a", "ordinal": 70}, {"policy": "b", "ordinal": 80}]}],
   "next_actions": ["..."]}}
```
### `GET /comparisons`, `GET /comparisons/{id}`, `DELETE /comparisons/{id}`

---

## Dashboard

### `GET /dashboard/summary`
`kpis` (policies, ready_policies, questions, avg_faithfulness, median_response_ms, claim_checks, comparisons, high_risks, ai_calls, ai_tokens), `activity_by_day[14]`, `faithfulness_bins`, `verdicts`, `risks_by_policy`, `response_times`, `recent`.

---

## Model performance (no login needed)

### `GET /evaluation/latest` -> `{"run": "eval-20260921-2354", "metrics": {...metrics.json...}, "plots": ["retrieval_ablation.png", "..."]}` (`404 no_evaluation` before the first run)
### `GET /evaluation/runs` -> `[{"run": "...", "updated_at": "...", "headline": {...}}]`
### `GET /evaluation/runs/{run}` -> one run.
### `GET /evaluation/runs/{run}/plots/{file}.png` -> the plot image.
