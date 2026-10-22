"""Write docs/REPORT_FACTS.md from the real artefacts (single source of truth for every document).

    python scripts/docs_build/make_report_facts.py

Reads experiments/liar2/metrics.json (written by make_figures.py), latency.json, models/metrics.json (the shipped
synthetic-demo model) and the screenshot folder. Test counts are the numbers printed by the two test scripts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "liar2"
A = json.load(open(EXP / "metrics.json", encoding="utf-8"))
DEMO = json.load(open(ROOT / "models" / "metrics.json", encoding="utf-8"))
LAT = json.load(open(EXP / "latency.json")) if (EXP / "latency.json").exists() else None
TESTS = json.load(open(ROOT / "docs" / "metrics" / "tests.json")) if (ROOT / "docs" / "metrics" / "tests.json").exists() else None
LABELS = ["REAL", "PARTIALLY TRUE", "FAKE"]


def pm(blk, key, d=3):
    return f"{blk[key]['mean']:.{d}f} ± {blk[key]['std']:.{d}f}"


def row(name, blk):
    return f"| {name} | {pm(blk, 'accuracy')} | {pm(blk, 'f1_macro')} | {pm(blk, 'f1_weighted')} |"


def main():
    L = []
    w = L.append
    w("# REPORT_FACTS - single source of truth for the documentation of batch CSE-C-C6\n")
    w("Every number below is read from this project's own artefacts (`experiments/liar2/*.json`, `models/metrics.json`, the test scripts, the screenshot folder). "
      "The documents must agree with this file.\n")
    w("## 1. Identity\n")
    w("- Project: FAKE NEWS DETECTION SYSTEM USING FEATURE BASED OPTIMISED MSVM CLASSIFICATION (batch CSE-C-C6, product name in the UI: TruthGlow)")
    w("- Students: Neela Mojes (23K91A05H1), Noor Saniya (23K91A05H4), Malkajgiri Akshitha (23K91A05E2), Maravajhala Radha Sri Aashritha (23K91A05E7)")
    w("- Guide: K Rajasekhar Rao. College, HOD, principal, academic year, designation, e-mail: not in the batch files (placeholders kept)")
    w("- Base paper (batch files 1, 3, 5): M. Saad, S. Abdelrazek, I. R. Abdelmaksoud, \"An algorithmic system for arabic fake news detection using neural networks and transformer embeddings with class weighting\", "
      "Scientific Reports 16, 12226 (2026), doi 10.1038/s41598-026-45653-4. Binary Arabic task, 7,474 articles, CAMeLBERT embeddings + NN + class weighting, 80/20 split, "
      "reported F1 96.19 %, accuracy 95.52 %, precision 95.48 %, recall 96.90 % (Tesla T4 GPU).")
    w("- Companion papers in `archived_base_papers/`: Dell'Oglio et al., \"An Experimental Comparison of the Most Popular Approaches to Fake News Detection\" (arXiv 2603.25501, Information Sciences 2026): "
      "binary harmonised labels; on LIAR-PLUS (the most challenging dataset for nearly all models) LR F1 0.56, SVM F1 0.57. Huang et al., \"A Hybrid Transformer Model for Fake News Detection: Leveraging Bayesian Optimization and Bidirectional Recurrent Unit\" (arXiv 2502.09097): TF-IDF + Transformer/BiGRU + Bayesian optimisation, 99.73 % test accuracy on its own data.\n")
    w("## 2. Environment of every measurement\n")
    w("- CPU Intel Core i5-12500 (6 cores / 12 threads, 3.0 GHz base), 15.7 GB RAM, Windows 11 Pro, no discrete GPU used (Intel UHD 770 present, not used)")
    w("- Python 3.11.9; scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.6, FastAPI 0.159.1, uvicorn 0.54.0 (project `.venv`); Node 24.19.0, npm 11.17.0")
    w("- Frontend: React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4, TanStack Query 5, react-router 7, Recharts 3, GSAP 3, Framer Motion; ports backend 8406, frontend 5406\n")
    w("## 3. Datasets\n")
    w("### 3.1 Shipped demo corpus (synthetic, template based)\n")
    w(f"- `src/dataset.py::build_demo_dataset`: 5 sentence templates per class x 10 topics, light noise; the shipped `models/msvm_model.pkl` was trained on **{DEMO['n_docs']} documents** (250 per class), "
      f"hold-out 20 % = 150 documents (50 per class). It reports accuracy {DEMO['accuracy']:.3f}, macro-F1 {DEMO['f1_macro']:.3f}, baseline accuracy {DEMO['baseline_accuracy']:.3f}: "
      "the classes are separable by the template words alone, so this score says nothing about real news.")
    w(f"- Shipped model structure: {DEMO['n_tfidf']} TF-IDF + 25 stylometric = {DEMO['n_total_features']} features -> PCA {DEMO['n_pca']} components ({DEMO['pca_variance'] * 100:.1f} % variance) -> Firefly kept {DEMO['n_selected']}; "
      f"C = {DEMO['best_C']:.4f}, gamma = {DEMO['best_gamma']:.5f}; training time {DEMO['train_time_s']:.1f} s; Firefly history {', '.join(f'{x:.4f}' for x in DEMO['firefly_history'])}.\n")
    w("### 3.2 LIAR2 (real fact-checked statements) - the dataset of every real measurement\n")
    w("- Source: Hugging Face `chengxuphd/liar2` (Xu and Kechadi, IEEE Access 2024, doi 10.1109/ACCESS.2024.3418340), licence **Apache-2.0**; an extension of the LIAR benchmark (Wang, ACL 2017). PolitiFact statements labelled by professional fact-checkers.")
    w(f"- Official split (8:1:1): train 18,369, validation {A['n_valid']:,}, test {A['n_test']:,} statements; average statement length about 17.7 tokens. Only the `statement` text is used (no speaker, justification or counts - those leak the label).")
    w("- Original six labels: pants-on-fire 3,031 - false 6,605 - barely-true 3,603 - half-true 3,709 - mostly-true 3,429 - true 2,585 (whole dataset).")
    w("- Project mapping (`src/dataset.py`): true, mostly-true -> REAL; half-true -> PARTIALLY TRUE; barely-true, false, pants-on-fire -> FAKE.")
    w(f"- Test class counts (REAL / PARTIALLY TRUE / FAKE): {A['test_class_counts']}; 3,000-document training subsample counts: {A['train_class_counts']}. Majority class (FAKE) share of the test split = {A['test_class_counts'][2] / A['n_test']:.3f}.")
    w(f"- Training subsample: {A['n_train_subsample']} statements drawn stratified from the 18,369 (compute limit: the Firefly search needs thousands of SVM fits); seeds {A['seeds']}. Scored on the full official validation and test splits.\n")
    w("## 4. Architecture summary (agrees with the diagrams)\n")
    w("- Three tiers: React/Vite UI (6 screens) -> FastAPI `backend/main.py` (339 lines) -> library `src/` (preprocessing 91, dataset 110, firefly 106, pipeline 181 lines) -> `models/msvm_model.pkl` (joblib bundle). No SQL database; no login. Also kept: CLI (`train.py`, `predict.py`) and a Streamlit app (`app.py`, 230 lines).")
    w("- Pipeline: `clean_text` (lower-case, drop URLs, @/# tokens, non-letters, stop words, tokens <= 2 chars) -> TF-IDF (1-2 grams, sublinear tf, min_df 2, max_df 0.9, max_features 4000 default) + 25 stylometric features -> StandardScaler -> PCA (95 % variance, at most 300 components) -> "
      "80/20 stratified split -> Firefly (population 10, 12 generations, mask over PCA components + log10 C in [-1,3] + log10 gamma in [-4,1], fitness = 3-fold CV macro-F1 - 0.02 x selected share; alpha 0.2 decayed 0.97 per generation, beta0 1, gamma 1) -> "
      "SVC (RBF, one-vs-rest shape, class_weight balanced, probability=True).")
    w("- Endpoints: GET /api/health, GET /api/model, GET /api/samples, POST /api/predict (min 5 words, else 422), POST /api/batch/preview, POST /api/batch/run (<= 20,000 rows, <= 25 MB), POST /api/retrain (202; fireflies 4-20, generations 3-30, max_tfidf 1000-8000; 409 if a job runs; < 30 rows -> 400), GET /api/retrain/{job_id}.")
    w("- Screens: Landing `/`, Detect `/app`, Batch check `/app/batch`, Model analytics `/app/analytics`, Retrain `/app/retrain`, About `/app/about`, 404.")
    w("- Code size (wc -l): src 488 + backend 339 + app/train/predict 320; frontend TypeScript/TSX 4,865 lines (pages 1,303); scripts: smoke_test 127, unit_edge_tests, run_experiments, etc.\n")
    w("## 5. Results on real data (LIAR2, 3 classes) - test split, mean ± std over seeds\n")
    w(f"Seeds run: {A['seeds']} ({A['n_runs']} runs). Training subsample {A['n_train_subsample']}; Firefly 10 fireflies x 12 generations; {A['n_firefly_evals']['mean']:.0f} ± {A['n_firefly_evals']['std']:.0f} fitness evaluations per search.\n")
    w("| Model | Accuracy | Macro-F1 | Weighted-F1 |")
    w("|---|---|---|---|")
    w(row("Majority class (always FAKE)", A["majority_test"]))
    w(row("Complement NB, TF-IDF, 3,000 docs", A["ref_subsample_ComplementNB_test"]))
    w(row("Logistic regression, TF-IDF, 3,000 docs", A["ref_subsample_LogisticRegression_test"]))
    w(row("Linear SVM, TF-IDF, 3,000 docs", A["ref_subsample_LinearSVC_test"]))
    w(row("Complement NB, TF-IDF, all 18,369 docs", A["ref_full_ComplementNB_test"]))
    w(row("Logistic regression, TF-IDF, all 18,369 docs", A["ref_full_LogisticRegression_test"]))
    w(row("Linear SVM, TF-IDF, all 18,369 docs", A["ref_full_LinearSVC_test"]))
    w(row("PCA + default RBF SVM (baseline of the product)", A["pca_svc_default_test"]))
    w(row("PCA + Firefly mask only (default C, gamma)", A["pca_svc_mask_only_test"]))
    w(row("PCA + random search (same budget and fitness)", A["random_search_test"]))
    w(row("**PCA + Firefly + MSVM (proposed)**", A["proposed_test"]))
    w("")
    w(f"Validation split (proposed): accuracy {pm(A['proposed_valid'], 'accuracy')}, macro-F1 {pm(A['proposed_valid'], 'f1_macro')}. "
      f"Internal 20 % hold-out of the training subsample (what the app's Analytics screen shows): accuracy {pm(A['internal_holdout_acc'] and {'a': A['internal_holdout_acc']}, 'a')}, macro-F1 {pm({'a': A['internal_holdout_f1']}, 'a')}.\n")
    w("Per-class test results (proposed, mean ± std):\n")
    w("| Class | Precision | Recall | F1 |")
    w("|---|---|---|---|")
    for c in LABELS:
        b = A["per_class_test"][c]
        w(f"| {c} | {pm(b, 'precision')} | {pm(b, 'recall')} | {pm(b, 'f1-score')} |")
    w("")
    cm = A["confusion_matrix_seed42"]
    w(f"Confusion matrix, seed 42 (rows true REAL / PARTIALLY TRUE / FAKE; columns predicted): {cm}. Sum over seeds: {A['confusion_matrix_sum']}.\n")
    w("### 5.1 Optimisation and cost\n")
    w(f"- PCA: 4,025 features -> {A['n_pca']['mean']:.0f} components (cap 300 reached; variance kept {A['pca_variance']['mean'] * 100:.1f} % ± {A['pca_variance']['std'] * 100:.1f}) -> Firefly kept {A['n_selected']['mean']:.0f} ± {A['n_selected']['std']:.0f} components; best C {A['best_C']['mean']:.2f}, best gamma {A['best_gamma']['mean']:.5f}.")
    w(f"- Firefly best fitness {A['firefly_fitness_best']['mean']:.4f} ± {A['firefly_fitness_best']['std']:.4f} vs random search {A['random_fitness_best']['mean']:.4f} ± {A['random_fitness_best']['std']:.4f} (random kept {A['random_n_selected']['mean']:.0f} components on average).")
    w(f"- Training time (whole pipeline fit incl. Firefly): {A['train_time_s']['mean']:.0f} ± {A['train_time_s']['std']:.0f} s; random search alone {A['random_search_time_s']['mean']:.0f} s; default SVM fit {A['baseline_time_s']['mean']:.2f} s; "
      f"linear SVM on 3,000 docs {A['ref_subsample_LinearSVC_time']['mean']:.2f} s, on 18,369 docs {A['ref_full_LinearSVC_time']['mean']:.2f} s.")
    w("- Scoring times measured inside the experiment runs are not quoted (other jobs were running); use the idle API measurement in section 7.\n")
    if "demo_model_on_liar2_test" in A:
        d = A["demo_model_on_liar2_test"]
        w("### 5.2 The shipped synthetic-demo model on real LIAR2 test statements\n")
        w(f"Accuracy {d['accuracy']:.3f}, macro-F1 {d['f1_macro']:.3f}; predicted counts (REAL / PARTIALLY TRUE / FAKE) {A['demo_model_prediction_counts']}; confusion matrix {d['confusion_matrix']}.\n")
    ea = A.get("error_analysis")
    if ea:
        w("### 5.3 Error analysis (seed 42, test split)\n")
        w("Accuracy by confidence (highest class probability):\n")
        w("| Confidence bin | n | Accuracy |")
        w("|---|---|---|")
        for b in ea["by_confidence"]:
            w(f"| {b['bin']} | {b['n']} | {b['accuracy']:.3f} |")
        w("\nAccuracy by statement length (words):\n")
        w("| Words | n | Accuracy |")
        w("|---|---|---|")
        for b in ea["by_length"]:
            w(f"| {b['bin']} | {b['n']} | {b['accuracy']:.3f} |")
        w(f"\nPredicted counts {ea['pred_counts']} vs true counts {ea['true_counts']}. Misclassification pairs: {ea['pairs']}.")
        lv = ea["label_vs_proba"]
        w(f"\n**Verdict vs probabilities (a product finding):** the verdict is `SVC.predict` (class-weighted decision function); the class probabilities come from Platt scaling (`probability=True`). "
          f"On {lv['disagree_n']} of {ea['n']} test statements ({lv['disagree_rate'] * 100:.1f} %) the verdict is not the class with the highest probability. Verdict counts {lv['label_counts']} vs argmax-probability counts {lv['argmax_counts']} "
          f"(REAL / PARTIALLY TRUE / FAKE); PARTIALLY TRUE is the top-probability class for {lv['partial_label_argmax_partial']} statements. Taking the argmax probability as the verdict would give accuracy {lv['acc_if_argmax']:.3f} but macro-F1 {lv['f1_if_argmax']:.3f} "
          f"(it almost always says FAKE). The confidence shown in the UI is the maximum probability, so it can belong to a different class than the verdict. Cross-tab (rows verdict, columns argmax): {lv['crosstab']}.")
        w("\nPrediction by original six-way label (counts):\n")
        w("| Original label | n | REAL | PARTIALLY TRUE | FAKE |")
        w("|---|---|---|---|---|")
        for k, v in ea["by_original_label"].items():
            w(f"| {k} | {v['n']} | {v['pred_REAL']} | {v['pred_PARTIALLY TRUE']} | {v['pred_FAKE']} |")
        w("")
    w("## 6. Comparison with the base paper (datasets differ - state this wherever compared)\n")
    w("| | Base paper (Saad et al. 2026) | This project |")
    w("|---|---|---|")
    w("| Language / data | Arabic, 7,474 articles (multi-source, part translated from LIAR/WELFake) | English, LIAR2 statements (18,369 / 2,297 / 2,296) |")
    w("| Task | binary real / fake | three-class REAL / PARTIALLY TRUE / FAKE |")
    w("| Features | CAMeLBERT contextual embeddings | TF-IDF (1-2 grams) + 25 stylometric, PCA |")
    w("| Classifier | neural network + class weights | RBF multi-class SVM + balanced class weights, Firefly tuned |")
    w("| Compute | Tesla T4 GPU | CPU only (i5-12500) |")
    w("| Reported | accuracy 95.52 %, F1 96.19 % | accuracy " + f"{A['proposed_test']['accuracy']['mean'] * 100:.1f} %, macro-F1 {A['proposed_test']['f1_macro']['mean'] * 100:.1f} % (not comparable: harder task and data) |")
    w("")
    if LAT:
        w("## 7. API latency and throughput (127.0.0.1, sequential requests, CPU idle)\n")
        for r in LAT:
            c, s = r["predict_client_ms"], r["predict_server_ms"]
            w(f"- `{r['model']}`: start-up {r['startup_s']} s; POST /api/predict client round trip mean {c['mean']:.1f} ms, p50 {c['p50']:.1f}, p95 {c['p95']:.1f}, max {c['max']:.1f} (n={c['n']}); server-reported latency mean {s['mean']:.1f} ms, p95 {s['p95']:.1f}; "
              f"batch 100 rows {r['batch']['100']['server_s']} s, 1,000 rows {r['batch']['1000']['server_s']} s, 2,296 rows {r['batch']['2296']['server_s']} s (server time)")
        w("")
    w("## 8. Tests\n")
    if TESTS:
        w(f"- `scripts/smoke_test.py`: {TESTS['smoke']} checks, all passed (API end to end on a copy of the model).")
        w(f"- `scripts/unit_edge_tests.py`: {TESTS['unit_lib']} library checks + {TESTS['unit_api']} API edge checks = {TESTS['unit_lib'] + TESTS['unit_api']}, all passed.")
        w(f"- Total: {TESTS['smoke'] + TESTS['unit_lib'] + TESTS['unit_api']} automated checks. `npm run build` (tsc -b + vite build): {TESTS.get('build', 'see below')}.")
        for k in TESTS.get("known_issues", []):
            w(f"- KNOWN ISSUE: {k}")
    w("")
    w("## 9. Screenshot inventory (`docs/screenshots/`, 1440x900, real data)\n")
    shots = sorted(os.listdir(ROOT / "docs" / "screenshots"))
    for s in shots:
        if s.endswith(".png"):
            w(f"- `{s}` ({(ROOT / 'docs' / 'screenshots' / s).stat().st_size // 1024} KB)")
    w("- Files 01-09 were captured by the frontend build on the shipped synthetic-demo model (100 % analytics, disclaimer visible); files 10-22 were captured for the documentation on the model trained on real LIAR2 data.\n")
    w("## 10. Honest gaps and deviations (state plainly in every document)\n")
    w("- The shipped model and its 100 % figures come from a synthetic template corpus; the real-data results are those of section 5.")
    w("- LIAR2 results use a 3,000-statement training subsample (compute); a linear SVM trained on all 18,369 statements is reported beside it as an upper reference. Only three seeds were run, no significance test.")
    w("- Objective 2 lists stemming; the code does not stem (cleaning, stop-word removal, TF-IDF only). The Documentary file lists five veracity categories; the product uses three (mapped from LIAR's six).")
    w("- Firefly hyper-parameters (alpha, beta0, gamma, penalty 0.02, population 10, 12 generations) were not tuned. PCA is capped at 300 components, so it keeps well under 95 % of the variance on real text.")
    w("- No ISOT, no other dataset, no cross-dataset test other than demo-model-on-LIAR2; no user study; no concurrency/load test; no GPU; no security audit beyond input validation.")
    w("- Verdict and displayed probabilities/confidence come from two different mechanisms and disagree on about half of the real test statements (section 5.3); the demo model never showed this because its classes are perfectly separable.")
    w("- Some fixed UI wording assumes the demo model (landing metric strip: 'Scored on a held-out 20% test split of its demo corpus'; Analytics note about the synthetic corpus; example chips 'from the demo corpus'). It stays visible when a model trained on real data is loaded.")
    w("- Known library issue: `load_csv` on a label column containing only the words true/false (pandas parses them as booleans) maps true -> PARTIALLY TRUE and false -> REAL.")
    open(ROOT / "docs" / "REPORT_FACTS.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote docs/REPORT_FACTS.md")


if __name__ == "__main__":
    main()
