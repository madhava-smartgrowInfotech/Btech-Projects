# 06 · API reference

Base URL: `http://127.0.0.1:8204/api` (through the web app: `http://localhost:5204/api`).
Interactive documentation with every schema: **`/docs`** (OpenAPI JSON at `/openapi.json`).

**Authentication.** `POST /auth/login` returns a JWT. Send it as `Authorization: Bearer <token>`.
Endpoints marked 🔒 need a signed-in user, 🛡 need the `admin` role, 🌐 are public.

**Money** is in rupees (float) in the API and stored as integer paise. **Times** are ISO-8601 UTC.

**Errors** always look like:

```json
{ "detail": { "code": "payee_not_found", "message": "No sandbox wallet has this UPI ID." } }
```

`code` is stable (the web app translates it); validation errors use `validation_error` and add
`field` and `errors` (submitted values are never echoed back).

---

## Health

### 🌐 `GET /health`
```json
{ "status": "ok", "database": "ok",
  "models": { "behaviour": {"loaded": true, "version": "m1-xgb-20260922"},
              "sms": {"loaded": true, "version": "m2-tfidf-lr-20260922"},
              "risk": {"loaded": true, "version": "m3-xgb-20260922"} } }
```

## Auth

### 🌐 `POST /auth/register`
```json
{ "full_name": "Asha Rao", "phone": "9876500001", "email": "asha@example.com",
  "password": "at-least-8-chars", "pin": "4321", "language": "te" }
```
→ `201` with the same body as login. Errors: `account_exists` (409), `validation_error` (422).

### 🌐 `POST /auth/login`
```json
{ "identifier": "demo@upiguardian.app", "password": "Guardian@123" }
```
```json
{ "access_token": "eyJhbGciOi…", "token_type": "bearer",
  "user": { "id": 1, "full_name": "Meera Sharma", "phone": "9000000001", "email": "demo@upiguardian.app",
            "role": "user", "is_sample": true, "upi_id": "meera@upg", "balance": 85000.0,
            "language": "en", "created_at": "2024-04-05T12:06:51Z" } }
```
Error: `bad_credentials` (401).

### 🔒 `GET /auth/me` → the `user` object above.
### 🔒 `POST /auth/pin` — `{ "current_pin": "1234", "new_pin": "5678" }` → `204`. Error: `wrong_pin`.

## Wallet and payees (F1, F3)

### 🔒 `GET /wallet`
```json
{ "upi_id": "meera@upg", "display_name": "Meera Sharma", "balance": 85000.0, "is_sample": true,
  "qr_uri": "upi://pay?pa=meera%40upg&pn=Meera%20Sharma&cu=INR",
  "stats": { "spent_this_month": 9510.0, "received_this_month": 0.0, "payments_checked": 167,
             "payments_stopped": 0, "money_protected": 0.0, "on_hold": 0,
             "levels_30d": { "low": 22, "medium": 0, "high": 0 } },
  "daily_spend": [ { "date": "2026-09-10", "amount": 830.0 }, "…14 days" ] }
```

### 🔒 `GET /wallet/qr.png?amount=` — PNG QR code of the user's `upi://pay` link.

### 🔒 `GET /payees/lookup?upi_id=vikram.4411@upg`
```json
{ "upi_id": "vikram.4411@upg", "name": "Vikram Rao", "is_merchant": false, "category": null,
  "is_sample": true, "is_self": false, "times_paid": 0, "saved_as": null,
  "trust": { "score": 46, "band": "caution", "components": [ { "code": "account_age", "delta": -14 } ],
             "account_age_days": 12, "report_count": 0, "report_score": 0.0, "distinct_payers_24h": 0,
             "distinct_payers_7d": 2, "new_payer_share_7d": 1.0, "distinct_payers_90d": 2,
             "collect_targets_7d": 0, "is_merchant": false } }
```
Error: `payee_not_found` (404).

### 🔒 `GET /payees/recent` → `{ "saved": [ {…party, "nickname", "relation", "times_paid"} ], "recent": [ … ] }`
### 🔒 `POST /payees/save` — `{ "upi_id", "nickname", "relation" }` → `201`.

## Payments (F2, F5, F6, F7)

