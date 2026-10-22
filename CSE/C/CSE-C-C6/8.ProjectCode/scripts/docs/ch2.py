"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, EQ, H1, H2, H3, N, P, TAB
from .lit import LIT_TABLE
from .refs import cite


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P("This chapter reviews the work on which the project builds and against which it must be judged. It starts with the base paper assigned to the batch "
          f"{cite('base')}, analyses it in detail, and then groups related work by theme: datasets and benchmarks, classical and feature-based detection, deep and transformer "
          "models, and optimisation and feature selection. It then describes the datasets and algorithms the project itself uses, summarises the strengths and limitations of "
          "the approaches, lists the additional sources named in the project's literature survey, and ends with the research gap."),
        P("Two comments on method. Numerical results are quoted only where we read them in the paper itself (this holds for the base paper, for the experimental comparison "
          f"{cite('compare')}, for the Bayesian-optimisation paper {cite('hybrid')} and for the LIAR2 dataset card) or where a publisher's record states the bibliographic details. "
          "For the other works the table gives the approach and the stated limitation without reproducing figures that we did not verify."),

        H2("2.2 Analysis of the Base Paper"),
        P("The base paper is \"An algorithmic system for Arabic fake news detection using neural networks and transformer embeddings with class weighting\" by Saad, Abdelrazek "
          f"and Abdelmaksoud, published in Scientific Reports in 2026 {cite('base')}. Its subject is binary detection of fake news in Arabic. Its starting observation is that Arabic "
          "is under-explored because datasets are limited and the language is morphologically and semantically complex, and that existing Arabic systems rely on classical learners, "
          "data-level resampling (undersampling, oversampling, SMOTE) or transformer models, each with a known weakness: synthetic noise in SMOTE, over-fitting in oversampling and data "
          "loss in undersampling."),
        H3("2.2.1 Problem and idea"),
        P("The authors argue that algorithm-level class weighting, which changes the loss function instead of the data, has been little studied for Arabic fake news. Their "
          "framework has three parts. First, class weighting counters the imbalance between real and fake articles. Second, CAMeLBERT is used as a fixed feature extractor, "
          "giving contextual embeddings that they report as better than TF-IDF and bag-of-words. Third, a neural-network classifier models the non-linear relations in the dense "
          "embedding space. The paper compares four Arabic transformers (CAMeLBERT, AraBERT, AraELECTRA and MARBERTv2) and four imbalance strategies (class weighting, undersampling, "
          "oversampling and SMOTE), and adds LIME and SHAP analyses to explain the classifier."),
        H3("2.2.2 Data and experimental set-up"),
        P("The dataset has 7,474 Arabic news articles from 2015 to 2025. About 45 % come from established news agencies, about 30 % from blogs, open Facebook pages and user posts "
          "that the team labelled against fact-checking platforms, and about 25 % from benchmark datasets such as WELFake and LIAR whose articles were translated into Arabic and "
          "post-edited by a native speaker. Labelling quality was checked by double-coding a subset of 500 samples, giving a Fleiss' kappa of 0.80. The split is 80 % training and "
          "20 % testing with a fixed random state of 44. CAMeLBERT inputs are limited to 128 tokens; the classifier is trained with the Adam optimiser and binary cross-entropy "
          "weighted by class, with batch size 16, learning rate 0.0005, 256 dense units, dropout 0.2 and 10 epochs. Experiments ran on a Tesla T4 graphics processor with 12 GB of memory."),
        H3("2.2.3 Results reported"),
        TAB("Results of the base paper [1] (as stated in the paper; binary Arabic task)", ["Configuration", "Reported value"], [
            ["TF-IDF (2,000 uni- and bigram features) + neural network", "accuracy 90.97 %, F1 92.20 %"],
            ["TF-IDF + decision tree", "accuracy 88.03 %, F1 89.73 %"],
            ["CAMeLBERT embeddings + neural network", "accuracy 93.98 %, F1 95.05 %, recall 99.08 %, ROC-AUC 98.65 %"],
            ["CAMeLBERT + SMOTE + neural network", "F1 95.71 %"],
            ["CAMeLBERT + undersampling + neural network", "accuracy 92.51 %"],
            ["CAMeLBERT + class weighting + neural network (proposed)", "accuracy 95.52 %, F1 96.19 %, precision 95.48 %, recall 96.90 %"],
        ], widths=[3.4, 2.9], align=["l", "l"]),
        H3("2.2.4 Strengths and stated limits"),
        P("The paper is careful in several respects: it validates label quality with an agreement statistic, it compares several transformers and several imbalance techniques "
          "under one protocol, it reports accuracy, precision, recall, F1 and ROC-AUC, it keeps a TF-IDF baseline for reference, and it explains predictions with LIME and SHAP. "
          "The authors name as future work the assessment of cross-domain generalisation and the feasibility of real-time deployment, and they describe the system as suitable for "
          "resource-constrained applications although the reported hardware is a graphics processor."),
        H3("2.2.5 Relation to this project"),
        P("It is important to be precise about what the project takes from this paper and what it does not. It takes three ideas: handle class imbalance at the algorithm level "
          "(the SVM here uses balanced class weights), report several metrics instead of accuracy alone, and compare against baselines. It does not use transformer embeddings, "
          "it works in English, and its task has three classes instead of two. The data, language, task and compute therefore differ, and the numbers of the two works are not "
          "comparable; Chapter 8 presents the comparison as context only. The base paper's own TF-IDF-plus-neural-network baseline (accuracy 90.97 %) shows that classical features "
          "are a respectable starting point on its data, which is the premise on which the present pipeline is built."),

        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Datasets and benchmarks"),
        P(f"Wang introduced LIAR, a collection of short statements from PolitiFact with six truthfulness labels, as a benchmark for fine-grained fake news detection {cite('liar')}. "
          f"Xu and Kechadi extended it to LIAR2, about 23 thousand statements split 18,369 / 2,297 / 2,296 for training, validation and testing {cite('liar2')}; LIAR2 is the dataset "
          f"used for every real measurement in this project. Dell'Oglio et al. compared 12 approaches on 10 public datasets after harmonising labels to real and fake {cite('compare')}. "
          "They found that LIAR-PLUS, the six-class LIAR extended with justification text, was the most challenging dataset for nearly all models: in-domain logistic regression scored an "
          "F1 of 0.56 and a support vector machine 0.57, and a fine-tuned transformer trained on a generic aggregate could not exceed an F1 of 0.57 on it. They attribute part of the "
          "difficulty to the blurry boundary between fabrication and half-truth, which is exactly the boundary the third class of this project tries to represent."),
        H3("2.3.2 Classical and feature-based detection"),
        P(f"Ahmed, Traore and Saad used n-gram TF-IDF features with several classical learners, among which a linear SVM was strong {cite('ahmed')}. Perez-Rosas et al. built "
          f"fake-news corpora and showed that linguistic features carry signal {cite('perez')}. Potthast et al. showed that style-based features can separate hyperpartisan and "
          f"mainstream news, although style is a weak proxy for truthfulness {cite('potthast')}. Rashkin et al. analysed the language of different degrees of falsehood in political "
          f"fact-checking and in propaganda, hoax and satire, which supports giving middle grades such as half-true their own class {cite('rashkin')}. Al-Tarawneh et al. compared TF-IDF, "
          f"Word2Vec and FastText with classical and deep classifiers {cite('embed')}. The 25 stylometric features of this project (capital letters, exclamation and question marks, "
          "digits, lexicon ratios) follow this line."),
        H3("2.3.3 Deep and transformer models"),
        P(f"BERT {cite('bert')} made contextual embeddings the standard input for text classifiers, and the base paper uses a language-specific variant {cite('base')}. Huang et al. "
          f"combined TF-IDF features with a Transformer and a bidirectional recurrent unit and tuned it with Bayesian optimisation, reporting 99.67 % test accuracy without and "
          f"99.73 % with the Bayesian step {cite('hybrid')}. The comparison of Dell'Oglio et al. {cite('compare')} shows that fine-tuned models do well in-domain and degrade across "
          "domains. Near-perfect scores on a single corpus therefore say little about harder fact-checking text, a caution that applies, in a different way, to the 100 % score of "
          "this project's own synthetic demonstration model."),
        H3("2.3.4 Optimisation and feature selection"),
        P(f"The Firefly algorithm was proposed by Yang as a swarm method in which each candidate solution is a firefly whose brightness is its fitness and which moves towards brighter "
          f"ones {cite('firefly09', 'firefly10')}. Xue et al. surveyed evolutionary computation for feature selection {cite('fs_survey')}, and Zhang et al. applied firefly optimisation "
          f"to feature selection for classification and regression {cite('ffs')}. These works motivate using a metaheuristic to choose a feature subset and to tune a classifier at the "
          "same time, at the price of repeated model evaluations. Class imbalance, the other recurring difficulty, is reviewed by He and Garcia "
          f"{cite('imbalance')} and handled in this project by class weights."),
        H3("2.3.5 Surveys"),
        P(f"Shu et al. {cite('shu')} and Zhou and Zafarani {cite('survey')} organise the field by content, style, propagation and source, and Vosoughi et al. {cite('vosoughi')} document how "
          "false news spreads. They define the setting in which a text-only detector sits: it can use the content and style of the statement but not who said it, who shared it or what "
          "evidence exists."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [list(r) for r in LIT_TABLE],
            widths=[1.15, 1.45, 1.1, 1.3, 1.1], size=9, align=["l", "l", "l", "l", "l"]),

        H2("2.4 Datasets and Algorithms Used in This Project"),
        H3("2.4.1 Datasets"),
        P(f"LIAR2 {cite('liar2')} is released under the Apache-2.0 licence and consists of PolitiFact statements labelled by professional fact-checkers with six grades: pants-on-fire, "
          f"false, barely-true, half-true, mostly-true and true. The official split has {F.NTRAIN_FULL:,} training, {F.NVALID:,} validation and {F.NTEST:,} test statements, with an average "
          "length of about 18 tokens. The project maps the grades to three classes: true and mostly-true to REAL, half-true to PARTIALLY TRUE, and barely-true, false and pants-on-fire "
          f"to FAKE. The test split then has {F.A['test_class_counts'][0]} REAL, {F.A['test_class_counts'][1]} PARTIALLY TRUE and {F.A['test_class_counts'][2]} FAKE statements, so FAKE is the "
          f"majority class ({F.pct(F.A['test_class_counts'][2] / F.NTEST)}). Only the statement text is used; the speaker, the justification and the speaker's history counts are not, "
          "because they would leak the label. The product also contains a small synthetic template corpus used for a quick demonstration model; it is described in Chapter 6 and is not "
          "evidence of accuracy."),
        H3("2.4.2 Algorithms"),
        P(f"Text is weighted with TF-IDF {cite('tfidf')}, which scores a term high when it is frequent in a document and rare in the collection. The high-dimensional vectors are standardised "
          f"and compressed with PCA {cite('pca', 'pca87')}, which projects the data onto the orthogonal directions of largest variance. Classification uses the support vector machine "
          f"of Cortes and Vapnik {cite('svm')} with a radial-basis kernel, extended to several classes by a one-vs-rest or one-vs-one scheme {cite('msvm')}; the implementation is scikit-learn "
          f"{cite('sklearn')}. An SVM produces decision scores, and probabilities are obtained by Platt scaling {cite('platt')}, which fits a sigmoid to the scores by cross-validation."),
        P("The Firefly algorithm treats each candidate as a firefly with position x. The attractiveness of firefly j to firefly i falls with the squared distance between them, and "
          "firefly i moves towards any brighter firefly j with a random step:"),
        EQ("beta = beta0 * exp(-gamma * r^2),   x_i <- x_i + beta * (x_j - x_i) + alpha * (u - 0.5)"),
        P("In this project a position holds one logit per PCA component (a component is kept when its sigmoid exceeds 0.5), log10 of the SVM parameter C and log10 of the kernel width "
          "gamma. Brightness is the three-fold cross-validated macro-F1 on the training split minus a penalty proportional to the share of components kept. Chapter 6 gives the full "
          "formulation and the settings."),

        H2("2.5 Strengths and Limitations of the Surveyed Approaches"),
        TAB("Approach families compared", ["Family", "Strengths", "Limitations for a light, three-class screening aid"], [
            ["N-gram TF-IDF with classical learners [19]", "Cheap, fast, easy to retrain", "Surface features; sensitive to vocabulary and topic"],
            ["Stylometric and linguistic features [21], [22]", "Cheap; capture exaggeration and tone", "Style is a weak proxy for truth"],
            ["Transformer embeddings and fine-tuning [1], [23]", "Strong in-domain accuracy", "Need pre-trained models and often a GPU; weak across domains [2]"],
            ["Bayesian-optimised transformer [3]", "Very high reported accuracy on its corpus", "Binary task; says little about harder fact-checking text"],
            ["Metaheuristic feature selection [24], [25]", "Can shrink the feature set and tune parameters", "Many model evaluations; gains depend on the data"],
            ["Binary harmonised benchmarks [2]", "Comparable across datasets", "Remove the half-true nuance"],
        ], widths=[1.9, 2.0, 2.4], align=["l", "l", "l"]),

        H2("2.6 Sources Named in the Project Survey"),
        P("The batch literature survey (5.LITERATURE SURVEY) lists five papers, the base paper and four others. For the four others it records only a title, a year and, for two of "
          "them, a venue. A web search could not locate them, so we could not verify their authors or findings. We list them as references [27] to [30] with that caveat, we quote no "
          "result from them, and they are not used as evidence anywhere in this report."),
        TAB("Additional sources named in the project literature survey", ["Title as recorded", "Year", "Source as recorded", "Reference"], [
            ["Word Embedding and Classification Methods and Their Effects on Fake News Detection", "2024", "not recorded", "[27]"],
            ["A Deep Learning Ensemble Framework for Fake News Stance Detection and Classification", "2024", "Nanotechnology Perceptions", "[28]"],
            ["Fake News Detection Using Machine Learning Techniques", "2025", "not recorded", "[29]"],
            ["Analysis of Fake News Detection and Prevention of Various Fake News Detection Algorithms and their Research Challenges", "2024",
             "Text and Social Media Analytics for Fake News and Hate Speech Detection", "[30]"],
        ], widths=[3.2, 0.6, 1.8, 0.7], align=["l", "c", "l", "c"]),

        H2("2.7 Research Gap"),
        P(lit.GAP + " Four observations from the survey sharpen it."),
        N("The strongest recent systems depend on transformer embeddings and often on a GPU [1], [3], while the cost of a light classical pipeline is rarely reported next to its accuracy.",
          "Most detectors are binary and benchmarks are often harmonised to two labels [2], so the middle grades of fact-checking are lost; an explicit PARTIALLY TRUE class is uncommon.",
          "Metaheuristic feature selection and parameter tuning is well studied on generic benchmarks [24], [25], but it is seldom compared with a simple, equal-budget random search on text data.",
          "Few openly available projects deliver the whole chain, from a labelled file through training and evaluation to a usable screening interface, in one inspectable tool."),
        P("The project addresses the first, second and fourth by construction and the third by measurement: it implements the three-class pipeline and the application, and it compares "
          "the Firefly optimiser with a default SVM, a mask-only variant, an equal-budget random search and linear baselines on real data. It does not address transformer models, "
          "cross-domain generalisation or evidence-based fact checking, and Chapter 10 lists these as future work."),
    ]
