# Frontend Plan - Adaptive Learning Intelligence Platform (Kit V1 - Aurora Glass)

Existing app: **Flask + Jinja templates + Bootstrap**, cookie sessions, SQLite (`instance/app.db`). It has **no JSON API**
except `GET /api/performance`. The Flask app stays untouched. A thin **FastAPI layer in `backend/`** will import the
existing `db`, `config` and `utils/*` functions and expose them as JSON on port **8301**. The new React app in
`frontend/` runs on **5301**.

## 1. Existing endpoints (Flask, `app.py`)

| Method | Path | Request | Response (today) |
|---|---|---|---|
| GET | `/` | - | landing HTML (redirects to dashboard if logged in) |
| GET/POST | `/register` | form: `username`, `password`, `interests?` | HTML; errors: empty fields, "Username already taken" |
| GET/POST | `/login` | form: `username`, `password` | sets session `user_id`/`username`; "Invalid username or password." |
| GET | `/logout` | - | clears session |
| GET | `/dashboard` | - | HTML: `doc_count`, `query_count`, `quiz_attempts`, `performance[{subject, accuracy}]`, 5 recent documents |
| GET | `/api/performance` | - | JSON `{labels[], data[]}` (subject accuracy %) |
| GET/POST | `/upload` | multipart: `document` (pdf/docx/txt, 16 MB), `subject?` | extracts text, topics, chunks; stores; rebuilds RAG index |
| GET | `/documents` | - | HTML: documents `{id, filename, subject, topics[], uploaded_at}` |
| POST | `/documents/<id>/delete` | - | deletes chunks, document, file; rebuilds RAG index |
| GET/POST | `/ask` | form: `question` | answer text + `sources[{doc_name, doc_id, chunk_index, score, text}]` + last 10 `queries` history |
| GET | `/quiz` | - | document picker |
| GET | `/quiz?doc_id=` | - | generates 5 MCQs (`question, options[4], answer_index, topic, subject`) kept in session |
| POST | `/quiz` | form `q0..qN` option indexes | grades, stores `quiz_results` rows, returns per-question results + score % |
| GET | `/roadmap` | - | topic rows `{topic, subject, accuracy, attempts, priority High/Medium/Low}` sorted weakest-first |

## 2. Planned JSON API (`backend/main.py`, FastAPI, prefix `/api`)

Each route calls the same code Flask uses (same SQL, same `utils` functions); no logic is rewritten. Auth is a
signed session cookie (HttpOnly) so behaviour matches Flask.

| Method | Path | Mirrors |
|---|---|---|
| POST | `/api/auth/register` | `/register` |
| POST | `/api/auth/login` | `/login` |
| POST | `/api/auth/logout` | `/logout` |
| GET | `/api/auth/me` | **new, read-only** (session user, for route guards) |
| GET | `/api/dashboard` | `/dashboard` + `/api/performance` |
| POST | `/api/documents` (multipart) | `/upload` |
| GET | `/api/documents` | `/documents` |
| DELETE | `/api/documents/{id}` | `/documents/<id>/delete` |
| POST | `/api/ask` | `/ask` POST |
| GET | `/api/ask/history` | `/ask` history list |
| POST | `/api/quiz/generate` `{doc_id}` | `/quiz?doc_id=` |
| POST | `/api/quiz/submit` `{answers}` | `/quiz` POST |
| GET | `/api/roadmap` | `/roadmap` |
| GET | `/api/health` | **new**, for smoke test |

Additive items (flagged for the summary): `/api/auth/me`, `/api/health`, and quiz state held server-side per user
(same in-session idea as Flask) so `answer_index` is not sent to the browser until grading.

## 3. Features and screens that exist today

