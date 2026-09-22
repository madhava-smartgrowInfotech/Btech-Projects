# 09 · Testing

## 1. Backend tests (pytest)

```bat
cd backend
..\venv\Scripts\python -m pytest
```

The suite starts the real FastAPI app in-process against a **throwaway SQLite database** loaded
with the sample data, uses the **real trained models**, and replaces speech synthesis with a fake
so no internet is needed. Result on the reference PC: **20 passed in ≈ 14 s**.

| File | What it checks |
|---|---|
| `tests/test_demo_scenarios.py` | The four product demo scenarios end to end through the API (below) |
| `tests/test_protection.py` | Hold released after the cooling-off time · trusted contact stops a held payment (refunded) · hold without approval expires and refunds · wrong PIN rejected · reported scam account blocked · QR guard (scan-to-receive, name mismatch, genuine, website link) · register / login / auth errors and no password echo · analytics require admin, policy validation · model metrics and plots served |
| `tests/test_ml_units.py` | Shared feature builders (M1 and M3), trust score components, monotonic 0–100 score mapping, OTP negation rule, language detection (native + romanised), entity extraction, SMS verdicts in English / Hindi / Telugu |

## 2. Frontend checks

```bat
cd frontend
npm run build        :: TypeScript type-check (tsc -b) + production build + PWA service worker
```

The type-check also guarantees that the Hindi and Telugu dictionaries contain **every** English
key (756 keys each).

## 3. Model evaluation

Each training script evaluates on held-out, time-based test data and writes `metrics.json` and
plots (see [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md)). To re-run everything:
`venv\Scripts\python ml\train_all.py`.

## 4. Demo scenario (manual walkthrough)

Start with `run.bat` (or `run_phone.bat` on a phone), sign in as **Meera**
(`demo@upiguardian.app` / `Guardian@123`, PIN `1234`).

| # | Steps | Expected result | Automated in |
|---|---|---|---|
| 1 | Install the PWA on the phone (Chrome ⋮ → *Install app*). **Send money** → **Ravi (friend)** → ₹800 → *Check and pay* → *Pay ₹800* → PIN | **Low risk**, reasons *paid Ravi Kumar 18 times before / saved contact / normal amount*, *Payment sent* immediately | `test_1_known_contact_normal_amount_is_low_and_paid_instantly` |
| 2 | **SMS check** → paste *"Your KYC expires today, click link http://kyc-verify-now.top/a77 to update or your account will be blocked."* → *Check message* → language **हिन्दी** → **सुनें** | **Scam** (fake KYC / account block, ≈ 100 %), highlighted *KYC expires, today, link, update, account will be blocked*, Hindi advice spoken | `test_2_kyc_sms_is_a_scam_with_highlights_and_hindi_voice` |
| 3 | **Settings → Sandbox clock** `01:30`. **Send money** → `vikram.4411@upg`, ₹25,000 → *Check and pay* → open *How the model decided* → *Continue to safety check* → *Family or a friend*, *Yes*, *No* → PIN → *Cancel this payment* | **High risk** (score ≈ 98): *account only 12 days old, 54× usual amount, 01:30 late night*; SHAP bars; impersonation warning; payment **held** with a 30-minute countdown; cancelled, money back | `test_3_large_new_payee_at_night_is_high_needs_intent_is_held_and_cancelled` |
| 4 | **Requests** → *Refund Desk* "Refund for order #48213 – approve to receive Rs 4,999" → *Review and pay* | Banner **Approving will DEBIT ₹4,999**, deceptive words highlighted, first reason *This is a request to PAY ₹4,999, not to receive money*, High risk; answering *refund* shows the collect-request scam warning | `test_4_collect_request_disguised_as_refund_warns_it_is_a_debit` |

## 5. End-to-end verification performed

| Check | Result |
|---|---|
| `setup.bat` on a clean export of the repository (new venv, `npm install`, `.env` created) | Completed in 2.1 minutes, exit code 0 |
| `run.bat` from that clean copy | API on 8204 with all three models loaded, web app on 5204 |
| The four demo scenarios through the **real UI** on a 390 px phone viewport (Playwright, Microsoft Edge) | All four passed, no page errors; Hindi warning generated and played (MP3) |
| `stop.bat` | Stopped only the processes on 8204 / 5204 and the phone tunnel |
| `run_phone.bat` pieces (production build, `vite preview`, Cloudflare quick tunnel) | App, API, PWA manifest, service worker and `/docs` returned 200 over `https://…trycloudflare.com`; the live WebSocket answered `hello` / `pong` through the tunnel |
| Screens at 1366 px and 390 px, light and dark, English / Hindi / Telugu | Checked visually |
