"""Chapter 2 sections (Literature Survey) and the novelty discussion."""
from __future__ import annotations

from doc_common import LAT, X, p, REF_NOTE


def sec_lit_overview(d):
    d.h2("Overview of the Literature")
    d.p("The batch literature survey recorded five works: the base paper [1] and four further papers on phishing URL detection [2]-[5]. "
        "To place the project in the wider field, this chapter also draws on the related work that the base paper itself reviews "
        "[6]-[14], and on a small number of well-known references on URL-based detection [18], [19]. " + REF_NOTE)
    d.p("The literature falls into three groups. Supervised machine-learning detectors dominate and report the highest accuracy. "
        "Unsupervised detectors aim at novel sites but score lower. A small and recent group studies how crowd input can support "
        "automated systems; only the base paper applies it directly to phishing URL detection with a feedback loop [1].")


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p("The base paper is \"A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence\" "
        "by L. Aldhuwayhi and A. Alromih of King Saud University, published in IEEE Access, volume 14, 2026, pages 88393 to 88404 [1]. "
        "It was read in full for this project.")
    d.table([["Aspect", "What the base paper does"],
             ["Problem", "Static phishing detectors depend on old datasets, cannot retrain by themselves, and do not use crowd reports as a live input."],
             ["Design", "Three phases: Extractor (features; known patterns answered directly), Detection (ML classifier; unknown inputs flagged as novel), Updating by crowdsourcing (novel URLs queued for human verification, then added to the training set and used to retrain)."],
             ["Dataset", "PhiUSIIL [17]: 235,804 URLs (134,850 legitimate, 100,945 phishing), 54 URL and page-content features; undersampled to 100,945 per class; 34 features kept after ANOVA and chi-square selection."],
             ["Model", "Hybrid deep network: embedding (50) and LSTM with attention over the URL text, a dense branch (64) for the 34 numeric features, concatenation (128) and a sigmoid output."],
             ["Evaluation", "Stratified split; 5-fold cross-validation; accuracy, precision, recall, F1; learning-curve simulation of crowd data growth; timing over 10 runs of 40,342 URLs."],
             ["Reported results", "Accuracy 0.9980, F1 0.9988, test loss 0.0262; about 0.20 ms per URL; accuracy plateau near 99.7 % beyond 50 % of the training data."],
             ["Stated limits", "Results come from one dataset and setup; real-world validation, scalability, adversarial misuse of the crowd channel and user privacy remain open."]],
            "Summary of the base paper", widths=[0.2, 0.8], font=10)
    d.h3("Strengths")
    d.bullets(["It names a real gap: crowd input is rarely a live, structured input to a phishing detector.",
               "The human-in-the-loop step protects the training data from noisy or malicious reports.",
               "Large dataset, balanced classes, stratified split and cross-validation; the experimental method is clear.",
               "The learning-curve experiment is a sensible way to study the effect of growing data without a live crowd."])
    d.h3("Weaknesses and open points")
    d.bullets(["The crowd loop itself is not evaluated with real reports; the learning curve only simulates data growth with a fixed test set.",
               "The accuracy of 99.8 % is reported for one benchmark and the paper says further validation in real environments is needed.",
               "The model uses page-content features from the PhiUSIIL dataset in addition to the URL; a live system would need to fetch every page to compute them, which the paper does not discuss.",
               "The quoted model size of 48 bytes cannot be the size of an LSTM network with attention; it is treated here as an unexplained figure."])


