"""Evaluate CivicPulse against its objectives -> experiments/eval/metrics.json

    venv\\Scripts\\python ml\\eval.py

1. Classification (NLP)       category accuracy / macro-F1, by language, vs a majority-class baseline
2. Priority + resolution time priority accuracy vs the text-only model; days error vs category median
3. Department recommendation  top-1 / top-3 accuracy vs baseline
4. Explanations (XAI)         LIME faithfulness (deleting the top words vs random words), SHAP additivity
5. Human-in-the-loop          simulated officer overrides -> retrain -> agreement on seen / unseen cases
6. Real-time support          end-to-end intake latency (prediction + explanations)
Nothing here overwrites the saved models.
"""
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import training as T  # noqa: E402
from app.services.predictor import SEPARATORS, Predictor  # noqa: E402
from app.services.taxonomy import CATEGORIES, PRIORITIES  # noqa: E402

OUT = ROOT / "experiments" / "eval" / "metrics.json"
rng = random.Random(42)


def r4(x):
    return round(float(x), 4)


def load():
    text = joblib.load(T.TEXT_PATH)
    prio = joblib.load(T.PRIORITY_PATH)
    if T.CACHE_PATH.exists():
        cache = joblib.load(T.CACHE_PATH)
    else:
        _, cache = T.prepare(refit=False)
    return text, prio, cache


def classification(text, prio, cache):
    base = T.evaluate_classifiers(text, prio, cache)
    out = {}
    for field, classes in (("category", CATEGORIES), ("department", T.DEPTS)):
        ytr = T._enc(cache["tr"][field], classes)
        yte = T._enc(cache["te"][field], classes)
        majority = np.bincount(ytr).argmax()
        proba = text[field].predict_proba(cache["Xte"])
        top3 = (np.argsort(-proba, axis=1)[:, :3] == yte[:, None]).any(axis=1).mean()
        out[field] = {**base[field], "top3_accuracy": r4(top3),
                      "majority_baseline_accuracy": r4((yte == majority).mean())}
    # priority: stacked XGBoost vs the text-only urgency model it builds on
    P, y = cache["Pte"], cache["ypte"]
    text_only = np.column_stack([1 - P[:, :3].sum(axis=1), P[:, 0], P[:, 1], P[:, 2]]).argmax(axis=1)
    out["priority"] = {**base["priority"],
                       "text_only_model_accuracy": r4((text_only == y).mean()),
                       "majority_baseline_accuracy": r4((y == np.bincount(cache["yptr"]).argmax()).mean())}
    return out


def _tokens(t):
    return [w for w in re.split(SEPARATORS, t) if w]


def xai(pred, cache, n=60):
    te = cache["te"]
    idx = rng.sample(range(len(te)), n)
    drops_lime, drops_rand, flips_lime, flips_rand = [], [], 0, 0
    for i in idx:
        toks = _tokens(te.text.iloc[i])
        if len(toks) < 6:
            continue
        full = " ".join(toks)
        p = pred._cat_proba([full])[0]
        k = int(p.argmax())
        words = [w["word"] for w in pred.lime_words(full, k) if w["weight"] > 0][:3]
        if not words:
            continue
        rand_words = rng.sample(sorted(set(toks)), min(len(words), len(set(toks))))
        for removed, drops, is_lime in ((words, drops_lime, True), (rand_words, drops_rand, False)):
            q = pred._cat_proba([" ".join(w for w in toks if w not in removed) or "."])[0]
            drops.append(p[k] - q[k])
            if q.argmax() != k:
                if is_lime:
                    flips_lime += 1
                else:
                    flips_rand += 1
    n_ok = len(drops_lime)

    # SHAP additivity: base value + sum of contributions == model output
    P = cache["Pte"][:200]
    sv = np.asarray(pred.prio_exp.shap_values(P))
    margin = pred.prio["model"].predict(P, output_margin=True)
    ev = np.ravel(pred.prio_exp.expected_value)
    add_err = np.abs(sv.sum(axis=1) + ev[None, :] - margin).max()
    return {
        "lime_faithfulness": {
            "complaints": n_ok,
            "mean_confidence_drop_removing_top3_lime_words": r4(np.mean(drops_lime)),
            "mean_confidence_drop_removing_3_random_words": r4(np.mean(drops_rand)),
            "prediction_flip_rate_lime_words": r4(flips_lime / n_ok),
            "prediction_flip_rate_random_words": r4(flips_rand / n_ok),
        },
        "shap_additivity_max_error": float(f"{add_err:.2e}"),
        "explanation_coverage": "every suggestion carries LIME words + SHAP priority and time factors",
    }


