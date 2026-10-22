# Frontend plan - LearnPathIQ (kit V2, Neo Brutal Grid)

Backend: FastAPI + SQLite in `app/` (port **8407**). New React frontend: `frontend/` (Vite, port **5407**, proxies
`/api` and `/static` to the backend, so the HttpOnly `lpq_token` cookie stays same-origin). The old Jinja UI keeps
working untouched at `http://localhost:8407/`.

## 1. Backend endpoints

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | - | `{name, email, password, confirm_password}` | `{ok, token, user{id,name,email}}`, sets cookie; 400 on mismatch / duplicate email |
| POST | `/api/auth/login` | - | `{email, password}` | `{ok, token, user}`, sets cookie; 401 on bad credentials |
| POST | `/api/auth/logout` | - | - | `{ok}` |
| GET | `/api/me` | optional | - | `{user: {id,name,email} \| null}` |
| GET | `/api/profile` | yes | - | `{education, skill_level, interests, preferred_topics, learning_style, goals, course_preferences, weekly_hours, age_band, gender}` |
| PUT | `/api/profile` | yes | same fields as above | `{ok, profile}` |
| GET | `/api/courses` | - | query `q, category, level` | `{courses[], count}` (course = id,title,category,topic,skill_level,description,duration_hours,difficulty,prerequisites,outcomes,tags,resource_type,rating) |
| GET | `/api/courses/{id}` | optional | - | course + `explanation`; when signed in also `match_score, success_prob, est_benefit, suggested_action` |
| GET | `/api/recommendations` | yes | query `top_n` | `{recommendations[{course,score,content_sim,skill_compat,topic_fit,success_prob,behavior,est_benefit,suggested_action,suggested_action_label,explanation}], engagement{label,score,total,quizzes,forums,completes}, success_probability, uplift{action:benefit}, feature_contrib{feature:importance}}` |
| POST | `/api/recommendations/refresh` | yes | - | same as above (reloads model bundle) |
| POST | `/api/interactions` | yes | `{course_id, event_type, value}`; event_type in view/open/start/quiz/content/forum/complete/dismiss/save | `{ok}`; 400 on bad type |
| GET | `/api/activity` | yes | query `limit` | `{events[{course_id,event_type,value,at}]}` |
| GET | `/api/history` | yes | - | `{history[{course_id,score,explanation,at}]}` (latest 40) |
| GET | `/api/learning-path` | yes | - | `{steps[{step,course,score,why,action,est_benefit}], engagement, next_action, next_action_key}` |
| GET | `/api/insights` | yes | - | `{engagement, success_probability, risk, contributing_features, uplift, recommended_action, recommended_action_key, strengths[], attention[], by_type{}, state{}}` |
| GET | `/api/metrics` | - | - | model metrics JSON (models, confusion matrices, feature_importance, policy_evaluation, fairness, dataset_source, notes); 503 if not trained |
| GET | `/api/fairness` | - | - | `{fairness{age_band{},gender{}}, note}` |
| GET | `/api/health` | - | - | `{ok, models_ready, app}` |
| GET | `/static/roc_curve.png` (+ `confusion_matrix.png`, `feature_importance.png`) | - | - | training plots |

Old server-rendered pages (stay as they are): `/`, `/register`, `/login`, `/onboarding`, `/dashboard`,
`/recommendations`, `/course/{id}`, `/path`, `/activity`, `/insights`, `/analytics`.

No new endpoints are needed. One additive backend change: `app/config.py` now has `extra = "ignore"` so the
shared `.env` can also carry `BACKEND_PORT` / `FRONTEND_PORT` (pydantic-settings otherwise rejects unknown keys).

## 2. Existing features (from README + old UI)

