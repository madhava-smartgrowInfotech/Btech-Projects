# SkillVerse - Frontend plan (kit V3 "Depth Studio")

Batch CSDS-B-B3 · backend port **8203** · frontend port **5203** · kit `D:\abstracts\Frontend_Kits\V3` (JavaScript `.jsx`)

## 1. What exists today

The product is a **Streamlit** app (`app.py` + `pages/`) over plain Python modules (`services/`, `ai/`, `graph/`,
`database/`). There is **no HTTP API**. Streamlit stays untouched and runnable (`streamlit run app.py`). The new
React app talks to a **thin FastAPI layer in `backend/`** that imports and calls the existing functions - no logic is
rewritten. (The Streamlit title bar says "KnowledgeX AI"; the new UI uses the product name from the project prompts,
**SkillVerse**.)

Roles: `student`, `mentor`, `admin` (role-based nav in `app.py`). Seeded demo accounts, password `Demo@1234`:
`student@example.com`, `mentor@example.com`, `admin@example.com`.

## 2. Backend endpoint inventory (new `backend/` layer → existing function it wraps)

Auth is a stateless HMAC-signed bearer token (replaces `st.session_state.user_id`). All routes are under `/api`.

| # | Method + path | Request | Response | Wraps |
|---|---|---|---|---|
| 1 | GET `/api/health` | - | `{status}` | - |
| 2 | POST `/api/auth/login` | `{email,password}` | `{token,user}` | `authenticate_user` |
| 3 | POST `/api/auth/register` | `{name,email,password,role}` | `{message}` | `register_user` + profile/points + `award_xp` |
| 4 | GET `/api/auth/me` | - | `{user}` | `User` |
| 5 | GET `/api/student/dashboard` | - | profile, points, badges, counts, latest roadmap (top 5), seller stats, purchases, leaderboard top 5, upcoming sessions | `get_topic_overview`, `get_user_points`, `get_user_badges`, `get_seller_dashboard`, `get_leaderboard`, `get_sessions_for_student` |
| 6 | GET `/api/learning/assessments` | - | `[{id,topic,title,description,question_count}]` | `Assessment` |
| 7 | GET `/api/learning/assessments/{id}` | - | assessment + questions (options only, **no answers**) | `AssessmentQuestion` |
| 8 | POST `/api/learning/assessments/{id}/submit` | `{answers:{qid:"A".."D"}}` | `{score,correct,total,xp_gained,badge}` | scoring + `StudentSkill`/`update_topic_progress`/`award_xp`/`grant_badge` (logic from `pages/learning.py`) |
| 9 | GET `/api/learning/roadmap` | - | saved roadmap, career goal | `get_latest_saved_roadmap` |
| 10 | POST `/api/learning/roadmap` | `{career_goal}` | `{career_goal,weak_prerequisites,roadmap,generated_at}` | `analyze_and_generate_roadmap` |
| 11 | GET `/api/learning/topics` | - | `[{id,name,difficulty,completion_percent,status}]` | `LearningTopic`, `LearningProgress` |
| 12 | POST `/api/learning/progress` | `{topic_id,completion_percent}` | updated progress | `update_topic_progress` + XP/badge ≥85 |
| 13 | GET `/api/graph` | - | `{nodes[{id,name,status,proficiency,difficulty,description,estimated_hours,prerequisites,next_topics,x,y}],edges,counts}` | `build_topic_graph`, `classify_topics`, NetworkX `spring_layout` |
| 14 | GET `/api/career/recommendations?top_n=8` | - | ranked careers | `recommend_careers` |
| 15 | POST `/api/career/goal` | `{title}` | `{career_goal}` | sets `StudentProfile.career_goal` |
| 16 | GET `/api/marketplace/meta` | - | categories, types, wallet balance | constants + `get_wallet_profile` |
| 17 | GET `/api/marketplace/resources` | `category,search,only_free` | resources + author + owned flag | `list_resources`, `get_author_name`, `has_purchased` |
| 18 | POST `/api/marketplace/resources/{id}/purchase` | - | `{message,wallet_balance}` | `purchase_resource` + `award_xp` |
| 19 | GET `/api/marketplace/purchases` | - | purchase history | `get_purchase_history` |
| 20 | POST `/api/marketplace/resources` | `{title,description,category,resource_type,price,skill_tags}` | resource | `upload_resource` + `award_xp` + badge |
| 21 | GET `/api/marketplace/seller` | - | resources, sales, earnings | `get_seller_dashboard` |
| 22 | POST `/api/mentors/recommend` | `{required_skill,career_goal,domain}` | ranked mentors | `recommend_mentors` |
| 23 | POST `/api/mentors/requests` | `{mentor_id,message}` | request | `send_request` |
| 24 | GET `/api/mentors/requests` | - | student's requests | `get_requests_for_student` |
| 25 | GET `/api/mentors/sessions` | - | student's sessions | `get_sessions_for_student` |
| 26 | POST `/api/mentors/sessions/{id}/complete` | `{rating 1-5}` | session | `submit_feedback` + `award_xp` |
| 27 | GET `/api/mentor/panel` | - | verification flag, pending requests, sessions + mentee skill/progress snapshot | `get_requests_for_mentor`, `get_sessions_for_mentor`, `student_skill_dataframe`, `learning_completion_dataframe` |
| 28 | POST `/api/mentor/requests/{id}/respond` | `{accept}` | ok | `respond_to_request` |
| 29 | POST `/api/mentor/sessions/{id}/feedback` | `{feedback}` | ok | `submit_feedback` |
| 30 | GET `/api/interview/meta` | - | roles, types, difficulties | `CareerRole` |
| 31 | POST `/api/interview/start` | `{role,interview_type,difficulty,num_questions}` | questions (id, text) | `get_questions` |
| 32 | POST `/api/interview/submit` | `{role,interview_type,difficulty,answers[{question_id,answer}]}` | scores + feedback + per-answer scores | `score_answer_semantic`, `generate_feedback`, + persistence/XP/badge from `pages/mock_interview.py` |
| 33 | GET `/api/interview/history` | - | past interviews | `interview_performance_dataframe` |
| 34 | GET `/api/coding/problems` | `difficulty` | list | `CodingProblem` |
| 35 | GET `/api/coding/problems/{id}` | - | problem + starter code (test cases hidden) | `CodingProblem` |
| 36 | POST `/api/coding/problems/{id}/submit` | `{code}` | `{passed,tests_passed,tests_total,details,error}` | `run_submission` + persistence/XP/badges |
| 37 | GET `/api/coding/stats` | - | attempted, solved, accuracy, recent | `coding_performance_dataframe` |
| 38 | GET `/api/progress/analytics` | - | counts, skills, topic completion, interview trend, coding pie, earnings | all `analytics_service` frames + `get_topic_overview` |
| 39 | GET `/api/profile` | - | student or mentor profile + skills + points + badges | models + gamification |
| 40 | PUT `/api/profile` | profile fields | updated | profile forms |
| 41 | PUT `/api/profile/skills` | `{skills:{skill_id:0-100}}` | ok | skills form |
| 42 | GET `/api/gamification/leaderboard?limit=` | - | leaderboard | `get_leaderboard` |
| 43 | GET `/api/admin/overview` | - | platform totals | `platform_overview` |
| 44 | GET `/api/admin/users` · POST `/api/admin/users/{id}/toggle` | - | users; toggled user | `User.is_active` |
| 45 | GET `/api/admin/mentors/pending` · POST `/api/admin/mentors/{id}/verify` | - | pending mentors; ok | `MentorProfile.is_verified` |
| 46 | GET `/api/admin/resources` · DELETE `/api/admin/resources/{id}` | - | all resources; ok | `Resource` |
| 47 | GET `/api/admin/reports` · POST `/api/admin/reports/{id}/resolve` | - | open reports; ok | `Report` |

