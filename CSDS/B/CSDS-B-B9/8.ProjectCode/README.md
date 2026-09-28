# TalentTrack

Builds and proves job readiness: aptitude and coding practice with an automatic judge, contests, levels, AI mock
interviews and resume analysis - connected to recruiters who shortlist by real skill.

## Features
- **Aptitude practice** - 463 questions across 10 topics, timed tests, server-side scoring, explanations (+ AI step-by-step).
- **Coding judge** - 32 original problems, Monaco editor, Python / C++ / Java, 267 hidden tests, time limits, five verdicts.
- **Technical MCQs** - Programming, DBMS, Operating Systems, Computer Networks, DSA (150 questions).
- **Contests & leaderboards** - scheduled contests, live standings, Elo-style ratings, live practice leaderboard.
- **Level progression** - five levels unlocked by score; the final expert-led interview awards the Job-ready badge.
- **AI mock interviews** - Gemini role-specific questions, 5-criterion rubric feedback, NLP metrics, voice answers.
- **AI resume analysis** - PDF parsing, ATS score, role match and missing skills from a classifier trained on 2,400+ resumes.
- **Recruiter drives** - eligibility rules, ranked shortlist with skill evidence, status pipeline, invitations.
- **Readiness analytics** - cohort readiness, level funnel, weakest topics, coding acceptance.

## Quick start (Windows)
```
setup.bat          # venv, packages, .env, database, frontend packages
notepad .env       # set GEMINI_API_KEY (https://aistudio.google.com/apikey)
run.bat            # API on :8209, web app on :5209, opens the browser
```
Requirements: Python 3.11+, Node.js LTS; g++ and JDK 17 for C++/Java submissions. Details in
[docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo login (password `Demo@123`)
| Role | Email |
|---|---|
| Candidate | candidate@talenttrack.dev |
| Recruiter | recruiter@talenttrack.dev |
| Career services | career@talenttrack.dev |
| Expert interviewer | expert@talenttrack.dev |

24 **sample** candidates (clearly tagged "sample data") are created on first start so leaderboards, shortlists and
analytics have data; their results come from the real scorer, judge, classifier and rating engine.

## Evaluation results
From `python ml/eval.py` -> [experiments/eval/metrics.json](experiments/eval/metrics.json):

| Objective | Measure | Result |
|---|---|---|
| 1. Practice with automated evaluation | Judge verdict accuracy on 105 labelled submissions (AC / WA / TLE / RE / CE, Python + C++ + Java) | **100%** (105/105) |
| | Mean judge time per submission | 0.39 s |
| | Question bank | 613 MCQs (463 aptitude, 150 technical in 5 areas); 32 problems, 267 hidden tests |
| 2. Contests and leaderboards | Spearman(true skill, rating) in 30-player simulation, after 1 / 15 contests | 0.78 / **0.95** |
| 3. Progress through levels and interviews | Sample cohort reaching L2 / L3 | 17 / 15 of 24 |
| | NLP relevance AUC, on-topic vs off-topic answers | 0.875 |
| 4. Resume analysis | Role classifier (24 roles): accuracy / macro-F1 / top-3 accuracy | 0.684 / 0.635 / **0.883** |
| | ATS score AUC, correct vs wrong target role (150 resumes) | **0.957** (mean 66.9 vs 45.3) |
| | Sample PDFs parsed / true role in top-3 | 24/24 / 24/24 |
| 5. Recruiter shortlisting | Eligibility precision / recall over 3 drive rules | **1.0 / 1.0** |
| | Spearman(shortlist score, readiness) | 0.995 |
| 6. Readiness analytics | Candidates with a readiness score / topics tracked | 26 of 27 / 15 |

Smoke test (`python scripts/smoke_test.py`): 12/12 steps pass; the AI interview step reports SKIP until
`GEMINI_API_KEY` is set.

## Tech stack
React + Vite + Tailwind + Monaco (frontend, port 5209) - FastAPI + SQLAlchemy + SQLite (backend, port 8209) -
local subprocess judge - scikit-learn (TF-IDF + logistic regression) - pdfplumber - Google Gemini.

## Documentation
- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, levels, readiness score
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - architecture, pipelines, model, data sources and licences
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, run, demo walk-through, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan

## Project layout
```
backend/app/     FastAPI app: routes/, services/, db.py, auth.py, seed.py
frontend/src/    React screens (pages/), components/, api.js
ml/              train_resume.py, eval.py
scripts/         smoke_test.py, gen_problems.py, build_question_bank.py, download_data.py
data/            datasets, problems.json, question_bank.json, sample resumes (app.db is created at runtime)
models/          resume_clf.joblib, role_skills.json
experiments/     resume_classifier/metrics.json, eval/metrics.json
```