def human_in_the_loop(text, cache, n=100):
    """Officers correct department errors on 100 complaints; do the fixes carry to 100 similar unseen ones?"""
    yte = T._enc(cache["te"]["department"], T.DEPTS)
    wrong = np.where(text["department"].predict(cache["Xte"]) != yte)[0].tolist()
    rng.shuffle(wrong)
    seen, unseen = wrong[:n], wrong[n:2 * n]
    rest = np.setdiff1d(np.arange(len(yte)), seen)
    te = cache["te"]
    feedback = [{"text": te.text.iloc[i], "category": te.category.iloc[i], "department": te.department.iloc[i],
                 "priority": None} for i in seen]

    def scores(model):
        pred = model.predict(cache["Xte"])
        return {"agreement_on_corrected": r4((pred[seen] == yte[seen]).mean()),
                "agreement_on_similar_unseen_errors": r4((pred[unseen] == yte[unseen]).mean()),
                "accuracy_on_rest_of_test_set": r4((pred[rest] == yte[rest]).mean())}

    before = scores(text["department"])
    fresh = joblib.load(T.TEXT_PATH)  # separate copy - saved models stay untouched
    t0 = time.time()
    T.fit_classifiers(fresh, cache, feedback, log=lambda *_: None, warm=True)
    secs = time.time() - t0
    return {"officer_labels": len(feedback), "before": before, "after": scores(fresh["department"]),
            "retrain_seconds": round(secs, 1)}


def latency(pred, cache, n=30):
    texts = rng.sample(list(cache["te"].text), n)
    full, fast = [], []
    for t in texts:
        t0 = time.perf_counter()
        pred.predict(t, datetime.now(), explain=True)
        full.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        pred.predict(t, datetime.now(), explain=False)
        fast.append(time.perf_counter() - t0)
    return {"complaints": n,
            "prediction_only_ms_median": round(1000 * float(np.median(fast)), 1),
            "with_explanations_ms_median": round(1000 * float(np.median(full)), 1),
            "with_explanations_ms_p95": round(1000 * float(np.percentile(full, 95)), 1)}


if __name__ == "__main__":
    t0 = time.time()
    text, prio, cache = load()
    pred = Predictor()
    train_metrics = json.loads(T.METRICS_PATH.read_text(encoding="utf-8"))
    print("classification...")
    res = {"model_version": text["version"], "evaluated_at": datetime.now().isoformat(timespec="seconds")}
    res.update(classification(text, prio, cache))
    res["resolution"] = train_metrics["resolution"]
    print("explanations...")
    res["explanations"] = xai(pred, cache)
    print("human-in-the-loop simulation...")
    res["human_in_the_loop"] = human_in_the_loop(text, cache)
    print("latency...")
    res["latency"] = latency(pred, cache)
    res["eval_seconds"] = round(time.time() - t0, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    c, d, p, r = res["category"], res["department"], res["priority"], res["resolution"]
    x, h, lt = res["explanations"]["lime_faithfulness"], res["human_in_the_loop"], res["latency"]
    print(f"category   acc {c['test']['accuracy']:.3f} (majority {c['majority_baseline_accuracy']:.3f}) "
          f"macro-F1 {c['test']['macro_f1']:.3f} by language {c['by_language']}")
    print(f"department acc {d['test']['accuracy']:.3f} top-3 {d['top3_accuracy']:.3f} (majority {d['majority_baseline_accuracy']:.3f})")
    print(f"priority   acc {p['test']['accuracy']:.3f} (text-only {p['text_only_model_accuracy']:.3f}) "
          f"macro-F1 {p['test']['macro_f1']:.3f} within-one-level {p['within_one_level']:.3f}")
    print(f"resolution median error {r['median_abs_error_days']} d (baseline {r['baseline_category_median_median_abs_error_days']}), "
          f"SLA flag {r['sla_breach_flag_accuracy']}")
    print(f"LIME: top-3 words drop confidence {x['mean_confidence_drop_removing_top3_lime_words']} vs random "
          f"{x['mean_confidence_drop_removing_3_random_words']}; SHAP additivity error {res['explanations']['shap_additivity_max_error']}")
    print(f"HITL: corrected {h['before']['agreement_on_corrected']} -> {h['after']['agreement_on_corrected']}, "
          f"unseen similar {h['before']['agreement_on_similar_unseen_errors']} -> {h['after']['agreement_on_similar_unseen_errors']}, "
          f"rest {h['before']['accuracy_on_rest_of_test_set']} -> {h['after']['accuracy_on_rest_of_test_set']} ({h['retrain_seconds']}s)")
    print(f"latency median {lt['with_explanations_ms_median']} ms with explanations, {lt['prediction_only_ms_median']} ms without")
    print("->", OUT)
