"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives, problem statement, literature table."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
OBJECTIVES = [
    "Assemble a labelled dataset of genuine and fabricated news articles.",
    "Preprocess the text with tokenisation, stop-word removal, stemming and vectorisation.",
    "Apply Principal Component Analysis to reduce feature dimensionality.",
    "Use the Firefly algorithm to optimise feature selection and MSVM parameters.",
    "Train a Multi-class Support Vector Machine classifier on the optimised feature set.",
    "Evaluate accuracy, precision, recall and F1-score against unoptimised baselines.",
]

PROBLEM_POINTS = [
    "Fabricated news reaches large audiences before any fact-check is published.",
    "High-dimensional text features make classifiers slow and prone to overfitting.",
    "Default classifier parameters give suboptimal accuracy on noisy news text.",
    "Many published detectors report accuracy without addressing computational cost.",
]
NEED = ("an optimised classifier that reduces feature dimensionality and tunes its own parameters to detect fabricated news accurately and efficiently.")

PROBLEM_STATEMENT = ("Given the text of a news item or claim, assign it one of three verdicts - REAL, PARTIALLY TRUE or FAKE - with a confidence, using a "
                     "computationally light pipeline (TF-IDF and stylometric features reduced by PCA, with the Firefly algorithm choosing the feature subset and "
                     "the SVM parameters), and report honestly how accurate and how costly it is, through an application that a non-expert can run.")

GAP = ("The surveyed work applies neural and transformer models to fake news detection. The gap is a computationally light pipeline where feature reduction and "
       "metaheuristic parameter tuning deliver comparable accuracy at lower cost.")

# (Work, Approach, Data, Reported result, Limitation); only facts from the PDFs read or the dataset card
LIT_TABLE = [
    ["Saad et al. 2026 [1] (base paper)", "CAMeLBERT contextual embeddings + neural network, class weighting for imbalance; compared with AraBERT, AraELECTRA, MARBERTv2 and resampling",
     "7,474 Arabic news articles (multi-source, part translated from LIAR / WELFake), binary real/fake, 80/20 split", "F1 96.19 %, accuracy 95.52 %, precision 95.48 %, recall 96.90 % (Tesla T4 GPU); TF-IDF + NN baseline accuracy 90.97 %",
     "Arabic, binary, GPU-based transformer; cross-domain generalisation and real-time use left as future work"],
    ["Dell'Oglio et al. 2026 [2]", "Experimental comparison of 12 approaches (classical ML, deep learning, transformers, cross-domain, LLMs) on 10 public datasets, labels harmonised to binary",
     "10 English datasets incl. LIAR-PLUS, Politifact, Isot", "LIAR-PLUS is the hardest dataset for nearly all models: F1 0.56 (LR) and 0.57 (SVM) in-domain; fine-tuned models generalise poorly across domains",
     "Binary harmonisation removes label nuance (no PARTIALLY TRUE class)"],
    ["Huang et al. 2025 [3]", "TF-IDF features, Transformer with BiGRU, Bayesian optimisation of hyper-parameters", "A fake/real news corpus (details in the paper)",
     "99.67 % test accuracy (BiGRU Transformer), 99.73 % with Bayesian optimisation", "Binary task; near-perfect score on its own data says little about harder fact-checking text"],
    ["Xu and Kechadi 2024 [4]", "Fuzzy deep hybrid network for fake news detection; releases LIAR2", "LIAR2: 18,369 / 2,297 / 2,296 statements, six labels",
     "Introduces the LIAR2 benchmark used for every real measurement in this project", "Deep model; the dataset card gives the split, not a cheap-pipeline baseline"],
    ["Wang 2017 [5]", "LIAR benchmark: short PolitiFact statements with six-way truthfulness labels", "About 12.8 k statements", "Text-only models score far below the usual fake/real benchmarks",
     "Short statements, six fine-grained labels"],
    ["Ahmed et al. 2017 [19]", "N-gram TF-IDF features with classical classifiers (including linear SVM)", "News article corpora", "Linear SVM among the strongest classical choices on n-gram TF-IDF",
     "Binary, article-level data"],
    ["Rashkin et al. 2017 [22]", "Linguistic analysis of varying degrees of falsehood in political fact-checking (LIAR-style scales) and of propaganda, hoax and satire", "PolitiFact statements and news corpora",
     "Shows that language cues differ between true, half-true and false content", "Analysis and classifiers on word-category features"],
    ["Potthast et al. 2018 [21]", "Style-based (stylometric) features separate hyperpartisan and fake from mainstream news", "BuzzFeed-Webis fact-checked news corpus", "Style alone detects hyperpartisan style better than truthfulness",
     "Style is a weak proxy for veracity"],
    ["Zhang et al. 2018 [25]; Xue et al. 2016 [24]", "Firefly-based and evolutionary feature selection for classification", "Benchmark classification datasets", "Metaheuristic feature selection can shrink feature sets at similar accuracy",
     "Search cost; gains depend on the data"],
]

# one short statement per source for the survey chapter, grouped by theme (keys into refs.KEY)
THEMES = {
    "Datasets and benchmarks": ["liar", "liar2", "compare"],
    "Classical and feature-based detection": ["ahmed", "perez", "potthast", "rashkin", "embed"],
    "Deep and transformer models": ["base", "hybrid", "bert"],
    "Optimisation and feature selection": ["firefly09", "firefly10", "fs_survey", "ffs"],
}