### 🔒 `POST /payments/assess` — score a payment **before** confirmation
```json
{ "upi_id": "vikram.4411@upg", "amount": 25000, "note": null,
  "channel": "send", "qr_payload": null, "device": "mobile", "lat": null, "lon": null }
```
Returns a **draft** payment with the full risk panel:
```json
{ "id": 359, "reference": "260922489068", "direction": "sent", "status": "draft", "channel": "send",
  "counterparty": { "upi_id": "vikram.4411@upg", "name": "Vikram Rao", "is_merchant": false, "is_sample": true },
  "amount": 25000.0, "level": "high", "score": 98,
  "assessment": {
    "score": 98, "level": "high", "final_level": "high", "action": "hold",
    "probability": 0.920166, "behaviour_score": 0.0043, "payee_trust": 46, "trust": { "…": "see lookup" },
    "reasons": [
      { "code": "NEW_ACCOUNT", "params": { "payee": "Vikram Rao", "days": 12 }, "feature": "payee_account_age_days",
        "contribution": 4.8208, "kind": "model",
        "text": { "en": "Vikram Rao's account is only 12 days old.",
                  "hi": "Vikram Rao का खाता सिर्फ़ 12 दिन पुराना है।",
                  "te": "Vikram Rao ఖాతా కేవలం 12 రోజుల పాతది." } },
      { "code": "AMOUNT_UNUSUAL", "params": { "ratio": "54" }, "contribution": 1.1291, "…": "…" }
    ],
    "reassurance": [],
    "contributions": [ { "feature": "payee_account_age_days", "value": 4.8208 }, "…top 12 SHAP values" ],
    "base_value": -5.4419, "features": { "behaviour_score": 0.0043, "is_new_payee": 1.0, "…": "25 features" },
    "guard": {}, "local_time": "01:30", "sandbox_clock": true, "model_version": "m1-xgb-20260922+m3-xgb-20260922" },
  "intent": null, "hold": null,
  "questions": [ { "id": "purpose", "type": "choice", "options": ["family_friend", "shopping", "bill", "refund", "prize", "kyc", "job", "loan", "investment", "other"] },
                 { "id": "asked_by_someone", "type": "yes_no" },
                 { "id": "verified_by_call", "type": "yes_no", "only_for_purpose": ["family_friend"] },
                 { "id": "advance_to_online_seller", "type": "yes_no", "only_for_purpose": ["shopping"] } ] }
```
`action`: `pay` (Low) · `verify` (Medium) · `hold` (High) · `block` (High and the receiver's
weighted reports ≥ the block threshold). Errors: `payee_not_found`, `self_payment`,
`amount_invalid`, `models_missing` (503).

### 🔒 `POST /payments/{id}/intent` — answer the safety check
```json
{ "purpose": "refund", "asked_by_someone": true, "verified_by_call": null, "advance_to_online_seller": null }
```
```json
{ "result": { "purpose": "refund", "signals": ["scam_purpose", "pressured_by_someone"],
              "scam_type": "refund_scam", "escalated": false, "final_level": "high", "recommend_cancel": true,
              "warning": { "scam_type": "refund_scam",
                           "name": { "en": "fake refund or cashback", "hi": "नकली रिफंड या कैशबैक", "te": "…" },
                           "advice": { "en": "You never need to pay, scan a QR code or enter your PIN to receive a refund.", "hi": "…", "te": "…" } } },
  "payment": { "…": "updated payment" } }
```

### 🔒 `POST /payments/{id}/confirm` — `{ "pin": "1234" }`
Low / Medium → `status: "completed"` (money moves). High → `status: "held"` and a `hold` object:
```json
{ "status": "held", "hold": { "id": 12, "status": "active", "hold_minutes": 30,
  "hold_until": "2026-09-22T12:37:58Z", "needs_approval": false, "approval_status": "none" } }
```
Errors: `intent_required` (409, Medium/High without an answer), `wrong_pin` (400, counted as a
failed attempt), `insufficient_funds` (400), `payment_blocked` (403), `payment_closed` (409).

### 🔒 `POST /payments/{id}/cancel`
Draft → `cancelled` (`status_reason: "cancelled_after_warning"` when it was risky). Held →
refunded, `cancelled_during_hold`.

### 🔒 `GET /payments?direction=all|sent|received&level=all|low|medium|high&status=&q=&limit=30&offset=0`
`{ "items": [ …payments without the assessment block… ], "has_more": true, "offset": 0 }`

### 🔒 `GET /payments/{id}` — one payment (payer sees the full assessment; the receiver sees only amount, status and payer).

## QR (F9)

### 🔒 `POST /qr/parse` — check a scanned code before paying
```json
{ "payload": "upi://pay?pa=cashback.offer@upg&pn=Cashback%20Offers&cu=INR&am=5000.00&tn=Scan%20to%20receive%20cashback" }
```
```json
{ "valid": true, "payee_upi_id": "cashback.offer@upg", "payee_name_in_qr": "Cashback Offers",
  "registered_name": "Cashback Offers", "amount": 5000.0, "note": "Scan to receive cashback",
  "note_analysis": { "score": 0.9525, "verdict": "scam", "promises_money": true, "highlights": [ "…" ] },
  "flags": ["scan_to_receive"], "qr_flag": 1.0, "is_self": false }
```
Flags: `scan_to_receive`, `name_mismatch`, `receive_words`, `qr_is_link`, `unknown_upi_id`, `not_upi`, `bad_amount`.

