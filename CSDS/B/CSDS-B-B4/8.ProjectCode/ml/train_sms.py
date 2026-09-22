"""M2 - SMS / payment-note scam classifier.

Data: SMS Spam Collection (UCI, English) + the Indian UPI-scam SMS set (English, Hindi, Telugu).
Split: the UCI part is de-duplicated and split at random (stratified); the Indian part is split
by *template family*, so test messages never share a template with training messages.
Models: TF-IDF (word 1-2 + character 2-5 grams) with Logistic Regression and with a calibrated
Linear SVM; the better one on validation is deployed. Run: venv\\Scripts\\python ml\\train_sms.py
"""
from __future__ import annotations

import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from common import (
    DATA_PROCESSED,
    DATA_RAW,
    MODELS,
    SEED,
    Experiment,
    best_f1_threshold,
    classification_metrics,
    plot_bars,
    plot_calibration,
    plot_confusion,
    plot_pr_roc,
    run_name,
    threshold_for_precision,
    threshold_for_recall,
    write_json,
)
from app.ml.sms import TOKEN_PATTERN, analyze, batch_scores  # noqa: E402


def load_uci() -> pd.DataFrame:
    df = pd.read_csv(DATA_RAW / "sms_spam_collection" / "spam.csv", encoding="latin-1")[["v1", "v2"]]
    df.columns = ["label", "text"]
    df["text"] = df["text"].astype(str).str.strip()
    df = df.drop_duplicates("text").reset_index(drop=True)
    return pd.DataFrame(
        {
            "text": df["text"],
            "label": (df["label"] == "spam").astype(int),
            "category": np.where(df["label"] == "spam", "uci_spam", "uci_ham"),
            "language": "en",
            "script": "latin",
            "template_id": [f"uci-{i}" for i in range(len(df))],
            "kind": "sms",
            "source": "uci",
        }
    )


def load_indian() -> pd.DataFrame:
    df = pd.read_csv(DATA_RAW / "upi_scam_sms" / "upi_scam_sms.csv")
    df["source"] = "indian_upi"
    return df.drop(columns=["id"])