def sec_related(d):
    d.h2("Related Work")
    d.p("Related work is grouped by approach. Descriptions of works [6]-[14] are taken from the account in the base paper [1], not from the "
        "original papers, and the accuracies are the values reported there.")
    d.h3("Supervised classifiers on URL features")
    d.p("Vajrobol et al. combined mutual-information feature ranking with logistic regression and reported 99.97 % accuracy with only five "
        "features on the PhiUSIIL dataset [6]. Etem and Teke reduced 51 features to two with t-SNE and reported 99.7 % for a decision tree "
        "[7]. Alnemari and Alshammari compared classical classifiers for phishing domains and found Random Forest best at 97.3 % on a UCI "
        "dataset [8]. These studies show that carefully chosen features let simple models reach high accuracy, but all rely on a fixed dataset.")
    d.h3("Ensembles, deep models and multi-modal features")
    d.p("Butt et al. studied cloud-based e-mail phishing with SVM and LSTM models (up to 99.62 %) [9]. Rathee and Mann reviewed e-mail phishing detection "
        "and report Random Forest results up to 99.87 % [10]. Fan combined SVM and Naive Bayes over textual, visual and URL features (99.16 %) [13]. "
        "A reported XGBoost model reached 94.16 % on a 5,000-URL set built from page source images [1]. These works broaden the "
        "feature space but depend on predefined features that attackers can change.")
    d.h3("Deployed tools")
    d.p("Priya et al. built a Random Forest and logistic regression browser extension (97 % on 11,055 URLs) [11], and Sawant et al. integrated "
        "machine learning, deep learning and NLP in an extension [12]. The base paper notes that both neglect latency, high-traffic evaluation "
        "and continuous retraining [1].")
    d.h3("Unsupervised and anomaly-based detection")
    d.p("Assefa and Katarya applied an autoencoder to 16 URL features and reported 91.24 % accuracy [14]. Anomaly detection suits novel sites but "
        "scores below supervised models and was tested on a small dataset.")
    d.h3("Crowdsourcing and humans in the loop")
    d.p("Huang et al. studied crowdsourced analysis for cyber-threat intelligence and found that crowd data can contain misleading information "
        "[15]; Lazaros et al. reviewed human-in-the-loop AI and its role in high-stakes systems [16]. Both motivate the base paper's choice "
        "of a verification step before reports reach the training data.")
    d.h3("Other works in the batch survey")
    d.p("The batch survey also lists four further papers on phishing URL detection: [2] (machine learning, 2023), [3] (reinforcement learning "
        "for real-time detection, 2025), [4] (machine learning and deep learning, 2024) and [5] (URL analysis and machine learning, 2025). "
        "They are cited here for completeness; their methods and results were not retrieved and are not summarised.")
    d.table([["Work", "Approach", "Data", "Reported result", "Limitation noted"],
             ["Base paper [1]", "LSTM-attention + dense; crowd feedback loop", "PhiUSIIL, 235,804 URLs", "Acc. 99.8 %, F1 0.9988", "Crowd loop simulated only"],
             ["Vajrobol et al. [6]", "Mutual information + logistic regression", "PhiUSIIL", "99.97 % (5 features)", "No real-time or evolving-threat test"],
             ["Etem and Teke [7]", "t-SNE reduction + decision tree", "51-feature URL set", "99.7 %", "Single dataset"],
             ["Alnemari and Alshammari [8]", "Classical classifiers, Random Forest best", "UCI phishing domains", "97.3 %", "Static data"],
             ["Priya et al. [11]", "RF / LR browser extension", "11,055 URLs", "97 %", "Latency and overhead not discussed"],
             ["Assefa and Katarya [14]", "Autoencoder, 16 features", "Small URL set", "91.24 %", "Lower than supervised models"],
             ["Fan [13]", "SVM + Naive Bayes ensemble", "Text, visual and URL features", "99.16 %", "Predefined features, scalability"]],
            "Comparison of selected related work (as summarised in [1])", widths=[0.19, 0.25, 0.19, 0.17, 0.2], font=9)


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms in the Literature")
    d.p("Most reviewed studies use a public benchmark: PhiUSIIL (235,804 URLs, 54 features) [17], the UCI phishing-websites dataset of Mohammad and "
        "McCluskey, or small collections of a few thousand URLs. Features come from three sources: the URL string, page content and "
        "external services. Studies that use only the URL string, as this project does, trade some accuracy for speed and safety, since no "
        "page is fetched [18], [19].")
    d.p("The algorithms are Random Forest [21], gradient-boosted trees such as XGBoost [22], logistic regression, support-vector machines, "
        "decision trees, and neural networks such as LSTM and CNN. Tree ensembles are popular on tabular features because they need little "
        "preprocessing, handle mixed feature scales and give feature importances; logistic regression is the standard linear baseline. "
        "These are the three algorithms compared in this project.")


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Work")
    d.table([["Strengths", "Limitations"],
             ["Very high reported accuracy on public benchmarks (97 % to 99.97 %).", "Static, small or historical datasets; models are obsolete on deployment."],
             ["Simple models with good features are competitive with deep networks.", "No structured, continuous retraining from new threat data."],
             ["URL-only features are cheap and safe to compute.", "Crowd input is not used as a live channel; reports are manual."],
             ["Browser extensions show client-side use is feasible.", "Latency, load and false-positive cost are rarely measured."],
             ["Human-in-the-loop verification improves data quality [15], [16].", "Verification adds delay and requires staff."]],
            "Strengths and limitations of the reviewed literature", widths=[0.5, 0.5], font=10)


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Static blacklist-based detection fails on zero-day phishing URLs, and few systems combine lexical, structural and domain features "
        "with continuously updated crowdsourced threat feeds. Three gaps follow from the literature, and the base paper names the same three [1]:")
    d.numbered(["**Dependence on static datasets.** Most models are trained once on historical data and cannot follow new attacks.",
                "**No dynamic adaptation.** There is rarely an automated mechanism that retrains with live threat intelligence.",
                "**Crowd input not operationalised.** Collective user knowledge is not turned into a structured, validated feed for the model."])
    d.p(f"PhishGuard addresses the three gaps at small scale: a labelled dataset is the starting point, a vote-based store with trusted feeds "
        f"supplies fresh evidence, and a retraining loop with hot reload applies it. The honest limits are that the dataset is small, the "
        f"verification is a vote count and not a human review, and the benefit of the loop on new campaigns is not measured (see Chapter 8).")


