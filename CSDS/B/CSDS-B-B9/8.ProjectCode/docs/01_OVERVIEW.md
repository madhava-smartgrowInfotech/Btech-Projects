# TalentTrack - Overview

TalentTrack builds and proves job readiness. Candidates practise aptitude, coding and technical skills with
automatic evaluation, compete in contests, climb five readiness levels, take AI mock interviews and get their
resume analysed. Recruiters run hiring drives that shortlist by verified skill, and career-services teams track
cohort readiness with data.

## The problem
- Hiring-readiness programmes lack continuous skill assessment and tracking.
- Candidates practise on scattered platforms with little guidance.
- Recruiters shortlist without evidence of actual skills.
- Career-services teams cannot measure readiness with data.

## Who uses it
| Role | What they do |
|---|---|
| Candidate | Practice tests, coding judge, contests, AI mock interviews, resume analysis, level progression |
| Recruiter | Create drives with eligibility rules, review ranked shortlists with evidence, move candidates through a pipeline, send invites |
| Career services | Cohort readiness analytics, weak topics, level funnel, schedule contests |
| Expert interviewer | Schedule and score the final-level mock interview that awards the Job-ready badge |

## Features
| # | Feature | What it does |
|---|---|---|
| F1 | Aptitude practice | 463 questions in 10 topics with Easy/Medium/Hard tags; timed tests (60 s per question), server-side scoring, per-topic breakdown, method explanations plus on-demand AI step-by-step explanations |
| F2 | Coding practice and judge | 32 original problems, Monaco editor, Python / C++17 / Java 17, sample runs with I/O diff, submissions judged on 267 hidden tests with time limits; verdicts Accepted, Wrong Answer, Time Limit Exceeded, Runtime Error, Compile Error |
| F3 | Technical MCQs | 150 questions: Programming, DBMS, Operating Systems, Computer Networks, Data Structures & Algorithms |
| F4 | Contests and leaderboard | Scheduled contests, live standings (solved, then penalty), Elo-style rating updates after each contest, live practice leaderboard |
| F5 | Level-based progression | Foundation -> Aptitude -> Coder -> Interview-ready -> Job-ready; levels unlock automatically by score; the last level is an expert-led mock interview |
| F6 | AI mock interviews | Gemini writes role-specific questions (using the candidate's resume skills), scores every answer on a 5-criterion rubric with feedback and a model answer; local NLP metrics (TF-IDF relevance, fillers, sentence length); voice answers through the browser's speech recognition |
| F7 | AI resume analysis | PDF upload -> pdfplumber text -> role classifier (TF-IDF + logistic regression trained on 2,483 resumes, 24 roles) -> ATS score (sections, skill match, role fit, content quality), missing skills, issues and optional Gemini tips |
| F8 | Recruiter module | Drives with minimum level, required skills, minimum readiness and aptitude; ranked shortlist with evidence (levels, scores, accepted-code counts per language, resume skills); status pipeline and invitations that notify candidates |
| F9 | Readiness analytics | Cohort size, average readiness, distribution, level funnel, component averages, weakest topics, coding acceptance by topic, verdict mix, per-candidate table |

## Readiness score
`readiness = 25% aptitude + 20% technical + 25% coding + 15% AI interview + 15% resume ATS` (each 0-100; aptitude and
technical use the average of the last five tests, coding uses solved problems capped at 10, interview uses the best AI
interview score x 10).

## Levels
| Level | Name | Unlocks when |
|---|---|---|
| 1 | Foundation | Account created |
| 2 | Aptitude | Best aptitude test (10+ questions) >= 60% |
| 3 | Coder | 3 problems Accepted on hidden tests and a technical test >= 60% |
| 4 | Interview-ready | AI mock interview >= 6/10 and resume ATS >= 55 |
| 5 | Job-ready | Expert mock interview average >= 7/10 - awards the Job-ready badge |

## Scope notes
Deferred to keep the build fast: Judge0 (the local runner replaces it), the career chatbot and code-similarity checks.
