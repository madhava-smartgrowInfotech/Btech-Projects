"""Appendices A (important code, read from the real source files at build time), B (installation and user guide), C (additional screens)."""

import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB

APP = os.path.join(F.CODE, "backend", "app")


def _lines(rel):
    with open(os.path.join(APP, rel), encoding="utf-8") as f:
        return f.read().split("\n")


def excerpt(rel, start, end=None, max_lines=45):
    """Source text beginning at the first line containing `start`.

    Ends before the first later line containing `end`; without `end`, at the end of the indented block that starts there.
    A decorator line directly above the start line is included. The result is dedented and capped at `max_lines`.
    """
    ls = _lines(rel)
    i = next(k for k, ln in enumerate(ls) if start in ln)
    j0 = i
    if i > 0 and ls[i - 1].strip().startswith("@"):
        j0 = i - 1
    indent = len(ls[i]) - len(ls[i].lstrip())
    out = []
    for k in range(j0, len(ls)):
        ln = ls[k]
        if k > i:
            if end is not None and end in ln:
                break
            if end is None and ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
                break
        out.append(ln)
    while out and not out[-1].strip():
        out.pop()
    cut = out[:max_lines]
    if len(out) > max_lines:
        cut.append(" " * indent + "...")
    return textwrap.dedent("\n".join(cut))


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The excerpts below are read from the source files of the project when this report is built, so they always match the delivered code; long functions are cut "
          "at about 45 lines (marked with `...`). Paths are relative to `backend/app/`. The explanation of each excerpt is in Chapters 5 and 6."),
        H2("A.1 The action schema (`models/actions.py`)"),
        P("Everything an agent or a language model may say is one `EnergyAction`. Unknown fields are forbidden, numbers are bounded and finite, and reason codes have a fixed pattern."),
        CODE(excerpt("models/actions.py", "class EnergyAction"), 7.5),
        H2("A.2 Shield evaluation, steps 1 to 3 (`safety/shield.py`)"),
        P("Structural checks, the idle shortcut, and the evaluation of the request exactly as proposed. Only violations that are new or worse than the no-action state count."),
        CODE(excerpt("safety/shield.py", "def evaluate(", "# 4. projection"), 7.5),
        H2("A.3 Shield evaluation, step 4: projection (`safety/shield.py`)"),
        P("The largest safe scale is found by bisection, the rounded action is verified again, and an action with nothing safe left, or below the minimum size, is rejected."),
        CODE(excerpt("safety/shield.py", "# 4. projection", "corrections = [", 30), 7.5),
        H2("A.4 Bisection (`safety/projector.py`)"),
        CODE(excerpt("safety/projector.py", "def bisect_max"), 7.5),
        H2("A.5 Hash-chained safety events (`safety/events.py`)"),
        CODE(excerpt("safety/events.py", "def create("), 7.5),
        CODE(excerpt("safety/events.py", "def verify_chain"), 7.5),
        H2("A.6 Sequential validation and commit (`simulation/engine.py`)"),
        P("The CPU-bound part of a step. The counterfactual power flow of the raw proposals is used only for evaluation; the loop validates the ordered proposals against the "
          "cumulative state, and only the validated set-points are committed."),
        CODE(excerpt("simulation/engine.py", "def _validate_and_commit", None, 45), 7.5),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 (the one-click script is a batch file; the commands below also work on macOS and Linux).",
          "Python 3.10 or newer (3.11.9 was used) and Node.js 18 or newer (v24.19.0 was used).",
          "About 1 GB of disk space; the first installation takes a few minutes because pandapower is large.",
          "A modern browser; no GPU (machine used: " + F.MACHINE + "); no API key, since the default agent brain is the mock provider."),
        H2("B.2 One-click start (Windows)"),
        N("Open the folder `8.ProjectCode/safegrid-ai` and double-click **`run.bat`**.",
          "The script checks Python and Node, creates `backend\\.venv`, installs the packages, creates `backend\\.env` from the example, starts the "
          "API on port 8313 and the console on port 5313, and opens http://localhost:5313.",
          "Press **Continue with the demo account** (or sign in with `operator@safegrid.ai` and `SafeGrid@2026`); the sign-in only gates the browser session.",
          "To stop, press Ctrl+C in the console window and close the window titled SafeGrid-AI API."),
        H2("B.3 Manual start"),
        CODE("# backend (first terminal)\ncd backend\npython -m venv .venv\n.venv\\Scripts\\activate          # macOS/Linux: source .venv/bin/activate\n"
             "pip install -r requirements.txt\ncopy .env.example .env             # macOS/Linux: cp .env.example .env\nuvicorn app.main:app --host 127.0.0.1 --port 8313\n\n"
             "# frontend (second terminal)\ncd frontend\nnpm install\nnpm run dev                         # http://localhost:5313", 8.5),
        P("The API documentation is at http://127.0.0.1:8313/docs and a health check at http://127.0.0.1:8313/api/health. Ports can be changed in the `.env` file in "
          "`safegrid-ai/` (`BACKEND_PORT`, `FRONTEND_PORT`)."),
        H2("B.4 Using the console"),
        TAB("Console screens", ["Screen", "What to do there"], [
            ["Run bar (every screen)", "Choose a scenario, an agent brain (mock, baseline, real LLM, failing) and a seed; Start streams the run, Step advances one step, Stop and Reset control it."],
            ["Dashboard", "KPI tiles (including shield interventions and violations caused), charts, the latest intervention and the event timeline."],
            ["Grid view", "Single-line diagram with bus voltages and line loadings coloured against their limits, and the line and transformer table."],
            ["Agent monitor", "Select an agent card to see its latest and recent decisions and the context it saw."],
            ["Safety shield", "Counters and events table (filter by status; open an event for its checks, violations and hashes), active constraints, and **Dry run**: write your own action, for example an export of 1000 kW, and see how the shield decides; nothing is applied."],
            ["Power flow", "Eight charts: bus voltage with the 0.95-1.05 band, line loading with the 100 % limit, node exchange, battery power, generation and consumption, import and export, price, losses."],
            ["Scenarios", "Run any of the seven scenarios to completion and open its summary; run the strategy comparison (below)."],
            ["Explainability", "Pick an agent and read the decision lane (proposal, shield, executed), the decision factors, the context and the raw JSON."],
        ], widths=[1.5, 5.0], size=9.5),
        P("A good first run: choose **Malicious / invalid AI action**, set the fastest playback, press Start, then open **Safety shield**. The injected requests "
          "(export 1000 kW, import 900 kW, a malformed answer) are rejected or scaled down, the counters show the interventions, and the chain status shows the audit log is valid."),
        H2("B.5 Running a strategy comparison"),
        P("On **Scenarios**, enter the seeds (for example `0,1,2`) and the steps per run, and press **Run comparison**. The service runs every scenario under the three controllers "
          "with identical seeds: 7 x 3 x the number of seeds simulations. With one seed and 8 steps it takes roughly a minute; "
          f"the {F.N_RUNS} runs of Chapter 8 (three seeds, 24 steps) took about ten minutes on the measurement machine. The page shows a table of means, a bar chart of steps "
          "with violations caused by actions, and the notes that qualify the numbers."),
        H2("B.6 Running the checks"),
        CODE("python scripts/smoke_test.py            # 20 end-to-end API checks (backend must be running)\ncd backend && pytest                # 55 backend test functions\n"
             "cd backend && pytest --deselect tests/test_api.py::test_websocket_receives_events\ncd frontend && npm run build        # production build into frontend/dist\n"
             "python scripts/capture_screens.py   # regenerate docs/screenshots (needs Playwright)\npython scripts/verify_docs.py       # checks the documentation set", 8.5),
        P(f"**Test status, stated plainly.** In the final run, {F.TESTS['passed']} of the {F.TESTS['total']} tests passed in {F.TESTS['seconds']} s with the WebSocket test excluded. "
          "Two tests in `test_grid.py` fail: `test_power_flow_converges_and_balances` (external-grid power 10.995 kW against an expected 10.0 plus or minus 0.5 kW) and "
          "`test_trial_does_not_change_committed_state` (-3.12314 against -3.123 plus or minus 1e-6); their tolerances were set for an older pandapower, and the power flow itself converges. "
          "`test_websocket_receives_events` hangs under the installed Starlette test client although the WebSocket route works in the running application. None of the three was "
          "changed for this report. The smoke test passes 20 of 20 checks."),
        H2("B.7 Using a real language model"),
        P("Edit `backend\\.env`: `LLM_PROVIDER=api`, `LLM_API_KEY=...`, `LLM_MODEL=...`; `LLM_API_STYLE` is `anthropic` (default) or `openai`, and `LLM_BASE_URL` may point to a "
          "compatible endpoint. Restart the API and choose **Real LLM (API)** as the agent brain; without a key the agents use the labelled fallback policy. This path is "
          "unit-tested for answer validation and unconfigured behaviour, but it was not run against a live model, and no result in this report comes from one."),
        H2("B.8 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and remedy"], [
            ["Port already in use", "Another program holds 5313 or 8313. Find it with `netstat -ano | findstr :5313` and end it, or change the port in `.env`."],
            ["Banner: the SafeGrid API is not reachable", "The backend is not running or is still starting (importing pandapower takes about 10 seconds). Wait and press Retry."],
            ["First start is slow", "The first run installs the packages; later starts reuse `backend\\.venv` and `node_modules`."],
            ["Comparison seems stuck", "21 simulations per seed run one after another; the page shows the elapsed time. Use fewer seeds or steps for a quicker check."],
            ["Agents show source `fallback`", "No LLM key is configured for the Real LLM brain, or the call failed or returned an invalid answer; the fallback is deterministic and still shielded."],
        ], widths=[2.0, 4.5], size=9.5),
    ]