### 🌐 `GET /qr/image?payload=` — PNG for any UPI payload (sample codes).

## Collect requests (F9)

| Method | Path | Body / result |
|---|---|---|
| 🔒 POST | `/collect` | `{ "upi_id": "<who should pay>", "amount": 650, "note": "Dinner split" }` → `201`; the payer is notified |
| 🔒 GET | `/collect/incoming` | `{ "items": [ { "id", "direction": "incoming", "counterparty", "amount", "note", "status", "guard": { "is_debit": true, "flags": ["collect_is_debit", "deceptive_note"], "note": {…}, "requester_trust": {…} }, "expires_at", "created_at" } ] }` |
| 🔒 GET | `/collect/outgoing` | requests you sent |
| 🔒 POST | `/collect/{id}/assess` | starts a risk-checked payment with `channel: "collect"` → payment (continue with `/payments/{id}/intent` and `/confirm`) |
| 🔒 POST | `/collect/{id}/decline` | → request with `status: "declined"` |

## Delayed Protection and approvals (F6)

| Method | Path | Result |
|---|---|---|
| 🔒 GET | `/holds` | your held payments (as payment objects) |
| 🔒 POST | `/holds/{hold_id}/cancel` | refund and close the hold |
| 🔒 GET | `/approvals` | holds waiting for **you** as a trusted contact: `{ hold_id, status, approval_status, hold_until, amount, requested_by, payee, assessment, intent }` |
| 🔒 POST | `/approvals/{hold_id}/approve` | sends the money now |
| 🔒 POST | `/approvals/{hold_id}/reject` | refunds the payer |

## Trusted contacts

| Method | Path | Body / result |
|---|---|---|
| 🔒 GET | `/trusted-contacts` | `{ "trusted": [ { id, name, upi_id, phone_last4, relation, can_approve } ], "protecting": [ … ] }` |
| 🔒 POST | `/trusted-contacts` | `{ "identifier": "arjun@upg" or "9000000002", "relation": "son", "can_approve": true }` → `201` |
| 🔒 DELETE | `/trusted-contacts/{id}` | `204` |

## Trust and reports (F3)

| Method | Path | Body / result |
|---|---|---|
| 🔒 GET | `/trust/{upi_id}` | party + `trust` object + `reported_by_you` |
| 🔒 POST | `/reports` | `{ "upi_id": "kyc.helpdesk@upg", "category": "kyc_fraud", "note": "…", "source": "manual" }` → `201` |

## SMS check (F4)

### 🔒 `POST /sms/check` — `{ "text": "Your KYC expires today, click link http://kyc-verify-now.top/a77 …" }`
```json
{ "id": 20, "language": "en", "script": "latin", "verdict": "scam", "probability": 0.9994,
  "model_probability": 0.9963, "rules_score": 0.8421, "scam_type": "kyc_fraud",
  "scam_type_name": { "en": "fake KYC / account block", "hi": "नकली KYC / खाता बंद", "te": "నకిలీ KYC / ఖాతా బ్లాక్" },
  "advice": { "en": "Banks never ask you to update KYC through a link or by paying anyone. …", "hi": "…", "te": "…" },
  "highlights": [ { "start": 5, "end": 16, "text": "KYC expires", "sources": ["model", "rule"], "rules": ["kyc_expiry"] }, "…" ],
  "signals": [ { "rule": "kyc_expiry", "weight": 0.5, "category": "kyc_fraud" }, "…" ],
  "model_terms": [ { "term": "kyc", "weight": 0.4284 }, "…" ],
  "entities": { "upi_ids": [], "urls": ["http://kyc-verify-now.top/a77"], "phones": [], "amounts": [] },
  "linked_accounts": [], "thresholds": { "scam": 0.5, "suspicious": 0.3531 }, "created_at": "…" }
```
### 🔒 `GET /sms/history?limit=20` → `{ "items": [ …same shape… ] }`
### 🔒 `POST /sms/{id}/report` → `{ "reported": ["luckydraw.winner@upg"] }` (reports every UPI ID in the message)

## Voice (F8)

All voice endpoints return `{ "url": "/api/voice/audio/<hash>.mp3", "text": "…", "lang": "hi", "cached": false }`.
Errors: `voice_offline` / `voice_disabled` (503) — the web app then uses the browser's own voice.

