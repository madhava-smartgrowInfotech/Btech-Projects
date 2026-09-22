"""Train and retrain the CivicPulse models.

- category + department: TF-IDF (word 1-2 grams + char 2-4 grams) -> Logistic Regression
- priority: XGBoost on text-urgency probabilities + multilingual urgency cues + category
- resolution days: XGBoost regressor on NYC 311 created/closed times

`train_full()` builds everything from the raw data (ml/train.py).
`retrain(feedback)` refits the classifiers with officer labels added (one click in the UI).
"""
import json
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion

from ..config import CACHE_DIR, EXPERIMENTS_DIR, FEEDBACK_WEIGHT, MODELS_DIR, SEED
from .datasets import load_nyc, load_text_dataset
from .taxonomy import CATEGORIES, CATEGORY_TO_DEPT, DEPARTMENTS, PRIORITIES
from .textutil import CUE_NAMES, TOKEN_PATTERN, cue_counts

DEPTS = list(DEPARTMENTS)
TEXT_PATH = MODELS_DIR / "text_models.joblib"
PRIORITY_PATH = MODELS_DIR / "priority_xgb.joblib"
RESOLUTION_PATH = MODELS_DIR / "resolution_xgb.joblib"
CACHE_PATH = CACHE_DIR / "train_cache.joblib"
METRICS_PATH = EXPERIMENTS_DIR / "metrics.json"
RUNS_DIR = EXPERIMENTS_DIR / "runs"

PRIORITY_FEATURES = (["Text model: medium urgency", "Text model: high urgency", "Text model: critical urgency"]
                     + CUE_NAMES + [f"Category: {c}" for c in CATEGORIES] + ["Length (words)"])
RESOLUTION_FEATURES = [f"Category: {c}" for c in CATEGORIES] + ["Priority level", "Day of week", "Hour filed"]


# ---------- feature builders (shared with the live predictor) ----------

def make_vectorizer():
    return FeatureUnion([
        ("word", TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2), min_df=2,
                                 max_features=100_000, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=3,
                                 max_features=100_000, sublinear_tf=True)),
    ])


def make_lr():
    return LogisticRegression(C=5.0, max_iter=300, class_weight="balanced")


def priority_features(texts, categories, urgency_proba):
    """urgency_proba columns follow PRIORITIES order."""
    X = np.zeros((len(texts), len(PRIORITY_FEATURES)), dtype=np.float32)
    n_cue = len(CUE_NAMES)
    for i, (t, c) in enumerate(zip(texts, categories)):
        X[i, 0:3] = urgency_proba[i, 1:4]
        cc = cue_counts(t)
        X[i, 3:3 + n_cue] = [cc[n] for n in CUE_NAMES]
        X[i, 3 + n_cue + CATEGORIES.index(c)] = 1
        X[i, -1] = len(t.split())
    return X


def resolution_features(categories, priority_levels, created):
    X = np.zeros((len(categories), len(RESOLUTION_FEATURES)), dtype=np.float32)
    n = len(CATEGORIES)
    for i, (c, p, ts) in enumerate(zip(categories, priority_levels, created)):
        ts = pd.Timestamp(ts)
        X[i, CATEGORIES.index(c)] = 1
        X[i, n:] = [p, ts.dayofweek, ts.hour]
    return X


def _enc(values, classes):
    idx = {c: i for i, c in enumerate(classes)}
    return np.array([idx[v] for v in values])


# ---------- data preparation ----------

def prepare(refit, log=print):
    """Vectorise the dataset. refit=True learns a new vocabulary + text-urgency model."""
    df = load_text_dataset()
    tr, te, ho = (df[df.split == s].reset_index(drop=True) for s in ("train", "test", "holdout"))
    log(f"text rows: train {len(tr)}, test {len(te)}, holdout {len(ho)}")

    t0 = time.time()
    if refit:
        vec = make_vectorizer().fit(tr.text)
        text = {"vectorizer": vec, "version": 0}
    else:
        text = joblib.load(TEXT_PATH)
        vec = text["vectorizer"]
    Xtr, Xte, Xho = vec.transform(tr.text), vec.transform(te.text), vec.transform(ho.text)
    log(f"vectorised in {time.time() - t0:.0f}s, {Xtr.shape[1]} features")

    # text-urgency model on the rows that have severity labels (CivicComp)
    ptr = tr[tr.priority.notna()].reset_index(drop=True)
    pte = te[te.priority.notna()].reset_index(drop=True)
    Xptr = Xtr[tr.index[tr.priority.notna()]]
    Xpte = Xte[te.index[te.priority.notna()]]
    yptr = _enc(ptr.priority, PRIORITIES)
    if refit:
        t0 = time.time()
        urg = LogisticRegression(C=2.0, max_iter=300)
        # out-of-fold probabilities so the XGBoost stage sees honest text scores
        oof = cross_val_predict(urg, Xptr, yptr, cv=GroupKFold(3), groups=ptr.group, method="predict_proba")
        urg.fit(Xptr, yptr)
        text.update(urgency=urg, urgency_oof=oof.astype(np.float32))
        log(f"text-urgency model trained in {time.time() - t0:.0f}s")
    urg, oof = text["urgency"], text["urgency_oof"]

    cache = {
        "Xtr": Xtr, "Xte": Xte, "Xho": Xho,
        "tr": tr[["text", "category", "department", "lang", "source"]],
        "te": te[["text", "category", "department", "lang", "source"]],
        "ho": ho[["text", "category", "department", "lang", "source"]],
        "Ptr": priority_features(ptr.text, ptr.category, oof), "yptr": yptr,
        "Pte": priority_features(pte.text, pte.category, urg.predict_proba(Xpte)),
        "ypte": _enc(pte.priority, PRIORITIES), "pte_lang": pte.lang.values,
    }
    joblib.dump(cache, CACHE_PATH)
    return text, cache


