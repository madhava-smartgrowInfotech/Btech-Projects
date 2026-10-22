"""Chapter 8: Results and Output Screens (also document 14). Every number is built from facts.py (experiments/liar2/metrics.json, latency.json)."""

import os

import pandas as pd

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import cite

A = F.A
PROP = A["proposed_test"]
DEF = A["pca_svc_default_test"]
RND = A["random_search_test"]
MSK = A["pca_svc_mask_only_test"]
MAJ = A["majority_test"]
LR_FULL = A["ref_full_LogisticRegression_test"]
LR_SUB = A["ref_subsample_LogisticRegression_test"]
SVM_FULL = A["ref_full_LinearSVC_test"]
SVM_SUB = A["ref_subsample_LinearSVC_test"]
NB_FULL = A["ref_full_ComplementNB_test"]
NB_SUB = A["ref_subsample_ComplementNB_test"]
LAT_L, LAT_D = F.LAT[0], F.LAT[1]
CM42 = A["confusion_matrix_seed42"]


def m(blk, key="f1_macro", d=3):
    return f"{blk[key]['mean']:.{d}f}"


def pmv(blk, key="f1_macro", d=3):
    return F.pm(blk, key, d)


def shot_pair(left, right, cap_l, cap_r, width=3.0):
    return PAIR([(F.shot(left), cap_l), (F.shot(right), cap_r)], width)


def screen(name, caption, base=5.4, max_h=3.4):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def _examples():
    df = pd.read_csv(os.path.join(F.EXP, "test_predictions_seed42.csv"))

    def row(start):
        r = df[df["statement"].str.startswith(start)].iloc[0]
        return r

    picks = [("Says Milken Institute rated San Antonio", "success"), ("Expanding Medicaid would require borrowing", "success"), ("Photo shows Ron DeSantis holding", "success"),
             ("Says Melania Trump lied under oath", "failure"), ("It's highly unusual to have a Supreme Court confirmation", "failure"),
             ("Pritzker and Madigan want to change the constitution", "failure"), ("The signers of the Declaration of Independence", "failure")]
    rows = []
    for s, kind in picks:
        r = row(s)
        text = r["statement"] if len(r["statement"]) < 125 else r["statement"][:122] + "..."
        rows.append([text, r["true"], r["pred"], f"{r['p_real']:.2f} / {r['p_partial']:.2f} / {r['p_fake']:.2f}", "correct" if kind == "success" else "wrong"])
    return rows


def _seed_rows():
    rows = []
    for i, s in enumerate(A["seeds"]):
        rows.append([str(s), f"{A['proposed_test']['f1_macro']['values'][i]:.3f}", f"{A['pca_svc_default_test']['f1_macro']['values'][i]:.3f}",
                     f"{A['random_search_test']['f1_macro']['values'][i]:.3f}", f"{A['firefly_fitness_best']['values'][i]:.4f}", f"{A['random_fitness_best']['values'][i]:.4f}",
                     str(A["n_selected"]["values"][i])])
    return rows


