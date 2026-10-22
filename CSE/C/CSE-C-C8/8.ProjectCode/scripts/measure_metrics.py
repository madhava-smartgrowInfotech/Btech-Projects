"""Measure everything the project documents quote (decision model, reviewer matching, pipeline timings).

    python scripts/measure_metrics.py            # writes docs/metrics/metrics.json

Nothing in the documents is typed by hand: they read the JSON written here. The shipped artifacts in models/ are
NOT modified; supplementary experiments retrain in memory only.
"""
from __future__ import annotations

import json
import platform
import re
import statistics as st
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder, label_binarize

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "docs" / "metrics"
OUT.mkdir(parents=True, exist_ok=True)
R: dict = {}


def r4(x):
    return round(float(x), 4)


# ------------------------------------------------------------------ environment
def environment():
    import importlib.metadata as md

    def v(p):
        try:
            return md.version(p)
        except Exception:
            return None

    import subprocess
    cpu = ""
    try:
        cpu = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        ram = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        ram = ""
    R["environment"] = {
        "os": platform.platform(), "cpu": cpu, "ram_gb": ram, "gpu": "none used (CPU only)",
        "python": platform.python_version(),
        "packages": {p: v(p) for p in ("scikit-learn", "numpy", "pandas", "scipy", "PyMuPDF", "fastapi", "uvicorn",
                                       "SQLAlchemy", "pydantic", "torch", "transformers", "sentence-transformers",
                                       "reportlab", "requests", "joblib")},
    }


# ------------------------------------------------------------------ decision model
def load_split(seed=42):
    df = pd.read_csv(ROOT / "data" / "processed_dataset.csv").dropna(subset=["title", "text", "label"])
    df = df[(df["title"].str.len() > 3) & (df["text"].str.len() > 20)]
    blob = df["title"].fillna("") + " " + df["text"].fillna("")
    le = LabelEncoder()
    y = le.fit_transform(df["label"].astype(str))
    Xtr, Xte, ytr, yte = train_test_split(blob, y, test_size=0.2, random_state=seed, stratify=y)
    return df, blob, le, Xtr, Xte, ytr, yte


def fit_lr(Xtr, ytr, class_weight="balanced", word_only=False):
    w = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), lowercase=True, stop_words="english")
    c = TfidfVectorizer(max_features=4000, ngram_range=(3, 5), analyzer="char_wb", lowercase=True)
    if word_only:
        A = w.fit_transform(Xtr)
        feat = lambda X: w.transform(X)  # noqa: E731
    else:
        A = hstack([w.fit_transform(Xtr), c.fit_transform(Xtr)])
        feat = lambda X: hstack([w.transform(X), c.transform(X)])  # noqa: E731
    clf = LogisticRegression(max_iter=1000, class_weight=class_weight, C=1.0, random_state=42).fit(A, ytr)
    return clf, feat


def summarise(y, p, P=None, n_classes=3):
    out = {"accuracy": r4(accuracy_score(y, p)),
           "precision_macro": r4(precision_score(y, p, average="macro", zero_division=0)),
           "recall_macro": r4(recall_score(y, p, average="macro", zero_division=0)),
           "f1_macro": r4(f1_score(y, p, average="macro", zero_division=0))}
    if P is not None:
        try:
            out["roc_auc"] = r4(roc_auc_score(label_binarize(y, classes=list(range(n_classes))), P, average="macro", multi_class="ovr"))
        except Exception:
            out["roc_auc"] = None
    return out