Read-only endpoints marked as additive (not in Streamlit but needed because Streamlit held the state in
`st.session_state`): #9, #11, #33, #35, #42 and the token auth in #2/#4. Also added during the build:
`GET /api/auth/public/stats` (real catalogue counts for the landing page; no login) and a `mentor_id` field on
`GET /api/mentors/requests` (so the UI can disable "Send request" for a mentor who already has a pending request).
No existing function or data model was changed.

## 3. Feature / screen inventory (every item must still work)

Student (11 nav items) · Mentor (4) · Admin (2) · public (login/register/demo accounts).

| Area | Features |
|---|---|
| Login page | Login · Register (student/mentor, mentor needs admin verification) · Demo accounts table |
| Dashboard | Welcome + branch/year/goal · XP/level · streak · topics completed · wallet · active mentors · learning snapshot progress + completed/strong/weak/locked · latest roadmap top 5 · badges · marketplace uploads/purchases/earnings · leaderboard top 5 |
| Learning | Skill Assessment (pick topic, answer all, submit → score, skill+topic update, XP, ≥80% badge) · AI Roadmap (career goal, generate/refresh, weak prerequisites warning, step details: difficulty/hours/prereqs/why/resources) · Mark Progress (topic, %, XP+badge at ≥85) |
| Knowledge Graph | Prerequisite graph coloured by status (completed/strong/weak/recommended/locked) · legend · explore a topic (description, status, proficiency, difficulty, hours, prerequisites, next topics) |
| Career AI | Generate recommendations · match %, skill coverage, matched/missing skills, salary · certifications, projects, interview topics · Set as career goal |
| Marketplace | Browse (search, category, free-only, wallet balance, get/buy, owned) · My Purchases · Upload resource (publish) · Seller dashboard (listed, sales, earnings, list) - also for mentors |
| Mentors (student) | Find matching mentors (skill, goal, domain) + match score · Send request · My Requests (status) · My Sessions (mark completed + rate 1-5) |
| Mock Interview | Configure (role, type, difficulty, 3-8 questions) · answer · submit → overall/technical/communication/relevance/confidence, summary, strengths, weaknesses, topics, per-answer scores · cancel · past performance chart |
| Coding Practice | Difficulty filter · pick problem · description/concept · editor with starter code · Run & Submit (per-test results, sandbox errors) · My Stats (attempted/solved/accuracy/recent chart) |
| Progress | Topic-status counts · skill proficiency · learning completion · interview trend · coding pass-rate · marketplace earnings |
| Research & Innovation | Base paper · contribution · proposed extension · architecture flow · reviewer note (static content) |
| Profile | Student: branch/year/college/bio/interests/goal · skills sliders · achievements (level/XP/streak/badges). Mentor: expertise/domain/experience/bio/availability · verification status · rating |
| Mentor Panel | Pending-verification notice · requests (accept/reject) · sessions with mentee skill + progress snapshot · save feedback |
| Admin Panel | Overview metrics + chart · manage users (activate/deactivate, not admin) · verify mentors · moderate resources (remove) · open reports (resolve) |
| Cross-cutting | Role-based nav · logout · session end if account deactivated · gamification XP/levels/badges/streaks |

