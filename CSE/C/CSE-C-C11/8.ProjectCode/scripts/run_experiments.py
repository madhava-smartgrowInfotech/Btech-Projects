"""Measure the three ML pieces of FINJARVIS and the rule-based assistant. Writes experiments/metrics.json.

Run with the project interpreter (the one the app uses, so scikit-learn matches):
    .venv\\Scripts\\python.exe scripts\\run_experiments.py

Nothing here touches finjarvis.db or ml/expense_model.pkl: the model is re-trained in memory with the
same function the app uses (ml.expense_classifier._train_pipeline) and the database is a temp file.
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import LeaveOneOut

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as db_module
from database.models import Base

_tmp = tempfile.mkdtemp(prefix="finjarvis_exp_")
_engine = create_engine(f"sqlite:///{os.path.join(_tmp, 'exp.db')}", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_engine)
db_module.engine = _engine
db_module.SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

from backend import demo_seed
from ml import expense_classifier as ec
from ml.financial_health import WEIGHTS, calculate_financial_health
from ml.spending_prediction import predict_category_spending, predict_next_month_expense
from probe_data import ASSISTANT_QUESTIONS, PROBE
from services.analytics_service import spending_by_category, transactions_dataframe
from services.ai_service import answer_question

OUT = os.path.join(ROOT, "experiments")
os.makedirs(OUT, exist_ok=True)
CATS = list(PROBE.keys())
result: dict = {"generated": date.today().isoformat()}


def keyword_predict(description: str) -> str:
    low = (description or "").lower()
    for kw, cat in ec.KEYWORD_FALLBACK.items():
        if kw in low:
            return cat
    return "Other"


def prf(y_true, y_pred, labels):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {l: {"precision": round(float(p[i]), 3), "recall": round(float(r[i]), 3),
                "f1": round(float(f[i]), 3), "support": int(s[i])} for i, l in enumerate(labels)}


# ============================================================================ A. expense categoriser
seed = list(ec.SEED_TRAINING_DATA)
model = ec._train_pipeline([d for d, _ in seed], [c for _, c in seed])

rows = [(desc, cat, tier) for cat, tiers in PROBE.items() for tier, descs in tiers.items() for desc in descs]
X = [r[0] for r in rows]
y = [r[1] for r in rows]
tier = [r[2] for r in rows]
pred_lr = list(model.predict(X))
pred_kw = [keyword_predict(d) for d in X]
majority = Counter(c for _, c in seed).most_common(1)[0][0]
pred_maj = [majority] * len(X)
# shipped behaviour: LR when the model loads (it does), keyword table only if the pickle fails
labels_all = CATS + ["Other"]


def summarise(pred):
    acc = accuracy_score(y, pred)
    p, r, f, _ = precision_recall_fscore_support(y, pred, labels=CATS, average="macro", zero_division=0)
    by_tier = {t: round(float(np.mean([pp == yy for pp, yy, tt in zip(pred, y, tier) if tt == t])), 3) for t in "ABC"}
    return {"accuracy": round(float(acc), 4), "macro_precision": round(float(p), 4),
            "macro_recall": round(float(r), 4), "macro_f1": round(float(f), 4), "accuracy_by_tier": by_tier}


cm = confusion_matrix(y, pred_lr, labels=CATS)
proba = model.predict_proba(X)
conf = proba.max(axis=1)
correct = np.array([a == b for a, b in zip(pred_lr, y)])
curve = []
for th in [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60]:
    keep = conf >= th
    curve.append({"threshold": th, "coverage": round(float(keep.mean()), 3),
                  "accuracy_on_kept": round(float(correct[keep].mean()), 3) if keep.any() else None})

# user-sample CSV (the file the demo loader reads): 33 rows, labels from the file
sample = pd.read_csv(os.path.join(ROOT, "data", "sample_transactions.csv"))
s_pred = list(model.predict(sample["description"].tolist()))
s_acc = float(np.mean([a == b for a, b in zip(s_pred, sample["category"])]))

# leave-one-out cross-validation on the 51 seed pairs
loo_hits = []
sd, sl = [d for d, _ in seed], [c for _, c in seed]
for tr, te in LeaveOneOut().split(sd):
    m = ec._train_pipeline([sd[i] for i in tr], [sl[i] for i in tr])
    loo_hits.append(m.predict([sd[te[0]]])[0] == sl[te[0]])

# learning from corrections: user corrects k of the tier-C (unseen) items, evaluated on the rest of tier C
c_idx = [i for i, t in enumerate(tier) if t == "C"]
learn = []
rng = random.Random(2026)
for k in [0, 3, 6, 12, 24, 36, 48]:
    accs_c, accs_all = [], []
    for rep in range(30):
        picked = set(rng.sample(c_idx, k)) if k else set()
        extra = [(X[i], y[i]) for i in picked]
        m = ec._train_pipeline(sd + [d for d, _ in extra], sl + [c for _, c in extra])
        rest = [i for i in c_idx if i not in picked]
        accs_c.append(np.mean([m.predict([X[i]])[0] == y[i] for i in rest]))
    learn.append({"corrections": k, "tier_C_accuracy_mean": round(float(np.mean(accs_c)), 3),
                  "tier_C_accuracy_sd": round(float(np.std(accs_c)), 3)})

# repeat-merchant learning: the user corrects ONE unseen item once; does the same merchant, narrated differently
# the next time (three templates), come out right? (train = seed + that single correction)
VARIANTS = [lambda d: "UPI-" + d.upper().replace(" ", "-") + "-4412", lambda d: "POS " + d.upper(),
            lambda d: d + " 2"]
before, after = [], []
for i in c_idx:
    m1 = ec._train_pipeline(sd + [X[i]], sl + [y[i]])
    for v in VARIANTS:
        before.append(model.predict([v(X[i])])[0] == y[i])
        after.append(m1.predict([v(X[i])])[0] == y[i])
repeat = {"items": len(c_idx), "variants_per_item": len(VARIANTS), "tests": len(before),
          "accuracy_before_correction": round(float(np.mean(before)), 3),
          "accuracy_after_one_correction": round(float(np.mean(after)), 3)}
zero = model.predict(["xyzabc123 qqq"])[0]
zero_proba = dict(zip(model.classes_, np.round(model.predict_proba(["xyzabc123 qqq"])[0], 4).tolist()))

# timing: predict + retrain
t0 = time.perf_counter()
for d in X:
    model.predict([d])
predict_ms = (time.perf_counter() - t0) / len(X) * 1000
t0 = time.perf_counter()
for _ in range(10):
    ec._train_pipeline(sd, sl)
train_ms = (time.perf_counter() - t0) / 10 * 1000

wrong = [{"description": d, "true": t, "predicted": p, "tier": tr}
         for d, t, p, tr in zip(X, y, pred_lr, tier) if t != p]
result["classifier"] = {
    "seed_examples": len(seed), "seed_categories": len(set(sl)),
    "seed_per_category": dict(Counter(sl)),
    "probe_examples": len(X), "probe_per_tier": dict(Counter(tier)),
    "tfidf_lr": summarise(pred_lr), "keyword_table": summarise(pred_kw), "majority_class": summarise(pred_maj),
    "majority_label": majority,
    "per_category": prf(y, pred_lr, CATS),
    "confusion_labels": CATS, "confusion_matrix": cm.tolist(),
    "confidence_curve": curve,
    "mean_confidence_correct": round(float(conf[correct].mean()), 3),
    "mean_confidence_wrong": round(float(conf[~correct].mean()), 3),
    "sample_csv_rows": int(len(sample)), "sample_csv_accuracy": round(s_acc, 4),
    "loo_cv_accuracy_on_seed": round(float(np.mean(loo_hits)), 4), "loo_n": len(loo_hits),
    "learning_from_corrections": learn, "repeat_merchant_learning": repeat,
    "unseen_text_prediction": {"text": "xyzabc123 qqq", "predicted": zero, "probabilities": zero_proba},
    "errors_predicted_as_transport": int(sum(1 for e in wrong if e["predicted"] == "Transport")),
    "predict_ms_per_description": round(predict_ms, 2), "retrain_ms_seed_only": round(train_ms, 1),
    "errors": wrong,
    "never_predicts_other": "Other" not in set(model.classes_),
    "sklearn_version": __import__("sklearn").__version__,
}
print("classifier acc", result["classifier"]["tfidf_lr"], "kw", result["classifier"]["keyword_table"]["accuracy"], flush=True)

# ============================================================================ B. forecasting
demo_id = demo_seed.ensure_demo_user()
df = transactions_dataframe(demo_id)
df["month"] = df["date"].dt.to_period("M")
exp = df[df.transaction_type == "expense"].groupby("month")["amount"].sum().sort_index()
months = [str(m) for m in exp.index]
vals = exp.values.astype(float)


def f_lin(h):
    x = np.arange(len(h))
    s, i = np.polyfit(x, h, 1)
    return max(0.0, s * len(h) + i)


def f_mean(h):
    return float(np.mean(h))


def f_last3(h):
    return float(np.mean(h[-3:]))


def f_last(h):
    return float(h[-1])


METHODS = {"linear_trend (app)": f_lin, "mean_of_all": f_mean, "mean_of_last_3": f_last3, "last_value": f_last}
bt = {"months": months, "actual": [round(float(v), 2) for v in vals], "steps": []}
for t in range(3, len(vals)):
    step = {"predict_month": months[t], "actual": round(float(vals[t]), 2)}
    for name, fn in METHODS.items():
        step[name] = round(fn(vals[:t]), 2)
    bt["steps"].append(step)
bt["mae"] = {n: round(float(np.mean([abs(s[n] - s["actual"]) for s in bt["steps"]])), 1) for n in METHODS}
bt["mape_pct"] = {n: round(float(np.mean([abs(s[n] - s["actual"]) / s["actual"] for s in bt["steps"]])) * 100, 1) for n in METHODS}
app_pred = predict_next_month_expense(df[["date", "amount", "transaction_type", "category"]])
bt["app_prediction_for_next_month"] = app_pred
bt["category_prediction"] = predict_category_spending(df[["date", "amount", "transaction_type", "category"]])
bt["demo_transactions"] = int(len(df))

# synthetic simulation (labelled as such): 12-month histories, linear drift + noise + occasional spikes
sim_rng = np.random.default_rng(7)
N_USERS = 2000
sim = []
by_hist = defaultdict(lambda: defaultdict(list))
for rho in [0.05, 0.10, 0.20, 0.30]:
    errs = {n: [] for n in METHODS}
    for _ in range(N_USERS):
        base = sim_rng.uniform(20000, 60000)
        slope = sim_rng.normal(0, 0.03) * base
        noise = sim_rng.normal(0, rho * base, 12)
        spikes = (sim_rng.random(12) < 0.10) * 0.5 * base
        series = np.maximum(1000.0, base + slope * np.arange(12) + noise + spikes)
        for t in range(3, 12):
            for n, fn in METHODS.items():
                e = abs(fn(series[:t]) - series[t]) / series[t]
                errs[n].append(e)
                if rho == 0.10:
                    by_hist[t][n].append(e)
    sim.append({"noise_ratio": rho, **{n: round(float(np.mean(v)) * 100, 2) for n, v in errs.items()}})
hist_curve = [{"history_months": t, **{n: round(float(np.mean(v)) * 100, 2) for n, v in by_hist[t].items()}}
              for t in sorted(by_hist)]
result["forecast"] = {"demo_backtest": bt, "sim_users_per_setting": N_USERS, "sim_mape_by_noise_pct": sim,
                      "sim_mape_by_history_pct_noise_0.10": hist_curve,
                      "min_months_required": 3, "trend_labels": {"increasing": "slope > 1", "decreasing": "slope < -1"}}
print("forecast backtest", bt["mape_pct"], flush=True)

# ============================================================================ C. health score
def profile(**kw):
    base = dict(monthly_income=65000, monthly_expenses=32500, savings_rate=20.0, total_balance=100000,
                budget_status=[{"percent_used": 60}, {"percent_used": 90}], holdings=[{"asset_type": "ETF"}, {"asset_type": "Gold"}],
                goals=[{"percent_complete": 40}])
    base.update(kw)
    return base


base_score = calculate_financial_health(**profile())
sweeps = {
    "savings_rate": [(v, calculate_financial_health(**profile(savings_rate=v))["score"]) for v in [-10, 0, 5, 10, 15, 20, 30]],
    "monthly_expenses": [(v, calculate_financial_health(**profile(monthly_expenses=v))["score"]) for v in [20000, 32500, 45000, 55000, 65000, 75000]],
    "total_balance": [(v, calculate_financial_health(**profile(total_balance=v))["score"]) for v in [0, 50000, 100000, 195000, 390000, 600000]],
    "goal_progress": [(v, calculate_financial_health(**profile(goals=[{"percent_complete": v}]))["score"]) for v in [0, 25, 50, 75, 100]],
    "asset_types": [(n, calculate_financial_health(**profile(holdings=[{"asset_type": f"T{i}"} for i in range(n)]))["score"]) for n in range(0, 7)],
}
hr = np.random.default_rng(11)
scores, bands = [], Counter()
viol = 0
for _ in range(5000):
    inc = float(hr.uniform(10000, 150000))
    exp_ = float(hr.uniform(0.2, 1.3) * inc)
    p = profile(monthly_income=inc, monthly_expenses=exp_, savings_rate=(inc - exp_) / inc * 100,
                total_balance=float(hr.uniform(0, 12) * exp_),
                budget_status=[{"percent_used": float(hr.uniform(0, 160))} for _ in range(int(hr.integers(0, 6)))],
                holdings=[{"asset_type": f"T{i}"} for i in range(int(hr.integers(0, 7)))],
                goals=[{"percent_complete": float(hr.uniform(0, 100))} for _ in range(int(hr.integers(0, 4)))])
    r = calculate_financial_health(**p)
    scores.append(r["score"])
    bands[r["rating"]] += 1
    better = calculate_financial_health(**{**p, "savings_rate": p["savings_rate"] + 5})
    if better["score"] + 1e-9 < r["score"]:
        viol += 1
result["health"] = {
    "weights": WEIGHTS, "weights_sum": round(sum(WEIGHTS.values()), 6),
    "baseline_profile_score": base_score["score"], "baseline_components": base_score["components"],
    "sweeps": {k: [[a, b] for a, b in v] for k, v in sweeps.items()},
    "random_profiles": 5000, "score_min": float(min(scores)), "score_max": float(max(scores)),
    "score_mean": round(float(np.mean(scores)), 2), "rating_counts": dict(bands),
    "monotonic_violations_when_savings_rate_plus5": viol,
    "demo_score": None,
}

# ============================================================================ D. assistant routing
rows_ai = []
for q, answerable in ASSISTANT_QUESTIONS:
    a = answer_question(q, demo_id, 65000.0)
    rows_ai.append({"question": q, "answerable": answerable, "source": a["source"], "answer": a["answer"][:160]})
ans = [r for r in rows_ai if r["answerable"]]
una = [r for r in rows_ai if not r["answerable"]]
by_cat = spending_by_category(demo_id)
truth_food = float(by_cat.loc[by_cat.category == "Food", "amount"].sum())
food_ans = answer_question("How much did I spend on Food?", demo_id, 65000.0)["answer"]
top_ans = answer_question("Where am I spending the most money?", demo_id, 65000.0)["answer"]
result["assistant"] = {
    "questions": len(rows_ai), "answerable": len(ans), "not_answerable": len(una),
    "answerable_handled_by_analytics": sum(r["source"] == "analytics" for r in ans),
    "unanswerable_correctly_declined": sum(r["source"] == "fallback" for r in una),
    "unanswerable_wrongly_answered": sum(r["source"] != "fallback" for r in una),
    "numeric_check_food_truth": round(truth_food, 2), "numeric_check_food_answer": food_ans,
    "numeric_check_top_category_truth": str(by_cat.iloc[0]["category"]), "numeric_check_top_answer": top_ans,
    "detail": rows_ai, "llm_layer_tested": False,
}
print("assistant", result["assistant"]["answerable_handled_by_analytics"], "/", len(ans), flush=True)

# ============================================================================ E. import pipeline
from services.data_import_service import clean_and_prepare, commit_import, load_and_validate
import io

irng = random.Random(99)
descs = [d for t in PROBE.values() for tiers in [t] for ds in tiers.values() for d in ds]
rows_csv = ["date,description,amount,category,type"]
n_bad = {"bad_date": 0, "negative_amount": 0, "blank_description": 0, "non_numeric_amount": 0}
N_IMP = 1000
for i in range(N_IMP):
    d = f"2026-{irng.randint(1, 9):02d}-{irng.randint(1, 28):02d}"
    desc, amt, cat, typ = irng.choice(descs), round(irng.uniform(50, 5000), 2), "", "expense"
    r = irng.random()
    if r < 0.02:
        d = "31/31/2026"; n_bad["bad_date"] += 1
    elif r < 0.04:
        amt = -amt; n_bad["negative_amount"] += 1
    elif r < 0.06:
        desc = ""; n_bad["blank_description"] += 1
    elif r < 0.08:
        amt = "abc"; n_bad["non_numeric_amount"] += 1
    rows_csv.append(f"{d},{desc},{amt},{cat},{typ}")
buf = io.BytesIO("\n".join(rows_csv).encode())
buf.name = "import.csv"
t0 = time.perf_counter()
df_in, errs_ = load_and_validate(buf)
cleaned, warns = clean_and_prepare(df_in)
t_clean = time.perf_counter() - t0
uid = demo_id
t0 = time.perf_counter()
n_ins = commit_import(uid, cleaned)
t_commit = time.perf_counter() - t0
result["import"] = {"rows_in_file": N_IMP, "injected_bad_rows": n_bad, "injected_bad_total": sum(n_bad.values()),
                    "rows_skipped": len(warns), "rows_imported": n_ins,
                    "clean_and_categorise_s": round(t_clean, 2), "commit_s": round(t_commit, 2),
                    "rows_per_second_commit": round(n_ins / t_commit, 1), "blank_category_rows_auto_labelled": int(len(cleaned))}

with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print("wrote", os.path.join(OUT, "metrics.json"))