def decision_model():
    import joblib

    df, blob, le, Xtr, Xte, ytr, yte = load_split(42)
    labels = list(le.classes_)
    D = {"rows": int(len(df)), "labels": labels, "train": int(len(ytr)), "test": int(len(yte)),
         "class_counts": {k: int(v) for k, v in Counter(df["label"]).items()}}

    # 1. shipped artifacts re-evaluated on the same split
    model = joblib.load(ROOT / "models" / "decision_model.joblib")
    vec = joblib.load(ROOT / "models" / "tfidf_vectorizer.joblib")
    P = model.predict_proba(vec.transform(Xte))
    pred = P.argmax(1)
    D["shipped"] = summarise(yte, pred, P)
    D["shipped"]["confusion_matrix"] = confusion_matrix(yte, pred).tolist()
    pr, rc, f1, sup = precision_recall_fscore_support(yte, pred, zero_division=0)
    D["per_class"] = {l: {"precision": r4(pr[i]), "recall": r4(rc[i]), "f1": r4(f1[i]), "support": int(sup[i])} for i, l in enumerate(labels)}
    saved = json.loads((ROOT / "models" / "metrics.json").read_text(encoding="utf-8"))
    D["matches_saved_metrics_json"] = bool(abs(saved["accuracy"] - D["shipped"]["accuracy"]) < 1e-4 and saved["confusion_matrix"] == D["shipped"]["confusion_matrix"])
    cm = np.array(D["shipped"]["confusion_matrix"])
    dec = cm[np.ix_([0, 2], [0, 2])]
    D["decisive_only"] = {"note": "accept vs reject items only, borderline predictions counted as wrong",
                          "n": int(cm[0].sum() + cm[2].sum()), "correct": int(cm[0, 0] + cm[2, 2]),
                          "accuracy": r4((cm[0, 0] + cm[2, 2]) / (cm[0].sum() + cm[2].sum()))}
    D["borderline_row"] = {"predicted_accept": int(cm[1, 0]), "predicted_borderline": int(cm[1, 1]), "predicted_reject": int(cm[1, 2])}

    # 2. confidence threshold analysis (max class probability)
    conf = P.max(1)
    thr = []
    for t in (0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= t
        thr.append({"threshold": t, "coverage": r4(m.mean()), "n": int(m.sum()),
                    "accuracy_on_kept": r4(accuracy_score(yte[m], pred[m])) if m.any() else None})
    D["threshold_analysis"] = thr

    # 3. baselines on the same split
    base = {}
    maj = Counter(ytr).most_common(1)[0][0]
    base["majority_class"] = summarise(yte, np.full_like(yte, maj))
    base["majority_class"]["predicts"] = labels[maj]
    w = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), stop_words="english")
    A = w.fit_transform(Xtr)
    nb = MultinomialNB().fit(A, ytr)
    pnb = nb.predict_proba(w.transform(Xte))
    base["naive_bayes_word_tfidf"] = summarise(yte, pnb.argmax(1), pnb)
    clf, feat = fit_lr(Xtr, ytr, class_weight=None)
    pu = clf.predict_proba(feat(Xte))
    base["logreg_unweighted_word_char"] = summarise(yte, pu.argmax(1), pu)
    base["logreg_unweighted_word_char"]["confusion_matrix"] = confusion_matrix(yte, pu.argmax(1)).tolist()
    clf, feat = fit_lr(Xtr, ytr, word_only=True)
    pw = clf.predict_proba(feat(Xte))
    base["logreg_balanced_word_only"] = summarise(yte, pw.argmax(1), pw)
    D["baselines"] = base

    # 4. structure of the synthetic labelling process (why accuracy cannot exceed ~0.6)
    from prepare_dataset import STRONG, WEAK
    txt = (df["title"] + " " + df["text"]).str.lower()
    # word-boundary match: "unclear methodology" must not count as the strong phrase "clear methodology"
    sre = [re.compile(r"\b" + re.escape(p)) for p in STRONG]
    wre = [re.compile(r"\b" + re.escape(p)) for p in WEAK]
    strong = txt.apply(lambda s: any(r.search(s) for r in sre))
    weak = txt.apply(lambda s: any(r.search(s) for r in wre))
    lab = df["label"].astype(str)
    g = {}
    for name, mask in (("strong_phrase_papers", strong & ~weak), ("weak_phrase_papers", weak & ~strong), ("both_or_none", ~(strong ^ weak))):
        c = Counter(lab[mask])
        g[name] = {"n": int(mask.sum()), "label_counts": dict(c)}
    D["generator_structure"] = g
    best = sum(max(v["label_counts"].values()) for k, v in g.items() if v["n"] and k != "both_or_none")
    n_used = sum(v["n"] for k, v in g.items() if k != "both_or_none")
    D["generator_structure"]["best_possible_accuracy_from_phrases"] = r4(best / max(n_used, 1))
    D["generator_structure"]["borderline_share_of_dataset"] = r4((lab == "borderline").mean())
    # rule: strong -> accept, weak -> reject, never borderline
    rule = np.where(strong & ~weak, "accept", np.where(weak & ~strong, "reject", "borderline"))
    D["generator_structure"]["phrase_rule_accuracy_all_rows"] = r4((rule == lab.values).mean())

    # 5. five different splits / seeds
    seeds = []
    for s in (0, 1, 2, 3, 4):
        _, _, le_s, a, b, ya, yb = load_split(s)
        clf, feat = fit_lr(a, ya)
        Ps = clf.predict_proba(feat(b))
        seeds.append({"seed": s, **summarise(yb, Ps.argmax(1), Ps)})
    D["seed_study"] = {"runs": seeds}
    for k in ("accuracy", "f1_macro", "roc_auc"):
        vals = [x[k] for x in seeds]
        D["seed_study"][k] = {"mean": r4(st.mean(vals)), "sd": r4(st.stdev(vals)), "min": r4(min(vals)), "max": r4(max(vals))}
    R["decision_model"] = D