# ---------- classifiers ----------

def _fit_lr(prev, X, y, w):
    if prev is not None:  # start from the current weights -> converges in a few seconds
        model = prev
        model.set_params(warm_start=True)
    else:
        model = make_lr()
    return model.fit(X, y, sample_weight=w)


def _clf_metrics(y_true, y_pred, labels):
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        # macro-F1 over the classes present in this test set
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", labels=sorted(set(y_true)),
                                         zero_division=0)), 4),
        "n": int(len(y_true)),
    }


def _group_acc(y_true, y_pred, groups):
    out = {}
    for g in sorted(set(groups)):
        m = np.asarray(groups) == g
        out[g] = round(float(accuracy_score(y_true[m], y_pred[m])), 4)
    return out


def fit_classifiers(text, cache, feedback, log=print, warm=False):
    """Fit category / department LR and the priority XGBoost, with officer labels added."""
    vec = text["vectorizer"]
    fb = pd.DataFrame(feedback or [], columns=["text", "category", "department", "priority"])
    fb_before = agreement(text, None, fb) if len(fb) and warm else None

    for field, classes in (("category", CATEGORIES), ("department", DEPTS)):
        t0 = time.time()
        X, y = cache["Xtr"], _enc(cache["tr"][field], classes)
        w = np.ones(len(y))
        rows = fb[fb[field].notna()]
        if len(rows):
            X = sparse.vstack([X, vec.transform(rows.text)]).tocsr()
            y = np.concatenate([y, _enc(rows[field], classes)])
            w = np.concatenate([w, np.full(len(rows), FEEDBACK_WEIGHT)])
        text[field] = _fit_lr(text.get(field) if warm else None, X, y, w)
        log(f"{field} model trained in {time.time() - t0:.0f}s ({len(rows)} officer labels)")

    # priority
    t0 = time.time()
    P, y = cache["Ptr"], cache["yptr"]
    rows = fb[fb.priority.notna()]
    if len(rows):
        cats = [c if c in CATEGORIES else CATEGORIES[0] for c in rows.category.fillna(CATEGORIES[0])]
        urg = text["urgency"].predict_proba(vec.transform(rows.text))
        P = np.vstack([P, priority_features(rows.text.tolist(), cats, urg)])
        y = np.concatenate([y, _enc(rows.priority, PRIORITIES)])
    counts = np.bincount(y, minlength=len(PRIORITIES))
    w = (len(y) / (len(PRIORITIES) * counts))[y] ** 0.5  # soften the class imbalance
    if len(rows):
        w[-len(rows):] *= FEEDBACK_WEIGHT
    prio = xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.08, subsample=0.9,
                             colsample_bytree=0.9, tree_method="hist", random_state=SEED, n_jobs=4)
    prio.fit(P, y, sample_weight=w)
    log(f"priority model trained in {time.time() - t0:.0f}s ({len(rows)} officer labels)")
    return {"model": prio, "features": PRIORITY_FEATURES}, fb, fb_before


def agreement(text, prio, fb):
    """Share of officer labels the given models reproduce (per field)."""
    if not len(fb):
        return None
    out = {}
    X = text["vectorizer"].transform(fb.text)
    for field, classes in (("category", CATEGORIES), ("department", DEPTS)):
        m = fb[field].notna().values
        if m.any():
            pred = np.array(classes)[text[field].predict(X[np.where(m)[0]])]
            out[field] = round(float((pred == fb[field][m].values).mean()), 4)
    return out


