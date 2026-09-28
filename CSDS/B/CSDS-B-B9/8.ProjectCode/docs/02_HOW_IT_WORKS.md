# How TalentTrack works

## Architecture
```
React + Vite (5209) --/api proxy--> FastAPI (8209) --> SQLite  data/app.db
                                          |--> local judge (subprocess per test, temp folder, time limit)
                                          |--> resume classifier  models/resume_clf.joblib (scikit-learn)
                                          |--> Gemini API (questions, rubric scoring, explanations, resume tips)
```
- **Backend** `backend/app/`: `main.py` (app + startup seeding), `db.py` (SQLAlchemy models), `auth.py` (bcrypt + JWT),
  `routes/` (one module per feature), `services/` (judge, problems, progress/levels, contests/ratings, resume, skills, ai).
- **Frontend** `frontend/src/`: `pages/` (10 screens), `components/` (UI kit, Monaco editor), `api.js` (axios + token).

## Data model
`users`, `questions`, `test_attempts`, `answer_logs` (per-question correctness, used for weak topics), `submissions`,
`contests`, `interviews` (AI and expert), `resumes`, `drives`, `applications` (shortlist + status), `notifications`.
Coding problems live in `data/problems.json`.

## Pipelines
**Tests (F1, F3).** `POST /api/practice/start` samples questions for the topic/difficulty and stores the attempt with its
time limit; the client never receives answers. `POST /api/practice/{id}/submit` scores on the server (answers submitted
after the limit + 30 s grace are not counted), writes one `answer_log` per question and returns the review with
explanations. `POST /api/practice/explain/{qid}` asks Gemini for a step-by-step explanation once and caches it.

**Judge (F2).** Each submission is written to a fresh temp folder. C++ is compiled with `g++ -O2 -std=c++17 -static`,
Java with `javac` and run with a 256 MB heap cap, Python with `python -I`. Every test runs in its own subprocess with a
wall-clock limit (2 s base; x1.5 for Python and Java) and an 8 MB output cap. Output is compared line by line ignoring
trailing whitespace. The first failing test decides the verdict: non-zero exit -> Runtime Error, timeout -> Time Limit
Exceeded, mismatch -> Wrong Answer, compiler failure -> Compile Error. "Run" executes only the samples and shows I/O.
Limitation: the runner is process-isolated but not an OS sandbox (no seccomp/containers on Windows) - run it on a
machine you control.

**Contests (F4).** Contest submissions carry `contest_id` and must arrive while the contest runs. Standings: solved
count desc, then penalty = minutes to each accept + 5 per earlier wrong attempt. When a finished contest is first viewed
it is rated once: for every participant, `delta = round(80 x (actual - expected))`, where actual is the pairwise
win/tie share and expected is the Elo expectation `1 / (1 + 10^((Rj - Ri)/400))` averaged over opponents.
The practice leaderboard ranks by points (Easy 10, Medium 20, Hard 30 per distinct accepted problem), then rating.

**Levels and readiness (F5).** `services/progress.py` recomputes stats after every scored action and moves the
candidate up the ladder, sending a notification. The expert flow: candidate at Level 4 requests -> expert schedules
(candidate notified) -> expert submits 5 rubric scores -> average >= 7 gives Level 5 and the Job-ready badge.

**AI interview (F6).** Gemini generates N role-specific questions with "ideal points" (JSON mode). On submit, Gemini
scores every answer 0-10 on relevance, technical accuracy, clarity, structure and depth, with feedback, a model answer,
strengths, improvements and a hire signal. Blank answers are forced to 0. Local NLP adds TF-IDF cosine relevance to
the question + ideal points, word count, sentence length and filler-word count.

**Resume (F7).** pdfplumber extracts text (first 10 pages). The classifier returns role probabilities. Skills are
matched against a 200-term vocabulary (`services/skills.py`). The required skills per role are the 12 skills with the
highest share x lift in that role's resumes (computed at training time, `models/role_skills.json`). ATS score (0-100)
= sections & contact (25) + role skill match (35) + role fit from the classifier (15) + content quality: length,
quantified results, action verbs, skill breadth (25).

**Recruiter (F8).** Eligibility: level >= minimum, every required skill present (resume skills plus languages with
accepted code), readiness and aptitude minimums. Ranking score = 0.5 readiness + 0.2 level + 0.15 coding + 0.15 rating.
Each shortlisted row stores its evidence. Status changes notify the candidate.

**Analytics (F9).** Aggregates every candidate's readiness, level, components; topic accuracy from `answer_logs`
(weakest first); coding acceptance by problem topic and the verdict mix. A toggle excludes the sample cohort.

## Model
`ml/train_resume.py` - TF-IDF (1-2 grams, 60k features, sublinear tf) + Logistic Regression (C=10), stratified
80/20 split with seed 42, CPU training in ~20 s. Test results (`experiments/resume_classifier/metrics.json`):
accuracy 0.684, macro-F1 0.635, top-3 accuracy 0.883 over 24 roles. The served model is refit on all data.

## Evaluation
`ml/eval.py` -> `experiments/eval/metrics.json` (numbers in the README).

## Data sources
| Source | Licence | What is committed | Used for |
|---|---|---|---|
| [Engineering Aptitude Test Questions](https://www.kaggle.com/datasets/keithzidandsouza/engineering-aptitude-test-questions) (Kaggle) | MIT | All three CSVs in `data/aptitude/` | Aptitude bank (quantitative + logical) and the DSA part of the technical bank |
| [Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) (Kaggle) | CC0 | `data/resume/Resume.csv` (2,484 resumes, 24 categories) and one sample PDF per category in `data/sample/resumes/` | Role classifier, role skill profiles, sample cohort resumes, PDF parsing tests |
| Original coding problems | Own work | `data/problems.json` generated by `scripts/gen_problems.py` (seed 2024; expected outputs produced by the reference solutions) | Judge, contests |
| Original technical MCQs | Own work | Inside `scripts/build_question_bank.py` | DBMS / OS / Networks / Programming questions |

`scripts/build_question_bank.py` is deterministic: topic tags come from keyword rules, difficulty from a
length/number-count tercile heuristic, explanations from per-topic method hints plus the answer key.
The full PDF folder of the resume dataset (~65 MB) is not committed; `python scripts/download_data.py` fetches both
datasets with `kagglehub`.

## Sample data
On first start `app/seed.py` creates the demo accounts, three contests and **24 sample candidates** (names
"Sample Candidate NN", flagged `is_sample` and shown with a "sample data" tag). Their activity is generated with seed 7
but every result goes through the real pipeline: tests are scored by the practice scorer, code is judged by the local
judge, resumes are real dataset resumes analysed by the trained classifier, and the finished sample contest is rated by
the rating engine.
