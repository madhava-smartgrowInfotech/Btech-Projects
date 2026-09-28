"""Evaluation report: detection accuracy vs the rule baseline, ring/chain recovery, a PaySim transfer
check of the JEPA module, and explanation quality (when GEMINI_API_KEY is set).

Writes experiments/eval/metrics.json.
Usage: python -m ml.eval [--explanations 10] [--skip-paysim]
"""
import argparse
import csv
import json
import math
import os
import time

import numpy as np

from ml import jepa as J
from ml.metrics import ranking_report
from ml.pipeline import run_pipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYSIM = os.path.join(ROOT, "data", "sample", "paysim_sample.csv")
TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def paysim_check(seed=42, epochs=15):
    """Train the same JEPA module (window=0, three blocks: transaction / origin / destination) on
    unlabelled PaySim transactions and score how well its prediction error ranks the fraud rows."""
    rows = list(csv.DictReader(open(PAYSIM, newline="")))
    X, y, amount = [], [], []
    for r in rows:
        a = float(r["amount"])
        oo, no_, od, nd = (float(r[k]) for k in ("oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"))
        e_org = max(-5, min(5, (oo - a - no_) / (a + 1)))
        e_dst = max(-5, min(5, (od + a - nd) / (a + 1)))
        X.append([float(r["type"] == t) for t in TYPES] + [math.log1p(a), (int(r["step"]) % 24) / 24] +
                 [math.log1p(oo), math.log1p(no_), e_org] + [math.log1p(od), math.log1p(nd), e_dst])
        y.append(int(r["isFraud"]))
        amount.append(a)
    X, y = np.array(X, np.float32), np.array(y)
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = ((X - mu) / sd).astype(np.float32)
    groups = [list(range(0, 7)), [7, 8, 9], [10, 11, 12]]
    empty_c, empty_p = np.zeros((len(Z), 0, Z.shape[1]), np.float32), np.zeros((len(Z), 0), np.float32)
    model, info = J.train_jepa(empty_c, empty_p, Z, groups, window=0, epochs=epochs, batch=1024, seed=seed)
    err = J.score(model, empty_c, empty_p, Z)
    score = np.exp(np.log(err / np.median(err, axis=0)).mean(1))
    ks = [100, 500, int(y.sum())]
    rep = ranking_report(y, score, ks)
    base = ranking_report(y, np.array(amount), ks)
    return dict(rows=len(y), fraud_rows=int(y.sum()), train_seconds=info["train_seconds"], epochs=epochs,
                roc_auc=rep["roc_auc"], average_precision=rep["average_precision"],
                precision_at_k=rep["precision_at_k"], recall_at_k=rep["recall_at_k"],
                amount_baseline=dict(roc_auc=base["roc_auc"], average_precision=base["average_precision"],
                                     precision_at_k=base["precision_at_k"]),
                note="Unsupervised: labels are used only for scoring. Baseline ranks transactions by amount.")


def explanation_check(state, n, pause):
    from backend.app.config import GEMINI_API_KEY
    from backend.app.services.explainer import ExplainError, build_prompt, check_quality, generate

    if not GEMINI_API_KEY:
        return dict(evaluated=0, note="GEMINI_API_KEY not set - explanation quality not measured. "
                                      "Add the key to .env and rerun: python -m ml.eval")
    flagged = sorted((t for t in state["taxpayers"] if t["flagged"]), key=lambda t: t["rank"])[:n]
    cases, errors = [], []
    for t in flagged:
        ev = state["details"][t["idx"]]["evidence"]
        try:
            text, model = generate(build_prompt(t, ev, state["config"]["pattern_labels"]))
        except ExplainError as e:
            errors.append(f"{t['gstin']}: {e}")
            continue
        q = check_quality(text, ev)
        # does the note name the suspected pattern(s)?
        words = {"circular_trading": "circular", "shell_entity": "shell", "fake_invoices": "invoice",
                 "itc_spike": "spike", "behaviour_anomaly": "deviat"}
        q["pattern_named"] = all(words[p] in text.lower() for p in t["patterns"]) if t["patterns"] else True
        cases.append(dict(gstin=t["gstin"], legal_name=t["legal_name"], model=model, quality=q, text=text))
        time.sleep(pause)
    if not cases:
        return dict(evaluated=0, note="All Gemini calls failed", errors=errors)
    qs = [c["quality"] for c in cases]
    mean = lambda k: round(float(np.mean([q[k] for q in qs if q[k] is not None])), 3)
    return dict(evaluated=len(cases), errors=errors, summary=dict(
        mean_citations=mean("citations"), invalid_citation_rate=round(
            sum(q["invalid_citations"] for q in qs) / max(1, sum(q["citations"] for q in qs)), 3),
        evidence_coverage=mean("evidence_coverage"), high_severity_coverage=mean("high_severity_coverage"),
        numeric_grounding=mean("numeric_grounding"),
        all_sections_present=round(float(np.mean([q["has_sections"] for q in qs])), 3),
        pattern_named=round(float(np.mean([q["pattern_named"] for q in qs])), 3), mean_words=mean("words")),
        cases=cases)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--explanations", type=int, default=10)
    ap.add_argument("--pause", type=float, default=4.0, help="seconds between Gemini calls (free-tier rate limits)")
    ap.add_argument("--skip-paysim", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    state = run_pipeline(os.path.join(ROOT, "data", "generated"), model_path=os.path.join(ROOT, "models", "jepa.pt"),
                         train=False)
    ev = state["evaluation"]
    out = dict(dataset="data/generated (seed 42, synthetic sample data)", model="models/jepa.pt",
               config={k: state["config"][k] for k in ("risk_weights", "flag_threshold", "invoice_flag_threshold")},
               detection=ev, stats={k: state["stats"][k] for k in ("taxpayers", "invoices", "flagged", "rings",
                                                                     "suspicious_clusters", "chains")})
    if not a.skip_paysim and os.path.exists(PAYSIM):
        print("PaySim transfer check...")
        out["paysim"] = paysim_check()
    print("Explanation quality...")
    out["explanations"] = explanation_check(state, a.explanations, a.pause)
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(ROOT, "experiments", "eval"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "eval", "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    tp, k = ev["taxpayer"], str(ev["n_fraud"])
    print(f"\nTaxpayers: {ev['n_taxpayers']} ({ev['n_fraud']} injected fraud)")
    for name, r in (("TaxSentinel", tp["model"]), ("Rule baseline", tp["rule_baseline"])):
        t = r["at_threshold"]
        print(f"  {name:14s} P@{k}={r['precision_at_k'][k]:.3f} R@{k}={r['recall_at_k'][k]:.3f} "
              f"P={t['precision']:.3f} R={t['recall']:.3f} F1={t['f1']:.3f} AUC={r['roc_auc']}")
    print(f"  Rings recovered {ev['rings']['recovered']}/{ev['rings']['injected']}; "
          f"invoice F1 {ev['invoice']['model']['at_threshold']['f1']}")
    if "paysim" in out:
        print(f"  PaySim JEPA AUC {out['paysim']['roc_auc']} (amount baseline {out['paysim']['amount_baseline']['roc_auc']})")
    print(f"  Explanations: {out['explanations'].get('summary') or out['explanations'].get('note')}")


if __name__ == "__main__":
    main()
