# How to run TalentTrack

## Requirements
- Windows 10/11
- Python 3.11+ - https://www.python.org/downloads/
- Node.js LTS (20+) - https://nodejs.org/
- Git
- For C++ submissions: g++ - `winget install BrechtSanders.WinLibs.POSIX.UCRT` (or MSYS2)
- For Java submissions: JDK 17 - https://adoptium.net/
- A Gemini API key for AI interviews, AI explanations and resume tips - https://aistudio.google.com/apikey

Python submissions work without any extra compiler. If g++ or the JDK is missing, that language is shown as
"not installed" in the editor.

## First-time setup
1. Open a terminal in the `8.ProjectCode` folder.
2. Run `setup.bat` - it creates `venv`, installs Python packages, creates `.env` from `.env.example`, trains the resume
   model if it is missing, seeds the database and installs the frontend packages.
3. Open `.env` and set `GEMINI_API_KEY=` to your key. (Everything except the AI features works without it.)

## Start
Run `run.bat`. It opens two console windows (API on http://localhost:8209, web app on http://localhost:5209) and then
the browser. Close both console windows to stop.

Manual start (two terminals):
```
cd backend
..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8209

cd frontend
npm run dev
```

## Demo logins (password `Demo@123`)
| Role | Email |
|---|---|
| Candidate | candidate@talenttrack.dev |
| Recruiter | recruiter@talenttrack.dev |
| Career services | career@talenttrack.dev |
| Expert interviewer | expert@talenttrack.dev |

The login page has one-click buttons for each. 24 sample candidates (tagged "sample data") populate leaderboards,
shortlists and analytics.

## Demo walk-through
1. **Candidate** - Aptitude & MCQs -> pick a topic -> start a 10-question test -> submit -> review with explanations.
   Coding -> "Array Sum" -> write a solution -> Run samples -> Submit -> Accepted on hidden tests. Contests -> the live
   weekly contest -> open a problem -> submit -> the standings update within 5 seconds.
2. Resume -> upload a PDF (samples in `data/sample/resumes/`) -> ATS score, role match and missing skills.
   Mock interview -> role "Python Developer" -> answer (type or use the mic) -> feedback report.
3. **Recruiter** - Drives -> New drive -> minimum Level 3, skills "Python" -> ranked shortlist with evidence -> tick
   candidates -> Invite selected. Invited candidates see a notification on their dashboard.
4. **Career services** - Readiness analytics: distribution, level funnel, weakest topics.
5. **Expert** - Interview queue -> schedule -> score the rubric -> 7+/10 makes the candidate Job-ready.

## Checks
```
venv\Scripts\python scripts\smoke_test.py      (API must be running)
venv\Scripts\python ml\eval.py                 (writes experiments\eval\metrics.json)
cd frontend && npm run build
```

## Regenerating data and models
```
venv\Scripts\python scripts\download_data.py        (Kaggle datasets via kagglehub -> data/)
venv\Scripts\python scripts\build_question_bank.py  (data/question_bank.json)
venv\Scripts\python scripts\gen_problems.py         (data/problems.json)
venv\Scripts\python ml\train_resume.py              (models/ + experiments/resume_classifier/)
```
To reset the app, stop it and delete `data\app.db`; it is recreated and re-seeded on the next start.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Cannot reach the TalentTrack API" | The API window must be running on port 8209; check it for errors |
| AI actions return "AI features need GEMINI_API_KEY" | Put the key in `.env` and restart the API |
| "Gemini request failed ... model not found" | Set `GEMINI_MODEL` in `.env` to a model your key can use |
| Port already in use | Another program uses 8209/5209 - close it (ports are fixed on purpose) |
| C++/Java "not installed" | Install g++ / JDK 17, or set `GXX_PATH`, `JAVAC_PATH`, `JAVA_PATH` in `.env` |
