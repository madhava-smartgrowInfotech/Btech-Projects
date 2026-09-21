# Testing

PolicyLens is checked at four levels: automated backend tests, a production build of the web app, a measured evaluation of the AI pipeline, and a scripted end-to-end walk-through of the demo scenario in a real browser.

---

## 1. Backend tests (pytest)

```bat
cd backend
..\venv\Scripts\python -m pytest
```

The tests use an isolated temporary data folder, a synthetic two-page policy generated deterministically by `tests/fixtures.py`, and the real local models. Gemini is never called: where an AI step is needed, a stand-in returns a schema-valid response so the rest of the pipeline (retrieval, citation filtering, faithfulness scoring, persistence) runs for real.

| File | What it checks |
|---|---|
| `test_auth.py` | Health endpoint; register, duplicate email, case-insensitive login, bad credentials, missing/invalid token; password rules; language and password changes; demo account seeded |
| `test_parser.py` | Header removal, clause references (`2.1`, `3.1`, `Excl01`, `Excl02`), pages, highlight boxes, heading path, UIN detection; list items whose exclusion code opens, closes or wraps onto the next line become their own clause, a code mentioned in prose does not; scanned PDFs rejected |
| `test_units.py` | Reciprocal Rank Fusion; tokeniser and synonym expansion; fuzzy quote matching; risk rules and de-duplication of AI findings; waiting-period checks, co-payment and cost estimate with a sub-limit |
| `test_faithfulness.py` | Supported claims score high; wrong numbers and uncited claims score low; no claims -> not scored |
| `test_policy_flow.py` | Upload validation; full processing of an uploaded PDF; clause list; hybrid search in all four modes returns the cataract clause first; page image and original PDF; owner-only access; chat answer with citation filtering (a citation to a clause that was not retrieved is removed) and faithfulness; abstention; Claim Copilot with checklist ticks; dashboard; delete |

**Result:** `25 passed` (about 15 seconds).

## 2. Web app build

```bat
cd frontend
npm run build
```

Runs the TypeScript compiler (`tsc -b`, strict mode) and the Vite production build. **Result:** no type errors; build succeeds (about 4 seconds).

## 3. Evaluation of the AI pipeline

```bat
venv\Scripts\python ml\run_all.py
```

Measures retrieval, answers, citations, faithfulness, abstention, latency, Claim Copilot verdicts and Policy Card extraction on the evaluation set in `data/eval/`. Results and method: [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md); they are also shown on the **Model performance** page.

**Result (run `eval-20260922-0027`):** retrieval hit@5 100%, answer accuracy 100% (51/51), citation accuracy 100%, mean faithfulness 87.0, abstention 6/6 with no false abstentions, Hindi/Telugu 5/5, Claim Copilot verdicts 14/14, Policy Card values 51/52, median answer time 4.3 s.

## 4. Demo scenario (end-to-end)

Run from a fresh `run.bat`, in the browser at http://localhost:5101:

| # | Step | Expected | Verified |
|---|---|---|---|
| 1 | Register a new account, sign in, **Upload policy** -> choose a policy wording PDF | Processing steps appear; the tile turns **Ready**; the **Policy Card** shows sum insured, waiting periods and key exclusions, each with a **Clause · page** chip that opens the highlighted page | Yes |
| 2 | **Ask this policy** -> "Is cataract surgery covered and after how long?" | Answer: covered after the **24-month** specified-disease waiting period, subject to a per-eye limit; citations to the waiting-period clause (Excl02, p. 28) and the cataract limit (p. 10); **Faithfulness** badge | Yes |
| 3 | **Claim Copilot** -> same policy -> "Knee replacement", start date 3 years ago, age 64, bill ₹3,50,000 | **Partly covered** - waiting periods complete, 20% age-based co-payment; estimate ₹2,80,000 insurer / ₹70,000 you; document checklist; claim steps | Yes |
| 4 | Upload (or add) a second policy -> **Compare plans** | Side-by-side table with "better" ticks, trade-offs, choose A/B if | Yes |
| 5 | **Settings -> हिन्दी** (or the chat language menu) -> ask "Is there a co-payment in this policy?" | Answer in Hindi with citations; **Show in English** available; Policy Card viewable in Hindi | Yes |

The same scenario was also run against the API (`POST /api/policies`, `/conversations/{id}/messages`, `/claims`, `/comparisons`) with the live Gemini API, and every screen was captured in Microsoft Edge at 1440 px (light and dark) and 360-375 px (mobile) with an automated browser; no page scrolls horizontally on a 360 px screen and no console errors were reported.

## 5. Manual checklist

- [ ] `setup.bat` completes on a machine with Python 3.11 and Node LTS.
- [ ] `run.bat` refuses to start if port 8101 or 5101 is busy, otherwise opens the app.
- [ ] Demo login works; the four sample policies are **Ready** with Policy Cards.
- [ ] Uploading a scanned PDF shows "no readable text layer".
- [ ] Removing a policy asks for confirmation.
- [ ] With the Gemini key removed from `.env`, upload/search/viewer still work and the Policy Card explains how to add a key.
- [ ] Reduced motion (Windows: Settings -> Accessibility -> Visual effects -> Animation effects off) stops the landing animations.