## 4. Screen map (React routes)

| Route | Screen | Roles |
|---|---|---|
| `/` | Landing page (Depth Studio, three.js hero, scroll story) | public |
| `/login` | Sign in / Register / Demo accounts (tabs) | public |
| `/app/dashboard` | Dashboard | student |
| `/app/learning` | Learning (tabs: Assessment · Roadmap · Progress) | student |
| `/app/graph` | Knowledge Graph | student |
| `/app/career` | Career AI | student |
| `/app/marketplace` | Marketplace (tabs: Browse · Purchases · Upload · Seller) | student, mentor |
| `/app/mentors` | Mentors (tabs: Find · Requests · Sessions) | student |
| `/app/interview` | Mock Interview | student |
| `/app/coding` | Coding Practice (tabs: Practice · Stats) | student |
| `/app/progress` | Progress & Analytics | student |
| `/app/research` | Research & Innovation | all |
| `/app/profile` | Profile | student, mentor |
| `/app/mentor-panel` | Mentor Panel | mentor |
| `/app/admin` | Admin Panel (tabs: Overview · Users · Mentors · Resources · Reports) | admin |

## 5. Plan of work

1. `backend/` FastAPI (`backend/main.py`, routers per area) importing existing modules; CORS for `:5203`.
2. `frontend/` Vite + React (JS). Kit copied into `frontend/src/` (adapted copies: sidebar/nav driven by role,
   product name, no `lib/stats` dependency). New: `lib/api.js`, `lib/auth.jsx`, pages, landing.
3. `run.bat`, `scripts/smoke_test.py`, `.gitignore` (so `.env`, `node_modules`, `*.db` are never committed),
   `docs/03_HOW_TO_RUN.md`.
4. Verify: build, smoke test, browser walk-through at 360/768/1440 px, light + dark, console clean.

## 6. Sign-off checklist (ticked in Step 4)

- [x] Login / Register / Demo accounts
- [x] Dashboard
- [x] Learning: Assessment · Roadmap · Mark Progress
- [x] Knowledge Graph + topic explorer
- [x] Career AI + set goal
- [x] Marketplace: Browse/buy · Purchases · Upload · Seller dashboard
- [x] Mentors: Find/request · Requests · Sessions/rate
- [x] Mock Interview + report + history
- [x] Coding Practice + stats
- [x] Progress & Analytics
- [x] Research & Innovation
- [x] Profile (student) + skills + achievements
- [x] Profile (mentor)
- [x] Mentor Panel
- [x] Admin Panel: overview · users · verify · resources · reports
- [x] Streamlit app untouched: `app.py`, `pages/`, `services/`, `ai/`, `graph/`, `database/` have no diff (Streamlit itself is not installed on the build machine, so it was not launched; the shared Python modules were exercised through the API)

## 7. Verification log

- `npm run build` passes (Vite 7). `python scripts/smoke_test.py`: all checks pass (about 90 API calls, three roles, plus 403/401/422 cases).
- Browser walk-through with real Chrome (Playwright): 16 scripted UI flows pass (assessment, roadmap, progress, graph, career, marketplace
  buy/upload/seller, mentors, mock interview, coding pass + sandbox rejection + stats, profile + skills, logout, register, mentor panel,
  mentor profile, admin overview/users/verify/remove/reports, role guard). Console: 0 errors, 0 warnings, 0 failed requests.
- Layout at 360 / 768 / 1440 px in light and dark: no horizontal page overflow on landing or any student screen.
  Wide tables become cards below 640 px; the knowledge graph scrolls sideways inside its own region on phones.
- Reduced motion: hero swaps to the static image, entrance motion collapses to fades, Lenis smooth scroll is not started.
- Keyboard: Escape closes the drawer and dialogs, tabs use arrow keys, graph nodes are focusable buttons, the code editor
  releases Tab with Escape. Theme toggle persists in `localStorage` (`sv-theme`).
- Offline backend: every screen shows an error state that names the problem and offers "Try again" (verified by aborting `/api`).
