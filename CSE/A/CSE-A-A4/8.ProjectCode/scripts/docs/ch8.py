"""Chapter 8: Results and Output Screens. Every number is read from facts (metrics.json, latency.json, sample_io.json).

blocks() returns the full text; when facts.REPORT is True (the 17.Final Document build) it returns the compact variant
(four screenshot pairs instead of fourteen single screenshots, fewer figures, shorter prose and tables).
"""

import json
import os

from . import facts as F
from .blocks import FIG, H1, H2, P, B, TAB, PAIR
from .refs import cite as c


def pick(full, short):
    """Compact text for the full report (F.REPORT), full text for the chapter documents."""
    return short if F.REPORT else full


def _sample_io():
    p = os.path.join(F.EXP, "sample_io.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def _sw(rows, t):
    for r in rows:
        if abs(r["threshold"] - t) < 1e-9:
            return r
    raise KeyError(t)


def _shot(name, caption, base=5.6, max_h=5.0):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def blocks():
    R = F.REPORT
    S, SV, BB, IM, SE, FU = F.SAVED, F.SERVING, F.BASE_BAL, F.IMB, F.SEEDS, F.FULL
    pcd, sas, qs, ens = S["classical"], S["sa"], S["qa"], S["ensemble"]
    ns = F.SPLIT["test"][0]
    asv, scl = SV["as_served_no_scaling"]["ensemble"], SV["with_scaling"]["ensemble"]
    io = _sample_io()
    ep = {m: F.best_epoch(m) for m in ("classical", "sa", "qa")}
    L = F.LATENCY
    sw_e, sw_p = S["ensemble_threshold_sweep"], S["classical_threshold_sweep"]
    lr, rf, xg = BB["Logistic Regression"], BB["Random Forest"], BB["XGBoost"]
    b = [H1("8. RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1 screens
    ex = io[0] if io else None
    b += [H2("8.1 Output screens")]
    if R:
        def sp(name, cap):
            return F.shot(name), cap
        b += [P(f"The screens below were captured from the running application at 1440 x 900 pixels with its real data: the {F.DATASET['rows']:,}-row synthetic file, the three trained models and the pipeline rebuilt from the 8,000-row sample. "
                "The landing page, the other Analytics tabs, the dark theme, phone layouts and the offline and error states are in Appendix C."),
              PAIR([sp("03_dashboard.png", "Dashboard: dataset counts, best F1, loaded models and fraud rate by merchant category."),
                    sp("04_verify.png", "Verify: the high-risk example scored by the ensemble, with the risk meter and each model's probability.")], 2.75),
              P(f"The dashboard shows {F.DATASET['rows']:,} transactions in 29 columns, {F.DATASET['fraud']:,} fraud-labelled rows (50.0 %), the best F1 and the number of models loaded; merchant categories are ranked by their share of fraud-labelled rows (Electronics and Online highest), which describes the synthetic generator, not real merchants. "
                "On the Verify screen the user enters an amount, merchant, channel, card-present and country-match flags and a time, plus three optional signal fields (friendly names for synthetic features V3, V14, V17), and picks the ensemble or one model. "
                + (f"The capture shows the high-risk example: ensemble probability {F.pct(ex['served']['ensemble'])}, a MEDIUM band with the action *Challenge with 3-D Secure*; PCD {F.pct(ex['served']['classical'])}, QS {F.pct(ex['served']['qa'])}, SAS {F.pct(ex['served']['sa'])}. " if ex else "")
                + "The verdict flips to fraud above 50 %, whereas the action bands are 40 % and 70 %."),
              PAIR([sp("05_bulk.png", "Bulk verification: the 20-row sample file after upload, with 20 of 20 rows flagged and 50.0 % accuracy."),
                    sp("06_analytics-where.png", "Analytics, tab Where: fraud rate by merchant category and by channel.")], 2.75),
              P(f"The Bulk screen screens a CSV in three steps. With the bundled `sample_batch.csv` ({SV['sample_batch_true_fraud']} fraud and {SV['sample_batch_rows'] - SV['sample_batch_true_fraud']} legitimate rows) it reports every row as fraud, 50.0 % accuracy, 100 % recall and F1 66.7 %, and itself warns that *every row was flagged*. "
                "This is not a model result but the batch-route scaling defect of Section 8.9, shown because it is what the delivered application does. "
                "The Analytics screen has four tabs that read the full dataset; *Where* ranks Electronics highest (70.6 % labelled fraud). The *When* tab is flat at about 50 % per hour, as a generator that draws timestamps uniformly for both classes must produce, so it confirms the synthetic nature of the data."),
              PAIR([sp("10_models-comparison.png", "Model comparison, Comparison tab: metrics at each model's best epoch, with the paper's training time and the time measured here."),
                    sp("11_models-curves.png", "Model comparison, Training curves tab: per-epoch F1 of PCD, SAS and QS.")], 2.75),
              P(f"The comparison tab tabulates the best-epoch metrics beside the training time the *paper* reports (a quotation) and the time measured here. The curves tab shows why a best-epoch view is generous: PCD alternates between predicting everything legitimate (F1 0) and everything fraud (F1 66.9 %) and reaches {F.pct(ep['classical'][1])} only at epoch {ep['classical'][0]}; "
                "SAS climbs from epoch 4 and settles near 94 %; QS oscillates until epoch 12 and then settles."),
              PAIR([sp("13_models-qubo.png", "Model comparison, QUBO matrix tab: the 220 x 220 matrix of the PCD model, top-left 40 x 40 block."),
                    sp("14_lab.png", "Model lab: training state of each model and the three steps dataset, preprocessing and training.")], 2.4),
              P("The QUBO tab draws the energy function of the PCD model as a 220 x 220 matrix (18 visible, 2 label and 200 hidden units), the form a quantum annealer would accept; it visualises the weights and is not used for prediction. "
                "The Model lab regenerates the dataset, re-runs preprocessing (manual undersampling, SMOTE or Tomek links) and retrains the selected models; its cards show 20 epochs each and, for PCD, a last accuracy of 58.8 % beside a recall of 100 %, the signature of a model that flags nearly everything. "
                "Retraining overwrites the files in `models/`, so a run was captured separately in Appendix C and the files were then restored.")]
    else:
        b += [P(f"This section shows the application running with its real data: the 39,000-row synthetic file, the three trained models and the pipeline rebuilt from the 8,000-row sample. Every screenshot was captured from the running application at 1440 x 900 pixels. "
                "The screens are described in the order a user meets them; the dark theme, the phone layouts and the offline and error states are in Appendix C."),
              _shot("01_landing-light.png", "Landing page: product summary, the four-step flow from payment to decision band, and the six application screens. The headline figures are read from the loaded models and the dataset.", 4.2, 6.6),
              P(f"The landing page introduces the product and quotes four live figures: the dataset size ({F.DATASET['rows']:,}), the number of loaded models (3 of 3), the best F1 and the precision of the best model. "
                f"The F1 shown is the best epoch of the simulated-annealing model ({F.pct(ep['sa'][1])}, epoch {ep['sa'][0]}), which is chosen on the test split and is therefore slightly more favourable than the final-epoch value of {F.pct(sas['f1'])} used elsewhere in this report. "
                "A footer states that the models were trained on a synthetic dataset and are not for production payments."),
              _shot("03_dashboard.png", "Dashboard: dataset counts, best F1 and loaded models, fraud rate by merchant category and the best-epoch F1 of each model.", 5.4),
              P(f"The dashboard gives an overview of the data and the models. The four tiles show {F.DATASET['rows']:,} transactions in 29 columns, {F.DATASET['fraud']:,} fraud-labelled rows (50.0 %), the best F1 and the number of models loaded. "
                "The bar chart ranks merchant categories by the share of their transactions that carry the fraud label; Electronics and Online head the list, Grocery and Fuel are lowest. "
                "Because the file was balanced to 50/50, these rates describe the synthetic generator and say nothing about real merchants."),
              _shot("04_verify.png", "Verify transaction: the high-risk example scored by the ensemble, with the risk meter, the recommended action and each model's probability.", 5.4),
              P("The Verify screen is the main task. The user enters an amount, merchant category, channel, card-present and country-match flags and a transaction time, with three optional signal fields (V3, V14, V17), and chooses the ensemble or one model. "
                + (f"The capture shows the high-risk example (1,200, Online, card not present, country mismatch): the ensemble probability is {F.pct(ex['served']['ensemble'])}, a MEDIUM risk with the action *Challenge with 3-D Secure*; the per-model bars show PCD at {F.pct(ex['served']['classical'])}, QS at {F.pct(ex['served']['qa'])} and SAS at {F.pct(ex['served']['sa'])}. " if ex else "")
                + "The verdict flips to *fraud* above 50 %, whereas the action bands are 40 % and 70 %, so a transaction at 68 % is called fraud and still only challenged. The signal fields are friendly names for synthetic features; they are not real card-holder attributes."),
              _shot("05_bulk.png", "Bulk verification: the 20-row sample file after upload, showing 20 of 20 rows flagged as fraud and 50.0 % accuracy against the file's own labels.", 5.4),
              P(f"The Bulk screen screens a CSV in three steps (choose, analyse, review). With the bundled `sample_batch.csv`, which holds {SV['sample_batch_true_fraud']} fraud and {SV['sample_batch_rows'] - SV['sample_batch_true_fraud']} legitimate rows, the screen reports every row as fraud, 50.0 % accuracy, 100 % recall and an F1 of 66.7 %. "
                "The interface itself warns that *every row was flagged* and suggests checking the scale of the values. This is not a model result: it is the consequence of the scaling defect in the batch route that Section 8.9 explains, and it is shown here because it is what the delivered application does."),
              _shot("06_analytics-where.png", "Analytics, tab Where: fraud rate by merchant category and by channel.", 5.4),
              _shot("07_analytics-when.png", "Analytics, tab When: fraud rate by hour of day, taken from the timestamp modulo one day.", 5.4),
              P("The Analytics screen has four tabs that all read the full dataset through `/api/dataset_stats`. *Where* ranks merchant categories (Electronics highest at 70.6 % of its transactions labelled fraud) and channels. "
                "*When* plots the fraud rate for each hour of the day; the curve is flat at about 50 %, which is what a generator that draws timestamps uniformly for both classes should produce. A real fraud stream would show hour-of-day structure, so this panel confirms the synthetic nature of the data rather than any finding."),
              _shot("08_analytics-how-much.png", "Analytics, tab How much: transactions per amount band split by label, and the amount summary.", 5.4),
              _shot("09_analytics-card-signals.png", "Analytics, tab Card signals: fraud rate with and without the physical card, and with matching or mismatching country.", 5.4),
              P(f"*How much* shows that most legitimate amounts lie below 250 while most fraud amounts lie above it: mean {F.DATASET['amount_mean_fraud']:.2f} against {F.DATASET['amount_mean_legit']:.2f}, medians 352.13 and 80.25, and a largest amount of 1,257.23. "
                "*Card signals* confirms that fraud is much more frequent when the card is not present and when the country does not match. These are the same signals that the random forest ranks highest (Section 8.2), so the analytics and the model agree by construction."),
              _shot("10_models-comparison.png", "Model comparison, tab Comparison: metrics of the three models at their best epoch, with the paper's training time and the time measured here.", 5.4),
              _shot("11_models-curves.png", "Model comparison, tab Training curves: per-epoch F1 of PCD, SAS and QS over 20 epochs.", 5.4),
              P(f"The comparison tab plots accuracy, precision, recall and F1 for each model at its best epoch and tabulates them, with a column for the training time the *paper* reports and one for the wall-clock time measured on this PC; the paper's column is a quotation, not a measurement. "
                f"The curves tab shows why a best-epoch view is generous. PCD alternates between predicting everything legitimate (F1 0) and everything fraud (F1 66.9 %) and reaches {F.pct(ep['classical'][1])} only at epoch {ep['classical'][0]}; SAS climbs from epoch 4 and settles near 94 %; QS oscillates until epoch 12 and then settles."),
              _shot("12_models-features.png", "Model comparison, tab Features: random-forest feature importance and the numbers of the pipeline.", 5.4),
              _shot("13_models-qubo.png", "Model comparison, tab QUBO matrix: the 220 x 220 matrix of the PCD model, top-left 40 x 40 block.", 5.4),
              P(f"The features tab ranks the 18 retained features (Amount first, then V3, Card_Present, V17 and V7) and states the pipeline in numbers: training shape {F.SPLIT['train'][0]:,} x {F.SPLIT['train'][1]}, test shape {F.SPLIT['test'][0]:,} x {F.SPLIT['test'][1]}, no column dropped as correlated. "
                "The QUBO tab draws the energy function of a model as a matrix of 220 x 220 entries (18 visible, 2 label and 200 hidden units for the PCD model), the form a quantum annealer would accept; it is a visualisation of the weights and is not used for prediction."),
              _shot("14_lab.png", "Model lab: current training state of each model, and the three steps dataset, preprocessing and training.", 4.6, 6.6),
              P("The Model lab regenerates the synthetic dataset, re-runs the preprocessing with a choice of manual undersampling, SMOTE or Tomek links, and retrains the selected models. The three cards at the top show the state of the loaded models: 20 epochs each, the best F1 and the last accuracy and recall. "
                "The PCD card shows a last accuracy of 58.8 % beside a recall of 100 %, the signature of a model that flags nearly everything. The lab overwrites the files in `models/`, so it was not run for this screenshot; a retraining run captured separately, with the files restored afterwards, is in Appendix C.")]

    # ------------------------------------------------------------------ 8.2 dataset
    b += [H2("8.2 Data and pipeline"),
          P(f"All results come from one synthetic dataset of {F.DATASET['rows']:,} rows, half of them fraud-labelled, created by `backend/synthetic_data.py` to imitate the 39-thousand-row balanced set of the base paper {c('base')}. "
            f"The backend works on an 8,000-row random sample of it: one-hot encoding, z-scoring of 24 numeric columns, a correlation filter at 0.95 (nothing was removed), random undersampling to equal classes, a random-forest ranking that keeps the 18 most important features, and a stratified 80/20 split into {F.SPLIT['train'][0]:,} training and {F.SPLIT['test'][0]:,} test rows, of which {F.SPLIT['test_fraud']} are fraud."),
          FIG(F.fig("f01_dataset_overview.png"), "Synthetic dataset: class balance, amount distribution by class and fraud rate by merchant category and channel.", pick(5.8, 4.6))]
    if not R:
        b += [FIG(F.fig("f11_feature_importance.png"), "Random-forest importance of the ten strongest features on the training split.", 5.0)]
    b += [P(pick("Amount carries by far the largest share of importance, followed by V3, Card_Present, V17 and V7; the generator shifts exactly these signals for fraud, so a classifier that finds them has learned the generator. "
                 "This is the first reason the numbers below must not be read as a forecast for real transactions.",
                 "Random-forest importance ranks Amount far ahead of V3, Card_Present, V17 and V7; the generator shifts exactly these signals for fraud, so a classifier that finds them has learned the generator. "
                 "This is the first reason the numbers below must not be read as a forecast for real transactions."))]

    # ------------------------------------------------------------------ 8.3 model performance
    def row(n, r):
        return [n, str(r.get("n_hidden", "-")), F.pct(r["accuracy"]), F.pct(r["precision"]), F.pct(r["recall"]), F.pct(r["f1"]), F.f3(r["roc_auc"])]

    b += [H2("8.3 Model performance on the held-out split"),
          P(pick(f"The table below gives the shipped models on the {ns:,}-row test split at the decision threshold of 0.5 that the application uses. The models are the files in `models/`, trained for 20 epochs; the metrics are those of the final epoch.",
                 f"The table gives the shipped models (final epoch of 20) on the {ns:,}-row test split at the application's threshold of 0.5.")),
          TAB("Shipped models on the 1,600-row held-out split (threshold 0.5)", ["Model", "Hidden units", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"],
              [row("PCD (classical)", pcd), row("SAS (annealing)", sas), row("QS (quantum-inspired)", qs), row("Ensemble (mean of three)", ens)],
              widths=[1.7, 0.7, 0.8, 0.8, 0.7, 0.6, 0.7], align=["l", "c", "c", "c", "c", "c", "c"], size=pick(10, 9.5))]
    if not R:
        b += [FIG(F.fig("f02_model_metrics.png"), "Accuracy, precision, recall and F1 of the three shipped models and their ensemble.", 5.4)]
    b += [P(pick(f"The SAS and QS models are close to each other (F1 {F.pct(sas['f1'])} and {F.pct(qs['f1'])}) and the ensemble is marginally above both ({F.pct(ens['f1'])}). SAS errs towards missing fraud ({sas['fn']} false negatives against {sas['fp']} false alarms), QS is more balanced ({qs['fn']} against {qs['fp']}). "
                 f"The PCD model is the exception: its recall is {F.pct(pcd['recall'])}, but it raises {pcd['fp']} false alarms among {pcd['tn'] + pcd['fp']} legitimate rows, so its precision is {F.pct(pcd['precision'])} and its accuracy {F.pct(pcd['accuracy'])}. "
                 f"All three models have the same ROC-AUC of {F.f3(pcd['roc_auc'])}, which means they *rank* transactions equally well; the PCD model is wrong only about where to put the threshold.",
                 f"SAS and QS are close (F1 {F.pct(sas['f1'])} and {F.pct(qs['f1'])}) and the ensemble is marginally above both ({F.pct(ens['f1'])}); SAS errs towards missed fraud ({sas['fn']} false negatives against {sas['fp']} false alarms), QS is more balanced ({qs['fn']} against {qs['fp']}). "
                 f"PCD has recall {F.pct(pcd['recall'])} but {pcd['fp']} false alarms among {pcd['tn'] + pcd['fp']} legitimate rows (precision {F.pct(pcd['precision'])}, accuracy {F.pct(pcd['accuracy'])}). "
                 f"All three share ROC-AUC {F.f3(pcd['roc_auc'])}: they *rank* equally well, and PCD is wrong only about where to put the threshold.")),
          FIG(F.fig("f03_confusion_matrices.png"), "Confusion matrices of the three shipped models and the ensemble on the 1,600-row test split.", pick(5.8, 5.0))]
    if not R:
        b += [FIG(F.fig("f04_roc_curves.png"), "ROC curves of the shipped models and of Logistic Regression, Random Forest and XGBoost on the same split.", 4.8)]

    # ------------------------------------------------------------------ 8.4 threshold
    e4, e5, e6 = _sw(sw_e, 0.4), _sw(sw_e, 0.5), _sw(sw_e, 0.6)
    p5 = _sw(sw_p, 0.5)
    b += [H2("8.4 Threshold and calibration"),
          P(pick(f"The application labels a transaction as fraud above 0.5 and uses 0.4 and 0.7 as action bands. The figure below shows what each cut-off does to the ensemble and to the PCD model. "
                 f"For the ensemble, a threshold of 0.4 gives precision {F.pct(e4['precision'])} and recall {F.pct(e4['recall'])}; at 0.5 the values are {F.pct(e5['precision'])} and {F.pct(e5['recall'])}; at 0.6 precision rises to {F.pct(e6['precision'])} but recall falls to {F.pct(e6['recall'])}. "
                 "At 0.7 and above no transaction reaches the threshold, so the HIGH band of the interface is never triggered by the ensemble on this data: the probabilities from these energy models are compressed into a narrow range around 0.5 and are not calibrated.",
                 f"For the ensemble a threshold of 0.4 gives precision {F.pct(e4['precision'])} and recall {F.pct(e4['recall'])}; at 0.5 they are {F.pct(e5['precision'])} and {F.pct(e5['recall'])}; at 0.6 precision rises to {F.pct(e6['precision'])} but recall falls to {F.pct(e6['recall'])}. "
                 "At 0.7 and above no transaction qualifies, so the HIGH band is never triggered on this data: the probabilities are compressed around 0.5 and not calibrated.")),
          FIG(F.fig("f06_threshold_sweep.png"), "Precision, recall and F1 against the decision threshold for the ensemble and the PCD model.", pick(5.6, 4.4)),
          P(pick(f"The PCD model is even more compressed: its probabilities fall in a narrow band between about 0.4 and 0.6, so a threshold of 0.5 puts most of them on the fraud side (accuracy {F.pct(p5['accuracy'])}) and 0.6 puts all of them on the other side (recall 0 %). "
                 "This is why the ROC-AUC is high while every fixed threshold performs badly, and it argues for calibrating the output (Platt scaling or isotonic regression on a validation set) before the bands are used for decisions; the undersampling that balanced the data also shifts probabilities, a known effect of the technique "
                 f"{c('dp15')}.",
                 f"PCD is more compressed still: its probabilities lie between about 0.4 and 0.6, so 0.5 puts most on the fraud side (accuracy {F.pct(p5['accuracy'])}) and 0.6 puts all on the other (recall 0 %). "
                 f"The ROC-AUC is high while every fixed threshold performs badly, which argues for calibrating (Platt or isotonic scaling on a validation set); undersampling also shifts probabilities {c('dp15')}."))]

    # ------------------------------------------------------------------ 8.5 stability
    b += [H2("8.5 Training behaviour and stability"),
          P(pick("The shipped models come from a single run, so the retraining experiment repeats training for five random seeds with 20 epochs on the same split and reports the final epoch (table below). A single seed would hide the instability that the training curves already hint at.",
                 "The shipped models come from one run, so training was repeated for five seeds (20 epochs, same split, final epoch); a single seed would hide the instability the curves hint at.")),
          TAB("GRBMC retrained over five seeds (final epoch, mean +/- standard deviation, percent)", ["Trainer", "Accuracy", "Precision", "Recall", "F1", "Best-epoch F1", "Seconds"],
              [[n, F.seed_cell(m, "accuracy"), F.seed_cell(m, "precision"), F.seed_cell(m, "recall"), F.seed_cell(m, "f1"), F.seed_cell(m, "best_epoch_f1"), f"{SE[m]['elapsed_sec']['mean']:.1f}"]
               for n, m in (("PCD", "classical"), ("SAS", "sa"), ("QS", "qa"))],
              widths=[0.8, 1.1, 1.1, 1.1, 1.1, 1.1, 0.7], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("f07_seed_study.png"), "Final-epoch F1 and recall of the three trainers over five seeds.", pick(5.0, 4.2))]
    if not R:
        b += [FIG(F.fig("f05_training_curves.png"), "Per-epoch F1 and loss of the three shipped models over 20 epochs.", 5.6)]
    b += [P(f"SAS is stable (F1 {F.seed_cell('sa', 'f1')}), QS is acceptable (F1 {F.seed_cell('qa', 'f1')}) and PCD is not: its final-epoch F1 varies by {SE['classical']['f1']['std'] * 100:.0f} points between seeds, from a model that finds most fraud to one that finds almost none, even though the best epoch of every seed is good ({F.seed_cell('classical', 'best_epoch_f1')}). "
            + pick("A model whose result depends on which epoch is read is not deployable unless a validation set chooses the epoch. The best-epoch columns, like the figures on the landing page, are selected on the test split and are optimistic by construction.",
                   "A model whose result depends on the epoch read is not deployable unless a validation set chooses the epoch; the best-epoch columns are selected on the test split and are optimistic by construction.")),
          P(pick(f"Training took {SE['classical']['elapsed_sec']['mean']:.0f} to {SE['sa']['elapsed_sec']['mean']:.0f} seconds per run, and the full 39,000-row file took {FU['classical']['elapsed_sec']:.0f} s (PCD), {FU['sa']['elapsed_sec']:.0f} s (SAS) and {FU['qa']['elapsed_sec']:.0f} s (QS). "
                 "The paper's hours are not reproduced: the SAS and QS trainers here use ten sweeps and 16 reads on a subsample of 3,000 rows per epoch and estimate the negative phase from a single averaged vector, which is far cheaper than annealing the whole model on a simulator or quantum hardware.",
                 f"Training took {SE['classical']['elapsed_sec']['mean']:.0f} to {SE['sa']['elapsed_sec']['mean']:.0f} s per run and {FU['classical']['elapsed_sec']:.0f}, {FU['sa']['elapsed_sec']:.0f} and {FU['qa']['elapsed_sec']:.0f} s (PCD, SAS, QS) on the full file. "
                 "The paper's hours are not reproduced: the SAS and QS trainers use ten sweeps and 16 reads on a 3,000-row subsample per epoch and a single averaged vector for the negative phase, far cheaper than annealing the whole model."))]

    # ------------------------------------------------------------------ 8.6 baselines
    b += [H2("8.6 Comparison with standard classifiers"),
          P(pick("The batch objectives name Logistic Regression, Random Forest and XGBoost. They are not part of the delivered application; they were trained by `scripts/run_experiments.py` on exactly the same 6,400 training rows and 18 features and scored on the same 1,600 test rows, with scikit-learn and XGBoost defaults except 100 trees with a minimum leaf size of 2 (random forest) and 200 trees of depth 4 (XGBoost).",
                 "Logistic Regression, Random Forest and XGBoost (batch objective 4) are not part of the application; `scripts/run_experiments.py` trained them on the same 6,400 rows and 18 features and scored them on the same 1,600 test rows (defaults except 100 trees with leaf size 2 for the forest, 200 trees of depth 4 for XGBoost).")),
          TAB("Standard classifiers and the RBM models on the same balanced split", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"],
              [["Logistic Regression", F.pct(lr["accuracy"]), F.pct(lr["precision"]), F.pct(lr["recall"]), F.pct(lr["f1"]), F.f3(lr["roc_auc"])],
               ["Random Forest", F.pct(rf["accuracy"]), F.pct(rf["precision"]), F.pct(rf["recall"]), F.pct(rf["f1"]), F.f3(rf["roc_auc"])],
               ["XGBoost", F.pct(xg["accuracy"]), F.pct(xg["precision"]), F.pct(xg["recall"]), F.pct(xg["f1"]), F.f3(xg["roc_auc"])],
               ["RBM, SAS", F.pct(sas["accuracy"]), F.pct(sas["precision"]), F.pct(sas["recall"]), F.pct(sas["f1"]), F.f3(sas["roc_auc"])],
               ["RBM, QS", F.pct(qs["accuracy"]), F.pct(qs["precision"]), F.pct(qs["recall"]), F.pct(qs["f1"]), F.f3(qs["roc_auc"])],
               ["RBM ensemble", F.pct(ens["accuracy"]), F.pct(ens["precision"]), F.pct(ens["recall"]), F.pct(ens["f1"]), F.f3(ens["roc_auc"])]],
              widths=[1.7, 0.9, 0.9, 0.9, 0.8, 0.8], align=["l", "c", "c", "c", "c", "c"], size=pick(10, 9.5)),
          FIG(F.fig("f08_baseline_comparison.png"), "F1 of the RBM models and the standard classifiers on the 1,600-row split and on the 39,000-row file.", pick(5.4, 4.4)),
          P(f"The simple classifiers win on this data. Logistic Regression reaches F1 {F.pct(lr['f1'])} and ROC-AUC {F.f3(lr['roc_auc'])} against {F.pct(ens['f1'])} and {F.f3(ens['roc_auc'])} for the RBM ensemble, and it fits in {lr['fit_seconds'] * 1000:.0f} ms. "
            + pick("That a linear model is the best is itself informative: the synthetic classes differ by mean shifts, which a linear boundary separates well; the energy-based network does not help here. ",
                   "A linear model suffices because the synthetic classes differ by mean shifts. ")
            + f"On the full 39,000-row file the order is the same (XGBoost F1 {F.pct(FU['XGBoost']['f1'])}, Logistic Regression {F.pct(FU['Logistic Regression']['f1'])}, SAS {F.pct(FU['sa']['f1'])}, QS {F.pct(FU['qa']['f1'])}), and the gap is about two to three points. "
            f"This agrees with the literature in which tree ensembles are strong baselines on tabular fraud data {c('rfpaper', 'cfa', 'shi')}.")]

    # ------------------------------------------------------------------ 8.7 imbalance
    def ir(m, s):
        r = F.imb_row(m, s)
        return [m, s, f"{r['precision']['mean']:.3f}", f"{r['recall']['mean']:.3f}", f"{r['f1']['mean']:.3f}", f"{r['pr_auc']['mean']:.3f}", f"{r['mean_fp']:.1f}", f"{r['mean_fn']:.1f}"]

    rb = IM["rule_based"]
    if R:
        rows = [ir(m, s) for s in ("none", "undersample") for m in ("Logistic Regression", "Random Forest", "XGBoost")]
        rows.append(ir("XGBoost", "SMOTE"))
    else:
        rows = [ir(m, s) for s in ("none", "class_weight", "SMOTE", "undersample") for m in ("Logistic Regression", "Random Forest", "XGBoost")]
    rows.append(ir("GRBMC (SA)", "undersample"))
    rows.append(["Rule: 3 of 4 risk signals", "-", f"{rb['precision']['mean']:.3f}", f"{rb['recall']['mean']:.3f}", f"{rb['f1']['mean']:.3f}", "-", f"{rb['mean_fp']:.1f}", f"{rb['mean_fn']:.1f}"])
    b += [H2("8.7 Behaviour when fraud is rare"),
          P(pick(f"The balanced file hides the central difficulty of the problem. To see it, the generator was run again with 1 % fraud ({IM['rows']:,} rows), the data were split first (stratified 80/20), and each balancing strategy was fitted on the training rows only. "
                 f"The test set has {IM['test_rows_per_seed']:,} rows with {IM['test_fraud_per_seed']} fraud, and the results are means over five splits (table below). The strategies are the ones the base paper discusses: no resampling, class weights, SMOTE {c('smote')} and random undersampling {c('base', 'fernandez')}.",
                 f"The balanced file hides the central difficulty, so the generator was rerun with 1 % fraud ({IM['rows']:,} rows), split first (stratified 80/20) and balanced on the training rows only. "
                 f"Each test set has {IM['test_rows_per_seed']:,} rows with {IM['test_fraud_per_seed']} fraud; the table gives means over five splits"
                 + (" for a subset of the strategies (class weights and further SMOTE rows are in Chapter 8 of the results document)" if False else "")
                 + f" for no resampling, SMOTE {c('smote')} and random undersampling {c('base', 'fernandez')}.")),
          TAB("1 % fraud variant: precision, recall, F1, PR-AUC and mean error counts per 7,800 test rows (threshold 0.5)", ["Model", "Strategy", "Precision", "Recall", "F1", "PR-AUC", "FP", "FN"],
              rows, widths=[1.5, 0.95, 0.75, 0.65, 0.55, 0.65, 0.45, 0.45], align=["l", "l", "c", "c", "c", "c", "c", "c"], size=8.5),
          FIG(F.fig("f09_imbalance_study.png"), "Precision and recall by model and balancing strategy when fraud is 1 % of the stream.", pick(5.8, 4.6))]
    u = {m: F.imb_row(m, "undersample") for m in ("Logistic Regression", "Random Forest", "XGBoost")}
    n_ = {m: F.imb_row(m, "none") for m in ("Logistic Regression", "Random Forest", "XGBoost")}
    g = F.imb_row("GRBMC (SA)", "undersample")
    fpr = [r["mean_fp"] / max(r["recall"]["mean"] * IM["test_fraud_per_seed"], 1) for r in u.values()]
    fpr_lo, fpr_hi = min(fpr), max(fpr)
    if R:
        b += [P(f"Three findings follow. Undersampling, the strategy the base paper settled on, gives the highest recall (above {min(r['recall']['mean'] for r in u.values()):.2f}) but precision falls to {min(r['precision']['mean'] for r in u.values()):.2f} to {max(r['precision']['mean'] for r in u.values()):.2f}: an analyst would review roughly {fpr_lo:.1f} to {fpr_hi:.1f} false alerts per fraud found. "
                f"With no resampling the same models keep precision at {min(r['precision']['mean'] for r in n_.values()):.2f} or better and find {min(r['recall']['mean'] for r in n_.values()):.2f} to {max(r['recall']['mean'] for r in n_.values()):.2f} of the fraud, the best F1 (Logistic Regression {n_['Logistic Regression']['f1']['mean']:.3f}); SMOTE and class weights give XGBoost a balanced F1 ({F.imb_row('XGBoost', 'SMOTE')['f1']['mean']:.2f} and {F.imb_row('XGBoost', 'class_weight')['f1']['mean']:.2f}) but push Logistic Regression towards the undersampling pattern. "
                f"The RBM trained on undersampled data (SAS) has precision {g['precision']['mean']:.2f} but recall only {g['recall']['mean']:.2f}, and PR-AUC {g['pr_auc']['mean']:.2f} against {F.imb_row('Logistic Regression', 'none')['pr_auc']['mean']:.2f} for Logistic Regression. "
                f"The illustrative rule (three of four risk signals) reaches F1 {rb['f1']['mean']:.2f}, so learned models clearly beat a fixed rule. "
                f"This matches the base paper's finding that SMOTE and Tomek links did poorly when the minority class is very small and that undersampling distorts probabilities {c('base', 'dp15')}; real streams hold about 0.01 % to 4 % fraud {c('base', 'cfa')}, so models scored on a balanced set give an optimistic picture.")]
    else:
        b += [P(f"Three findings follow. First, undersampling, the strategy the base paper settled on, gives the highest recall (above {min(r['recall']['mean'] for r in u.values()):.2f}) but destroys precision: precision falls to {min(r['precision']['mean'] for r in u.values()):.2f} to {max(r['precision']['mean'] for r in u.values()):.2f} and a model raises {min(r['mean_fp'] for r in u.values()):.0f} to {max(r['mean_fp'] for r in u.values()):.0f} false alarms for every {IM['test_fraud_per_seed']} frauds. "
                f"An analyst would have to review roughly {fpr_lo:.1f} to {fpr_hi:.1f} false alerts for every fraud found. Second, with no resampling the same models keep precision at {min(r['precision']['mean'] for r in n_.values()):.2f} or better and still find {min(r['recall']['mean'] for r in n_.values()):.2f} to {max(r['recall']['mean'] for r in n_.values()):.2f} of the fraud, giving the best F1 (Logistic Regression {n_['Logistic Regression']['f1']['mean']:.3f}); SMOTE and class weights give XGBoost a balanced F1 ({F.imb_row('XGBoost', 'SMOTE')['f1']['mean']:.2f} and {F.imb_row('XGBoost', 'class_weight')['f1']['mean']:.2f}) but push Logistic Regression towards the undersampling pattern (precision {F.imb_row('Logistic Regression', 'SMOTE')['precision']['mean']:.2f} and {F.imb_row('Logistic Regression', 'class_weight')['precision']['mean']:.2f}). "
                f"Third, the RBM trained on undersampled data (SAS) has precision {g['precision']['mean']:.2f} but recall of only {g['recall']['mean']:.2f}, and a PR-AUC of {g['pr_auc']['mean']:.2f} against {F.imb_row('Logistic Regression', 'none')['pr_auc']['mean']:.2f} for Logistic Regression; the generative model loses most of its advantage once the class proportions it saw in training differ from those at test time. "
                f"The illustrative rule (flag when three of four risk signals are present) reaches F1 {rb['f1']['mean']:.2f}, so the learned models are far better than a fixed rule of this kind, which supports the first problem stated in the batch abstract."),
              P("The result is consistent with the observation of the base paper that SMOTE and Tomek links performed poorly when the minority class was very small, and with the known effect that undersampling distorts probabilities " + f"{c('base', 'dp15')}. "
                "It also shows that the application's models, trained and scored on a balanced set, would give an optimistic picture of a real stream, where the proportion of fraud is of the order of 0.01 % to 4 % " + f"{c('base', 'cfa')}.")]

    # ------------------------------------------------------------------ 8.8 base paper
    bt = F.BASE_TABLE
    b += [H2("8.8 Comparison with the base paper"),
          P(pick("The table below sets the results beside Table 1 of the base paper. The two sets of numbers are **not comparable**: the paper used about 145 million real transactions from a Brazilian payment company, balanced to 39 thousand rows, 50 epochs and real or simulated D-Wave sampling, while this project used a synthetic file of the same size, 20 epochs, subsampled classical samplers and no quantum hardware. "
                 "The table is given to show where the two stand, not to claim an improvement.",
                 "The table sets the results beside Table 1 of the base paper. They are **not comparable**: the paper used about 145 million real transactions balanced to 39 thousand rows, 50 epochs and real or simulated D-Wave sampling; this project used a synthetic file of the same size, 20 epochs, subsampled classical samplers and no quantum hardware. No improvement is claimed.")),
          TAB("Base paper (real data) and this project (synthetic data), best epoch by F1", ["Method", "Source", "Accuracy", "Precision", "Recall", "F1", "Training time"],
              [["PCD", "paper", f"{bt['PCD'][0]} %", f"{bt['PCD'][1]} %", f"{bt['PCD'][2]} %", f"{bt['PCD'][3]} %", bt["PCD"][4]],
               ["PCD", "this project", f"{F.pct(F.HIST['classical']['accuracy'][ep['classical'][0] - 1])}", f"{F.pct(F.HIST['classical']['precision'][ep['classical'][0] - 1])}", f"{F.pct(F.HIST['classical']['recall'][ep['classical'][0] - 1])}", F.pct(ep['classical'][1]), f"{F.HIST['classical']['elapsed_sec']:.1f} s"],
               ["SAS", "paper", f"{bt['SAS'][0]} %", f"{bt['SAS'][1]} %", f"{bt['SAS'][2]} %", f"{bt['SAS'][3]} %", bt["SAS"][4]],
               ["SAS", "this project", f"{F.pct(F.HIST['sa']['accuracy'][ep['sa'][0] - 1])}", f"{F.pct(F.HIST['sa']['precision'][ep['sa'][0] - 1])}", f"{F.pct(F.HIST['sa']['recall'][ep['sa'][0] - 1])}", F.pct(ep['sa'][1]), f"{F.HIST['sa']['elapsed_sec']:.1f} s"],
               ["QS", "paper", f"{bt['QS'][0]} %", f"{bt['QS'][1]} %", f"{bt['QS'][2]} %", f"{bt['QS'][3]} %", bt["QS"][4]],
               ["QS", "this project", f"{F.pct(F.HIST['qa']['accuracy'][ep['qa'][0] - 1])}", f"{F.pct(F.HIST['qa']['precision'][ep['qa'][0] - 1])}", f"{F.pct(F.HIST['qa']['recall'][ep['qa'][0] - 1])}", F.pct(ep['qa'][1]), f"{F.HIST['qa']['elapsed_sec']:.1f} s"]],
              widths=[0.6, 1.0, 0.85, 0.85, 0.75, 0.65, 1.1], align=["l", "l", "c", "c", "c", "c", "l"], size=9.5),
          FIG(F.fig("f13_paper_comparison.png"), "F1 of the base paper (real Stone data) and of this project (synthetic data). The data differ, so the bars are not directly comparable.", pick(5.2, 4.2)),
          P(pick("Qualitatively the ordering of the paper is partly reproduced: the annealing-based trainers beat classical PCD in both studies, and the simulated-annealing trainer is the best or tied for best. "
                 "Two things are not reproduced. The paper's quantum sampling is slightly below simulated annealing, whereas here the two are equal within noise; and the paper's classical model is a reasonable classifier at 84 % accuracy, whereas the PCD model here is unstable. "
                 "The synthetic data are easier than real data (a linear model scores 96.7 %), which is why accuracy exceeds the paper's even for a simplified sampler.",
                 "The paper's ordering is partly reproduced: the annealing-based trainers beat classical PCD in both studies and SAS is best or tied. Two things are not: the paper's quantum sampling is slightly below SAS whereas here they are equal within noise, and the paper's PCD is a reasonable 84 % classifier whereas the PCD model here is unstable. "
                 "The synthetic data are easier (a linear model scores 96.7 %), which is why accuracy exceeds the paper's even for a simplified sampler."))]

    # ------------------------------------------------------------------ 8.9 serving defect + sample IO
    b += [H2("8.9 Sample inputs and outputs, and the serving defect"),
          P(pick("The table below gives the real responses of `/api/predict_single` for three transactions, next to the probabilities computed offline with correct scaling. They are identical to full precision, so the single-transaction route is correct; "
                 "the high-risk example is flagged as fraud (MEDIUM band), the low-risk example is approved, and a middle example is a coin toss at 52.6 %.",
                 "The table gives the real responses of `/api/predict_single` for three transactions beside the probabilities computed offline with correct scaling; they are identical to full precision, so the single-transaction route is correct. "
                 "The high-risk example is flagged (MEDIUM band), the low-risk one approved, and the middle one is a coin toss at 52.6 %."))]
    if io:
        b += [TAB("Live responses of the single-transaction route and offline recomputation", ["Example", "PCD", "SAS", "QS", "Ensemble", "Verdict, band", "Offline ensemble"],
                  [[x["name"].split(" (")[0].capitalize(), F.pct(x["served"]["classical"]), F.pct(x["served"]["sa"]), F.pct(x["served"]["qa"]), F.pct(x["served"]["ensemble"]), f"{x['served']['label']}, {x['served']['risk']}", F.pct(x["scaled_offline"]["ensemble"])] for x in io],
                  widths=[1.25, 0.65, 0.65, 0.65, 0.8, 1.35, 0.9], align=["l", "c", "c", "c", "c", "l", "c"], size=9.5),
              P(pick("Inputs: high-risk = amount 1,200, merchant Online, channel Online, card not present, country mismatch, time 54,000 s, V3 1.8, V14 -1.1, V17 1.4; low-risk = amount 80, Grocery, Chip, card present, country match, V3, V14 and V17 at 0; middle = amount 350, Electronics, Contactless, card present, country match, V3 0.8, V14 -0.4, V17 0.6. Fields not given are filled with the dataset mean or mode.",
                     "Inputs: high-risk = 1,200, Online, Online, card not present, country mismatch, time 54,000 s, V3 1.8, V14 -1.1, V17 1.4; low-risk = 80, Grocery, Chip, card present, country match, V3/V14/V17 = 0; middle = 350, Electronics, Contactless, card present, country match, V3 0.8, V14 -0.4, V17 0.6.") )]
    b += [P(pick(f"The batch route behaves differently. In `predict_batch` the one-hot columns are first reduced to the 18 selected features and only then scaled; the scaler was fitted on 24 numeric columns, so `scaler.transform` on the 13 numeric columns that remain raises an error, "
                 f"and a bare `except: pass` hides it. The models then receive raw, unscaled values. The second table below measures the effect on a fresh 2,000-row balanced batch produced by the same generator with a new random seed, once as the route serves it and once with correct scaling.",
                 "The batch route behaves differently: `predict_batch` reduces the columns to the 18 selected features and only then scales; the scaler was fitted on 24 numeric columns, so `scaler.transform` on the remaining 13 raises an error that a bare `except: pass` hides, and the models receive unscaled values. "
                 "The next table measures the effect on a fresh 2,000-row balanced batch (new seed), as served and with correct scaling.")),
          TAB("Batch route: fresh 2,000-row balanced batch, as served and with correct scaling (ensemble)", ["Condition", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "FP", "FN"],
              [["As served (no scaling)", F.pct(asv["accuracy"]), F.pct(asv["precision"]), F.pct(asv["recall"]), F.pct(asv["f1"]), F.f3(asv["roc_auc"]), str(asv["fp"]), str(asv["fn"])],
               ["With scaling", F.pct(scl["accuracy"]), F.pct(scl["precision"]), F.pct(scl["recall"]), F.pct(scl["f1"]), F.f3(scl["roc_auc"]), str(scl["fp"]), str(scl["fn"])]],
              widths=[1.7, 0.8, 0.8, 0.7, 0.6, 0.7, 0.5, 0.5], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("f10_serving_defect.png"), "Effect of the skipped scaling in the batch route: accuracy, recall and false alarms as served and with correct scaling.", pick(5.4, 4.2)),
          P(f"As served, the batch route flags essentially every row (accuracy {F.pct(asv['accuracy'])}, recall {F.pct(asv['recall'])}, {asv['fp']} false alarms among 1000 legitimate rows); with scaling it matches the offline result ({F.pct(scl['accuracy'])}). "
            f"The bundled sample file shows it too: {SV['sample_batch_as_served_flagged']} of {SV['sample_batch_rows']} rows are flagged as served, {SV['sample_batch_scaled_flagged']} when scaled (the file holds {SV['sample_batch_true_fraud']} fraud rows). "
            + pick("The defect is documented and was deliberately not fixed in the delivered product: the repair is one line (apply the scaler to the full numeric block before selecting columns), but the report describes the system as built. "
                   "It also shows why the smoke test, which only checks that a response exists, did not catch it.",
                   "The defect is documented and deliberately not fixed: the repair is one line (scale the full numeric block before selecting columns), but the report describes the system as built. The smoke test, which only checks that a response exists, did not catch it."))]

    # ------------------------------------------------------------------ 8.10 success / failure
    b += [H2("8.10 Success and failure analysis"),
          P(pick("**Where the system works.** The simulated-annealing and quantum-inspired models separate the synthetic classes with ROC-AUC 0.986 and F1 about 94 %; the ensemble is at least as good as its members; the single-transaction route is numerically correct; a check takes "
                 f"a median of {L['predict_single_fraud_example']['median_ms']:.0f} ms; and the interface exposes the whole workflow (check, screen, analyse, compare, retrain) with real data behind every screen.",
                 "**Where the system works.** SAS and QS separate the synthetic classes with ROC-AUC 0.986 and F1 about 94 %, the ensemble is at least as good as its members, the single-transaction route is numerically correct and a check takes "
                 f"a median of {L['predict_single_fraud_example']['median_ms']:.0f} ms, with the whole workflow exposed in the interface.")),
          P("**Where it fails.** The concrete failure cases are these:"),
          B(f"*The PCD model flags almost everything.* At the application's threshold it has {pcd['fp']} false alarms against {pcd['tn']} correct approvals; its ranking is good (ROC-AUC {F.f3(pcd['roc_auc'])}) but it is not calibrated, and it is unstable across seeds.",
            f"*The batch route is broken by the scaling defect.* Accuracy falls to {F.pct(asv['accuracy'])} and the sample file is flagged 20 of 20 (Section 8.9).",
            "*An extreme amount produces NaN.* An amount of 1,000,000 yields a probability that is not a number and an LOW-risk approval (Section 7.6).",
            "*Precision collapses when fraud is rare.* With undersampling and 1 % fraud every model, standard or RBM, either raises hundreds of false alarms or misses a large part of the fraud (Section 8.7).",
            "*The HIGH band never fires.* The ensemble probabilities stay below 0.7 on this data, so *decline and alert* is unreachable in practice (Section 8.4).",
            f"*Oscillation of the annealed trainers.* The per-epoch F1 of SAS and QS moves by several points between neighbouring epochs and SAS drops to {F.pct(min(F.HIST['sa']['f1'][1:3]))} in the early epochs; choosing the last epoch, as done here, is safe only because the curves have settled by about epoch 13.",
            "*The simple models are better.* On this data Logistic Regression, Random Forest and XGBoost beat the RBM ensemble by about two points of F1, so the benefit of the base paper's method is not shown by this project.")]

    # ------------------------------------------------------------------ 8.11 limitations
    b += [H2("8.11 Limitations of the results")]
    if R:
        b += [B("The data are synthetic, built from simple mean shifts, so results are easier than on real transactions and do not transfer to a bank.",
                "The quantum sampler is a classical simulation (ten sweeps, subsampled epoch); no quantum hardware or D-Wave simulator was used, so nothing here tests quantum advantage.",
                "Best-epoch figures are chosen on the test split; the primary figures are final-epoch values. Scaling, balancing and feature ranking were fitted on the 8,000-row sample before the split, a mild leak that the 1 % experiment avoids.",
                "There is one dataset, one split for the shipped models and no confidence intervals beyond the five-seed spread; latency was measured on one PC with a development server.")]
    else:
        b += [B("The data are synthetic and generated with simple mean shifts, so accuracy is higher and easier than on real transactions, and no result transfers to a bank.",
                "The quantum sampler is a classical simulation with ten sweeps and a subsampled epoch; no quantum hardware, D-Wave simulator or Julia package was used, so nothing here tests quantum advantage.",
                "Best-epoch figures are chosen on the test split. The primary figures in this chapter are final-epoch values; the best-epoch values are shown only where the base paper's convention requires them.",
                "Scaling, balancing and feature ranking were fitted on the whole 8,000-row sample before the split, a mild leak; the 1 % experiment avoids it.",
                "There is a single dataset, single split for the shipped models and no confidence intervals beyond the five-seed spread.",
                "Latency was measured on one PC with a development server and says nothing about concurrent load.")]

    # ------------------------------------------------------------------ 8.12 objectives
    b += [H2("8.12 Objectives versus outcomes"),
          P(pick("The table below sets the six objectives of the project proposal against what was achieved.", "The six objectives of the proposal against what was achieved:")),
          TAB("Objectives and measured outcomes", ["No.", "Objective", "Outcome", "Evidence"],
              [["1", "Acquire a benchmark dataset and quantify the imbalance", "Partly met: a synthetic file, not a public benchmark; imbalance quantified by the 50/50 file and a 1 % variant", "Sections 8.2, 8.7"],
               ["2", "Scaling, feature selection, stratified split", "Met: z-score, correlation filter, RF top-18, stratified 80/20; mild leak noted", "Section 8.2"],
               ["3", "Compare SMOTE with random undersampling", "Met in experiments (not in the product UI, which offers it only through the lab): undersampling lifts recall and wrecks precision at 1 % fraud", "Section 8.7"],
               ["4", "Train Logistic Regression, Random Forest and XGBoost", "Met in `scripts/run_experiments.py`; not shipped inside the application", "Section 8.6"],
               ["5", "Evaluate with precision, recall, F1 and ROC-AUC", "Met: all four, plus PR-AUC and confusion matrices", "Sections 8.3-8.7"],
               ["6", "Deploy the best model behind an interface that flags a transaction", f"Met with defects: the interface flags transactions in a median {L['predict_single_fraud_example']['median_ms']:.0f} ms; the deployed model is the RBM ensemble, not the best model, and the batch route is mis-scaled", "Sections 8.1, 8.9"]],
              widths=[0.4, 1.9, 2.8, 1.1], align=["c", "l", "l", "l"], size=9.5)]
    return b
