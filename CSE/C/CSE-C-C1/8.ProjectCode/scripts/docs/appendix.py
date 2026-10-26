"""Appendices A (important code), B (installation and user guide) and C (additional screens) of the full report.

Code listings are read from the source files at build time (whole statements, verbatim) so they cannot drift from the code that was measured.
"""

import os

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, PAIR, TAB


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def _two(rel, a1, b1, a2, b2):
    return src(rel, a1, b1) + "\n    ...\n" + src(rel, a2, b2)


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from `8.ProjectCode` in the state in which the results of Chapter 8 were measured; each is a whole function or a stated range of one. They are the pieces on which the security arguments of "
          "Chapters 5 to 8 rest. Comments in the code are the authors' own and are reproduced as written."),
        H2("A.1 Verhoeff checksum (`app/identity/verhoeff.py`)"),
        CODE(src("app/identity/verhoeff.py", 30, 37), 7.5),
        H2("A.2 Aadhaar verification provider (`app/identity/provider.py`)"),
        CODE(src("app/identity/provider.py", 12, 39), 7.5),
        H2("A.5 Issuing the one-time token (`app/services/voting_service.py`)"),
        CODE(src("app/services/voting_service.py", 35, 64), 7.5),
        H2("A.6 Casting a ballot (`app/services/voting_service.py`)"),
        CODE(src("app/services/voting_service.py", 77, 139), 7.5),
        H2("A.8 Block proposal, validator quorum and commit (`app/ledger/ledger.py`)"),
        P("The loop in which each validator checks the transactions (lines 151 to 190) is omitted from the listing; the first part builds the block, the second part signs, tests the quorum and commits."),
        CODE(_two("app/ledger/ledger.py", 133, 150, 191, 229), 7.5),
        H2("A.9 Chain validation (`app/ledger/ledger.py`)"),
        CODE(src("app/ledger/ledger.py", 231, 252), 7.5),
        H2("A.11 Session guard, role guard and login route (`app/api_v1.py`)"),
        CODE(src("app/api_v1.py", 38, 60), 7.5),
        CODE(src("app/api_v1.py", 133, 150), 7.5),
    ]


