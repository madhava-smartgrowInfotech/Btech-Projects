"""Chapter 1: Introduction (the lists below are shared with the scope / limitations and conclusion documents)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import c

_M = F.METRICS["models"]
_LR = _M["logistic_regression"]
_REC = F.REC["summary"]
_N_COURSES = len(F.CATALOG)

# The six objectives exactly as proposed in the batch objectives document.
OBJECTIVES = [
    "Build learner profiles capturing interests, current skills, goals and completed courses.",
    "Construct a course catalogue with topic, level, prerequisite and outcome metadata.",
    "Implement collaborative filtering over learner interaction history.",
    "Implement content-based matching between learner profile and course metadata.",
    "Combine both into a hybrid recommender and order the output into a coherent learning path.",
    "Evaluate using precision, recall and learner feedback on recommendation relevance.",
]

# Status of each objective, as measured in this project (see Chapter 8 for the evidence).
OBJECTIVE_STATUS = [
    ("Achieved", f"A profile form with ten fields (education, skill level, interests, preferred topics, goals, course preferences, learning style, weekly hours, age band, gender) is stored per learner. "
                 "Completed courses are not a form field: they are recorded as `complete` events in the interaction log."),
    ("Achieved", f"{_N_COURSES} hand-written courses in {len({x['category'] for x in F.CATALOG})} categories, each with topic, level, duration, difficulty, prerequisites, outcomes, tags, resource type and rating. "
                 "Prerequisites are stored as text and shown to the learner; they are not used to order the path."),
    ("Not achieved", "There is no real log of many learners' course histories, so no collaborative filtering across learners was built. The behavioural term in the score is per learner: it reflects only the signed-in learner's own events."),
    ("Achieved", "TF-IDF cosine similarity between the learner's profile text and each course's text, plus skill-level, topic-interest and goal-match terms."),
    ("Achieved", "An eight-term hybrid score ranks the catalogue and the best six courses are ordered into a staged path by skill level and then by score. Caveat: the path is not built from a prerequisite graph, and the hybrid is content-led, not collaborative."),
    ("Partly achieved", f"Success-model AUC and F1 were measured, and a ten-persona check gives precision at 3 of {_REC['hybrid (shipped)']['p@3']:.2f} for the hybrid. "
                        "No precision, recall or relevance rating from real learners was collected, and no user study was run."),
]

SCOPE_IN = [
    f"Learner accounts and a stored learner profile, and a {_N_COURSES}-course catalogue with rich metadata that can be searched by text, category and level.",
    "A hybrid ranking of the whole catalogue for one learner, with the eight score terms, a match percentage and up to three plain-language reasons on every card.",
    "A feedback loop: nine interaction types (view, open, start, content, quiz, forum, save, complete, dismiss) are logged and change the next ranking at once.",
    "A learner-success estimate and an estimated benefit for five learning actions (quiz, content, forum, homepage, continue course), shown as a suggested next action.",
    "A staged learning path of up to six courses, an insights page, an activity and history log, and a model-analytics area with the offline policy evaluation and a fairness audit by age band and gender.",
    "A FastAPI and SQLAlchemy back end with eighteen JSON routes and the original server-rendered interface, a React front end, an automated test suite, a smoke test and a responsive-layout check.",
]

SCOPE_OUT = [
    "Collaborative filtering across learners, and any model trained on real learner-course histories. No such data were available.",
    "The Open University Learning Analytics Dataset itself. The success and action models are trained on a reproducible synthetic data set that imitates its structure; no result is a claim about real learners.",
    "The base paper's Actor-Critic reinforcement-learning agent and its causal regularisation. This project borrows only the uplift (T-learner), off-policy evaluation and fairness-audit ideas.",
    "A prerequisite graph or knowledge-tracing model. Learning paths are ordered by skill level and score.",
    "A live experiment: no A/B test, no user study and no collection of real learner feedback.",
    "Production concerns: a managed identity provider, a multi-node database, caching, monitoring, containers on a cloud service and load beyond a single machine.",
]

ASSUMPTIONS = [
    "The learner types free-text interests and goals in English; the TF-IDF step uses English stop words and no stemming.",
    "The 24-course catalogue is a fair stand-in for a real platform's catalogue. Its levels (15 Beginner, 6 Intermediate, 2 All levels and 1 Advanced) and ratings (4.3 to 4.7) were written by the authors.",
    "The synthetic data reproduce the shape of an online-learning log (weekly clicks, quizzes, forum posts, assessment scores, an outcome) closely enough to demonstrate the pipeline. They are not evidence about real learners.",
    "A single trusted user group on one machine: accounts and tokens are a convenience for the demonstration, not an identity system.",
    "The machine has Python 3.11 or newer, Node.js 20 or newer and a modern browser; all data stay in one local SQLite file.",
]

LIMITATIONS = [
    "**Synthetic training data.** Every model metric comes from the generator in `scripts/train_pipeline.py`. The real OULAD data were never downloaded or used, so there is no external validity.",
    f"**Modest predictive power.** The selected logistic-regression success model reaches a test AUC of {_LR['roc_auc']:.4f} (six-seed mean {F.SEEDS['summary']['logistic_regression']['test_auc']['mean']:.3f}). "
    f"Adding the hidden assessment score would lift it to {F.CEIL['with_assess_score']['logistic_regression']['test_auc']:.2f}, so the weak signal belongs to the generated data and the deployed features, not to a coding error.",
    f"**Weak policy evidence.** The offline policy evaluation gives IPS {F.METRICS['policy_evaluation']['ips']}, SNIPS {F.METRICS['policy_evaluation']['snips']} and doubly robust {F.METRICS['policy_evaluation']['doubly_robust']}, "
    f"but its effective sample size is {F.METRICS['policy_evaluation']['effective_sample_size']} of {F.METRICS['policy_evaluation']['test_samples']:,} test rows. It is not evidence that the action policy helps.",
    "**No collaborative filtering and no real feedback.** Objective 3 was not met and objective 6 only in part: precision and recall against real learner feedback were not measured.",
    f"**The hybrid does not beat content-only matching on the persona check** (precision at 3 of {_REC['hybrid (shipped)']['p@3']:.3f} against {_REC['content-only (TF-IDF)']['p@3']:.3f}). The extra terms add skill fit, goal fit and behavioural adaptation, not a measured gain in relevance.",
    "**Unstable action advice.** The estimated benefit of each action can change sign after a few events, and the suggested action depends on the learner's state only, so every card of one learner shows the same suggested action.",
    "**Demonstration-grade engineering.** One SQLite file, no cache (recommendations are recomputed on each request), token authentication meant for local use, and a stored token that does not expire in the database.",
    "**Not an educational authority.** The system suggests courses; it does not certify skills or predict real exam results.",
]

CONTRIBUTIONS = [
    f"A working hybrid course-recommendation engine with eight interpretable score terms and a plain-language explanation on every card, compared in a persona check with a popularity baseline (precision at 3 of {_REC['popularity (rating only)']['p@3']:.2f}) and a content-only baseline ({_REC['content-only (TF-IDF)']['p@3']:.2f}), with a drop-one-term ablation.",
    f"A learner-success model chosen by validation AUC among logistic regression, random forest and XGBoost, with a six-seed repeat study and a ceiling check that shows where the weak signal comes from.",
    "A one-versus-rest T-learner that turns the same learner state into an estimated benefit for five learning actions, and an offline policy evaluation (IPS, SNIPS and doubly robust) reported with its effective sample size, so the weakness of the evidence is visible.",
    "A feedback loop that is measurable: in a recorded example, six events raise the score of the course being studied from 0.4867 to 0.5514 and push a dismissed course from rank 3 to rank 4.",
    f"A full-stack deliverable: FastAPI, SQLAlchemy and SQLite, a React interface with twelve screens, {F.TESTS['pytest']['passed']} passing automated tests, a {F.TESTS['smoke']['checks']}-check smoke test, a responsive check at three widths and two themes, and measured response times.",
    "A candid account of what is missing: real data, collaborative filtering, a prerequisite graph, real feedback and a live experiment.",
]


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain overview"),
        P("Online learning platforms now publish more courses than any learner can compare. A learner who wants to \"learn data science\" meets dozens of titles whose levels, "
          "prerequisites, workloads and outcomes differ, and has little reliable way to judge which one fits. The base paper for this project notes that completion rates in massive open online "
          f"courses are often below ten per cent and that disengagement and dropout are widespread {c('base')}. A course that does not match a learner's level or goal is one of the plain reasons for that."),
        P("The field that addresses the choice problem is the recommendation system. A content-based method matches a course's description to what the learner says they want; a collaborative method "
          f"predicts preferences from the behaviour of similar learners; a hybrid combines both {c('tfidf', 'lightgcn')}. Educational data mining adds a second question that ordinary shopping "
          f"recommendation does not face: whether the learner will succeed in the course, and which learning action would help most at this moment {c('oulad', 'yu')}. The domain of this project is therefore machine "
          "learning applied to personalised e-learning, at the meeting point of recommendation, learner modelling and learning analytics."),
        H2("1.2 Background and motivation"),
        P(f"Two lines of recent work frame the project. The first moves from predicting who will fail to prescribing what to do about it: the base paper {c('base')} estimates the effect of candidate learning actions "
          "with uplift modelling, evaluates policies offline with inverse-propensity estimators and audits fairness by age and gender. The second line studies the recommendation step itself, "
          f"for example semantic matching of student interest statements to course descriptions with contrastive learning {c('khreis')} and collaborative filtering that uses time-to-event information such as time to dropout {c('gharahighehi')}."),
        P("The motivation of this project is to put the main ideas of both lines into one inspectable application that a learner can actually use. A learner states their background, skill level, interests and goals; "
          "the system ranks a catalogue, explains each suggestion, records what the learner does next and re-ranks, and also reports honestly how good its models are. "
          "The authors are students and the work was done on a single desktop with open-source software, so the emphasis is on a complete, explainable and measurable pipeline rather than on a new algorithm."),
        H2("1.3 Problem statement"),
        B("Learners face too many options and no reliable way to judge which suits them.",
          "Platform recommendations tend to optimise engagement rather than learning outcome.",
          "New learners receive poor recommendations because no interaction history exists (the cold-start problem).",
          "Courses are recommended one by one, with no regard for the order in which they should be taken."),
        P("The problem addressed here is: *given a learner's profile and, when it exists, their interaction history, rank the courses of a catalogue by how well they fit, explain each suggestion, "
          "estimate the learner's chance of success and the most useful next action, and arrange the best courses into a short learning path, all through a web interface a non-expert can use.*"),
        H2("1.4 Need for the system"),
        P("A hybrid recommendation engine is needed because each single signal fails alone. Matching text alone ignores the learner's level and what they did yesterday; popularity alone ignores the learner; "
          "behaviour alone gives nothing to a new learner. Combining profile text, skill fit, topic interest, goal fit, rating and behaviour gives a ranking that works from the first minute "
          "and adapts as events arrive."),
        P("There is also a need for transparency. A list of titles with no reason cannot be trusted or corrected. Here every card shows its match percentage, the estimated success probability, the suggested action "
          "and up to three reasons, and a model-analytics screen shows how the models were trained and how weak some of the evidence is. Open, inspectable software of this kind lets students and "
          "researchers study the whole pipeline, reproduce its numbers and extend it."),
        H2("1.5 Objectives"),
        P("The project was proposed with the six objectives below. The table that follows records, objective by objective, what was achieved; Chapter 8 gives the evidence."),
        N(*OBJECTIVES),
        TAB("Status of the six objectives", ["No.", "Status", "What was done or missing"],
            [[str(i), s, t] for i, (s, t) in enumerate(OBJECTIVE_STATUS, 1)], widths=[0.5, 1.2, 4.5], size=10, align=["c", "l", "l"]),
        H2("1.6 Scope"),
        P("**In scope.**"),
        B(*SCOPE_IN),
        P("**Out of scope.**"),
        B(*SCOPE_OUT),
        H2("1.7 Contributions"),
        N(*CONTRIBUTIONS),
        H2("1.8 Limitations and assumptions"),
        P("**Assumptions.**"),
        B(*ASSUMPTIONS),
        P("**Limitations.**"),
        B(*LIMITATIONS),
        H2("1.9 Organisation of the report"),
        TAB("Organisation of this report", ["Chapter", "Content"], [
            ["1  Introduction", "Domain, motivation, problem, objectives and their status, scope, contributions, limitations."],
            ["2  Literature Survey", "The base paper in depth, two companion papers, related work by theme, datasets and algorithms, research gap."],
            ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility, advantages and constraints."],
            ["4  System Requirements and Analysis", "Existing and proposed system, functional and non-functional requirements, hardware, software, users and data."],
            ["5  System Design", "Architecture, workflow, data-flow diagrams, UML, database, modules, API and screen design."],
            ["6  Methodology and Software Implementation", "Data, the hybrid score, the success and action models, offline evaluation, application, security, installation."],
            ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance and edge-case tests."],
            ["8  Results and Output Screens", "Model results, recommender checks, comparison with the base paper, output screens, failure analysis, objectives versus outcomes."],
            ["9  Conclusion", "Summary, objectives achieved, findings, applications, known limitations."],
            ["10 Future Scope", "Improvements, features, deployment and research directions."],
            ["Appendices", "A: important code; B: installation and user guide; C: additional screens."],
        ], widths=[2.3, 3.9]),
    ]