def group_split(df: pd.DataFrame, share: float, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Holds out whole template families, stratified by (label, category, language)."""
    held: set[str] = set()
    for _, grp in df.groupby(["label", "category", "language"]):
        templates = sorted(grp.template_id.unique())
        if len(templates) < 2:
            continue
        k = max(1, int(round(len(templates) * share)))
        held.update(rng.choice(templates, size=k, replace=False))
    mask = df.template_id.isin(held)
    return df[~mask], df[mask]


def make_pipeline(kind: str) -> Pipeline:
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True, lowercase=True, max_features=120000)),
        ]
    )
    if kind == "logreg":
        clf = LogisticRegression(C=8.0, max_iter=4000, class_weight="balanced")
    else:
        clf = CalibratedClassifierCV(LinearSVC(C=0.6, class_weight="balanced"), cv=4, method="sigmoid")
    return Pipeline([("features", features), ("clf", clf)])


def main() -> None:
    exp = Experiment(run_name("m2_sms"), family="sms")
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
    for name, d in [("train", train), ("validation", val), ("test", test)]:
        log.info("%-10s %5d messages  scam %4d  indian %4d  templates %d", name, len(d), d.label.sum(), (d.source == "indian_upi").sum(), d[d.source == "indian_upi"].template_id.nunique())
    assert not set(ind_train.template_id) & set(ind_test.template_id), "template leak"

    # Held-out Indian test texts are what the payment simulator may reuse (never seen in training).
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    ind_test.to_csv(DATA_PROCESSED / "sms_heldout_for_simulation.csv", index=False)

    candidates = {"TF-IDF + Logistic Regression": make_pipeline("logreg"), "TF-IDF + Linear SVM (calibrated)": make_pipeline("svm")}
    results, val_ap = {}, {}
    for name, pipe in candidates.items():
        pipe.fit(train.text, train.label)
        s_val = pipe.predict_proba(val.text)[:, 1]
        thr = best_f1_threshold(val.label.to_numpy(), s_val)
        s_test = pipe.predict_proba(test.text)[:, 1]
        results[name] = {"validation": classification_metrics(val.label, s_val, thr), "test": classification_metrics(test.label, s_test, thr)}
        val_ap[name] = results[name]["validation"]["pr_auc"]
        log.info("%-34s val PR-AUC %.4f F1 %.4f | test PR-AUC %.4f F1 %.4f", name, results[name]["validation"]["pr_auc"], results[name]["validation"]["f1"], results[name]["test"]["pr_auc"], results[name]["test"]["f1"])

    # Deploy the logistic model unless the SVM is clearly better: its per-word weights give the highlighted phrases.
    best = "TF-IDF + Logistic Regression"
    if val_ap["TF-IDF + Linear SVM (calibrated)"] > val_ap[best] + 0.01:
        log.info("SVM is better on validation by >0.01 PR-AUC, but highlighting needs linear word weights; keeping logistic regression")
    pipe = candidates[best]

    # Scam-type classifier for messages the rules cannot type.
    scam_train = ind_train[(ind_train.label == 1) & (ind_train.kind == "sms")]
    scam_test = ind_test[(ind_test.label == 1) & (ind_test.kind == "sms")]
    type_model = Pipeline(
        [
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2), sublinear_tf=True)),
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)),
            ])),
            ("clf", LogisticRegression(C=10.0, max_iter=4000)),
        ]
    )
    type_model.fit(pd.concat([scam_train.text, ind_val[(ind_val.label == 1) & (ind_val.kind == "sms")].text]), pd.concat([scam_train.category, ind_val[(ind_val.label == 1) & (ind_val.kind == "sms")].category]))
    type_pred = type_model.predict(scam_test.text)
    type_metrics = {"n": int(len(scam_test)), "accuracy": round(float(accuracy_score(scam_test.category, type_pred)), 4), "macro_f1": round(float(f1_score(scam_test.category, type_pred, average="macro")), 4)}
    log.info("scam-type classifier on held-out templates: %s", type_metrics)

    # Combined verdict (model + rules): thresholds tuned on validation only.
    bundle = {"pipeline": pipe, "type_model": type_model}
    c_val = batch_scores(bundle, val.text.tolist())
    scam_thr = max(0.5, threshold_for_precision(val.label.to_numpy(), c_val, 0.95))
    susp_thr = min(scam_thr - 0.1, threshold_for_recall(val.label.to_numpy(), c_val, 0.97))
    susp_thr = max(0.25, susp_thr)
    thresholds = {"scam": round(float(scam_thr), 4), "suspicious": round(float(susp_thr), 4)}
    log.info("verdict thresholds from validation: %s", thresholds)
    # Typing as the product does it: rule category first, classifier only when no rule names a type.
    full_bundle = bundle | {"thresholds": thresholds}
    typed = [analyze(full_bundle, t)["scam_type"] for t in scam_test.text]
    pairs = [(p_, c) for p_, c in zip(typed, scam_test.category) if p_ is not None]
    type_metrics["pipeline_rules_then_classifier"] = {
        "typed_share": round(len(pairs) / max(1, len(scam_test)), 4),
        "accuracy_when_typed": round(sum(p_ == c for p_, c in pairs) / max(1, len(pairs)), 4),
    }
    log.info("scam typing in the product pipeline: %s", type_metrics["pipeline_rules_then_classifier"])
    c_test = batch_scores(bundle, test.text.tolist())
    s_test = pipe.predict_proba(test.text)[:, 1]
    combined = {
        "validation": classification_metrics(val.label, c_val, thresholds["scam"]),
        "test": classification_metrics(test.label, c_test, thresholds["scam"]),
        "test_flagged_suspicious_or_scam": classification_metrics(test.label, c_test, thresholds["suspicious"]),
    }
    log.info("combined verdict test: P %.4f R %.4f F1 %.4f PR-AUC %.4f", combined["test"]["precision"], combined["test"]["recall"], combined["test"]["f1"], combined["test"]["pr_auc"])

    # Slices of the test set.
    slices = {}
    t = test.assign(model=s_test, combined=c_test)
    for key, sub in [("uci", t[t.source == "uci"]), ("indian_upi", t[t.source == "indian_upi"])] + [
        (f"indian_{lang}", t[(t.source == "indian_upi") & (t.language == lang)]) for lang in ("en", "hi", "te")
    ] + [("collect_notes", t[t.kind == "collect_note"])]:
        if sub.label.nunique() < 2:
            slices[key] = {"n": int(len(sub)), "note": "single class in this slice", "accuracy_at_scam_threshold": round(float(((sub.combined >= thresholds["scam"]).astype(int) == sub.label).mean()), 4)}
            continue
        slices[key] = {"model_only": classification_metrics(sub.label, sub.model.to_numpy(), results[best]["validation"]["threshold"]), "model_plus_rules": classification_metrics(sub.label, sub.combined.to_numpy(), thresholds["scam"])}
    for k, v in slices.items():
        if "model_plus_rules" in v:
            log.info("slice %-14s n=%4d  model F1 %.4f  model+rules F1 %.4f", k, v["model_plus_rules"]["n"], v["model_only"]["f1"], v["model_plus_rules"]["f1"])

    # Worked examples for the docs (fixed messages, not from the dataset).
    examples = [
        "Your KYC expires today, click link http://kyc-verify-now.top/a77 to update or your account will be blocked.",
        "आपका KYC आज समाप्त हो रहा है, खाता बंद हो जाएगा। तुरंत लिंक पर क्लिक करें",
        "మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే KYC అప్‌డేట్ చేయండి",
        "Rs 450 debited from A/c XX1234 to Lakshmi Stores via UPI. Never share your OTP with anyone.",
        "Hey, are we still meeting for lunch at 1?",
    ]
    worked = [{k: v for k, v in analyze(bundle | {"thresholds": thresholds}, e).items() if k in ("text", "language", "probability", "verdict", "scam_type")} for e in examples]
    for w in worked:
        log.info("example %-10s %.3f %s", w["verdict"], w["probability"], w["text"][:60])

    # Plots.
    plot_pr_roc({"Model only": (test.label.to_numpy(), s_test), "Model + rules": (test.label.to_numpy(), c_test)}, "M2 SMS (test)", exp.path("pr_curve.png"), exp.path("roc_curve.png"))
    plot_confusion(combined["test"]["confusion"], "M2 verdict - test confusion", exp.path("confusion_matrix.png"), labels=("Legitimate", "Scam"))
    plot_calibration(test.label.to_numpy(), s_test, "M2 model", exp.path("calibration.png"))
    f1_by_slice = {k: v["model_plus_rules"]["f1"] for k, v in slices.items() if "model_plus_rules" in v}
    plot_bars(f1_by_slice, "M2 - F1 by test slice (model + rules)", "F1", exp.path("f1_by_slice.png"))
    word_vec = dict(pipe.named_steps["features"].transformer_list)["word"]
    coef = pipe.named_steps["clf"].coef_.ravel()[: len(word_vec.vocabulary_)]
    names = word_vec.get_feature_names_out()
    top = np.argsort(coef)[-20:]
    plot_bars({names[i]: float(coef[i]) for i in top}, "M2 - strongest scam words", "Model weight", exp.path("top_terms.png"))

    version = f"m2-tfidf-lr-{exp.name.split('_')[-1]}"
    bundle = {
        "version": version,
        "pipeline": pipe,
        "type_model": type_model,
        "thresholds": thresholds,
        "metrics": {"test": combined["test"]},
        "run": exp.name,
    }
    joblib.dump(bundle, exp.path("sms_model.joblib"), compress=3)
    shutil.copy(exp.path("sms_model.joblib"), MODELS / "sms_model.joblib")
    write_json(exp.path("worked_examples.json"), worked)

    exp.save_metrics(
        {
            "model": "M2 SMS scam classifier",
            "deployed": best,
            "version": version,
            "dataset": {
                "sources": {
                    "uci": "SMS Spam Collection (UCI / Kaggle mirror), de-duplicated",
                    "indian_upi": "UPI Guardian Indian UPI-scam SMS set (scripts/generate_scam_sms.py, seed 2026)",
                },
                "split": "UCI stratified random 60/15/25; Indian set grouped by template family (30% of templates held out for test, 25% of the rest for validation)",
                "rows": {"train": len(train), "validation": len(val), "test": len(test)},
                "scam_share": {"train": round(float(train.label.mean()), 4), "test": round(float(test.label.mean()), 4)},
                "languages_in_test": test[test.source == "indian_upi"].language.value_counts().to_dict(),
            },
            "models": results,
            "verdict": {"thresholds": thresholds, "rule": "combined = 1 - (1 - model) * (1 - rules); scam >= scam threshold (95% precision on validation), suspicious >= suspicious threshold", **combined},
            "slices": slices,
            "scam_type_classifier": type_metrics,
            "worked_examples": worked,
            "plots": ["pr_curve.png", "roc_curve.png", "confusion_matrix.png", "calibration.png", "f1_by_slice.png", "top_terms.png"],
        }
    )
    log.info("done in %s", exp.directory)


if __name__ == "__main__":
    main()
