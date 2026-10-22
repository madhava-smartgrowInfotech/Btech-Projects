"""Chapter 2: Literature Survey."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import K, c

_REC = F.REC["summary"]
_OPE = F.METRICS["policy_evaluation"]
_LR = F.METRICS["models"]["logistic_regression"]

# Rows of the comparison table: work, approach, data, reported result, limitation.
COMPARISON = [
    ["Isiwu et al. [%d] (base paper)" % K["base"], "Uplift (T-learner) effects of learning actions + Actor-Critic RL with causal regularisation; off-policy evaluation; fairness audit",
     "OULAD: 32,593 enrolments, about 1.7 million learner-week rows, 25,516 learners",
     "XGBoost AUC 0.795, Brier 0.074; Greedy-Uplift SNIPS about 0.619 against a logged pass rate of 0.589",
     "One data set; simulated, not live, evaluation; no learner-facing application"],
    ["Khreis et al. [%d]" % K["khreis"], "BERT embeddings fine-tuned by contrastive learning with isotropy regularisation; top-N retrieval for free-text interest statements",
     "More than 500 engineering courses at one university; synthetic student queries",
     "Better embedding separation and retrieval than vanilla BERT (as reported by the authors)",
     "Content only, no learner history or outcome model; one university's engineering catalogue"],
    ["Gharahighehi et al. [%d]" % K["gharahighehi"], "Collaborative filtering improved with survival analysis of time-to-event (dropout, completion)",
     "Three public MOOC data sets", "Better than plain collaborative filtering on two measures (as reported)",
     "Needs a large interaction log; cold-start learners not addressed"],
    ["Sujay et al. [%d]" % K["eduguide"], "TF-IDF vectors and cosine similarity combined with course ratings in a weighted hybrid score",
     "A Coursera course data set (descriptions, levels, skills, ratings)", "Not recorded in the batch survey", "Content and rating only; no learner behaviour or outcome model"],
    ["He et al. [%d]" % K["lightgcn"], "LightGCN: simplified graph convolution over the learner-item graph", "Standard recommendation benchmarks", "Higher recall and NDCG than earlier graph methods (as reported)",
     "Needs many interactions; no profile text; no explanation"],
    ["Batch survey item 2 [%d]" % K["s_ml"], "Machine-learning course recommendation (title and year only)", "Not recorded", "Not recorded", "Authors and details not recorded in the batch survey"],
    ["Batch survey item 3 [%d]" % K["s_lightgcn"], "LightGCN with learning-behaviour data (title and year only)", "Not recorded", "Not recorded", "Authors and details not recorded in the batch survey"],
    ["Batch survey item 4 [%d]" % K["s_review"], "Literature review of course recommendation for personalised e-learning (title and year only)", "Not applicable (review)", "Not applicable", "Authors and details not recorded in the batch survey"],
    ["This project (LearnPathIQ)", "Eight-term hybrid score (TF-IDF, skill, topic, goal, rating, behaviour, success, engagement); T-learner action benefit; offline policy evaluation; fairness audit",
     f"24 hand-written courses; synthetic OULAD-like learner log (2,200 learners x 12 weeks)",
     f"Success-model test AUC {_LR['roc_auc']:.4f}; persona precision at 3 of {_REC['hybrid (shipped)']['p@3']:.2f}",
     "Synthetic data; no collaborative filtering across learners; no RL agent; no user study"],
]


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P(f"This chapter surveys the work behind the project. It begins with the base paper {c('base')} and the two companion papers kept with this batch {c('khreis', 'gharahighehi')}, "
          "then groups related work by theme: content-based recommendation, collaborative and graph methods, learner modelling and dropout, causal and policy methods, and learning paths. "
          "Five items were recorded in the batch literature survey; for items 2, 3 and 4 only the title and year are known, so they are listed as recorded and nothing beyond the title is claimed for them. "
          "The chapter ends with the datasets and algorithms used and the research gap that the project addresses."),
        H2("2.2 Base paper analysis"),
        P(f"**Reference.** C. P. Isiwu, L. C. Nnadi and Y. Watanobe, \"From prediction to prescription: A Causal-AI for personalized learning path optimization in MOOCs,\" IEEE Access, vol. 14, pp. 29105-29118, 2026 {c('base')}."),
        H3("2.2.1 Problem and idea"),
        P("Predictive models for massive open online courses can say who is likely to fail but not what to do about it. The paper moves \"from prediction to prescription\": it estimates the effect "
          "of each candidate learning action on the outcome, and uses those estimates to steer a reinforcement-learning agent towards actions with a causal benefit."),
        H3("2.2.2 Method"),
        P("The framework is a nine-stage pipeline: data integration, preprocessing into weekly learner-state panels, definition of an action space (for example resource review, quiz and forum), "
          "a supervised baseline (XGBoost) with feature importance, causal effect estimation with uplift or T-learner models, policy generation by choosing the action with the largest estimated effect "
          "under fairness and workload constraints, off-policy evaluation, reinforcement-learning optimisation with an Actor-Critic agent regularised by the causal estimates, and personalised weekly recommendations. "
          f"The observed action in each learner-week is a proxy: the dominant activity type by clicks. Rewards are sparse and terminal (1 for a pass). Policies are scored offline with inverse propensity scoring (IPS), "
          f"self-normalised IPS (SNIPS) and doubly robust (DR) estimators {c('dudik')}."),
        H3("2.2.3 Data and results reported"),
        P("The authors use the Open University Learning Analytics Dataset, OULAD " + c('oulad') + ": 32,593 enrolments, about 1.7 million learner-week observations and 25,516 learners over 22 module-presentation combinations. "
          "The reported results are:"),
        B("A baseline XGBoost predictor with AUC 0.795 and Brier score 0.074.",
          "Heavy-tailed uplift distributions, meaning a minority of learner-weeks respond strongly to an action.",
          "A logged pass rate of 0.589 and a Greedy-Uplift policy value of about 0.619 by SNIPS (interval 0.613 to 0.625). The IPS estimate (9.956) is far from the SNIPS estimate (0.643), which the paper itself treats as a sign that SNIPS is the safer number.",
          "Sensitivity to the regularisation weight: SNIPS about 0.603 with no causal term and 0.625 to 0.642 with it.",
          "A value-based fitted Q-iteration baseline with IPS about 0.0039 and SNIPS about 0.0010, far below the logged policy.",
          "A subgroup audit: for example SNIPS of 0.139 for older learners, which the authors take as a call for fairness-aware extensions."),
        H3("2.2.4 Strengths and limits"),
        B("**Strengths:** a clear causal framing; a large real data set; offline evaluation with three estimators and conservative reading of them; a fairness audit; an honest statement that all evidence comes from one data set.",
          "**Limits:** evaluation is offline and simulated, so no learner was ever shown a recommendation; the observed action is a proxy for the intervention; the paper delivers a research pipeline, not a learner-facing application; and it does not recommend courses from a catalogue.",
          "**Relevance to this project:** the uplift (T-learner) step, the three offline estimators and the age and gender audit are reproduced at small scale here; the Actor-Critic agent and the causal regularisation are not."),
        H2("2.3 Companion papers kept with the batch"),
        P(f"**Semantic matching.** Khreis, Nasr and Hilal {c('khreis')} fine-tune a BERT encoder with a self-supervised contrastive objective and an isotropy regulariser, because raw BERT embeddings of course descriptions are all similar "
          "to each other. A student's free-text interest statement and the course descriptions are embedded in one space and the top-N nearest courses are returned. It targets the cold-start problem through content, "
          "on more than 500 engineering courses, and shows the strength of text matching. It uses no learner behaviour."),
        P(f"**Time-to-event collaborative filtering.** Gharahighehi, Ghinis, Venturini, Cornillie and Vens {c('gharahighehi')} observe that MOOC enrolments often end in dropout, and add survival analysis (time to dropout, time to completion) to collaborative filtering. "
          "On three public data sets the approach beats collaborative filtering that uses enrolments alone. It shows that outcome and timing information improves course recommendation, but it needs a large interaction log, which this project does not have."),
        H2("2.4 Related work by theme"),
        H3("2.4.1 Content-based recommendation"),
        P(f"Term-weighting with TF-IDF {c('tfidf')} remains the simplest way to compare a learner's text with course descriptions and is the content term of this project. "
          f"The batch survey also records EduGuide {c('eduguide')}, a hybrid of TF-IDF, cosine similarity and course ratings with machine learning for personalised online learning. It is close in spirit to the content part of LearnPathIQ "
          "and, like it, relies on text and ratings; what it lacks, and what LearnPathIQ adds, is the learner's behaviour, a success estimate and an action suggestion."),
        H3("2.4.2 Collaborative and graph methods"),
        P(f"Collaborative filtering predicts a learner's preferences from similar learners. LightGCN {c('lightgcn')} simplifies graph convolution over the learner-item graph and has been applied to course recommendation; "
          f"the batch survey lists a 2025 conference paper that applies LightGCN to learning-behaviour data {c('s_lightgcn')}. These methods need many recorded interactions and do not serve a new learner or a new course, "
          "which is why the batch objectives ask for a hybrid."),
        H3("2.4.3 Learner modelling and dropout"),
        P(f"Early work predicts dropout from clickstream features with logistic regression and later with deep networks, as summarised by the base paper {c('base')}. Yu et al. {c('yu')} set out a broad vision of AI-powered personalisation in MOOCs, "
          "from optimisation of learning paths to virtual tutors. This project uses the same kind of weekly learner-state features (clicks, quizzes, forum posts, completions, engagement, weekly hours, skill level) for a success model."),
        H3("2.4.4 Causal and policy methods"),
        P(f"Uplift modelling estimates the difference in outcome between treated and untreated cases {c('uplift')}; meta-learners such as the T-learner fit one outcome model per arm and subtract them {c('kunzel')}. "
          f"The doubly robust estimator combines an outcome model with importance weights to evaluate a policy offline {c('dudik')}; the formal ideas of causal effects come from {c('pearl', 'imbens')}. "
          f"Reinforcement learning treats learning as a sequence of states, actions and rewards {c('sutton')}; hierarchical RL has been applied to course recommendation {c('hrl')}."),
        H3("2.4.5 Learning paths and generation"),
        P(f"Adaptive learning-path navigation combines knowledge tracing with reinforcement learning {c('lpnav')}; neural networks have been used to sequence programming exercises {c('saito')}; and retrieval-augmented generation has been proposed to ease the cold-start problem in MOOCs {c('ramo')}. "
          "These works assume either rich knowledge-tracing data or a language model, neither of which this project uses."),
        H3("2.4.6 Surveys recorded in the batch"),
        P(f"The batch survey also lists a 2025 paper on personalised course recommendation with machine learning {c('s_ml')} and a 2026 literature review of course recommendation for personalised e-learning {c('s_review')}. "
          "For both, only the title and year were recorded; the authors and the venue of the first are not known, so they are cited as recorded and not summarised."),
        TAB("Comparison of the surveyed work with this project", ["Work", "Approach", "Data", "Reported result", "Limitation"], COMPARISON,
            widths=[1.0, 1.5, 1.2, 1.3, 1.2], size=8.5, align=["l", "l", "l", "l", "l"]),
        H2("2.5 Datasets and algorithms used in the surveyed work"),
        TAB("Datasets and algorithms across the survey", ["Item", "Seen in", "Used here?"], [
            ["OULAD (demographics, VLE clicks, assessments)", f"Base paper {c('base')}, {c('oulad')}", "No. A synthetic data set with the same kind of weekly features replaces it."],
            ["Course descriptions and ratings (Coursera-style)", f"EduGuide {c('eduguide')}", "No. A 24-course catalogue was written for the project."],
            ["TF-IDF and cosine similarity", f"{c('eduguide')}, {c('tfidf')}", "Yes: the content term of the score."],
            ["Contrastive BERT embeddings", f"{c('khreis')}", "No."],
            ["Collaborative filtering, LightGCN, survival analysis", f"{c('gharahighehi')}, {c('lightgcn')}, {c('s_lightgcn')}", "No: no cross-learner history exists."],
            ["XGBoost, random forest, logistic regression", f"{c('base')}, {c('xgboost')}, {c('breiman')}, {c('sklearn')}", "Yes: the success model compares the three."],
            ["T-learner uplift", f"{c('base')}, {c('kunzel')}, {c('uplift')}", "Yes: logistic regressions per action arm."],
            ["IPS, SNIPS, doubly robust off-policy evaluation", f"{c('base')}, {c('dudik')}", "Yes, with an effective-sample-size warning."],
            ["Actor-Critic reinforcement learning", f"{c('base')}, {c('sutton')}", "No."],
            ["Fairness audit by age and gender", f"{c('base')}", "Yes: reporting only."],
        ], widths=[2.4, 2.0, 1.8], size=9.5),
        H2("2.6 Strengths and limitations of the surveyed approaches"),
        TAB("Strengths and limitations by family of method", ["Family", "Strengths", "Limitations"], [
            ["Content-based (TF-IDF, embeddings)", "Works for new learners and new courses; easy to explain", "Ignores outcomes and behaviour; keyword mismatch for TF-IDF"],
            ["Collaborative and graph", "Learns taste from many learners; no need for course text", "Cold start; needs a large log; hard to explain"],
            ["Outcome and survival models", "Use success or dropout, not only clicks", "Need outcome labels and timing; prediction alone gives no action"],
            ["Uplift and offline policy evaluation", "Estimate what an action would change; safe pre-deployment checks", "Rely on assumptions about confounding; estimates can be unstable"],
            ["Reinforcement learning", "Optimises a sequence of actions over time", "Needs large logs and careful evaluation; hard to deploy"],
        ], widths=[1.8, 2.2, 2.2], size=9),
        H2("2.7 Research gap"),
        P("The batch survey identifies the gap as combining collaborative and content-based signals in a deployable platform that also handles the cold-start learner. Read together with the base paper, the gap has three parts:"),
        N("Most prescriptive work stops at a research pipeline; there is little open, learner-facing software that ranks a catalogue, explains each suggestion and records feedback.",
          "Content-based course recommenders ignore whether the learner is likely to succeed, while outcome models ignore what the learner is reading; few combine them in one score.",
          "Offline policy evaluation is easy to over-read. A deployable system should report how reliable its own estimate is, for example through the effective sample size."),
        H2("2.8 Positioning of this project"),
        P("LearnPathIQ addresses the gap at small scale and states what it leaves open. It combines a text term with skill, topic, goal, rating, behavioural, success and engagement terms in one explainable score, serves a "
          "new learner from the first profile, adapts to events immediately and reports the weakness of its own evidence. It does not claim to beat the surveyed work: "
          f"its models are trained on synthetic data (success-model test AUC {_LR['roc_auc']:.4f}, against 0.795 for the base paper on real OULAD data), its offline policy value rests on an effective sample size of {_OPE['effective_sample_size']}, "
          f"and on a ten-persona check the hybrid (precision at 3 of {_REC['hybrid (shipped)']['p@3']:.3f}) does not beat plain content matching ({_REC['content-only (TF-IDF)']['p@3']:.3f}). "
          "Collaborative filtering, the reinforcement-learning agent and a user study remain open."),
    ]