def sec_novelty(d):
    d.h2("Novelty against the Base Paper")
    d.p("PhishGuard follows the three-phase design of the base paper, so the architecture is not new. The differences below are the places where this "
        "project made its own choices; they are listed as differences, not as improvements, because the two systems were not evaluated on the same data.")
    d.table([["Aspect", "Base paper [1]", "PhishGuard"],
             ["Features", "54 URL and page-content features; 34 kept", "47 URL-only offline features in three named groups; no page fetch"],
             ["Model", "LSTM-attention + dense hybrid network", "Random Forest, XGBoost and Logistic Regression compared; best by F1 selected"],
             ["Explainability", "Not part of the system", "Red flags and a reason text with every verdict"],
             ["Crowd verification", "Administrator verifies novel URLs", "Net-vote consensus (2) and trusted public feeds; no administrator step"],
             ["Use of crowd verdicts", "Added to the training set; retrained periodically", "Applied at once at decision time, then added to training data (weight x3)"],
             ["False positives", "Not discussed as a crowd task", "Community can mark a URL safe; two net safe votes override the model"],
             ["Model update", "Periodic retraining", "Retrain from the interface or automatically after 25 new confirmations; hot reload without restart"],
             ["Evaluation of the crowd loop", "Learning-curve simulation", "Live end-to-end run on real feed data, plus a crowd-feedback experiment"],
             ["Deployment", "Not described", "Flask API, React interface, CLI, one-command start on Windows"]],
            "Differences between the base paper and PhishGuard", widths=[0.2, 0.38, 0.42], font=9.5)
    d.p(f"Two honest points go with the table. First, the base paper's accuracy (99.8 %) is far above this project's ({p(X['accuracy'])}); the datasets, "
        "features and models differ, and nothing here suggests the design is better. Second, replacing the administrator with a vote count makes the "
        "system faster to update but exposes the training data to coordinated false reports, which the base paper specifically warns against.")
