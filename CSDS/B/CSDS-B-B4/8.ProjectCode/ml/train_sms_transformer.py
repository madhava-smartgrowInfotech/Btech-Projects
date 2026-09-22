"""M2 comparison - small multilingual transformer for the SMS scam task.

Uses frozen sentence embeddings from paraphrase-multilingual-MiniLM-L12-v2 (118M parameters,
supports English, Hindi and Telugu) with a logistic-regression head, on exactly the same
template-grouped split as ml/train_sms.py. The deployed TF-IDF model is only replaced if the
transformer is clearly better; either way the comparison is recorded under experiments/.
Needs the training extras: setup.bat train  (or pip install -r ml/requirements-train.txt)
Run: venv\\Scripts\\python ml\\train_sms_transformer.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from common import SEED, Experiment, best_f1_threshold, classification_metrics, plot_pr_roc, run_name
from train_sms import group_split, load_indian, load_uci, make_pipeline

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    from sentence_transformers import SentenceTransformer

    exp = Experiment(run_name("m2_sms_transformer"), family="sms_comparison")
    log = exp.log
    rng = np.random.default_rng(SEED)
    uci, ind = load_uci(), load_indian()
    uci_rest, uci_test = train_test_split(uci, test_size=0.25, stratify=uci.label, random_state=SEED)
    uci_train, uci_val = train_test_split(uci_rest, test_size=0.2, stratify=uci_rest.label, random_state=SEED)
    ind_rest, ind_test = group_split(ind, 0.3, rng)
    ind_train, ind_val = group_split(ind_rest, 0.25, rng)
    train = pd.concat([uci_train, ind_train], ignore_index=True)
    val = pd.concat([uci_val, ind_val], ignore_index=True)
    test = pd.concat([uci_test, ind_test], ignore_index=True)
    log.info("same split as train_sms.py: train %d, validation %d, test %d", len(train), len(val), len(test))

    log.info("loading %s (downloaded to the Hugging Face cache on first use)", MODEL_NAME)
    encoder = SentenceTransformer(MODEL_NAME, device="cpu")
    embed = lambda texts: encoder.encode(list(texts), batch_size=64, show_progress_bar=False, normalize_embeddings=True)  # noqa: E731
    e_tr, e_va, e_te = embed(train.text), embed(val.text), embed(test.text)
    head = LogisticRegression(C=4.0, max_iter=4000, class_weight="balanced").fit(e_tr, train.label)
    s_va, s_te = head.predict_proba(e_va)[:, 1], head.predict_proba(e_te)[:, 1]
    thr = best_f1_threshold(val.label.to_numpy(), s_va)

    tfidf = make_pipeline("logreg").fit(train.text, train.label)
    t_va, t_te = tfidf.predict_proba(val.text)[:, 1], tfidf.predict_proba(test.text)[:, 1]
    t_thr = best_f1_threshold(val.label.to_numpy(), t_va)

    results = {
        "MiniLM embeddings + LR": {"validation": classification_metrics(val.label, s_va, thr), "test": classification_metrics(test.label, s_te, thr)},
        "TF-IDF + LR (deployed)": {"validation": classification_metrics(val.label, t_va, t_thr), "test": classification_metrics(test.label, t_te, t_thr)},
    }
    slices = {}
    for lang in ("en", "hi", "te"):
        m = ((test.source == "indian_upi") & (test.language == lang)).to_numpy()
        slices[f"indian_{lang}"] = {
            "MiniLM embeddings + LR": classification_metrics(test.label[m], s_te[m], thr)["f1"],
            "TF-IDF + LR (deployed)": classification_metrics(test.label[m], t_te[m], t_thr)["f1"],
        }
    for name, r in results.items():
        log.info("%-26s test PR-AUC %.4f F1 %.4f", name, r["test"]["pr_auc"], r["test"]["f1"])
    log.info("F1 by language (Indian test templates): %s", slices)
    gain = results["MiniLM embeddings + LR"]["test"]["pr_auc"] - results["TF-IDF + LR (deployed)"]["test"]["pr_auc"]
    decision = (
        "transformer is clearly better - consider deploying it" if gain > 0.02 else
        f"transformer does not clearly beat TF-IDF (PR-AUC difference {gain:+.4f}); TF-IDF stays deployed because it is faster, "
        "fully offline and gives word-level highlights"
    )
    log.info(decision)
    plot_pr_roc({"MiniLM + LR": (test.label.to_numpy(), s_te), "TF-IDF + LR": (test.label.to_numpy(), t_te)}, "M2 comparison (test)", exp.path("pr_curve.png"), exp.path("roc_curve.png"))
    exp.save_metrics(
        {
            "model": "M2 comparison: small multilingual transformer vs TF-IDF",
            "transformer": MODEL_NAME,
            "method": "frozen mean-pooled sentence embeddings (normalised) + logistic regression head",
            "dataset": {"split": "identical to ml/train_sms.py", "rows": {"train": len(train), "validation": len(val), "test": len(test)}},
            "models": results,
            "f1_by_language": slices,
            "decision": decision,
            "plots": ["pr_curve.png", "roc_curve.png"],
        }
    )


if __name__ == "__main__":
    main()