# ------------------------------------------------------------------ real PDFs through the shipped pipeline stages
def real_pdfs():
    from app.services import features as feat_svc
    from app.services import ml_predict as ml_svc
    from app.services import pdf_extract as pdf_svc
    from app.services import review_synthesis as rev_svc

    files = [("demo_paper.pdf (generated fixture)", ROOT / "data" / "demo" / "demo_paper.pdf")]
    for p in sorted((BATCH / "archived_base_papers").glob("*.pdf")) + sorted((BATCH / "Documentary").glob("*.pdf")):
        files.append((p.name, p))
    rows = []
    ml_svc.predict_decision("warm", "up")
    for label, p in files:
        t = {}
        t0 = time.perf_counter(); doc = pdf_svc.extract_pdf(p); t["extract_ms"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter(); f = feat_svc.extract_features(doc); t["features_ms"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter(); ml = ml_svc.predict_decision(doc["title"], doc["paper_summary"], doc["full_text"]); t["ml_ms"] = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter(); rv = rev_svc.deterministic_review(doc, f); t["review_det_ms"] = (time.perf_counter() - t0) * 1000
        rows.append({"file": label, "size_kb": round(p.stat().st_size / 1024), "pages": doc["page_count"], "words": doc["word_count"],
                     "sections_detected": sorted(doc["sections"].keys()), "references_detected": doc["reference_count"],
                     "title_extracted": doc["title"][:120], "structural_score": f["overall_structural"],
                     "structure_completeness": f["structure_completeness"], "evidence_coverage": f["evidence_coverage"],
                     "method_clarity": f["method_clarity_signal"], "presentation": f["presentation_signal"],
                     "ml_label": ml.get("label"), "ml_confidence": ml.get("confidence"), "ml_probabilities": ml.get("probabilities"),
                     "major_concerns": len(rv["major_concerns"]), "minor_concerns": len(rv["minor_concerns"]),
                     "timings_ms": {k: round(v, 1) for k, v in t.items()}})
    R["real_pdfs"] = rows


# ------------------------------------------------------------------ reviewer matching
def reviewers_ns(extra=0):
    from app.services.seed import DEMO_REVIEWERS
    rs = [SimpleNamespace(id=i + 1, **d) for i, d in enumerate(DEMO_REVIEWERS)]
    n = len(rs)
    for k in range(extra):
        d = DEMO_REVIEWERS[k % len(DEMO_REVIEWERS)]
        rs.append(SimpleNamespace(id=n + k + 1, **{**d, "display_name": f"{d['display_name']} {k}", "current_load": k % 5}))
    return rs


def paper_profile_from(title, text):
    from app.services import features as feat_svc
    from app.services import matching as m
    doc = {"title": title, "paper_summary": text, "full_text": f"{title}\n{text}", "sections": {}, "page_count": 1, "reference_count": 0}
    f = feat_svc.extract_features(doc)
    return m.paper_profile(title, text, f["keywords"], f["methodology_terms"], f["research_topics"]), doc["full_text"]


def eval_matching(mode):
    """mode: 'minilm' (sentence-transformers) or 'tfidf' (the product's offline fallback, frozen after its first call)."""
    from app.config import MATCH_WEIGHTS
    from app.services import embeddings
    from app.services import matching as m
    from eval_data import CONFLICT_INJECT, PROBE

    if mode == "tfidf":
        embeddings._model = None
        embeddings._get_model = lambda: None
        embeddings._FALLBACK_VEC = None
    revs = reviewers_ns()
    names = {r.display_name: r for r in revs}
    base_w = dict(MATCH_WEIGHTS)
    cfgs = {
        "full_hybrid_shipped_weights": dict(base_w),
        "semantic_similarity_only": {**base_w, "expertise_similarity": 1.0, "keyword_score": 0, "method_score": 0, "availability_score": 0, "conflict_penalty": 0.6},
        "lexical_only_keyword_and_method": {**base_w, "expertise_similarity": 0, "keyword_score": 0.5, "method_score": 0.5, "availability_score": 0, "conflict_penalty": 0.6},
        "hybrid_without_availability": {**base_w, "availability_score": 0},
    }
    res = {}
    profiles = [(paper_profile_from(t, x), exp) for t, x, exp in PROBE]
    # warm-up for minilm so timings below are model-warm; for tfidf the first call fits the frozen vocabulary
    for cname, w in cfgs.items():
        MATCH_WEIGHTS.clear(); MATCH_WEIGHTS.update(w)
        top1 = top3 = 0
        rr = []
        for (prof, text), exp in profiles:
            ranked = m.match_reviewers(prof, revs, text[:4000])
            order = [d["display_name"] for d in ranked]
            pos = min(order.index(e) + 1 for e in exp)
            top1 += pos == 1
            top3 += pos <= 3
            rr.append(1 / pos)
        n = len(profiles)
        res[cname] = {"top1": r4(top1 / n), "top3": r4(top3 / n), "mrr": r4(sum(rr) / n), "n": n}
    MATCH_WEIGHTS.clear(); MATCH_WEIGHTS.update(base_w)
    res["random_expectation_top1"] = r4(sum(len(e) / 6 for _, _, e in PROBE) / len(PROBE))
    res["random_expectation_top3"] = r4(np.mean([1 - (6 - len(e)) * (5 - len(e)) * (4 - len(e)) / (6 * 5 * 4) if len(e) < 4 else 1 for _, _, e in PROBE]))

    # per-area top-1 for the shipped weights and the confusing cases
    per, misses = {}, []
    for (prof, text), exp in profiles:
        ranked = m.match_reviewers(prof, revs, text[:4000])
        key = exp[0] if len(exp) == 1 else "cross-area"
        per.setdefault(key, [0, 0])
        per[key][1] += 1
        ok = ranked[0]["display_name"] in exp
        per[key][0] += ok
        if not ok:
            misses.append({"title": prof["text"][:70], "expected": exp, "got": ranked[0]["display_name"], "top_score": ranked[0]["score"],
                           "expected_score": next(d["score"] for d in ranked if d["display_name"] in exp)})
    res["per_area_top1"] = {k: {"correct": v[0], "n": v[1]} for k, v in per.items()}
    res["top1_misses_shipped"] = misses
    # score separation for the shipped config
    seps = []
    for (prof, text), exp in profiles:
        ranked = m.match_reviewers(prof, revs, text[:4000])
        seps.append(ranked[0]["score"] - ranked[1]["score"])
    res["mean_gap_rank1_rank2"] = r4(np.mean(seps))

    # conflict-of-interest handling
    inj = []
    clean = profiles[0]
    for rname, kind, sentence in CONFLICT_INJECT:
        (prof, text), _ = clean
        text2 = text + "\n" + sentence
        before = {d["display_name"]: d for d in m.match_reviewers(prof, revs, text[:4000])}
        after = {d["display_name"]: d for d in m.match_reviewers(prof, revs, text2[:4000])}
        a, b = before[rname], after[rname]
        others = [d for k, d in after.items() if k != rname and d["conflict"]["conflicted"]]
        inj.append({"reviewer": rname, "kind": kind, "detected": bool(b["conflict"]["conflicted"]), "score_before": a["score"], "score_after": b["score"],
                    "rank_before": a["rank"], "rank_after": b["rank"], "other_reviewers_flagged": len(others)})
    fp = 0
    pairs = 0
    for (prof, text), _ in profiles:
        for d in m.match_reviewers(prof, revs, text[:4000]):
            pairs += 1
            fp += bool(d["conflict"]["conflicted"])
    kinds = {}
    for x in inj:
        kinds.setdefault(x["kind"], [0, 0]); kinds[x["kind"]][1] += 1; kinds[x["kind"]][0] += x["detected"]
    res["conflict"] = {"injected": inj, "detected_by_kind": {k: {"detected": v[0], "n": v[1]} for k, v in kinds.items()},
                       "clean_pairs_checked": pairs, "false_flags_on_clean_papers": fp}
    # scaling (warm)
    sc = []
    prof, text = profiles[1][0]
    for extra in (0, 44, 194, 494):
        rv = reviewers_ns(extra)
        m.match_reviewers(prof, rv, text[:4000])
        ts = []
        for _ in range(3):
            t0 = time.perf_counter(); m.match_reviewers(prof, rv, text[:4000]); ts.append((time.perf_counter() - t0) * 1000)
        sc.append({"pool": len(rv), "median_ms": round(st.median(ts), 1)})
    res["scaling_ms"] = sc
    return res


def matching():
    from app.services import embeddings
    out = {}
    try:
        import sentence_transformers  # noqa: F401
        t0 = time.perf_counter()
        mdl = embeddings._get_model()
        load_s = time.perf_counter() - t0
        out["minilm_status"] = {"loaded": mdl is not None, "load_seconds": round(load_s, 1), "error": embeddings._model_error}
        if mdl is not None:
            out["sentence_transformer_minilm"] = eval_matching("minilm")
    except Exception as exc:
        out["minilm_status"] = {"loaded": False, "error": str(exc)[:200]}
    # tfidf fallback (restore original function afterwards is not needed: process ends)
    out["tfidf_fallback"] = eval_matching("tfidf")
    R["matching"] = out


# ------------------------------------------------------------------ literature retrieval latency
def literature():
    from app.services import literature as lit
    rows = []
    for q in ("Retrieval-grounded text classification transformer", "Reviewer assignment expertise matching language models", "Network anomaly detection graph"):
        t0 = time.perf_counter()
        r = lit.retrieve_literature(q, [], [])
        rows.append({"query": q, "status": r["literature_retrieval_status"], "works": len(r.get("works", [])), "ms": round((time.perf_counter() - t0) * 1000), "error": (r.get("error") or "")[:120]})
    R["literature"] = rows


def code_size():
    def loc(globs):
        n = 0
        for g in globs:
            for p in ROOT.glob(g):
                if "node_modules" in p.parts or "__pycache__" in p.parts or "dist" in p.parts or ".venv" in p.parts:
                    continue
                n += len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        return n
    R["loc"] = {"backend_app": loc(["app/**/*.py"]), "scripts_core": loc(["scripts/prepare_dataset.py", "scripts/train_model.py", "scripts/evaluate_model.py", "scripts/make_demo_pdf.py", "scripts/smoke_test.py", "scripts/capture_screens.py"]),
                "tests": loc(["tests/*.py"]), "frontend_src": loc(["frontend/src/**/*.jsx", "frontend/src/**/*.js", "frontend/src/**/*.css"]), "static_fallback_ui": loc(["static/*"])}


if __name__ == "__main__":
    steps = [environment, decision_model, real_pdfs, matching, literature, code_size]
    only = set(sys.argv[1:])
    for fn in steps:
        if only and fn.__name__ not in only:
            continue
        t0 = time.time()
        print("running", fn.__name__, flush=True)
        try:
            fn()
        except Exception as exc:  # keep going: a failed step is recorded, not hidden
            import traceback
            traceback.print_exc()
            R[f"error_{fn.__name__}"] = f"{type(exc).__name__}: {exc}"
        print(f"  done in {time.time() - t0:.1f}s", flush=True)
        path = OUT / ("metrics.json" if not only else "metrics_partial.json")
        path.write_text(json.dumps(R, indent=2), encoding="utf-8")
    print("wrote", path)