1. Landing page (public)
2. Register (username, password, interests/goals)
3. Login / Logout
4. Dashboard: 3 counters (documents, questions asked, quiz questions attempted), subject-wise performance chart, recent documents, quick links
5. Upload study material (subject + PDF/DOCX/TXT) with processing result (topics detected, chunks indexed)
6. Documents / knowledge repository: filename, subject badge, detected topics, upload time, Generate Quiz, Delete
7. Ask AI (RAG): question, answer (Claude if `ANTHROPIC_API_KEY`, else extractive), sources, last-10 history
8. Quiz: pick document, 5 auto-generated MCQs, submit, score + per-question correct/incorrect review, link to roadmap
9. Adaptive roadmap: priority-ranked topics (High <50%, Medium 50-80%, Low >=80%), accuracy bar, attempts
10. Flash feedback on every action (success/info/warning/danger)

## 4. Screen map (React, `frontend/src/pages`)

| Route | Screen | Features covered | Auth |
|---|---|---|---|
| `/` | Landing (Aurora hero, how it works, stats strip, example answer) | 1 | public |
| `/login` | Login | 3 | public |
| `/register` | Register | 2 | public |
| `/app` | Dashboard | 4 | yes |
| `/app/upload` | Upload | 5, 10 | yes |
| `/app/documents` | Documents (table, delete confirm modal, Generate Quiz) | 6, 10 | yes |
| `/app/ask` | Ask AI + history + sources | 7 | yes |
| `/app/quiz` | Quiz picker -> take -> results (tabs/steps in one page) | 8 | yes |
| `/app/roadmap` | Roadmap | 9 | yes |

Shell: kit `AppShell` (sidebar drawer on mobile), theme toggle in topbar, logout in user menu, toasts for feedback.

## 5. Ports / environment

- Backend 8301 and frontend 5301 will be set in `.env` (not committed; `.env.example` committed) and `run.bat`.
- Flask app on 5000 is unchanged and still runs with `python app.py`.
- Backend check: existing Flask app imports cleanly and registers the 12 routes above. FastAPI, uvicorn and
  python-multipart are not yet installed in `venv`; they go in `backend/requirements.txt`.

## 6. Verification (done - Step 4)

Verified with `scripts/smoke_test.py` (25 API checks, all pass) and `scripts/capture_screens.py` (real browser walk
of every screen with real data; console clean; no horizontal overflow at 360 / 768 / 1440 in light and dark).

- [x] Landing (light + dark, Aurora hero, marquee, features, pinned how-it-works, facts strip)
- [x] Register (auto sign-in, lands on Upload)
- [x] Login / logout (wrong password message, session cookie, deep-link return)
- [x] Dashboard counters + subject chart (with table view) + recent docs
- [x] Upload (pdf/docx/txt) with topic/chunk result, type/size validation, error state
- [x] Documents list, search, sort, Generate Quiz, delete with confirm
- [x] Ask AI answer + passage sources + last-10 history (reopen an old answer)
- [x] Quiz pick, generate, take (all answers required), submit, review
- [x] Roadmap priorities (High / Medium / Low) with filter
- [x] Feedback states (skeleton loading / empty with action / error with retry / success toast) on every screen
- [x] Dark mode toggle (persisted), reduced motion, 360 / 768 / 1440, keyboard (focus ring, Escape closes modal + drawer), labelled inputs

## 7. What was added beyond the original app

- `backend/main.py` (FastAPI): JSON wrappers around the existing code. Flask `app.py` is unchanged.
- Additive endpoints: `GET /api/auth/me` (returns `null` when signed out), `GET /api/health`.
- Additive fields: `chunk_count` on documents, `attempts` per subject on the dashboard, `llm_enabled` on answers.
- Register signs the new user in automatically (Flask asked them to log in again).
- Kit adaptations (copies in `frontend/src`, kit folder untouched): brand/nav/user menu in `AppShell`, new `lib/api`,
  `lib/auth`, `lib/queries`, `lib/gsap`, `reactbits/AuroraBackground`, landing components rewritten with this
  product's real content (the landing example is a real answer from the bundled sample notes; the facts strip shows
  real configuration limits, no measured numbers).