def blocks():
    diffs = [a - b for a, b in zip(PROP["f1_macro"]["values"], DEF["f1_macro"]["values"])]
    n_test = F.NTEST
    pc = A["per_class_test"]
    lv = F.LV
    ea = F.EA
    conf_rows = [[b["bin"].replace("[", "").replace(")", "").replace(", ", " to "), str(b["n"]), f"{b['accuracy']:.3f}"] for b in ea["by_confidence"]]
    len_rows = [[b["bin"], str(b["n"]), f"{b['accuracy']:.3f}"] for b in ea["by_length"]]
    six_rows = [[k, str(v["n"]), str(v["pred_REAL"]), str(v["pred_PARTIALLY TRUE"]), str(v["pred_FAKE"])] for k, v in ea["by_original_label"].items()]

    out = [
        H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
        P("This chapter shows the system running on real data and measures it. Section 8.1 gives the set-up, 8.2 the output screens, 8.3 the measurements, 8.4 the comparison with the base paper, 8.5 sample outputs with success and failure analysis, 8.6 the limits of the results and 8.7 the objectives against the outcomes. "
          "The results are modest, and where they fall short of the aims of the project the text says so."),
        H2("8.1 Experimental set-up"),
        P(f"The product ships a model trained on a synthetic template corpus (750 documents). Its own score of {F.f3(F.DEMO['f1_macro'])} macro-F1 only shows that the three template families are easy to tell apart, so every real measurement in this report "
          f"uses LIAR2 {cite('liar2')}, an extension of the LIAR benchmark {cite('liar')} of short fact-checked statements, licensed under Apache-2.0. LIAR2 has an official split of {F.NTRAIN_FULL:,} training, {F.NVALID:,} validation and {F.NTEST:,} test statements. "
          "Its six truthfulness labels are mapped to the three classes of the product with the mapping that `src/dataset.py` already contains: true and mostly-true become REAL, half-true becomes PARTIALLY TRUE, and barely-true, false and pants-on-fire become FAKE. "
          f"Only the statement text is used; the speaker, the justification and the speaker's past counts are left out because they would leak the label. The test split then holds {A['test_class_counts'][0]} REAL, {A['test_class_counts'][1]} PARTIALLY TRUE and {A['test_class_counts'][2]} FAKE statements, so a classifier that always says FAKE "
          f"reaches an accuracy of {m(MAJ, 'accuracy')} and a macro-F1 of only {m(MAJ)}."),
        P(f"The whole pipeline, as implemented in `src/pipeline.py`, was fitted on a stratified subsample of {F.NTRAIN:,} training statements with 10 fireflies and 12 generations (the defaults of `train.py`), because the search needs several hundred SVM fits and the machine is CPU-only. "
          f"Three seeds ({', '.join(str(s) for s in F.SEEDS)}) change the subsample, the 80/20 split inside the pipeline and the Firefly random numbers. Every model is scored on the full official validation and test splits. "
          f"The measurements ran on {F.HARDWARE}; the software was {F.SOFTWARE}."),
        P("The main metric is macro-F1, the unweighted mean of the three per-class F1 scores, because a classifier that ignores the two minority classes can have a respectable accuracy and a useless macro-F1; accuracy, precision, recall and the confusion matrix are reported beside it. "
          "The models compared are the majority class, Complement NB, logistic regression and linear SVM on TF-IDF, the product's own unoptimised baseline (PCA with a default RBF SVM), a Firefly mask-only variant, random search with the same fitness and number of evaluations as Firefly, and the proposed pipeline."),

        H2("8.2 Output screens"),
        P("All screens are real captures (1440 x 900) of the TruthGlow web application, served by the FastAPI backend and the Vite frontend. The backend loaded the model trained on LIAR2 (3,000 statements, seed 42); the statements typed into Detect and uploaded to Batch check are real LIAR2 test statements "
          "chosen by `scripts/capture_docs_screens.py` (the most confident correct prediction of each class, 14 to 45 words), and Retrain was driven with a 600-row CSV from the LIAR2 training split, on a copy of the model file."),
        H3("8.2.1 Landing page and About"),
        PAIR([(F.shot("10_liar2_landing.png"), "Landing page: tagline, live-demo card (clickbait example FAKE, 69.9 %) and the technique strip."),
              (F.shot("19_liar2_about.png"), "About: the four pipeline steps, the three classes and the loaded model (3,000 documents, 4025 to 300 to 154 features, 48.67 % / 0.4134).")], 2.8),
        P("The landing page presents the product as a screening aid. Its \"loaded model, by the numbers\" strip is fixed wording written for the demo model and is inaccurate when a real-data model is loaded (limitation L10). The About page reads the loaded model's facts from the API."),
        H3("8.2.2 Detect: verdicts on real statements"),
        P("Detect takes an optional headline and the text (at least five words) and returns the verdict, confidence, three class probabilities, latency and cue words. The captures below show the result for one statement of each class; the statement is quoted in each caption."),
        PAIR([(F.shot("11_liar2_detect_fake.png"), "FAKE-labelled statement (\"Photo shows Ron DeSantis holding a shirt that says, 'Your mask is as useless as Joe Biden.'\"): verdict FAKE, 83.8 %, 26 ms."),
              (F.shot("12_liar2_detect_real.png"), "REAL-labelled statement (\"In 1935, more than 50% of the elderly population lived in poverty. Today that poverty rate stands officially at 9.4%.\"): verdict REAL, about 54 %, 174 ms.")], 2.8),
        PAIR([(F.shot("13_liar2_detect_partial.png"), "Half-true statement about New Hampshire's unemployment rate: verdict PARTIALLY TRUE shown with 47.2 % confidence, while the tallest bar is FAKE."),
              (F.shot("14_liar2_detect_miss.png"), "False statement about the signers of the Declaration of Independence: verdict REAL, 53.4 % - a wrong answer.")], 2.8),
        P(f"The first two verdicts agree with their labels and probabilities, with modest margins unlike the 99 % of the demo corpus. The third capture shows a real defect: the verdict comes from the class-weighted decision function and the bars from Platt scaling, so the confidence belongs to FAKE; "
          f"on the {n_test:,} test statements the two disagree {lv['disagree_n']:,} times ({lv['disagree_rate'] * 100:.1f} %) (Section 8.3.5). The fourth is the central limit of the approach: a neutral-sounding historical claim cannot be checked, because the model sees only vocabulary, word pairs and style. "
          "The cue panels usually read \"None found\" because the cue lists are short fixed word lists."),
        H3("8.2.3 Batch check"),
        PAIR([(F.shot("15_liar2_batch_preview.png"), "Batch check after choosing liar2_test_sample.csv: 120 rows, 3 columns, first 10 rows previewed."),
              (F.shot("16_liar2_batch_results.png"), "Batch results: 120 articles screened (REAL 44, PARTIALLY TRUE 24, FAKE 52), distribution chart and results table.")], 2.8),
        P(f"The upload accepts a CSV of up to 25 MB, guesses the text column (statement) and shows ten rows; results can be downloaded with a verdict and confidence per row. The 40 statements of each class in the file were predicted as 44, 24 and 52, so PARTIALLY TRUE is under-predicted. "
          f"The 6.28 s on screen was measured while the experiments used every CPU core; with an idle CPU 100 rows took {LAT_L['batch']['100']['server_s']:.2f} s and all {n_test:,} test statements {LAT_L['batch']['2296']['server_s']:.1f} s (Section 8.3.6)."),
        H3("8.2.4 Model analytics"),
        PAIR([(F.shot("17_liar2_analytics.png"), "Analytics (top): accuracy 48.67 %, macro-F1 0.4134, features 4025 to 154, 442.3 s; PCA keeps 29.1 % of the variance; gain from optimisation -2.67 pp."),
              (F.shot("18_liar2_analytics_charts.png"), "Analytics (charts): confusion matrix of the 600-statement hold-out, Firefly curve (0.392 to 0.422), classification report, baseline against proposed.")], 2.8),
        P("Every number is read live from the loaded model, on its own 20 % hold-out (600 of the 3,000 statements): confusion matrix [[65, 20, 72], [26, 24, 47], [92, 51, 203]]; F1 0.382 (REAL), 0.250 (PARTIALLY TRUE); the default SVM (51.33 %, macro-F1 0.4215) was slightly better than the optimised one. "
          "The official test-split results are in Section 8.3."),
        H3("8.2.5 Retrain"),
        PAIR([(F.shot("20_liar2_retrain.png"), "Retrain: liar2_train_600.csv attached (71 KB), 4 fireflies, 3 generations, 4,000 TF-IDF features."),
              (F.shot("22_liar2_retrain_done.png"), "Retrain finished: 600 documents, PCA 300 to 147 components, accuracy 42.50 %, macro-F1 0.4113, 199 s.")], 2.8),
        P("A labelled CSV (label as REAL, PARTIALLY TRUE, FAKE, 0 to 2 or LIAR names) and a Firefly budget start a background job; the page polls it and, when it ends, the new model replaces the loaded one without a restart. The confirmation dialog captured while the job starts (file 21) is in Appendix C. "
          "The small run scored lower than the 3,000-statement model, as expected from five times less data."),
        H3("8.2.6 Captures of the shipped demo model"),
        P("Files 01 to 09 in `docs/screenshots/` show the same screens on the shipped demo model; they are in Appendix C. They report 99 to 100 % confidence on every example and a perfect confusion matrix (50, 50, 50), because the three classes are generated from three families of sentence templates."),

        H2("8.3 Model performance"),
        H3("8.3.1 Headline results"),
        P(f"The table gives accuracy, macro-F1 and weighted-F1 of every model on the {n_test:,} test statements as mean ± standard deviation over the three seeds (models trained on all {F.NTRAIN_FULL:,} statements have no spread)."),
        TAB("Test-split scores on LIAR2, three classes (mean ± standard deviation over 3 seeds)", ["Model", "Accuracy", "Macro-F1", "Weighted-F1"],
            [["Majority class (always FAKE)", pmv(MAJ, "accuracy"), pmv(MAJ), pmv(MAJ, "f1_weighted")],
             [f"Complement NB, TF-IDF, {F.NTRAIN:,} statements", pmv(NB_SUB, "accuracy"), pmv(NB_SUB), pmv(NB_SUB, "f1_weighted")],
             [f"Logistic regression, TF-IDF, {F.NTRAIN:,}", pmv(LR_SUB, "accuracy"), pmv(LR_SUB), pmv(LR_SUB, "f1_weighted")],
             [f"Linear SVM, TF-IDF, {F.NTRAIN:,}", pmv(SVM_SUB, "accuracy"), pmv(SVM_SUB), pmv(SVM_SUB, "f1_weighted")],
             [f"Complement NB, TF-IDF, all {F.NTRAIN_FULL:,}", pmv(NB_FULL, "accuracy"), pmv(NB_FULL), pmv(NB_FULL, "f1_weighted")],
             [f"Logistic regression, TF-IDF, all {F.NTRAIN_FULL:,}", pmv(LR_FULL, "accuracy"), pmv(LR_FULL), pmv(LR_FULL, "f1_weighted")],
             [f"Linear SVM, TF-IDF, all {F.NTRAIN_FULL:,}", pmv(SVM_FULL, "accuracy"), pmv(SVM_FULL), pmv(SVM_FULL, "f1_weighted")],
             ["PCA + default RBF SVM", pmv(DEF, "accuracy"), pmv(DEF), pmv(DEF, "f1_weighted")],
             ["PCA + Firefly mask only", pmv(MSK, "accuracy"), pmv(MSK), pmv(MSK, "f1_weighted")],
             ["PCA + random search (same budget)", pmv(RND, "accuracy"), pmv(RND), pmv(RND, "f1_weighted")],
             ["PCA + Firefly + MSVM (proposed)", pmv(PROP, "accuracy"), pmv(PROP), pmv(PROP, "f1_weighted")]],
            widths=[3.0, 1.1, 1.1, 1.1], align=["l", "c", "c", "c"], size=9.5),
        FIG(F.fig("f01_model_comparison.png"), "Test accuracy (light bars) and macro-F1 (dark bars) of the proposed pipeline and its comparisons; whiskers: standard deviation over seeds.", 4.8),
        P(f"The proposed pipeline reaches a macro-F1 of {pmv(PROP)} and an accuracy of {pmv(PROP, 'accuracy')}; on the validation split it scores {pmv(A['proposed_valid'], 'accuracy')} and {pmv(A['proposed_valid'])}, so the test split is not an unlucky draw. "
          f"Every real model beats the majority baseline on macro-F1 ({m(MAJ)}), so the features carry signal. Accuracy is a different story: the balanced class weights deliberately give up accuracy on the large FAKE class, so the proposed pipeline stays below the majority baseline's {m(MAJ, 'accuracy')}. "
          f"The plain TF-IDF linear models are at least as good as the proposed pipeline: logistic regression on all statements reaches {m(LR_FULL)} macro-F1 and linear SVM {m(SVM_FULL)}."),
        H3("8.3.2 Per-class results, confusion matrix and confidence"),
        TAB("Per-class test results of the proposed pipeline (mean ± std over 3 seeds)", ["Class", "Precision", "Recall", "F1", "Test statements"],
            [[c, F.pm(pc[c], "precision"), F.pm(pc[c], "recall"), F.pm(pc[c], "f1-score"), str(A["test_class_counts"][i])] for i, c in enumerate(F.CLASSES)],
            widths=[1.6, 1.3, 1.3, 1.3, 1.1], align=["l", "c", "c", "c", "c"], size=9.5),
        PAIR([(F.fig("f03_confusion_matrix.png"), "Confusion matrix of the test split, seed 42."),
              (F.fig("f06_confidence_bins.png"), "Accuracy by confidence bin (seed 42).")], 2.8),
        P(f"FAKE is recognised best (F1 {pc['FAKE']['f1-score']['mean']:.3f}), REAL is a weak second ({pc['REAL']['f1-score']['mean']:.3f}) and PARTIALLY TRUE is near chance (F1 {pc['PARTIALLY TRUE']['f1-score']['mean']:.3f}). "
          f"In the seed-42 matrix only {CM42[1][1]} of {sum(CM42[1])} half-true statements are labelled PARTIALLY TRUE; {CM42[1][0]} go to REAL and {CM42[1][2]} to FAKE, and the largest error block is FAKE called REAL ({CM42[2][0]}). "
          f"The predicted class changes only gently along the original truthfulness scale: {ea['by_original_label']['pants-on-fire']['pred_FAKE']} of {ea['by_original_label']['pants-on-fire']['n']} pants-on-fire statements are called FAKE, but so are {ea['by_original_label']['true']['pred_FAKE']} of {ea['by_original_label']['true']['n']} true ones. "
          f"Confidence does carry information: accuracy rises from {ea['by_confidence'][1]['accuracy']:.2f} in the 0.4 to 0.5 bin to {ea['by_confidence'][3]['accuracy']:.2f} and {ea['by_confidence'][4]['accuracy']:.2f} in the 0.6 to 0.7 and 0.7 to 0.8 bins, but about two thirds of the statements fall in the two lowest bins. "
          "Accuracy also falls with statement length, from 0.56 below ten words to 0.43 for thirty words or more."),
        H3("8.3.3 What the Firefly search did, and what it cost"),
        P(f"Each search evaluates about {A['n_firefly_evals']['mean']:.0f} candidates (mask, C, gamma) by 3-fold cross-validation, keeps {A['n_selected']['mean']:.0f} ± {A['n_selected']['std']:.0f} of 300 components and settles on C around {A['best_C']['mean']:.1f} and gamma around {A['best_gamma']['mean']:.4f}. "
          f"The curves converge within about ten generations and the swarm beats random search on the training fitness ({A['firefly_fitness_best']['mean']:.4f} against {A['random_fitness_best']['mean']:.4f}), but the advantage disappears on the test split:"),
        TAB("Firefly search against its baselines, per seed (test macro-F1 and training-split fitness)", ["Seed", "Firefly + MSVM", "PCA + default SVM", "Random search", "Firefly fitness", "Random fitness", "Components kept"], _seed_rows(),
            widths=[0.6, 1.0, 1.1, 1.0, 1.0, 1.0, 0.9], align=["c"] * 7, size=9.5),
        PAIR([(F.fig("f02_firefly_convergence.png"), "Best Firefly fitness per generation; dotted lines: random search with the same budget."),
              (F.fig("f07_training_time.png"), "Training time on a log scale (CPU only).")], 2.8),
        P(f"The proposed minus default-SVM difference is {diffs[0]:+.3f}, {diffs[1]:+.3f} and {diffs[2]:+.3f} macro-F1 for the three seeds (mean {sum(diffs) / 3:+.3f}); against random search the means are {m(PROP)} and {m(RND)}. With three seeds and a standard deviation of about 0.01 these differences are within noise and the sign is not stable; "
          f"selecting components alone is worse than either ({m(MSK)}). The Firefly algorithm tuned the fitness it was given, but a 3-fold macro-F1 on a few thousand noisy statements did not generalise better than an untuned SVM. One cause lies upstream: the PCA cap of 300 components keeps only {A['pca_variance']['mean'] * 100:.1f} % of the variance on real text, against 95 % with 136 components on the demo corpus. "
          f"Cost matters as much as score here: one fit took {A['train_time_s']['mean']:.0f} ± {A['train_time_s']['std']:.0f} s (random search {A['random_search_time_s']['mean']:.0f} s), the default SVM fit {A['baseline_time_s']['mean']:.2f} s, and logistic regression and linear SVM on all statements {A['ref_full_LogisticRegression_time']['mean']:.2f} s and {A['ref_full_LinearSVC_time']['mean']:.2f} s, "
          f"so the optimised pipeline is about {A['train_time_s']['mean'] / A['ref_full_LinearSVC_time']['mean']:.0f} times more expensive to train than a linear SVM that scores better."),
        H3("8.3.4 The shipped demo model on real statements"),
        P(f"Applied to the same {n_test:,} test statements, the shipped model reaches an accuracy of {A['demo_model_on_liar2_test']['accuracy']:.3f} and a macro-F1 of {A['demo_model_on_liar2_test']['f1_macro']:.3f}, worse than always answering FAKE, and calls {A['demo_model_prediction_counts'][1]:,} statements PARTIALLY TRUE because that template class resembles hedged, neutral language."),
        FIG(F.fig("f05_demo_vs_real.png"), "Left: macro-F1 of the demo model on its synthetic hold-out and on real LIAR2 statements, and of the LIAR2 model. Right: what the demo model predicts on the real test split.", 4.6),
        H3("8.3.5 Verdict against probabilities"),
        P(f"The verdict is the SVM's predicted class (class-weighted decision function); the probabilities come from Platt scaling {cite('platt')} fitted by internal cross-validation, which ignores the class weights. On the {n_test:,} seed-42 test statements the verdict is not the most probable class {lv['disagree_n']:,} times ({lv['disagree_rate'] * 100:.1f} %). "
          f"The highest probability is FAKE for {lv['argmax_counts'][2]:,} statements, REAL for {lv['argmax_counts'][0]} and PARTIALLY TRUE for none, whereas the verdicts number {lv['label_counts'][0]}, {lv['label_counts'][1]} and {lv['label_counts'][2]:,}. Using the highest probability as the verdict would give an accuracy of {lv['acc_if_argmax']:.3f} but a macro-F1 of {lv['f1_if_argmax']:.3f}, because it almost always answers FAKE. "
          "The confidence in the interface is the highest probability, so it can belong to another class than the verdict."),
        FIG(F.fig("f11_label_vs_probability.png"), "Test statements per class for the verdict shown (SVC.predict) and for the class with the highest Platt probability.", 3.8),
        H3("8.3.6 Response time, throughput and tests"),
        P(f"The API was timed on 127.0.0.1 with the CPU idle (300 sequential requests after ten warm-up calls). The server-side time of POST /api/predict averaged {LAT_L['predict_server_ms']['mean']:.1f} ms (95th percentile {LAT_L['predict_server_ms']['p95']:.1f} ms) and the client round trip {LAT_L['predict_client_ms']['mean']:.1f} ms; "
          f"{n_test:,} statements took {LAT_L['batch']['2296']['server_s']:.1f} s. {F.N_SMOKE} API smoke checks and {F.N_UNIT_LIB + F.N_UNIT_API} unit and edge-case checks ({F.N_TESTS} in all) pass (Chapter 7); they show correct behaviour, not accuracy."),
        TAB("API response time and throughput (127.0.0.1, CPU idle, 300 sequential requests)", ["Measure", "LIAR2 model (3,000 documents)", "Shipped demo model (750 documents)"],
            [["Start-up until /api/health answers", f"{LAT_L['startup_s']:.1f} s", f"{LAT_D['startup_s']:.1f} s"],
             ["/api/predict, server time, mean / p95", f"{LAT_L['predict_server_ms']['mean']:.1f} / {LAT_L['predict_server_ms']['p95']:.1f} ms", f"{LAT_D['predict_server_ms']['mean']:.1f} / {LAT_D['predict_server_ms']['p95']:.1f} ms"],
             ["/api/predict, client round trip, mean / p95 / max", f"{LAT_L['predict_client_ms']['mean']:.1f} / {LAT_L['predict_client_ms']['p95']:.1f} / {LAT_L['predict_client_ms']['max']:.1f} ms", f"{LAT_D['predict_client_ms']['mean']:.1f} / {LAT_D['predict_client_ms']['p95']:.1f} / {LAT_D['predict_client_ms']['max']:.1f} ms"],
             ["/api/batch/run, 100 / 1,000 rows", f"{LAT_L['batch']['100']['server_s']:.2f} / {LAT_L['batch']['1000']['server_s']:.2f} s", f"{LAT_D['batch']['100']['server_s']:.2f} / {LAT_D['batch']['1000']['server_s']:.2f} s"],
             [f"/api/batch/run, {n_test:,} rows", f"{LAT_L['batch']['2296']['server_s']:.2f} s", f"{LAT_D['batch']['2296']['server_s']:.2f} s"]],
            widths=[3.0, 1.8, 1.8], align=["l", "c", "c"], size=9.5),

        H2("8.4 Comparison with the base paper"),
        P(f"The base paper {cite('base')} combines CAMeLBERT embeddings, a neural network and class weighting for binary Arabic fake news detection and reports an accuracy of 95.52 % and an F1 of 96.19 %. These numbers cannot be compared with those of this project, as the table shows."),
        TAB("The base paper and this project: what differs", ["Aspect", "Base paper (Saad et al. 2026)", "This project"],
            [["Language and data", "Arabic; 7,474 articles, part translated from LIAR and WELFake; 80/20 split", f"English; LIAR2 statements ({F.NTRAIN_FULL:,} / {F.NVALID:,} / {F.NTEST:,}); official split"],
             ["Task and text", "Binary real/fake; news articles", "Three classes (REAL, PARTIALLY TRUE, FAKE); statements of about 18 words"],
             ["Features and classifier", "CAMeLBERT embeddings; neural network with class weights", "TF-IDF + 25 stylometric features, PCA; Firefly-tuned RBF SVM with balanced weights"],
             ["Compute", "Tesla T4 GPU", "CPU only"],
             ["Reported result", "Accuracy 95.52 %, F1 96.19 %", f"Accuracy {PROP['accuracy']['mean'] * 100:.1f} %, macro-F1 {PROP['f1_macro']['mean'] * 100:.1f} % (three classes)"]],
            widths=[1.4, 2.7, 2.6], align=["l", "l", "l"], size=9.5),
        P(f"A binary Arabic collection with high labelling agreement (Fleiss' kappa 0.80) is an easier problem than three-way grading of one-sentence political claims. The comparison study {cite('compare')} gives the scale for LIAR-style data: on LIAR-PLUS, collapsed to binary, logistic regression and an SVM reach an F1 of 0.56 and 0.57, and it is the hardest of ten datasets for nearly all models. "
          "A three-class macro-F1 of 0.43 to 0.50 is therefore not out of line, but not a number to set beside 96 %. Three lessons carry over: reporting several metrics together (here with macro-F1 and the confusion matrix, which matter more with three unbalanced classes); a TF-IDF baseline before anything fancier (the role of the linear models here); and class weighting against imbalance (visible here as accuracy below the majority baseline with macro-F1 far above it). "
          "Whether contextual embeddings, which gave the base paper about three points of accuracy over TF-IDF, would lift the LIAR2 scores was not tested."),

        H2("8.5 Sample inputs and outputs, success and failure analysis"),
        P("The table lists real test statements with the true class, the verdict and the probabilities for REAL, PARTIALLY TRUE and FAKE: three correct and four wrong cases from `experiments/liar2/test_predictions_seed42.csv`."),
        TAB("Real test statements and the model's output (seed 42)", ["Statement", "True class", "Verdict", "Probabilities R / PT / F", "Result"], _examples(),
            widths=[2.8, 0.9, 0.9, 1.3, 0.6], align=["l", "c", "c", "c", "c"], size=8.5),
        P("The PARTIALLY TRUE verdict for the Medicaid statement sits beside a FAKE probability of about 0.66. The wrong cases are of different kinds: a true claim written in an accusatory style (Melania Trump), a half-true statement phrased as historical fact (the Supreme Court), and two false claims worded unremarkably (the jobs tax, the Declaration of Independence)."),
        H3("Where the system works"),
        B("The software works end to end on real data, with a few milliseconds per statement.",
          f"FAKE is recognised with recall {pc['FAKE']['recall']['mean']:.2f} and precision {pc['FAKE']['precision']['mean']:.2f}; accuracy is {ea['by_confidence'][3]['accuracy']:.2f} to {ea['by_confidence'][4]['accuracy']:.2f} for confidence above 0.6, where about {sum(b['n'] for b in ea['by_confidence'][3:]) / n_test * 100:.0f} % of the statements lie.",
          f"The pipeline is stable across seeds (standard deviation of macro-F1 {A['proposed_test']['f1_macro']['std']:.3f}) and clearly above the majority class ({m(PROP)} against {m(MAJ)})."),
        H3("Where it fails"),
        B("PARTIALLY TRUE is almost not learned (F1 about 0.24); half-truths differ from falsehoods in content, not in vocabulary or style.",
          "The model cannot check facts: a well-phrased false claim is called REAL, and a true claim in an accusatory style is called FAKE; statements of thirty words or more reach only 0.43 accuracy.",
          f"The optimiser and the PCA step add cost (about {A['train_time_s']['mean']:.0f} s per fit) without a gain over default settings or linear models, and the displayed confidence does not belong to the verdict for {lv['disagree_rate'] * 100:.0f} % of the statements.",
          "The shipped model, trained on templates, fails on real text (macro-F1 0.155) and must be replaced by a model trained on real labelled data before any use beyond a demonstration."),

        H2("8.6 Limitations of these results"),
        B(f"Only {F.NTRAIN:,} of {F.NTRAIN_FULL:,} training statements were used for the pipeline; more data helps the linear models (logistic regression {m(LR_SUB)} with {F.NTRAIN:,}, {m(LR_FULL)} with all), and the full-data pipeline was not measured.",
          "Three seeds give a rough spread, not a significance test; differences of 0.01 macro-F1 should not be read as real.",
          "One dataset (one fact-checking organisation) was used; ISOT and cross-dataset transfer were not tested. The Firefly parameters and the PCA cap were not varied, and the three-class mapping (barely-true counted as FAKE) was not varied.",
          "Latency was measured on one machine with sequential requests; no load test and no user study were carried out."),

        H2("8.7 Objectives against outcomes"),
        TAB("The six objectives of the project and what was achieved", ["No.", "Objective", "Status", "Evidence"],
            [["1", "Assemble a labelled dataset of genuine and fabricated news", "Achieved for evaluation",
              f"LIAR2 ({F.NTRAIN_FULL + F.NVALID + F.NTEST:,} statements, three-class mapping) was obtained and used; the shipped model itself was trained on a 750-document synthetic corpus"],
             ["2", "Preprocess: tokenisation, stop-word removal, stemming, vectorisation", "Partly achieved", "Cleaning, tokenisation, stop-word removal, TF-IDF with 1-2 grams and 25 stylometric features are implemented; stemming is not"],
             ["3", "Apply PCA to reduce dimensionality", "Achieved", f"4,025 features reduced to at most 300 components; on real text the cap keeps only {A['pca_variance']['mean'] * 100:.1f} % of the variance"],
             ["4", "Use the Firefly algorithm to optimise feature selection and MSVM parameters", "Implemented; benefit not shown",
              f"Joint search over mask, C and gamma keeps about {A['n_selected']['mean']:.0f} of 300 components; test macro-F1 ({m(PROP)}) is not better than default SVM ({m(DEF)}) or random search ({m(RND)})"],
             ["5", "Train a multi-class SVM on the optimised feature set", "Achieved", "RBF SVM, balanced class weights, three classes including PARTIALLY TRUE"],
             ["6", "Evaluate accuracy, precision, recall and F1 against unoptimised baselines", "Achieved",
              "Reported against the majority class, default SVM, mask-only, random search and TF-IDF linear models; finding: no gain from optimisation"],
             ["Aim", "Improve accuracy and computational complexity while keeping the system reliable", "Not achieved", f"Not better than simple baselines; training about {A['train_time_s']['mean'] / A['ref_full_LinearSVC_time']['mean']:.0f} times slower than a linear SVM"],
             ["Aim", "Deliver an easy-to-use application", "Achieved", f"Six-screen web application with detection, batch, analytics and retraining; {F.N_TESTS} automated checks pass"]],
            widths=[0.45, 2.1, 1.2, 3.0], align=["c", "l", "c", "l"], size=9),
    ]
    return out
