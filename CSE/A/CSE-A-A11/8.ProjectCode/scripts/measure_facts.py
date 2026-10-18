"""Measure the numbers that the documentation quotes and that the trained-model report does not hold.

Run from the project root:   python scripts/measure_facts.py
Writes docs/measured_facts.json (read by the documentation builders). Nothing in autosecai/ is modified, and the trained
artefacts are never rewritten (this script does not call train_all).

Measurements
  1. engine_vs_ml   - on the SAME 1,500-function held-out split used by the trained report: the AST/taint rule engine,
                      the stored ML model and the two combined, against the corpus labels.
  2. seeds          - Random Forest / XGBoost re-run on five different corpus seeds (same pipeline, k fixed at the report's best_k).
  3. latency        - end-to-end review of the demo pull request (20 runs) with the per-agent split.
  4. retrieval      - codebase assistant on the demo repository: 12 hand-written questions with the file that should rank first.
  5. size           - lines of code per layer.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from autosecai import mlmodel, samples
from autosecai.agents import review_changes
from autosecai.codeintel import RepoIndex
from autosecai.dataset import build_dataset
from autosecai.diffutil import parse_unified_diff
from autosecai.knowledge import RULES
from autosecai.metrics import FEATURES
from autosecai.mlmodel import SEED, feature_selection, smote_tomek
from autosecai.rules import analyze_source

OUT = {}


def prf(y, p):
    return dict(precision=float(precision_score(y, p, zero_division=0)), recall=float(recall_score(y, p)),
                f1=float(f1_score(y, p)), tp=int(((y == 1) & (p == 1)).sum()), fp=int(((y == 0) & (p == 1)).sum()),
                fn=int(((y == 1) & (p == 0)).sum()), tn=int(((y == 0) & (p == 0)).sum()))


# ------------------------------------------------------------------ 1. rule engine vs ML on the held-out split
def engine_vs_ml():
    df = build_dataset(n=6000)                      # same defaults as train_all -> same corpus
    y = df["vulnerable"].values
    Xtr, Xte, ytr, yte = train_test_split(df[FEATURES], y, test_size=0.25, stratify=y, random_state=SEED)
    test_idx = Xte.index
    b = mlmodel.load_bundle()
    feats = b["features"]
    ml_pred = b["model"].predict(b["scaler"].transform(Xte[feats]))
    rule_pred = []
    t0 = time.time()
    for i in test_idx:
        fs, _ = analyze_source(df.loc[i, "source"], "f.py")
        rule_pred.append(int(any(f.category == "security" and f.severity in ("critical", "high", "medium") for f in fs)))
    rule_secs = time.time() - t0
    rule_pred = np.array(rule_pred)
    return dict(test_size=int(len(yte)), positives=int(yte.sum()), best_model=b["best_name"],
                rule_engine=prf(yte, rule_pred), ml_model=prf(yte, ml_pred),
                combined_or=prf(yte, np.maximum(rule_pred, ml_pred)), combined_and=prf(yte, np.minimum(rule_pred, ml_pred)),
                rule_engine_seconds_per_function_ms=round(1000 * rule_secs / len(yte), 2))


# ------------------------------------------------------------------ 2. five corpus seeds
def seeds():
    rep = mlmodel.load_report()
    k = rep["best_k"]
    rows = []
    for s in (7, 11, 23, 41, 59):
        df = build_dataset(n=6000, seed=s)
        X, y = df[FEATURES], df["vulnerable"].values
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
        _, _, order = feature_selection(Xtr, ytr, top=5)
        cols = list(order.index[:k])
        sc = MinMaxScaler().fit(Xtr[cols])
        Xb, yb, _ = smote_tomek(sc.transform(Xtr[cols]), ytr)
        row = dict(seed=s, positives=int(y.sum()))
        for name, model in (("Random Forest", RandomForestClassifier(300, random_state=SEED, n_jobs=-1)),
                            ("XGBoost", _xgb())):
            model.fit(Xb, yb)
            pr = model.predict(sc.transform(Xte[cols]))
            pp = model.predict_proba(sc.transform(Xte[cols]))[:, 1]
            row[name] = dict(f1=float(f1_score(yte, pr)), precision=float(precision_score(yte, pr, zero_division=0)),
                             recall=float(recall_score(yte, pr)), auc=float(roc_auc_score(yte, pp)))
        rows.append(row)
        print("seed", s, {n: round(row[n]["f1"], 3) for n in ("Random Forest", "XGBoost")}, flush=True)
    agg = {}
    for n in ("Random Forest", "XGBoost"):
        for m in ("f1", "precision", "recall", "auc"):
            v = [r[n][m] for r in rows]
            agg[f"{n}|{m}"] = dict(mean=float(st.mean(v)), sd=float(st.stdev(v)), min=float(min(v)), max=float(max(v)))
    return dict(k=k, runs=rows, summary=agg)


def _xgb():
    from xgboost import XGBClassifier
    return XGBClassifier(n_estimators=200, max_depth=5, learning_rate=.1, eval_metric="logloss", random_state=SEED, verbosity=0)


# ------------------------------------------------------------------ 3. latency of a full review
def latency():
    mlmodel.load_bundle()
    changed = parse_unified_diff(samples.DEMO_DIFF)
    review_changes(changed, "warm-up")
    ts, per = [], {}
    for _ in range(20):
        t = time.perf_counter()
        r = review_changes(changed, "Demo")
        ts.append(time.perf_counter() - t)
        for item in r["trace"]:
            per.setdefault(item["agent"], []).append(item["seconds"])
    ts.sort()
    return dict(runs=20, median_s=round(st.median(ts), 3), mean_s=round(st.mean(ts), 3), min_s=round(ts[0], 3),
                p95_s=round(ts[int(0.95 * (len(ts) - 1))], 3), max_s=round(ts[-1], 3),
                per_agent_median_s={k: round(st.median(v), 4) for k, v in per.items()},
                demo=dict(score=r["score"], verdict=r["verdict"], findings=len(r["findings"]), stats=r["stats"]))


# ------------------------------------------------------------------ 4. codebase assistant retrieval
QUESTIONS = [
    ("Where is the authentication mechanism implemented?", "app/auth.py"),
    ("Which function hashes the password?", "app/auth.py"),
    ("Where is the login route?", "app/auth.py"),
    ("How does the app connect to the database?", "app/db.py"),
    ("Where are database queries for orders written?", "app/db.py"),
    ("Which file defines the API routes for orders and the profile?", "app/routes.py"),
    ("What decorator protects routes from anonymous users?", "app/auth.py"),
    ("Where does the front end fetch the orders?", "static/app.js"),
    ("Which template holds the sign in form?", "templates/login.html"),
    ("Where are the unit tests?", "tests/test_auth.py"),
    ("How is the user looked up by name?", "app/db.py"),
    ("What clears the session on logout?", "app/auth.py"),
]


def retrieval():
    idx = RepoIndex(samples.DEMO_REPO, "demo-shop")
    t = time.perf_counter()
    idx2 = RepoIndex(samples.DEMO_REPO, "demo-shop")
    build_s = time.perf_counter() - t
    top1 = top3 = 0
    rows = []
    lat = []
    for q, want in QUESTIONS:
        t = time.perf_counter()
        res = idx.ask(q, k=6)
        lat.append(time.perf_counter() - t)
        files = []
        for h in res["hits"]:
            if h["file"] not in files:
                files.append(h["file"])
        rank = files.index(want) + 1 if want in files else None
        top1 += rank == 1
        top3 += bool(rank and rank <= 3)
        rows.append(dict(question=q, expected=want, got=files[:3], rank=rank))
    n = len(QUESTIONS)
    return dict(files=len(samples.DEMO_REPO), questions=n, top1=top1, top3=top3, index_build_ms=round(1000 * build_s, 1),
                ask_median_ms=round(1000 * st.median(lat), 1), rows=rows)


# ------------------------------------------------------------------ 5. size
def size():
    def loc(paths):
        n = 0
        for p in paths:
            n += sum(1 for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip())
        return n
    return dict(
        engine_py=loc(sorted((ROOT / "autosecai").glob("*.py"))),
        backend_py=loc(sorted((ROOT / "backend").glob("*.py"))),
        streamlit_app_py=loc([ROOT / "app.py"]),
        tests_py=loc(sorted((ROOT / "tests").glob("*.py"))),
        frontend_ts=loc(sorted((ROOT / "frontend" / "src").rglob("*.ts")) + sorted((ROOT / "frontend" / "src").rglob("*.tsx"))),
        frontend_files=len(list((ROOT / "frontend" / "src").rglob("*.ts"))) + len(list((ROOT / "frontend" / "src").rglob("*.tsx"))),
        rule_ids=len(RULES),
        security_rules=sum(1 for r in RULES.values() if r["category"] == "security"),
    )


if __name__ == "__main__":
    for name, fn in (("engine_vs_ml", engine_vs_ml), ("latency", latency), ("retrieval", retrieval), ("size", size), ("seeds", seeds)):
        t = time.time()
        OUT[name] = fn()
        print(f"[{name}] done in {time.time() - t:.0f}s", flush=True)
    (ROOT / "docs" / "measured_facts.json").write_text(json.dumps(OUT, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: v for k, v in OUT.items() if k != "seeds"}, indent=1, default=float)[:6000])