| Method | Path | Speaks |
|---|---|---|
| 🔒 POST | `/voice/payment/{id}` `{ "lang": "hi" }` | personalised payment warning (name, amount, payee, top reasons, scam advice, hold time) |
| 🔒 POST | `/voice/sms/{id}` `{ "lang": "te" }` | SMS verdict with scam type and advice |
| 🔒 POST | `/voice/collect/{id}` `{ "lang": "en" }` | "Approving this request will take ₹… out of your account" |
| 🔒 POST | `/voice/qr-trick` `{ "lang": "hi" }` | QR "scan to receive" warning |
| 🔒 GET | `/voice/guide/{screen}?lang=` | screen guide (`home, send, scan, collect, sms, history, trusted, settings, hold, intent`) |
| 🔒 POST | `/voice/speak` `{ "text": "…", "lang": "en" }` | any short text (≤ 900 chars) |
| 🌐 GET | `/voice/audio/{hash}.mp3` | the MP3 (cached) |

## Settings and notifications

| Method | Path | Body / result |
|---|---|---|
| 🔒 GET | `/settings` | `{ "language": "en", "voice_enabled": true, "auto_speak": true, "hold_minutes": 30, "hold_choices": [1,2,5,10,15,30,60,120], "trusted_approval_required": false, "has_trusted_approver": true, "sandbox_clock": null }` |
| 🔒 PUT | `/settings` | any subset, e.g. `{ "hold_minutes": 5, "sandbox_clock": "01:30" }` (`""` = real clock) |
| 🔒 GET | `/notifications?limit=30` | `{ "unread": 2, "items": [ { id, kind, payload, read, created_at } ] }` |
| 🔒 POST | `/notifications/read` | `{ "ids": [1, 2] }` or `{}` for all → `204` |
| 🔒 GET | `/notifications/summary` | `{ "collect": 2, "approvals": 0, "unread": 1 }` (navigation badges) |
| 🔒 WS | `/ws?token=<jwt>` | sends `{"type":"hello"}`, then `{"type":"notification","kind":"hold_started","payload":{…}}` events; answers `ping` with `pong` |

Notification kinds: `hold_started, hold_released, hold_cancelled, hold_expired, hold_approved,
hold_rejected, approval_requested, approval_closed, collect_received, payment_received`.

## Fraud analytics (F10) — 🛡 admin only

| Method | Path | Result |
|---|---|---|
| GET | `/admin/overview?days=30` | `{ "payments_scored": 110, "levels": {"low": 96, "medium": 3, "high": 11}, "held_now": 0, "holds_total": 7, "holds_released": 2, "payments_stopped": 9, "blocked": 1, "money_protected": 58494.0, "average_score": 13.8, "intent_checks": 14, "intent_escalations": 1, "sms_checks": 20, "sms_scams": 17, "reports": 10, "users": 26 }` (`intent_escalations` = answers matching a scam) |
| GET | `/admin/trends?days=30` | `{ "items": [ { "date", "scored", "medium", "high", "stopped", "held", "sms_scams" } ] }` |
| GET | `/admin/scam-types?days=30` | `{ "items": [ { "scam_type", "sms", "intent", "reports", "total" } ] }` |
| GET | `/admin/risk-distribution?days=30` | `{ "histogram": [ { "bucket": "0-9", "count" } ], "by_hour": [ { "hour", "payments", "high" } ] }` |
| GET | `/admin/flagged?limit=20` | recent Medium/High payments with outcome and top reasons |
| GET | `/admin/reports` | most-reported UPI IDs with category and trust score |
| GET | `/admin/policy` | `{ "medium": 35, "high": 70, "block_report_score": 2.5, "defaults": { … } }` |
| PUT | `/admin/policy` | `{ "medium": 35, "high": 70, "block_report_score": 2.5 }` (`high` must be > `medium`) |

## Models and public data

| Method | Path | Result |
|---|---|---|
| 🔒 GET | `/models` | latest `metrics.json` of each model family + `plot_urls`, load status, policy |
| 🌐 GET | `/models/{run}/plots/{file}.png` | a training plot |
| 🌐 GET | `/public/highlights` | `{ "languages": 3, "risk": { "pr_auc": 0.8944, "scams_checked": 0.9405, "genuine_straight_through": 0.9872, … }, "sms": { "f1": 0.9649, … }, "behaviour": { "roc_auc": 0.8439, … } }` |
| 🌐 GET | `/public/guide/{screen}.mp3?lang=` | a pre-recorded guide (landing page voice sample) |

## Sandbox tools

| Method | Path | Result |
|---|---|---|
| 🔒 GET | `/sandbox/samples` | sample SMS (3 languages, scam + genuine) and sample QR codes with image URLs |
| 🔒 POST | `/sandbox/incoming-collect` | `{ "kind": "refund_trick" | "genuine" }` — a sample account sends you a request |
| 🛡 POST | `/sandbox/reset` | deletes all data and reloads the sample data |
