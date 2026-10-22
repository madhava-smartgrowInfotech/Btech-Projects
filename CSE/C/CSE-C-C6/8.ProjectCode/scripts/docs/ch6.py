"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import cite

A = F.A


def _per_seed(key, fmt):
    return ", ".join(f"seed {s}: {fmt(v)}" for s, v in zip(A["seeds"], A[key]["values"]))


def methodology_blocks():
    tc = A["test_class_counts"]
    trc = A["train_class_counts"]
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P("The method is a classical supervised text-classification pipeline in which every stage is chosen to keep the model small and cheap to run on a CPU. A news statement is cleaned, turned into "
            "a sparse vector of word and word-pair weights (TF-IDF) and 25 hand-built stylistic measurements, standardised, compressed by Principal Component Analysis (PCA), and then classified by a "
            "multi-class Support Vector Machine (MSVM) with a radial-basis-function (RBF) kernel. The Firefly algorithm, a population-based metaheuristic, searches jointly for the subset of PCA components "
            f"to keep and for the SVM parameters C and gamma {cite('firefly09', 'firefly10')}. The classifier outputs one of three verdicts: REAL, PARTIALLY TRUE or FAKE, with a confidence. The steps are:"),
          N("**Assemble** a labelled corpus of statements with a truthfulness label (LIAR2 for the real measurements, a synthetic template corpus for the shipped demo model).",
            "**Clean** the text: lower-case, remove URLs, mentions and hashtags, keep letters only, drop stop words and tokens of two characters or fewer.",
            "**Featurise**: TF-IDF over unigrams and bigrams (vocabulary capped at 4,000 terms in the experiments) plus 25 stylometric features, 4,025 columns in all.",
            "**Standardise** every column and **reduce** with PCA (target 95 % of the variance, at most 300 components).",
            "**Split** the reduced vectors 80/20 with a stratified split; the Firefly search sees only the 80 % part.",
            "**Optimise**: the Firefly algorithm evolves a binary component mask and the values of C and gamma; a candidate's fitness is its 3-fold cross-validated macro-F1 minus a small penalty for the share of components kept.",
            "**Train and evaluate**: fit the final RBF SVM with balanced class weights on the masked training part, score the 20 % hold-out, and fit a default-parameter SVM on all components as the baseline.",
            "**Save and serve**: store the fitted vectoriser, scaler, PCA, mask, C, gamma, classifier and statistics in one `.pkl` bundle, used by the API, the command line and the Streamlit app."),
          FIG(F.diag("11_feature_pipeline.png"), "Shape of the data after each stage of the feature pipeline.", 5.6),
          P("**Evaluation protocol for the real-data results.** The pipeline code is the product's own (`src/pipeline.py`, unchanged). For LIAR2 a stratified subsample of "
            f"{F.NTRAIN:,} statements is drawn from the {F.NTRAIN_FULL:,}-statement training split, the pipeline is fitted on it, and the fitted model is scored on the complete official validation "
            f"({F.NVALID:,}) and test ({F.NTEST:,}) splits. This is repeated for {len(A['seeds'])} seeds ({', '.join(str(s) for s in A['seeds'])}); results are reported as mean and standard deviation. "
            "Beside the proposed pipeline the same test split scores (i) the default-parameter SVM on the same PCA space, (ii) an SVM using only the Firefly mask with default C and gamma, (iii) an SVM tuned by "
            "random search with exactly as many fitness evaluations as the Firefly run used and the same fitness function, (iv) three linear or probabilistic models on plain TF-IDF (complement naive Bayes, "
            "logistic regression, linear SVM) trained on the same subsample and on the full training split, and (v) a majority-class predictor. The subsample size is a compute limit: a Firefly run needs "
            f"about {A['n_firefly_evals']['mean']:.0f} cross-validated SVM fits.")]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          H3("6.2.1 LIAR2: the dataset behind every real measurement"),
          P(f"LIAR2 is a benchmark of about 23,000 short political statements checked by professional fact-checkers, released by Xu and Kechadi {cite('liar2')} as an extension of the LIAR dataset "
            f"of Wang {cite('liar')}. It was downloaded from the Hugging Face dataset `chengxuphd/liar2` (licence Apache-2.0) and is not redistributed with the submission; `data/liar2/` holds the "
            f"downloaded CSV files. The official 8:1:1 split gives {F.NTRAIN_FULL:,} training, {F.NVALID:,} validation and {F.NTEST:,} test statements, with an average of about 17.7 tokens per statement. Each "
            "statement carries one of six labels: pants-on-fire, false, barely-true, half-true, mostly-true, true. Only the `statement` text is used. The CSV also holds speaker, subject, "
            "justification and per-speaker historical counts of past ratings; these were deliberately left out because they leak the label (the justification is the fact-checker's verdict text, "
            "and the speaker counts record how often the same speaker was rated false) and would not exist for a new claim."),
          TAB("Mapping from the six LIAR2 labels to the three classes of the product", ["LIAR2 label (id)", "Project class", "Statements in the whole dataset"],
              [["true (5), mostly-true (4)", "REAL", "2,585 + 3,429 = 6,014"], ["half-true (3)", "PARTIALLY TRUE", "3,709"],
               ["barely-true (2), false (1), pants-on-fire (0)", "FAKE", "3,603 + 6,605 + 3,031 = 13,239"]],
              widths=[2.6, 1.5, 2.0], align=["l", "c", "c"], size=10),
          P("The mapping follows the one coded in `src/dataset.py` for LIAR-style word labels (true and mostly-true are REAL, half-true is PARTIALLY TRUE, the rest FAKE). The experiment script "
            "applies the same rule to the numeric ids. The result is imbalanced: FAKE is the majority class. "
            f"The test split holds {tc[0]} REAL, {tc[1]} PARTIALLY TRUE and {tc[2]} FAKE statements, so a predictor that always answers FAKE is right {tc[2] / F.NTEST * 100:.1f} % of the time; "
            f"the training subsample holds {trc[0]} / {trc[1]} / {trc[2]}. For this reason macro-F1, which weighs the three classes equally, is the headline metric and accuracy is always shown beside it."),
          H3("6.2.2 The synthetic demo corpus"),
          P("The repository also contains `build_demo_dataset` (`src/dataset.py`): a generator of a balanced three-class corpus from five sentence templates per class and ten topics, with a short phrase "
            "appended to about 30 % of the sentences. REAL templates read like official reports (\"... confirmed by independent experts with verified data\"), PARTIALLY TRUE templates mix a claim with "
            "doubt (\"... but experts say evidence is partial\"), and FAKE templates use clickbait words (\"SHOCKING secret ... miracle ... click now\"). The shipped model `models/msvm_model.pkl` was trained on "
            f"{F.DEMO['n_docs']} such documents (250 per class) with a hold-out of 150. Because the three classes differ in their template words alone, that model scores accuracy {F.DEMO['accuracy']:.3f} and macro-F1 "
            f"{F.DEMO['f1_macro']:.3f} on its own hold-out (Firefly fitness {F.DEMO['firefly_history'][-1]:.4f}); it is a pipeline check and a way to run the application without a download. "
            f"On the real LIAR2 test split the same model reaches accuracy {A['demo_model_on_liar2_test']['accuracy']:.3f} and macro-F1 {A['demo_model_on_liar2_test']['f1_macro']:.3f} and answers PARTIALLY TRUE for "
            f"{A['demo_model_prediction_counts'][1]:,} of the {F.NTEST:,} statements."),
          TAB("The two data sources", ["", "LIAR2 (real)", "Demo corpus (synthetic)"],
              [["Source", "Hugging Face `chengxuphd/liar2`, Apache-2.0", "`build_demo_dataset`, generated in code"],
               ["Documents used to fit", f"{F.NTRAIN:,} statements per run (subsample of {F.NTRAIN_FULL:,})", f"{F.DEMO['n_docs']} (250 per class)"],
               ["Evaluation", f"Official test split, {F.NTEST:,} statements; validation {F.NVALID:,}", "20 % hold-out of the same templates, 150 documents"],
               ["Class balance", "Imbalanced: FAKE is 57.6 % of the test split", "Balanced: 50 per class in the hold-out"],
               ["What a high score means", "Evidence about reading real claims", "Only that the template words separate the classes"]],
              widths=[1.5, 2.5, 2.5], align=["l", "l", "l"], size=10)]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing and feature construction"),
          H3("6.3.1 Text cleaning"),
          P("`clean_text` (`src/preprocessing.py`) prepares text for the TF-IDF vectoriser. It lower-cases the text, replaces URLs (`http://...`, `www...`) and tokens that start with `@` or `#` by a space, "
            "replaces line breaks and every character that is not an English letter by a space, collapses repeated spaces, splits on spaces and removes tokens that are stop words or have two characters or fewer. "
            "The stop-word list is a built-in set of 128 English function words, so no external download is needed. The function accepts any input: a non-string value returns an empty string. "
            "There is no stemming or lemmatisation; this differs from objective 2 of the project, which lists stemming, and is recorded as a deviation in Chapter 8. Because every non-letter is removed, "
            "digits and percentages (\"58 percent\", \"9.4%\") are discarded by the cleaner; they are still counted by the stylometric features, which read the raw text."),
          H3("6.3.2 TF-IDF features"),
          P(f"The cleaned text is vectorised with scikit-learn's `TfidfVectorizer` {cite('sklearn')}: unigrams and bigrams, sublinear term frequency (1 + ln tf), terms must occur in at least two documents "
            f"(`min_df=2`) and in at most 90 % of them (`max_df=0.9`), and the vocabulary is capped at `max_features` terms (4,000 in `train.py`, the Retrain screen and the experiments; 5,000 is the constructor "
            f"default). Rows are L2-normalised. On the 3,000-statement training subsample the vocabulary reaches the cap, giving 4,000 TF-IDF columns {cite('tfidf')}."),
          H3("6.3.3 The 25 stylometric features"),
          P("`stylometric_features` computes 25 numbers per document from the raw (uncleaned) text. They describe style rather than topic: length, punctuation, capitalisation, digits, lexical variety and the "
            "density of words from three small built-in lexicons. Style cues are a recognised, if weak, signal of veracity and hyperpartisanship "
            f"{cite('potthast', 'rashkin', 'perez')}."),
          TAB("The 25 stylometric features, in column order", ["#", "Feature", "Definition"],
              [["1", "chars", "Number of characters of the text"], ["2", "n_words", "Number of whitespace-separated words (at least 1)"], ["3", "n_sent", "Number of segments when splitting on . ! ? (at least 1)"],
               ["4", "avg_wlen", "Mean word length in characters"], ["5", "uniq_ratio", "Distinct words divided by words"], ["6", "stop_ratio", "Share of words that are stop words"],
               ["7", "pos", "Share of words from the positive lexicon (true, great, excellent, verified, confirmed, official, evidence, proven, real, accurate, trust)"],
               ["8", "neg", "Share of words from the negative lexicon (shocking, secret, unbelievable, miracle, hoax, conspiracy, exposed, urgent, breaking, viral, click, banned, hidden)"],
               ["9", "sens", "Share of words from the sensational lexicon (11 entries; \"you wont believe\" is a three-word entry that a single-token match can never hit)"],
               ["10", "caps_ratio", "All-capital words (two letters or more) divided by words"], ["11", "upper", "Count of all-capital words"], ["12", "exclaim", "Number of exclamation marks"],
               ["13", "question", "Number of question marks"], ["14", "punct_ratio", "Punctuation characters divided by characters"], ["15", "words_per_sent", "Words divided by sentences"],
               ["16", "long_word_ratio", "Share of words longer than 6 characters"], ["17", "short_word_ratio", "Share of words of 3 characters or fewer"], ["18", "digit_ratio", "Digits divided by characters"],
               ["19", "exclaim_flag", "1 if more than 2 exclamation marks, else 0"], ["20", "question_flag", "1 if more than 1 question mark, else 0"], ["21", "url_flag", "1 if the text contains a URL"],
               ["22", "urls", "Number of URLs"], ["23", "first_person", "Share of words in {i, we, us, our, my}"], ["24", "superlative", "Share of words longer than 5 characters ending in \"est\""],
               ["25", "neg_minus_pos", "neg minus pos"]],
              widths=[0.4, 1.4, 4.4], align=["c", "l", "l"], size=9),
          P("The features have very different scales, which is why the next stage standardises every column. The 4,025 columns are stored densely (about 100 MB for 3,000 documents), one reason the pipeline suits only corpora of a few thousand documents.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          TAB("Why each component was chosen, and what the measurements say", ["Component", "Role", "Why chosen", "What was found"],
              [["TF-IDF (1-2 grams)", "Sparse word and word-pair weights", f"Cheap, needs no pre-trained model or GPU, standard strong baseline for text {cite('tfidf', 'ahmed')}; bigrams catch short phrases",
                f"Linear models on TF-IDF alone reach macro-F1 {F.pm(A['ref_full_LogisticRegression_test'])} (logistic regression, full training split)"],
               ["25 stylometric features", "Style signals: caps, punctuation, lexicon density", "Cheap and interpretable; the lexicons also drive the cue words shown in the interface",
                "Not ablated separately; their individual contribution is not measured"],
               ["StandardScaler", "Zero mean, unit variance per column", "PCA and RBF-SVM are scale sensitive; stylometric columns are on very different scales",
                "Also gives rare TF-IDF terms the same variance as common ones, which spreads variance over many components"],
               ["PCA", "Dense low-dimensional representation", f"The task statement asks for dimensionality reduction; shrinks 4,025 columns before the SVM {cite('pca', 'pca87')}",
                f"Cap of 300 components keeps only {F.pct(A['pca_variance']['mean'])} of the variance on real text, far below the 95 % target"],
               ["Firefly algorithm", "Joint search of component mask, C, gamma", f"Metaheuristic that handles a mixed binary and continuous search space without gradients {cite('firefly09', 'firefly10', 'ffs', 'fs_survey')}",
                f"Fitness {A['firefly_fitness_best']['mean']:.4f} against {A['random_fitness_best']['mean']:.4f} for equal-budget random search, but no clear gain on the test split (Chapter 8)"],
               ["RBF multi-class SVM", "Final classifier", f"Margin classifier that works well with a few thousand dense, moderate-dimension samples {cite('svm', 'msvm')}",
                f"Test macro-F1 {F.pm(A['proposed_test'])}"],
               ["Balanced class weights", "Rescales the penalty C per class", f"FAKE is the majority class; weighting counteracts imbalance without resampling {cite('imbalance', 'base')}",
                "Raises recall of the minority classes at the cost of accuracy: the weighted model scores accuracy below the 0.576 majority baseline but macro-F1 above it (0.244)"],
               ["Platt scaling (`probability=True`)", "Class probabilities for the interface", f"The interface shows a confidence and a probability per class {cite('platt')}",
                f"Probabilities and verdict disagree on {F.pct(F.LV['disagree_rate'])} of the real test statements (Section 6.6.3)"]],
              widths=[1.2, 1.3, 2.1, 1.9], align=["l", "l", "l", "l"], size=9),
          P("**Why not a transformer.** The base paper's strongest system uses contextual transformer embeddings with a neural network on a GPU, reaching accuracy 95.52 % on a binary Arabic task "
            f"{cite('base')}; fine-tuned transformers also dominate the comparison of Dell'Oglio et al. {cite('compare')}. The gap named by this project is the opposite end of the trade-off: a pipeline "
            "that a student laptop can train and run without a GPU, whose cost is dominated by a search that can be shortened or switched off. The measurements in Chapter 8 test whether that cheaper pipeline "
            "keeps enough accuracy; the honest answer on LIAR2 is that it does not beat even simpler linear models, so the choice is justified by cost and transparency, not by accuracy.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Mathematical formulation"),
          H3("6.5.1 TF-IDF"),
          P("For term t in document d, with n documents and document frequency df(t), scikit-learn's smoothed, sublinear weight is"),
          EQ("w(t, d) = (1 + ln tf(t, d)) · idf(t),     idf(t) = ln((1 + n) / (1 + df(t))) + 1"),
          P("and each document vector is scaled to unit Euclidean length. Standardisation of every column j of the concatenated matrix is"),
          EQ("z(i, j) = (x(i, j) − μ_j) / σ_j"),
          H3("6.5.2 PCA"),
          P("Let Z be the standardised n × p matrix and λ_1 ≥ λ_2 ≥ ... the eigenvalues of its covariance matrix. The principal components are the corresponding eigenvectors and the projection keeps the first k "
            "components, where k is the smallest number whose explained-variance share reaches 0.95, then limited to the range 10 to 300 (and to n − 1):"),
          EQ("k = min( max(10, min(k_95, 300, n − 1)), p ),     k_95 = min{ k : (λ_1 + ... + λ_k) / (λ_1 + ... + λ_p) ≥ 0.95 }"),
          P(f"On the LIAR2 subsample k_95 is far larger than 300, so the cap decides: k = {int(A['n_pca']['mean'])} in every run and the retained variance is {F.pct(A['pca_variance']['mean'])} ± {F.pct(A['pca_variance']['std'])}."),
          H3("6.5.3 SVM with RBF kernel and class weights"),
          P("The kernel and the weighted soft-margin problem for a binary sub-problem are"),
          EQ("K(x, x') = exp(−γ ‖x − x'‖²)"),
          EQ("min over w, b, ξ :  ½ ‖w‖² + C · Σ_i c(y_i) · ξ_i      subject to  y_i (wᵀφ(x_i) + b) ≥ 1 − ξ_i,  ξ_i ≥ 0"),
          EQ("c(k) = n / (K · n_k)     (class_weight = \"balanced\", K = 3 classes, n_k = documents of class k)"),
          P("scikit-learn's `SVC` handles three classes by training K(K − 1)/2 = 3 one-versus-one binary classifiers and predicting by voting; the option `decision_function_shape=\"ovr\"` used here only reshapes "
            "the decision values into one score per class and does not change the predicted label. The project's \"MSVM\" is therefore this one-versus-one machine with a one-versus-rest view of its scores "
            f"{cite('msvm')}."),
          H3("6.5.4 Firefly search"),
          P("Each firefly i is a vector x_i of length d = n_c + 2, where n_c is the number of PCA components: n_c mask logits followed by log10 C and log10 gamma. It is decoded as"),
          EQ("m_k = 1 if sigmoid(x_ik) > 0.5 else 0 ;   C = 10^clip(x_i,n_c+1, −1, 3) ;   γ = 10^clip(x_i,n_c+2, −4, 1)"),
          P("(if no mask bit is set, the component with the largest logit is switched on). Brightness is the fitness: the mean macro-F1 of a stratified 3-fold cross-validation of the RBF SVM "
            "(balanced weights) on the masked training data, less a penalty on the size of the subset; a mask with fewer than two components scores 0:"),
          EQ("f(x_i) = F1_macro^(3-fold)(m, C, γ) − 0.02 · |m| / n_c"),
          P("A less bright firefly i moves toward each brighter firefly j. The attractiveness decays with the squared distance r², normalised by the dimension, and a random step shrinks every generation g:"),
          EQ("β = β_0 · exp(−γ_f · r_ij² / d) ,     r_ij² = ‖x_i − x_j‖² ,     α_g = α_0 · 0.97^g"),
          EQ("x_i ← x_i + β (x_j − x_i) + α_g · 2(u − ½) ,     u ~ Uniform(0, 1)^d"),
          P("with β_0 = 1, γ_f = 1 and α_0 = 0.2 (the absorption coefficient γ_f is the algorithm's own and is unrelated to the SVM's gamma). After each move the two hyper-parameter coordinates are clipped to their "
            "ranges and the firefly's brightness is recomputed, so every move costs one cross-validation. At the end of each generation the best vector so far is remembered and the dimmest firefly is "
            "replaced by that vector plus a small random step (elitism). The initial population is uniform in [−1, 1] for the mask logits, [−1, 2] for log10 C and [−3, 0] for log10 gamma. "
            f"With 10 fireflies and 12 generations a run made {_per_seed('n_firefly_evals', lambda v: str(int(v)))} fitness evaluations."),
          FIG(F.diag("10_core_algorithm_flowchart.png"), "Flowchart of the Firefly search and of the final model.", 4.4),
          H3("6.5.5 Metrics and Platt scaling"),
          EQ("P_k = TP_k / (TP_k + FP_k) ,     R_k = TP_k / (TP_k + FN_k) ,     F1_k = 2 P_k R_k / (P_k + R_k) ,     macro-F1 = (F1_1 + F1_2 + F1_3) / 3"),
          P("Macro-F1 gives the small PARTIALLY TRUE class the same weight as FAKE. The class probabilities shown in the interface come from Platt scaling: libsvm fits a sigmoid to the decision values by an "
            "internal 5-fold cross-validation and couples the pairwise results into three probabilities,"),
          EQ("P(y = 1 | f) = 1 / (1 + exp(A f + B))"),
          P("The sigmoid is fitted on the original class frequencies, whereas the class-weighted decision function that produces the verdict is not; this is the origin of the disagreement documented "
            "in Section 6.6.3.")]

    # ------------------------------------------------------------------ 6.6
    cfg = [["TF-IDF", "ngram (1, 2), sublinear tf, min_df 2, max_df 0.9, max_features 4,000 (class default 5,000)"],
           ["Stylometric features", "25 columns, concatenated: 4,025 in total"],
           ["Scaling", "StandardScaler, fitted on all training documents"],
           ["PCA", "95 % variance target, at least 10 and at most 300 components (`pca_max`), `random_state` 42"],
           ["Split", "80 / 20 stratified (`test_size` 0.2, `random_state` 42) of the PCA vectors"],
           ["Firefly", "10 fireflies, 12 generations in `train.py`, the Retrain screen and the experiments (class defaults 12 and 15); α_0 0.2, β_0 1, γ_f 1, penalty 0.02, 3-fold CV, decay 0.97"],
           ["SVM", "kernel rbf, `class_weight` balanced, `decision_function_shape` ovr, `probability` True, `random_state` 42; C and gamma from the Firefly search"],
           ["Baseline", "`SVC(class_weight=\"balanced\")` with default C = 1 and gamma = \"scale\" on all PCA components"],
           ["Experiments", f"{F.NTRAIN:,}-statement stratified subsample, seeds {', '.join(str(s) for s in A['seeds'])}"],
           ["Hardware", F.HARDWARE],
           ["Software", F.SOFTWARE]]
    b += [H2("6.6 Model architecture and training configuration"),
          H3("6.6.1 Architecture of the trained model"),
          P("The trained model is the chain vectoriser, scaler, PCA, mask, SVM. `FakeNewsMSVMPipeline.save` writes all of these, with the best mask, C, gamma and the statistics of the run, into one joblib file. "
            "`load` rebuilds the pipeline from the file, so the Firefly optimiser exists at prediction time only as its best mask. The data shrinks as in the figure below: "
            f"4,025 columns, {int(A['n_pca']['mean'])} PCA components and {A['n_selected']['mean']:.0f} ± {A['n_selected']['std']:.0f} selected components."),
          FIG(F.fig("f08_feature_funnel.png"), "Feature counts after each stage (mean of three runs).", 3.8),
          TAB("Training configuration", ["Item", "Setting"], cfg, widths=[1.5, 5.0], align=["l", "l"], size=9.5),
          P("The vectoriser, scaler and PCA are fitted on all documents given to `fit`, including the 20 % held out inside the pipeline. This uses no labels, but it makes the internal hold-out score (shown on the Analytics screen) slightly optimistic; Chapter 8 therefore reports scores on the separate official test split. The final SVM is trained on the 80 % part only (2,400 of 3,000 statements)."),
          H3("6.6.2 What the search found"),
          TAB("Firefly results per run (10 fireflies, 12 generations)", ["Seed", "Components kept (of 300)", "C", "gamma", "Best fitness (CV)", "Search + fit time (s)"],
              [[str(s), str(A["n_selected"]["values"][i]), f"{A['best_C']['values'][i]:.2f}", f"{A['best_gamma']['values'][i]:.5f}", f"{A['firefly_fitness_best']['values'][i]:.4f}",
                f"{A['train_time_s']['values'][i]:.0f}"] for i, s in enumerate(A["seeds"])],
              widths=[0.7, 1.4, 0.8, 1.0, 1.3, 1.4], align=["c", "c", "c", "c", "c", "c"], size=10),
          P(f"The three runs choose very different values of C ({min(A['best_C']['values']):.1f} to {max(A['best_C']['values']):.1f}) and about half of the components, which already suggests that the "
            "fitness surface is flat: many settings are almost equally good. the figure below shows the best fitness found in each generation. Most of the improvement comes in the first four generations. "
            f"The search costs {A['train_time_s']['mean']:.0f} ± {A['train_time_s']['std']:.0f} s per run, against {A['baseline_time_s']['mean']:.1f} s for one default SVM fit; "
            f"an equal-budget random search needs {A['random_search_time_s']['mean']:.0f} s."),
          FIG(F.fig("f02_firefly_convergence.png"), "Best fitness per generation for the three runs; dotted lines mark the best fitness of the equal-budget random search of the same run.", 4.2),
          H3("6.6.3 Verdict and probabilities"),
          P("`predict` returns two things: the class from `SVC.predict`, which uses the class-weighted decision function, and `predict_proba`, the Platt-scaled probabilities. The Detect screen displays the class as the "
            "verdict and the largest probability as the confidence. On real data the two differ: "
            f"on {F.LV['disagree_n']:,} of {F.NTEST:,} test statements ({F.pct(F.LV['disagree_rate'])}) the verdict is not the class with the highest probability, the probabilities name FAKE as the top class for "
            f"{F.LV['argmax_counts'][2]:,} statements, and PARTIALLY TRUE is never the top-probability class (it is the verdict for {F.LV['label_counts'][1]} statements). Using the largest probability as the verdict would "
            f"give accuracy {F.LV['acc_if_argmax']:.3f} but macro-F1 only {F.LV['f1_if_argmax']:.3f}, because it almost always answers FAKE. The behaviour is documented as a limitation; no change was made to the code.")]
    return b


