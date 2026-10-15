"""Appendices (important code, installation guide, additional screens) and the design-and-implementation walkthroughs.
Code is read from the real source files at build time (by function name), so it cannot drift from the product."""
import ast
import os

from common import *


def func_src(rel, name, max_lines=None):
    path = os.path.join(ROOT, rel)
    text = open(path, encoding="utf-8").read()
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            start = node.lineno - 1
            if getattr(node, "decorator_list", None):
                start = node.decorator_list[0].lineno - 1
            seg = lines[start:node.end_lineno]
            if max_lines and len(seg) > max_lines:
                seg = seg[:max_lines] + ["    ..."]
            return "\n".join(seg)
    raise KeyError(f"{name} not found in {rel}")


def line_range(rel, a, b):
    lines = open(os.path.join(ROOT, rel), encoding="utf-8").read().splitlines()
    return "\n".join(lines[a - 1:b])


def code_walkthroughs():
    W = {}
    W["jepa"] = [
        ("h3", "Walkthrough 1: the JEPA model (ml/jepa.py)"),
        ("p", "The model keeps two copies of the encoder and a predictor. `keep` is a (variants x features) mask: row 0 hides everything, row k hides feature group k. `predict` encodes the three previous months (zeroed where a month is absent), encodes the current month with the mask applied, appends a one-hot of the variant and lets the predictor output the *embedding* of the full current month. `update_target` implements the exponential moving average."),
        ("code", func_src("ml/jepa.py", "JEPA")),
        ("p", "The training loop draws a random mask variant per sample, computes the target with no gradient, adds the variance hinge and updates the target encoder after every step."),
        ("code", func_src("ml/jepa.py", "train_jepa")),
    ]
    W["score"] = [
        ("h3", "Walkthrough 2: from prediction error to a deviation score (ml/pipeline.py)"),
        ("p", "The error of every variant is normalised by the median over taxpayers of the same month; the variants are combined by a geometric mean; the taxpayer's raw score is the mean of its two worst months; `_calibrate` turns it into a 0-1 score with a robust z and a logistic."),
        ("code", line_range("ml/pipeline.py", 74, 79) + "\n\n" + line_range("ml/pipeline.py", 121, 139)),
    ]
    W["cycles"] = [
        ("h3", "Walkthrough 3: circular-trading detection (ml/graph.py)"),
        ("p", "Only recurring, above-median edges are kept. `simple_cycles` with a length bound enumerates the loops; each is scored by balance, recurrence and concentration; overlapping suspicious loops are merged into rings by union-find."),
        ("code", func_src("ml/graph.py", "detect_cycles")),
    ]
    W["risk"] = [
        ("h3", "Walkthrough 4: invoice scoring and the combined risk (ml/pipeline.py)"),
        ("p", "Each invoice collects flags; its score is the noisy-OR of the flag weights. Taxpayer layer scores are then combined with a weighted noisy-OR."),
        ("code", line_range("ml/pipeline.py", 200, 232) + "\n\n" + line_range("ml/pipeline.py", 233, 246)),
    ]
    W["explain"] = [
        ("h3", "Walkthrough 5: the grounding check for case notes (backend/app/services/explainer.py)"),
        ("p", "After Gemini answers, `check_quality` extracts the citations, counts the invalid ones, computes the evidence and high-severity coverage and the share of numbers in the text that occur in the evidence."),
        ("code", func_src("backend/app/services/explainer.py", "check_quality")),
    ]
    W["auth"] = [
        ("h3", "Walkthrough 6: authentication guard (backend/app/auth.py)"),
        ("p", "Every protected route depends on `current_user`, which decodes the bearer token, rejects bad or expired tokens with 401 and loads the user."),
        ("code", func_src("backend/app/auth.py", "current_user")),
    ]
    W["bg"] = [
        ("h3", "Walkthrough 7: background generation (backend/app/services/state.py)"),
        ("p", "`start_run` refuses a second concurrent run, records a run row and starts a thread; `_run` generates the data, runs the pipeline with progress callbacks, saves the state atomically and records the outcome."),
        ("code", func_src("backend/app/services/state.py", "start_run") + "\n\n" + func_src("backend/app/services/state.py", "_run")),
    ]
    return W


def appendix_a():
    W = code_walkthroughs()
    b = [("h1", "APPENDIX A: IMPORTANT CODE"),
         ("p", "The listings below are extracted from the source files by function name when this document is built, so they match the product exactly. Long functions are shown in full.")]
    for k in ("jepa", "score", "cycles", "risk", "explain", "auth", "bg"):
        b += W[k]
    return b


