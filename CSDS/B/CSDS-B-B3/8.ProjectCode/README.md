# 🧠 KnowledgeX AI
### AI-Driven Learning and Earning Ecosystem for Knowledge Engineers
**Tagline:** *Learn. Earn. Connect. Grow.*

A complete, Python-centric, working prototype built with **Streamlit + SQLAlchemy +
SQLite + NetworkX + scikit-learn + Plotly**. No JavaScript frameworks, no paid
external AI API required — everything runs locally out of the box.

---

## 1. Research Foundation

**Base Paper:** *Enhancing Efficient Personalized Learning and Educational
Management in Universities Using Graph Neural Networks in Intelligent
Tutoring Systems* — IEEE Access, 2026 — DOI: `10.1109/ACCESS.2026.3662800`

The base paper's core idea — representing curriculum as a directed
prerequisite graph and tracking per-topic knowledge state to drive
personalized recommendations — is implemented in `graph/knowledge_graph.py`
using NetworkX (a transparent graph-traversal substitute for the paper's
GNN). Everything beyond that (career AI, marketplace, mentorship, mock
interviews, coding practice, gamification, analytics) is a **proposed
extension** built on top of it. See the in-app **Research & Innovation**
page for the full breakdown.

---

## 2. Project Structure

```
project/
├── app.py                     # Main Streamlit entry point
├── requirements.txt
├── .env.example
├── database/
│   ├── database.py            # SQLAlchemy engine/session
│   ├── models.py               # All ORM models (28 tables)
│   └── seed.py                 # Demo data seeding
├── pages/                      # One module per screen (login, dashboard, ...)
├── ai/                         # Learning / career / mentor / interview engines
├── graph/                      # Knowledge graph + roadmap generator
├── services/                   # Auth, marketplace, mentorship, analytics,
│                                #   gamification, safe code execution
├── data/                       # Seed JSON: skills, careers, topics, questions
└── assets/
```

---

## 3. Setup Instructions

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) copy the environment template
cp .env.example .env
```

No `.env` values are required to run the app — it works fully in **local
AI mode** out of the box.

---

## 4. Run Instructions

```bash
streamlit run app.py
```

The app opens automatically in your browser (default: `http://localhost:8501`).
The SQLite database (`knowledgex.db`) and all demo data are created
automatically on first run.

---

## 5. Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| 🎓 Student | `student@example.com` | `Demo@1234` |
| 🧑‍🏫 Mentor | `mentor@example.com` | `Demo@1234` |
| 🛡️ Admin | `admin@example.com` | `Demo@1234` |

⚠️ **Change these credentials (`DEMO_PASSWORD` in `.env`) before any
production deployment.**

---

## 6. End-to-End Demo Flow

1. Log in as `student@example.com`.
2. Go to **Profile** → confirm/update career goal (e.g. *Machine Learning Engineer*).
3. Go to **Learning → Skill Assessment** → take a topic quiz.
4. Go to **Knowledge Graph** → see your personalized knowledge state.
5. Go to **Learning → AI Roadmap** → click *Generate/Refresh Roadmap*.
6. Go to **Marketplace** → purchase or claim a free resource.
7. Go to **Mentors → Find a Mentor** → get AI-recommended mentors and send a request.
8. Go to **Mock Interview** → start an interview, answer, and view your AI feedback report.
9. Go to **Coding Practice** → solve a problem and submit.
10. Go to **Dashboard / Progress** → see XP, badges, and analytics update in real time.

For the mentor side, log in as `mentor@example.com` to accept requests and
give mentee feedback. For admin moderation, log in as `admin@example.com`.

---

## 7. AI Modes

The app ships with a clean AI abstraction layer (`ai/recommendation_engine.py`):

- **Local Mode (default, `AI_MODE=local`)** — all recommendations, roadmap
  generation, mentor matching, career matching and interview scoring run on
  local rule-based logic, graph algorithms (NetworkX) and scikit-learn
  similarity matching. No internet connection or API key required.
- **API Mode (`AI_MODE=api`)** — a clearly marked integration point for
  plugging in an external LLM later, without changing any calling code.

Never hardcode API keys — always use `.env`.

---

## 8. Testing Instructions

Manual functional testing checklist:

- [ ] Register a new student and mentor account
- [ ] Log in/out with all three demo roles
- [ ] Take at least 2 skill assessments and confirm skill/topic state updates
- [ ] Generate a roadmap and confirm weak-prerequisite detection works
- [ ] Click through every node in the Knowledge Graph explorer
- [ ] Purchase a paid resource and confirm wallet balance + seller earnings update
- [ ] Upload a resource as a student, confirm it appears in Marketplace
- [ ] Send a mentorship request, then accept it from the mentor account
- [ ] Complete a mock interview and review the AI feedback report
- [ ] Solve a coding problem (including a deliberately wrong submission) to see
      the safe-execution sandbox reject failing/forbidden code correctly
- [ ] Confirm XP, levels, badges and the leaderboard update after each activity
- [ ] As admin, verify a pending mentor and remove a flagged resource

Basic automated smoke test:

```bash
python -c "from database.database import init_db, get_session; from database.seed import seed_all; init_db(); seed_all(); print('DB OK')"
```

---

## 9. Security Notes

- Passwords are hashed with **bcrypt** (via passlib) — never stored in plaintext.
- Role-based access control gates every page (`student` / `mentor` / `admin`).
- Coding submissions run in an **isolated subprocess** with a restricted
  builtins namespace and a hard timeout — no filesystem/network/OS access.
- No API keys are hardcoded; all secrets are read from `.env`.

---

## 10. Notes for Reviewers / Viva

This project is designed for final-year engineering project submission,
demonstration, and viva. The **Research & Innovation** page inside the app
clearly separates what is adopted from the base paper versus what is a new
contribution of this project.