def screens_blocks():
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens are real captures of the running application at 1440 x 900 pixels. The console screens used as evidence are in Chapter 8; the public pages and the "
             "sign-in screen are shown here.")]
    items = [
        (F.shot("01_landing_dark.png"), "C.1 Landing page, dark theme",
         "Landing page (dark theme) with the three.js hero",
         "The landing page states the idea in one line, \"Let the agents propose. Let the shield decide.\", and offers the console and a tour of how it works. The three-dimensional "
         "figure is drawn with three.js and is replaced by a still image when the visitor prefers reduced motion. The strip under the buttons repeats three facts of the system: three "
         "agents, seven reproducible scenarios, live updates over WebSocket."),
        (F.shot("01_landing_light.png"), "C.2 Landing page, light theme",
         "Landing page in the light theme",
         "The theme switch in the top bar changes every colour token at once and the choice is remembered in the browser. Both themes were checked at 360, 768 and 1440 pixels "
         "for console errors and horizontal overflow."),
        (F.shot("02_landing_how_it_works.png"), "C.3 How it works",
         "The \"How it works\" section: the ten ordered shield checks",
         "A scroll story walks through the pipeline. The capture shows the second step, the ten checks the shield runs in order (structure, power limits, battery, node limits, power "
         "balance, power flow, voltage, line loading, transformer, grid limits) and the statement that the same input and the same grid state always give the same decision."),
        (F.shot("03_login.png"), "C.4 Sign-in",
         "Sign-in screen with the demo account",
         "The sign-in offers an email and password form and a button for the demo account. The panel under the button shows the demo credentials and states that the sign-in only "
         "gates the browser session and that the API has no user accounts."),
    ]
    for f, head, cap, text in items:
        path = F.shot_view(os.path.basename(f))
        out.append(("fig", path, cap, F.shot_w(path, 3.9, 2.35)))
        out.append(P(text))
    return out
