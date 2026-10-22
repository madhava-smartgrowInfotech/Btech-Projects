"""Evaluation: 5x stratified 80/20, metrics, ablations, charts."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import StratifiedShuffleSplit

from app.config import (RANDOM_STATE, TEST_SIZE, N_SPLITS, RETRIEVAL_KS, ALPHA,
                        MODELS_DIR, EVAL_DIR, STATIC_IMG, EMBEDDING_DIM)
from app.ml.preprocessing import build_preprocessor, feature_names
from app.ml.embeddings import embed_texts, l2norm
from app.ml.retrieval import fuse, retrieve_similar
from app.ml.models import get_models

log = logging.getLogger(__name__)
METRIC_KEYS = ["accuracy", "balanced_accuracy", "precision", "recall", "f1"]


def compute_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def run_evaluation(df: pd.DataFrame, dataset_meta: dict) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_IMG.mkdir(parents=True, exist_ok=True)

    texts = df["description"].fillna("").astype(str).tolist()
    y_all = df["label"].to_numpy()
    log.info("Generating text embeddings for %d records...", len(texts))
    text_emb_all, emb_backend = embed_texts(texts)

    sss = StratifiedShuffleSplit(n_splits=N_SPLITS, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    model_names = list(get_models().keys())
    per_model: dict[str, list[dict]] = {m: [] for m in model_names}
    rep_modes = ["structured_only", "text_only", "combined"]
    rep_scores: dict[str, list[float]] = {r: [] for r in rep_modes}
    k_scores: dict[str, list[float]] = {f"k={k}": [] for k in RETRIEVAL_KS}

    last_split = None
    for split_i, (tr, te) in enumerate(sss.split(np.zeros(len(df)), y_all)):
        dtr, dte = df.iloc[tr].reset_index(drop=True), df.iloc[te].reset_index(drop=True)
        ytr, yte = y_all[tr], y_all[te]
        pre = build_preprocessor()
        Str = pre.fit_transform(dtr)
        Ste = pre.transform(dte)
        Ttr = text_emb_all[tr]
        Tte = text_emb_all[te]
        Ftr = fuse(Str, Ttr, ALPHA)
        Fte = fuse(Ste, Tte, ALPHA)
        # standard models on combined fused representation
        for name, model in get_models().items():
            model.fit(Ftr, ytr)
            pred = model.predict(Fte)
            per_model[name].append(compute_metrics(yte, pred))
        # representation ablation with logistic regression
        from sklearn.linear_model import LogisticRegression
        for mode, Xtrm, Xtem in [("structured_only", Str, Ste), ("text_only", l2norm(Ttr), l2norm(Tte)),
                                 ("combined", Ftr, Fte)]:
            lr = LogisticRegression(solver="lbfgs", class_weight="balanced", max_iter=1000, C=1.0)
            lr.fit(Xtrm, ytr)
            rep_scores[mode].append(float(balanced_accuracy_score(yte, lr.predict(Xtem))))
        # retrieval-k similarity-weighted vote balanced accuracy
        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(Fte, Ftr)
        for k in RETRIEVAL_KS:
            preds = []
            for r in range(len(dte)):
                order = np.argsort(-sims[r])
                # balanced pick
                quota_s, quota_f = k // 2, k - k // 2
                picked, wsum, wtot, cs, cf = [], 0.0, 0.0, 0, 0
                for idx in order:
                    lab = int(ytr[idx])
                    if lab == 1 and cs < quota_s:
                        picked.append(idx); cs += 1
                    elif lab == 0 and cf < quota_f:
                        picked.append(idx); cf += 1
                    if len(picked) >= min(k, len(order)):
                        break
                if len(picked) < min(k, len(order)):
                    chosen = set(picked)
                    for idx in order:
                        if int(idx) not in chosen:
                            picked.append(int(idx))
                            if len(picked) >= min(k, len(order)):
                                break
                for i in picked:
                    w = float(max(0.0, sims[r, i]))
                    wtot += w
                    wsum += w * int(ytr[i])
                score = (wsum / wtot) if wtot > 0 else 0.5
                preds.append(1 if score >= 0.5 else 0)
            k_scores[f"k={k}"].append(float(balanced_accuracy_score(yte, np.array(preds))))
        last_split = (dtr, dte, ytr, yte, pre, Ftr, Fte)
        log.info("Split %d done.", split_i + 1)

    # aggregate
    summary = {}
    for name, lst in per_model.items():
        arr = {k: np.array([d[k] for d in lst]) for k in METRIC_KEYS}
        summary[name] = {k: {"mean": float(v.mean()), "std": float(v.std())} for k, v in arr.items()}
        summary[name]["confusion_matrix_mean"] = np.mean([np.array(d["confusion_matrix"]) for d in lst], axis=0).tolist()
        summary[name]["confusion_matrix_last"] = lst[-1]["confusion_matrix"]
    best = max(summary, key=lambda m: summary[m]["balanced_accuracy"]["mean"])

    rep_summary = {k: {"mean": float(np.mean(v)), "std": float(np.std(v))} for k, v in rep_scores.items()}
    k_summary = {k: {"mean": float(np.mean(v)), "std": float(np.std(v))} for k, v in k_scores.items()}

    # retrain best on full data for serving
    from app.ml.preprocessing import prepare_frame  # noqa
    pre_full = build_preprocessor()
    S_full = pre_full.fit_transform(df)
    F_full = fuse(S_full, text_emb_all, ALPHA)
    best_model = get_models()[best]
    # handle fallback name mapping for serving key
    best_model.fit(F_full, y_all)
    joblib.dump(best_model, MODELS_DIR / "best_model.joblib")
    joblib.dump(pre_full, MODELS_DIR / "preprocessor.joblib")
    np.savez_compressed(MODELS_DIR / "train_fused.npz", fused=F_full)
    np.savez_compressed(MODELS_DIR / "text_embeddings.npz", embeddings=text_emb_all)
    df.to_pickle(MODELS_DIR / "train_frame.pkl")
    fnames = feature_names(pre_full)
    mutants = {
        "best_model": best,
        "model_names": model_names,
        "feature_names_structured": fnames,
        "structured_dim": int(S_full.shape[1]),
        "embedding_dim": int(text_emb_all.shape[1]),
        "embedding_backend": emb_backend,
        "alpha": ALPHA,
        "n_train": int(len(df)),
        "class_counts": {"SUCCESS": int((y_all == 1).sum()), "FAILURE": int((y_all == 0).sum())},
        "dataset_meta": dataset_meta,
    }
    (MODELS_DIR / "metadata.json").write_text(json.dumps(mutants, indent=2), encoding="utf-8")
    results = {
        "models": summary,
        "best_model": best,
        "representations": rep_summary,
        "retrieval_k": k_summary,
        "metadata": mutants,
    }
    (EVAL_DIR / "evaluation_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (MODELS_DIR / "evaluation_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    _charts(df, results, last_split)
    return results


def _bar(path, title, labels, values, ylabel, fmt="{:.3f}"):
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(labels, values, color="#2563eb", edgecolor="#1e3a8a")
    plt.title(title, fontsize=13, fontweight="bold")
    plt.ylabel(ylabel)
    plt.xticks(rotation=15, ha="right")
    for b, v in zip(bars, values):
        plt.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(v), ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _charts(df, results, last_split):
    # class distribution
    plt.figure(figsize=(6, 4))
    counts = df["outcome"].value_counts()
    plt.bar(counts.index.tolist(), counts.values.tolist(), color=["#16a34a", "#dc2626"])
    plt.title("Historical outcomes (SUCCESS vs FAILURE)")
    plt.ylabel("Count")
    for i, v in enumerate(counts.values.tolist()):
        plt.text(i, v, str(v), ha="center", va="bottom")
    plt.tight_layout(); plt.savefig(STATIC_IMG / "class_distribution.png", dpi=150); plt.close()

    models = list(results["models"].keys())
    ba = [results["models"][m]["balanced_accuracy"]["mean"] for m in models]
    f1 = [results["models"][m]["f1"]["mean"] for m in models]
    _bar(STATIC_IMG / "model_balanced_accuracy.png", "Model comparison — Balanced Accuracy (5×80/20)",
         models, ba, "Balanced accuracy")
    _bar(STATIC_IMG / "model_f1.png", "Model comparison — F1-score (5×80/20)", models, f1, "F1-score")

    # precision vs recall
    plt.figure(figsize=(6, 5))
    for m in models:
        p = results["models"][m]["precision"]["mean"]
        r = results["models"][m]["recall"]["mean"]
        plt.scatter([r], [p], s=120, label=m)
        plt.text(r, p, f" {m}", fontsize=8, va="center")
    plt.xlabel("Recall (mean)"); plt.ylabel("Precision (mean)")
    plt.title("Precision vs Recall by model"); plt.legend(fontsize=8); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(STATIC_IMG / "precision_recall.png", dpi=150); plt.close()

    # confusion matrix best model (last split)
    cm = np.array(results["models"][results["best_model"]]["confusion_matrix_last"])
    plt.figure(figsize=(5, 4.5))
    plt.imshow(cm, cmap="Blues")
    plt.title(f"Confusion matrix - {results['best_model']}")
    plt.xlabel("Predicted"); plt.ylabel("Actual")
    plt.xticks([0, 1], ["FAILURE", "SUCCESS"]); plt.yticks([0, 1], ["FAILURE", "SUCCESS"])
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(int(cm[i, j])), ha="center", va="center", fontsize=14,
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.tight_layout(); plt.savefig(STATIC_IMG / "confusion_matrix.png", dpi=150); plt.close()

    # retrieval-k comparison
    ks = sorted(results["retrieval_k"].keys(), key=lambda s: int(s.split("=")[1]))
    kv = [results["retrieval_k"][k]["mean"] for k in ks]
    _bar(STATIC_IMG / "retrieval_k.png", "Similar-case vote — Balanced Accuracy by retrieval size (k)",
         ks, kv, "Balanced accuracy")

    # representation comparison
    rep = results["representations"]
    _bar(STATIC_IMG / "representation.png", "Structured vs Text vs Combined (balanced accuracy)",
         list(rep.keys()), [rep[k]["mean"] for k in rep], "Balanced accuracy")

    # industry success rates
    grp = df.groupby("industry_type")["label"].agg(["mean", "count"]).sort_values("mean", ascending=False).head(10)
    plt.figure(figsize=(8, 4.5))
    plt.barh(grp.index.tolist()[::-1], grp["mean"].values.tolist()[::-1], color="#0ea5e9")
    plt.xlabel("Success rate"); plt.title("Success rate by industry (top 10)")
    plt.tight_layout(); plt.savefig(STATIC_IMG / "industry_success.png", dpi=150); plt.close()

    # funding distribution by outcome
    plt.figure(figsize=(7, 4.5))
    for lab, color in [(1, "#16a34a"), (0, "#dc2626")]:
        vals = np.log1p(df.loc[df["label"] == lab, "funding_total_usd"].clip(lower=0).to_numpy())
        plt.hist(vals, bins=25, alpha=0.55, label="SUCCESS" if lab == 1 else "FAILURE", color=color)
    plt.xlabel("log1p(funding_total_usd)"); plt.ylabel("Count")
    plt.title("Funding distribution by outcome"); plt.legend()
    plt.tight_layout(); plt.savefig(STATIC_IMG / "funding_dist.png", dpi=150); plt.close()

    # feature importance (best model if tree-based else logistic coefs)
    try:
        import joblib as jb
        m = jb.load(MODELS_DIR / "best_model.joblib")
        meta = json.loads((MODELS_DIR / "metadata.json").read_text(encoding="utf-8"))
        sdim = meta["structured_dim"]
        fnames = meta["feature_names_structured"]
        if hasattr(m, "feature_importances_"):
            imp = np.asarray(m.feature_importances_, dtype=float)
            simp = imp[:sdim]
            order = np.argsort(-simp)[:15]
            plt.figure(figsize=(8, 5))
            plt.barh([fnames[i] for i in order][::-1], simp[order][::-1], color="#7c3aed")
            plt.title(f"Top structured features — {meta['best_model']} (importance)")
            plt.tight_layout(); plt.savefig(STATIC_IMG / "feature_importance.png", dpi=150); plt.close()
        elif hasattr(m, "coef_"):
            coef = np.abs(np.asarray(m.coef_).ravel())[:sdim]
            order = np.argsort(-coef)[:15]
            plt.figure(figsize=(8, 5))
            plt.barh([fnames[i] for i in order][::-1], coef[order][::-1], color="#7c3aed")
            plt.title("Top structured features — |logistic coefficients|")
            plt.tight_layout(); plt.savefig(STATIC_IMG / "feature_importance.png", dpi=150); plt.close()
    except Exception:
        pass