def appendix_b():
    return [
        ("h1", "APPENDIX B: INSTALLATION AND USER GUIDE"),
        ("h2", "B.1 Requirements"),
        ("bul", ["Windows 10 or 11; Python 3.11 or later (with Add python.exe to PATH ticked); Node.js LTS.",
                 "A Gemini API key for written explanations (free from Google AI Studio); without it everything works except the Write explanation button.",
                 "Ports 8105 (API) and 5105 (web) free."]),
        ("h2", "B.2 Set up (once)"),
        ("p", "Open the `8.ProjectCode` folder and run `setup.bat`. It creates `venv`, installs the CPU build of PyTorch and `requirements.txt`, creates `.env` from `.env.example` with a random `JWT_SECRET`, trains the JEPA encoder if `models\\jepa.pt` is missing and runs `npm install` in `frontend`. Then open `.env` and set `GEMINI_API_KEY=your-key-here`."),
        ("h2", "B.3 Start"),
        ("p", "Run `run.bat`. It opens two windows (API and web), waits until the API reports the pipeline ready, and opens http://localhost:5105. Sign in with the demo account **demo@taxsentinel.app / Demo@1234** or register a new one. To stop, close the two server windows."),
        ("h2", "B.4 Demonstration walkthrough"),
        ("num", [
            "**Overview.** Press *Generate & analyse* (seed 42, 600 taxpayers; about 20 to 40 s). The stage stepper and the activity log follow the run; the counts, flagged taxpayers, patterns and chains refresh when it finishes.",
            "**Top-ranked taxpayer.** Open it from the list. The *Signals* tab shows the four layer scores and the monthly GSTR-2B against GSTR-3B chart; *Evidence*, *Network* and *Invoices* are the other tabs.",
            "**Case and explanation.** Choose *Open case & explanation*, then *Write explanation*. Click an E# chip to highlight the evidence item it cites.",
            "**Fraud rings.** Browse every loop, shell cluster and ranked invoice chain; click a chain to see its invoices.",
            "**Model performance.** Compare precision@k and recall with the rule baseline, the ablations and per-pattern recall.",
            "**Run history.** The last ten generations and the ecosystem currently loaded.",
        ]),
        ("p", "**Keyboard.** `/` searches taxpayers or jumps to a screen; `g` then `o`, `t`, `r`, `p`, `h` or `l` goes to overview, taxpayers, fraud rings, performance, run history or the activity log; `?` lists all shortcuts; `Esc` closes any overlay. The sun/moon button switches between light and dark mode."),
        ("h2", "B.5 Command line (optional)"),
        ("code", "venv\\Scripts\\python scripts\\generate_gst_data.py --seed 42 --taxpayers 600   :: regenerate data/generated\n"
                 "venv\\Scripts\\python -m ml.train                                              :: retrain models/jepa.pt\n"
                 "venv\\Scripts\\python -m ml.eval                                               :: experiments/eval/metrics.json\n"
                 "venv\\Scripts\\python scripts\\download_data.py                                 :: PaySim sample (Kaggle)\n"
                 "venv\\Scripts\\python scripts\\smoke_test.py                                    :: end-to-end API test (API running)\n"
                 "cd frontend && npm run build                                                 :: production build"),
        ("h2", "B.6 Troubleshooting"),
        ("tbl", "trouble", "Common problems", ["Symptom", "Fix"], [
            ["Port 5105 is already in use", "Another copy is running; close it or change FRONTEND_PORT in .env"],
            ["The page cannot reach the API", "Start the API window (run.bat) and check http://127.0.0.1:8105/api/health"],
            ["GEMINI_API_KEY is not set", "Add the key to .env and restart the API window"],
            ["Gemini 429 or quota errors", "The free tier is rate limited; wait a minute; fallback models are tried automatically"],
            ["Start over with a clean state", "Stop the servers, delete data\\workspace\\ and data\\app.db, start again"],
        ], [2.6, 4.4]),
    ]


def appendix_c(used_keys):
    b = [("h1", "APPENDIX C: ADDITIONAL SCREENS"),
         ("p", "Screens that are not shown in Chapter 8 are collected here. All were captured at 1440 x 900 from the running application with the bundled ecosystem (seed 42, 600 taxpayers) loaded.")]
    for k in SCREENS:
        if k not in used_keys:
            b.append(SCR(k, 4.5, label=f"app_{k}"))
    return b