def guide_blocks():
    rows = [[u, p, r] for u, p, r in F.DEMO_LOGINS]
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 (the launcher is a batch file; macOS and Linux use the manual commands).",
          "Python 3.11 or 3.12 with `pip` on the PATH, and Node.js 20 or newer with `npm`.",
          "About 1 GB of free disk space for `.venv` and `node_modules`; no database server, wallet, public-chain account or government credentials.",
          "Ports 8401 (backend) and 5401 (web app) free; both can be changed in `.env` (`BACKEND_PORT`, `FRONTEND_PORT`)."),
        H2("B.2 Installation and start (automatic)"),
        N("Open the project folder `8.ProjectCode` and double-click `run.bat`.",
          "The script checks for Python and Node, creates `.venv` if missing, installs `requirements.txt`, creates and seeds the database (`python -m app.seed`) and runs `npm install` in `frontend/` on the first run.",
          "It refuses to start if port 8401 or 5401 is already in use, then starts uvicorn on 8401 and Vite on 5401, each in its own console window, and opens http://localhost:5401.",
          "Wait until the backend window shows `Uvicorn running on http://127.0.0.1:8401` and the Vite window shows `Local: http://localhost:5401/`.",
          "To stop the system, close the two console windows."),
        H2("B.3 Manual start"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\npython -m app.seed\nuvicorn app.main:app --host 127.0.0.1 --port 8401\n"
             ":: in a second window\ncd frontend\nnpm install\nnpm run dev", 9),
        P("Docker is also supported (`docker build -t aegisballot .`); the image runs only the backend and serves the original server-rendered pages on port 8000, not the React application."),
        H2("B.4 Demonstration accounts"),
        TAB("Accounts created by the seed script", ["Username", "Password", "Role"], rows, widths=[2.2, 2.6, 1.2], size=10.5, align=["l", "l", "c"]),
        P("Each voter's synthetic Aadhaar number is written to `data/synthetic_identities.json` together with its masked form; the voter must type the number that belongs to the account that is signed in, otherwise the "
          "server answers 403. The seed also creates two elections: \"Campus Council Election 2026\" (open, four candidates) and \"Community Welfare Board 2026\" (closed, three candidates, eight seeded votes)."),
        H2("B.5 User guide by role"),
        P("**Voter.** Sign in with a voter account and open *My elections*. Choose an open election and press *Verify and vote*. Type the 12-digit Aadhaar number (spaces and hyphens are allowed) and press *Verify identity*; "
          "the screen shows a ten-minute countdown. Select a candidate, read the confirmation (the choice cannot be changed afterwards) and press *Confirm and submit vote*. The receipt page shows the ballot id, transaction hash, block number "
          "and block hash; copy them if you wish to check the block later. Back in *My elections* the election now shows that you have voted, and the results appear after the administrator closes it."),
        P("**Administrator.** Sign in as `admin`. The dashboard shows voters, votes, ledger height, turnout per election, the three validators, the latest benchmark, recent blocks and recent audit entries. In *Elections* press "
          "*New election*, enter a title, description, start and end, and create it (it starts as DRAFT and every registered voter becomes eligible). Open the election, add candidates (name, party, description, manifesto), then press *Open*. "
          "*Pause* stops voting without closing; *Close* ends it and publishes the results, which can then be opened from the election page. *Benchmarks* shows the throughput and latency of the stored runs."),
        P("**Auditor.** Sign in as `auditor`. *Ledger audit* shows the chain height and the validators. *Verify ledger integrity* recomputes the chain and reports the first invalid block and field, if any; *Run tamper-detection demo* shows "
          "the in-memory demonstration. The *Blocks*, *Transactions* and *Audit log* tabs list recent entries; selecting a block opens its detail page with previous hash, Merkle value, block hash and the validator signatures. "
          "The auditor never sees a candidate choice."),
        H2("B.6 Tests, benchmark and smoke test"),
        CODE("python -m pytest tests                     :: 17 tests; set DATABASE_URL to a scratch file first (the fixture drops all tables)\n"
             "python -m app.benchmarks.run_benchmark --voters 1000\n"
             "python scripts\\smoke_test.py                  :: needs both servers running\n"
             "python scripts\\run_experiments.py <scratch-dir>   :: growth, tamper and HTTP studies", 8.5),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["Python or Node not found", "Install them and tick \"Add to PATH\"; reopen the terminal"],
             ["Port 8401 or 5401 already in use", "Close the other program or change the port in `.env`"],
             ["Web app says it cannot reach the AegisBallot server", "The backend window is not running; start it with `run.bat`"],
             ["Login answers \"Too many attempts\"", "The limit is 10 logins per minute per address; wait one minute (also after the smoke test or the screenshot script)"],
             ["Vote fails with 400", "The message names the reason: wrong or expired token, election not open, Aadhaar not matching the account, duplicate vote"],
             ["`npm run dev` fails with a memory error", "Close other programs, or run `npm run build` and `npm run preview` in `frontend/`"],
             ["Corrupted environment or database", "Delete `.venv`, or `data/aegisballot.db` and `data/secrets.json`, and run again; the seed recreates the demo data and a new encryption key"]],
            widths=[2.4, 4.0], size=10, align=["l", "l"]),
    ]


def screens_blocks():
    def sh(name, caption):
        return (F.shot(name), caption)
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These screens complement the output screens of Chapter 8. All were captured from the running application at 1440 by 900 pixels (the phone view at 390 by 844) with the demonstration data: 200 registered voters, "
          "8 elections, 211 ballots and 212 blocks at the time of capture."),
        PAIR([sh("02_landing_dark_stats_and_features.png", "Landing page, live counters (elections, ballots recorded, blocks on the ledger, validators) and the three feature cards."),
              sh("03_landing_dark_how_it_works.png", "Landing page, \"From Aadhaar check to a verified receipt\": the four steps of a vote.")], 2.8),
        PAIR([sh("04_landing_dark_elections.png", "Landing page, \"What is on the ballot\": the elections held in the database with their status."),
              sh("11_admin_elections.png", "Administrator: election list with status, turnout and the open, pause, close and results actions.")], 2.8),
        PAIR([sh("13_admin_election_detail.png", "Administrator: election detail with eligible voters, votes cast, turnout and the candidate cards."),
              sh("15_admin_benchmarks.png", "Administrator: stored benchmark run with throughput, mean latency and per-mode charts.")], 2.8),
    ]