- [x] F1 Register (name, email, password, confirm) with validation errors
- [x] F2 Login / logout, session restore from cookie
- [x] F3 Learner profile: education, skill level, interests, preferred topics, goals, course preferences, learning style, weekly hours, age band, gender (create / update)
- [x] F4 Landing page (value proposition, how it works, catalog size)
- [x] F5 Dashboard: engagement status, success probability, interaction + quiz counts, recommended next action, recent activity, top recommendations (open / save)
- [x] F6 Recommendations: ranked list with match %, success %, explanation, suggested action + benefit; search; refresh; view / start / dismiss
- [x] F7 Course detail: metadata, prerequisites, outcomes, tags, why-recommended panel; save / start / content reviewed / quiz / discussion / complete (all logged as interactions); view event on open
- [x] F8 Learning path: staged steps with action + why, next best action, start step
- [x] F9 Insights: engagement, success estimate, recommended action, strengths, attention areas, action score (uplift) bars, contributing features
- [x] F10 Activity: interaction log + recommendation history
- [x] F11 Analytics / model transparency: model comparison table, selected model, dataset source, confusion matrices, feature importance, ROC plot, offline policy evaluation (IPS/SNIPS/DR or honest "unavailable" reason), fairness audit by age band and gender
- [x] F12 Course catalog search / filter by category and level (`GET /api/courses`, public)
- [x] F13 Feedback loop: every interaction posts to `/api/interactions` and changes later rankings

## 3. Screen map

| Route | Screen | Shell | Data |
|---|---|---|---|
| `/` | Landing (marquee, mask headline, how it works, live catalog stats) | Public | `/api/courses`, `/api/me` |
| `/login`, `/register` | Auth forms | Public | auth endpoints |
| `/courses` | Catalog with search + category + level filters | Public / App | `/api/courses` |
| `/courses/:id` | Course detail + action buttons | Public / App | `/api/courses/{id}`, `/api/interactions` |
| `/analytics` | Model transparency, fairness | Public / App | `/api/metrics`, `/api/fairness` |
| `/app/onboarding` | Profile form (also first-run after register) | App | `/api/profile` |
| `/app` | Dashboard | App | recommendations, activity |
| `/app/recommendations` | Recommendations | App | recommendations, refresh, interactions |
| `/app/path` | Learning path | App | `/api/learning-path` |
| `/app/insights` | Insights | App | `/api/insights` |
| `/app/activity` | Activity + history | App | `/api/activity`, `/api/history` |

Kit adaptations (copies only): `Layout.jsx` rebranded and its nav swapped to LearnPathIQ screens; missing kit
support files (`lib/auth`, `lib/storage`, `lib/gsap`) written in this project; `lib/format.js` labels replaced.

## 4. Verification (Step 4)

- 
pm run build passes; kit copied into rontend/src (no imports from outside this folder).
- python scripts/smoke_test.py: 33 checks pass (auth, profile, catalog filters, recommendations, interactions changing the ranking, learning path, insights, metrics, fairness, ROC plot, 401 handling), run through the React dev server's proxy.
- python scripts/capture_screens.py: every screen walked with a real registered learner (UI register + profile, 12 interactions), 20 PNGs in docs/screenshots/, console and network clean (no errors, no 4xx/5xx).
- python scripts/check_responsive.py: 360 / 768 / 1440 px x light / dark: no horizontal overflow, console clean, drawer opens and Escape closes it, skip link is the first Tab stop, focus outline visible. Run with prefers-reduced-motion: reduce; the kit collapses motion to fades.
- pytest tests: 5 passed (original backend tests, unchanged).
- Every feature F1-F13 above is ticked off against the running app.

## 5. Environment fixes made along the way

- .venv was copied from another machine and pointed at a missing Python 3.14; it was rebuilt from equirements.txt on Python 3.11.
- The shipped models/ and rtifacts/ were produced with scikit-learn 1.9.0, but equirements.txt pins 1.5.2. Under the pinned version the stored model could not predict ('LogisticRegression' object has no attribute 'multi_class'), so the backend silently fell back to a constant 55% success estimate and all-zero action scores, and offline policy evaluation was 
ull. scripts/train_pipeline.py was re-run unchanged under the pinned versions; selected model and test AUC are unchanged (logistic regression, 0.6028), and IPS / SNIPS / DR are now populated. The previous files are not in git (nothing in this folder was tracked); a copy was kept outside the repo.
- models/all_models.joblib (223 MB, only written by the training script, never read at runtime) is git-ignored, since GitHub rejects files over 100 MB.
- .env (ports) is git-ignored; .env.example carries the same keys.