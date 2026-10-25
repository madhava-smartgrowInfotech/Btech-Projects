"""Figure index: key -> (file in docs/figures, caption). Files are produced by scripts/docs_build/make_figures.py from experiments/*.json."""

FIGURES = {
    "dataset": ("f01_dataset_overview.png", "Synthetic dataset: class balance, transaction amount by class, and fraud rate by merchant category and by channel."),
    "metrics": ("f02_model_metrics.png", "Accuracy, precision, recall and F1 of the three shipped models and their ensemble on the held-out split at threshold 0.5."),
    "confusion": ("f03_confusion_matrices.png", "Confusion matrices of the shipped PCD, SAS and QS models and the ensemble on the held-out split."),
    "roc": ("f04_roc_curves.png", "ROC curves of the shipped models and the Logistic Regression, Random Forest and XGBoost baselines on the same split."),
    "training": ("f05_training_curves.png", "Per-epoch F1 on the test split and reconstruction loss of the three trainers over 20 epochs (saved training histories)."),
    "threshold": ("f06_threshold_sweep.png", "Precision, recall and F1 of the ensemble, and of PCD alone, as the decision threshold moves; 0.4, 0.5 and 0.7 are the application's risk cut-offs."),
    "seeds": ("f07_seed_study.png", "F1 and recall of PCD, SAS and QS retrained with five seeds (final epoch, mean and standard deviation)."),
    "baselines": ("f08_baseline_comparison.png", "F1 of the RBM models against Logistic Regression, Random Forest and XGBoost on the held-out split and on the whole 39,000-row file."),
    "imbalance": ("f09_imbalance_study.png", "Precision and recall at 1% fraud for each model and resampling strategy, for the RBM trained on undersampled data, and for a simple rule."),
    "serving": ("f10_serving_defect.png", "Serving-path defect: accuracy, recall and false positives on a fresh balanced batch when the scaler is skipped (as served) and when it is applied."),
    "importance": ("f11_feature_importance.png", "Random-forest feature importance for the ten strongest of the 18 selected features."),
    "latency": ("f12_latency.png", "Median and 95th-percentile response time of the API endpoints on the development PC."),
    "paper": ("f13_paper_comparison.png", "Base paper Table 1 against the shipped models of this project; the datasets differ (real Stone data against synthetic data), so the bars are not directly comparable."),
}