def evaluate_classifiers(text, prio, cache):
    res = {}
    for field, classes in (("category", CATEGORIES), ("department", DEPTS)):
        model = text[field]
        yte = _enc(cache["te"][field], classes)
        pte = model.predict(cache["Xte"])
        yho = _enc(cache["ho"][field], classes)
        pho = model.predict(cache["Xho"])
        res[field] = {
            "test": _clf_metrics(yte, pte, classes),
            "by_language": _group_acc(yte, pte, cache["te"].lang.values),
            "by_source": _group_acc(yte, pte, cache["te"].source.values),
            "holdout_templates": _clf_metrics(yho, pho, classes),
        }
    y, p = cache["ypte"], prio["model"].predict(cache["Pte"])
    cm = confusion_matrix(y, p, labels=range(len(PRIORITIES)))
    res["priority"] = {
        "test": _clf_metrics(y, p, PRIORITIES),
        "by_language": _group_acc(y, p, cache["pte_lang"]),
        "recall": {c: round(float(cm[i, i] / max(cm[i].sum(), 1)), 4) for i, c in enumerate(PRIORITIES)},
        "confusion_matrix": {"labels": PRIORITIES, "matrix": cm.tolist()},
        "within_one_level": round(float((np.abs(y - p) <= 1).mean()), 4),
    }
    return res


# ---------- resolution time ----------

def train_resolution(text, prio, log=print):
    t0 = time.time()
    nyc = load_nyc()
    # priority of each NYC request type/descriptor, scored by our own priority model
    uniq = nyc[["text", "category"]].drop_duplicates().reset_index(drop=True)
    urg = text["urgency"].predict_proba(text["vectorizer"].transform(uniq.text))
    uniq["plevel"] = prio["model"].predict(priority_features(uniq.text.tolist(), uniq.category.tolist(), urg))
    nyc = nyc.merge(uniq, on=["text", "category"], how="left")
    X = resolution_features(nyc.category.tolist(), nyc.plevel.tolist(), nyc.created.tolist())
    y = nyc.days.values
    tr = (nyc.split == "train").values
    # absolute-error objective -> predicts the typical (median) time, robust to the long tail
    model = xgb.XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.08, subsample=0.9,
                             colsample_bytree=0.9, tree_method="hist", objective="reg:absoluteerror",
                             random_state=SEED, n_jobs=4)
    model.fit(X[tr], y[tr])
    pred = model.predict(X[~tr])
    true = nyc.days.values[~tr]
    test_cats = nyc.category.values[~tr]
    # baseline: median days of the category in the training period
    med = nyc[tr].groupby("category").days.median()
    base = np.array([med[c] for c in test_cats])
    sla = np.array([DEPARTMENTS[CATEGORY_TO_DEPT[c]] for c in test_cats])
    metrics = {
        "rows_train": int(tr.sum()), "rows_test": int((~tr).sum()),
        "mae_days": round(float(np.abs(pred - true).mean()), 3),
        "median_abs_error_days": round(float(np.median(np.abs(pred - true))), 3),
        "baseline_category_median_mae_days": round(float(np.abs(base - true).mean()), 3),
        "baseline_category_median_median_abs_error_days": round(float(np.median(np.abs(base - true))), 3),
        "baseline_sla_breach_flag_accuracy": round(float(((base > sla) == (true > sla)).mean()), 4),
        "sla_breach_flag_accuracy": round(float(((pred > sla) == (true > sla)).mean()), 4),
        "actual_breach_rate": round(float((true > sla).mean()), 4),
        "by_category_median_days": {c: round(float(v), 2) for c, v in med.items()},
    }
    joblib.dump({"model": model, "features": RESOLUTION_FEATURES}, RESOLUTION_PATH)
    log(f"resolution model trained in {time.time() - t0:.0f}s on {tr.sum()} NYC 311 rows")
    return metrics


# ---------- orchestration ----------

def _save(text, prio, metrics):
    text["version"] = int(text.get("version", 0)) + 1
    text["trained_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metrics = {"version": text["version"], "trained_at": text["trained_at"], **metrics}
    joblib.dump(text, TEXT_PATH, compress=3)
    joblib.dump(prio, PRIORITY_PATH, compress=3)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for p in (METRICS_PATH, RUNS_DIR / f"v{text['version']:03d}.json"):
        p.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics


def train_full(log=print):
    t0 = time.time()
    text, cache = prepare(refit=True, log=log)
    prio, _, _ = fit_classifiers(text, cache, [], log=log)
    metrics = evaluate_classifiers(text, prio, cache)
    metrics["resolution"] = train_resolution(text, prio, log=log)
    metrics["feedback"] = {"labels_used": 0}
    metrics["train_seconds"] = round(time.time() - t0, 1)
    return _save(text, prio, metrics)


def retrain(feedback, log=print):
    """Refit the classifiers with officer labels added. Vocabulary and resolution model stay."""
    t0 = time.time()
    if CACHE_PATH.exists():
        text, cache = joblib.load(TEXT_PATH), joblib.load(CACHE_PATH)
    else:
        text, cache = prepare(refit=False, log=log)
    prev = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    prio, fb, before = fit_classifiers(text, cache, feedback, log=log, warm=True)
    metrics = evaluate_classifiers(text, prio, cache)
    metrics["resolution"] = prev.get("resolution")
    metrics["feedback"] = {"labels_used": int(len(fb)), "officer_agreement_before": before,
                           "officer_agreement_after": agreement(text, prio, fb)}
    metrics["train_seconds"] = round(time.time() - t0, 1)
    return _save(text, prio, metrics)