def application_blocks():
    LATL = F.LAT[0]
    b = []

    b += [H2("6.7 Application architecture"),
          P("The product has a three-tier structure and keeps every earlier entry point working. The **library** `src/` (preprocessing 91 lines, dataset 110, Firefly 106, pipeline 181) contains all "
            "model logic and has no web dependency. The **API layer** `backend/main.py` (339 lines, FastAPI) is a thin wrapper: every endpoint calls the same pipeline functions that the command line and the "
            "Streamlit app call, and no model logic lives in it. The **web interface** `frontend/` (React 18, TypeScript, Vite, Tailwind CSS; about 4,900 lines, of which the six page components are 1,300) "
            "talks to the API through one axios client on `/api`, proxied by the Vite server so no port is hard-coded in the browser code. The older entry points `train.py`, `predict.py` and `app.py` (Streamlit) "
            "remain and use the same model file."),
          TAB("Main files", ["File or folder", "Role"],
              [["`src/preprocessing.py`", "`clean_text`, `stylometric_features`, stop words, class labels"], ["`src/dataset.py`", "`load_csv` (CSV, ISOT and LIAR layouts), `build_demo_dataset`"],
               ["`src/firefly.py`", "`FireflyOptimizer`: decode, fitness, optimise"], ["`src/pipeline.py`", "`FakeNewsMSVMPipeline`: fit, transform, predict, save, load"],
               ["`backend/main.py`", "FastAPI application, endpoints, validation, retraining job"], ["`frontend/src/pages/`", "Landing, Detect, Batch, Analytics, Retrain, About, NotFound"],
               ["`models/`", "`msvm_model.pkl` (demo model), `liar2_msvm_model.pkl`, `metrics.json`"],
               ["`scripts/`, `run.bat`", "Tests, experiments, measurement and document builders; one-click launcher (ports 8406 and 5406)"]],
              widths=[2.3, 4.2], align=["l", "l"], size=10),
          P("**Model state.** The API holds exactly one fitted pipeline in memory (`get_pipe`), protected by a re-entrant lock. It is loaded from the path in the environment variable `FAKENEWS_MODEL` "
            "(default `models/msvm_model.pkl`) when the server starts; if the file does not exist the server trains a small demo model on the synthetic corpus (250 documents per class, 8 fireflies, "
            f"8 generations) and saves it. Loading takes {LATL['startup_s']:.1f} s for the 12.6 MB LIAR2 model and {F.LAT[1]['startup_s']:.1f} s for the 0.85 MB demo model, measured from process start to the first successful health check."),
          P("**Retraining.** `POST /api/retrain` validates the request, reads the optional CSV into texts and labels, creates a job record and starts a daemon thread that fits a new pipeline, writes it to a "
            "temporary file and replaces the model file with `os.replace`, then swaps the in-memory pipeline under the lock. The browser polls `GET /api/retrain/{job_id}` every 2 seconds. Only one job may run at a time. "
            "While training runs, `/api/predict` keeps using the old model, so detection never stops.")]

    b += [H2("6.8 API design"),
          P("All routes are under `/api` and exchange JSON (uploads use multipart form data). The interactive OpenAPI documentation is served at `/docs` by FastAPI."),
          TAB("Endpoints", ["Method and path", "Request", "Response", "Errors"],
              [["GET `/api/health`", "-", "`status`, `model_loaded`, `model_path`", "-"],
               ["GET `/api/model`", "-", "`labels`, `stats` (accuracy, macro-F1, PCA and Firefly facts, confusion matrix, report, baseline; the raw test predictions are removed), `pipeline` steps", "-"],
               ["GET `/api/samples`", "-", "Six real documents from the demo corpus, two per class", "-"],
               ["POST `/api/predict`", "JSON `{title, text}`", "`label`, `label_id`, `confidence`, `probabilities`, `latency_ms`, `word_count`, `cues{sensational, credibility}`", "422 if fewer than 5 words"],
               ["POST `/api/batch/preview`", "multipart `file` (.csv)", "`filename`, `n_rows`, `columns`, `guessed_column`, first 10 rows", "400 not a CSV, empty, unreadable; 413 over 25 MB"],
               ["POST `/api/batch/run`", "multipart `file`, `column`", "`n_rows`, `seconds`, `rows[{row, text, predicted, confidence}]`, `distribution`, `csv`", "400 bad column; 413 over 20,000 rows or 25 MB"],
               ["POST `/api/retrain`", "multipart optional `file`, `fireflies`, `generations`, `max_tfidf`", "202 `{job_id}`", "422 out of range; 400 bad CSV or under 30 rows; 409 a job is running"],
               ["GET `/api/retrain/{job_id}`", "-", "`status` running / done / error, `elapsed_s`, `source`, `settings`, `result` or `error`", "404 unknown job (also after a restart)"]],
              widths=[1.4, 1.5, 2.4, 1.2], align=["l", "l", "l", "l"], size=9),
          P("The cue words returned by `/api/predict` come from two fixed lists in the backend: 13 sensational words (shocking, secret, unbelievable, miracle, hoax, conspiracy, exposed, urgent, breaking, "
            "viral, click, banned, hidden) and 8 credibility words (official, confirmed, verified, evidence, report, data, expert, audit). They only illustrate the verdict, and on real statements they rarely match.")]

    b += [H2("6.9 Security and error handling"),
          P("The application is a local tool without accounts, so security work is limited to input validation and safe handling of files. What exists, and what does not, is stated below."),
          TAB("Validation and safety measures", ["Concern", "Measure"],
              [["Upload type, size and rows", "More than 20,000 rows or 25 MB gives 413; only `.csv` names accepted; empty or unreadable files are rejected with 400"],
               ["Free-text input", "A statement needs at least five words (title and text joined) or the API answers 422; the browser shows the same rule before sending"],
               ["Parameter ranges", "Fireflies 4-20, generations 3-30, max TF-IDF 1,000-8,000; otherwise 422"],
               ["Concurrent retraining", "A second retraining request while one runs gets 409; the job store is a dictionary guarded by the single-job rule"],
               ["Uploaded training data", "Written to a temporary file that is deleted in a `finally` block after parsing; fewer than 30 rows or an unknown label column gives 400"],
               ["Model file integrity", "A new model is written to `<model>.tmp` and moved into place with `os.replace`, so a crash cannot leave a half-written model; the live pipeline is swapped under a lock"],
               ["Cross-origin access", "CORS allows only `http://localhost:5406` and `http://127.0.0.1:5406`"],
               ["Output encoding", "The React interface renders text through JSX, which escapes HTML; a test confirms that script tags in an article do not break `/api/predict`"],
               ["Privacy", "Rows are read by the local backend only and are not stored"]],
              widths=[1.8, 4.7], align=["l", "l"], size=9.5),
          P("**Not implemented:** authentication, authorisation, rate limiting, HTTPS, audit logging, and any protection of the model file against replacement by the Retrain screen (it overwrites the "
            "file by design, and the interface asks for confirmation first). Pickle files can execute code when loaded, so a model file must come from a trusted source; loading a model pickled with a different "
            "scikit-learn version may fail, so `run.bat` installs the version the shipped model needs. These gaps are acceptable for a local demonstration and would have to be closed before any "
            "multi-user deployment.")]

    b += [H2("6.10 Installation and execution"),
          P(f"The measurements were made on: {F.HARDWARE}. Python 3.11 or newer and Node.js 20 or newer are required."),
          H3("6.10.1 One-click start"),
          N("Double-click `run.bat`. It checks that Python and Node.js are installed.",
            "It builds `.venv` (and rebuilds it if a copy from another computer does not run) and installs `backend/requirements.txt` (scikit-learn, pandas, NumPy, SciPy, joblib, FastAPI, uvicorn, python-multipart).",
            "It runs `npm install` in `frontend/` on the first start.",
            "It starts the backend on port 8406, waits until `/api/health` answers, then starts the frontend on port 5406 and opens http://localhost:5406.",
            "Closing the two minimised windows stops the servers."),
          H3("6.10.2 By hand"),
          CODE("python -m venv .venv\n.venv\\Scripts\\python -m pip install -r backend/requirements.txt\n.venv\\Scripts\\python -m uvicorn backend.main:app --port 8406\n\ncd frontend\nnpm install\nnpm run dev            # http://localhost:5406", 9),
          H3("6.10.3 Command line, Streamlit and checks"),
          CODE("python train.py                       # demo corpus, writes models/msvm_model.pkl and metrics.json\npython train.py --csv data/my.csv --fireflies 10 --generations 12 --max-tfidf 4000\npython predict.py --text \"Official report confirmed by experts with verified data\"\nstreamlit run app.py                  # the original interface\n\npython scripts/smoke_test.py          # API end to end on a copy of the model\npython scripts/unit_edge_tests.py     # library and edge-case tests\ncd frontend && npm run build          # type-check and production build", 9),
          P("A training CSV needs a `text` column (and optionally `title`) and a `label` column holding REAL, PARTIALLY TRUE, FAKE, the numbers 0, 1, 2, or LIAR's word labels. Numeric six-way LIAR2 ids must "
            "be converted to the three class names first, because `load_csv` reads the numbers 0, 1 and 2 as the project's classes directly. Retraining from the Retrain screen replaces "
            "`models/msvm_model.pkl`; keep a copy to return to the shipped model. To reproduce the real-data results: download the three LIAR2 CSV files into `data/liar2/`, run "
            "`scripts/run_experiments.py --seed 42` (and 7, 2024) with the project's Python, then `scripts/docs_build/make_figures.py`.")]
    return b


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] +methodology_blocks() + application_blocks()
