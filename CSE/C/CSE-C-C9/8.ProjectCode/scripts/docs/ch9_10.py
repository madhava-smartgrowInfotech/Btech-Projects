"""Chapters 9 (conclusion) and 10 (future scope) plus the shared sections used by documents 9, 10, 12 and 15."""

from . import facts as F
from .appendix import source
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from .shared import (ASSUMPTIONS, CONTRIBUTIONS, LIMITATIONS, OBJECTIVES, OBJECTIVE_STATUS, RESEARCH_GAP, SCOPE_IN, SCOPE_OUT)


# ------------------------------------------------------------------ numbers used in the text (all from artifacts)
def _v():
    M = F.METRICS
    c = F.COMPARE
    r = F.RM
    sw = {x["threshold"]: x for x in r["threshold_sweep_xgboost"]}
    bands = r["profile_band_counts_test"]
    rate = r["profile_band_actual_positive_rate"]
    lat = F.MEAS["api_latency_ms_127_0_0_1"]
    cal = {x["bin"]: x for x in r["calibration"]}
    fb = r["forecast_backtest"]
    return dict(M=M, c=c, r=r, sw=sw, bands=bands, rate=rate, lat=lat, cal=cal, fb=fb, xc=r["models"]["xgboost"],
                top=[x["label"] for x in F.SHAP["features"][:5]], py=F.MEAS["pytest"]["passed"], sm=F.MEAS["smoke_test"]["passed"])


def _auc(m):
    return F.f3(F.COMPARE[m]["roc_auc"])


# ------------------------------------------------------------------ novelty and contributions
def novelty_blocks():
    v = _v()
    return [
        P(f"The base paper {n('base')} presents a four-stage explainable framework (domain-adaptive feature engineering, multi-model training, SHAP interpretation, domain-specific validation) "
          "and instantiates it on 165 Korean hospitals and 825 hospital-year observations to detect financial distress. This project keeps the architecture of that framework and changes the "
          "object it is applied to: one person's demographic and financial profile instead of an organisation's disclosed accounts."),
        H2("What is new in this project"),
        N(f"**A different unit of analysis.** The framework is applied to {F.N_ROWS:,} individual records with demographic inputs (age, education, occupation, marital status, household role, country) and investment gains and losses. "
          "This is the gap named in the literature survey: the surveyed work targets organisations, and demographic context carries much of the signal for individuals.",
          "**SHAP as a live service.** The base paper computes SHAP once, offline, for a research figure. Here a TreeExplainer is built at start-up and `local_shap` returns the contributions of each request in the "
          "response, so every assessment carries its own explanation.",
          "**Explanations in plain language.** Each contribution is turned into a sentence, and one-hot features are read correctly: a value of 0 for `occupation = Prof-specialty` is reported as the *absence* of that category, "
          "not as an effect of the category itself.",
          "**A what-if screen.** `run_whatif` predicts twice, for a baseline and for a scenario with changed gains, losses, hours or education, and reports the change in score, profile and risk band, labelled as simulation and not as causation.",
          "**A forecasting component and a usable interface.** A Holt-Winters 12-month forecast with a 95% band, performance views and a React interface sit around the model. The base paper has no application layer.",
          f"**Evaluation of the served system.** Besides accuracy and AUC the project reports calibration bins, a threshold sweep, observed income rates per profile band, API latency ({v['lat']['POST /api/predict']['median']:.1f} ms median for a prediction) and automated test results."),
        H2("What is not new"),
        P(f"The model families (Logistic Regression, Random Forest, Gradient Boosting, XGBoost {n('breiman', 'friedman', 'xgboost')}), SHAP {n('shap', 'treeshap')}, stratified cross-validation {n('stone')} and Holt-Winters smoothing "
          f"{n('winters', 'holt')} are standard and used as published. The project does not reproduce the base paper's group-wise or temporal validation, its counterfactual subsidy analysis or its panel regression, because one row describes one person "
          "and the Adult data have no time dimension. The two studies use different data, targets and protocols, so their scores are not compared as a ranking."),
        TAB("Base paper and this project side by side", ["Aspect", "Base paper", "This project"], [
            ["Unit", "165 hospitals, 825 hospital-years (2019-2023)", f"{F.N_ROWS:,} individuals (UCI Adult)"],
            ["Target", "Deficit (net income below zero), 41.2% positive", "Income above 50K, 23.9% positive, read as a profile signal"],
            ["Models", "LR, RF, GB, XGBoost, MLP", "LR, RF, GB, XGBoost"],
            ["Validation", "Hospital-level Group K-Fold, temporal hold-out, stratified K-Fold", "Stratified 80/20 split and 5-fold stratified CV (one row per person)"],
            ["Best AUC", "0.842 (XGBoost, Group K-Fold)", f"{F.f3(v['M']['roc_auc'])} (XGBoost, test split)"],
            ["Explainability", "Offline global and local SHAP, cross-method reconciliation", "Global SHAP at training time plus live local SHAP per request"],
            ["Beyond the model", "Counterfactual subsidy analysis, panel regression", "Web application, what-if, 12-month forecast on a synthetic index"],
        ], widths=[1.2, 2.5, 2.6], size=9.5, align=["l", "l", "l"]),
    ]


CONTRIB_NOTES = [
    "Evidence: Chapters 4 and 6, the data description in `data/README.md` and the 12-field form validated by `validate_assessment`.",
    f"Evidence: the screens of Chapter 8 and Appendix C and the {_v()['py']} passing tests; every screen is backed by an API route.",
    "Evidence: `build_preprocessor` places the imputers, encoder and scaler inside each Pipeline, and `artifacts/*.json` hold every number quoted in this report.",
    "Evidence: `local_shap` and `build_insights` in `app/services/predictor.py` and the *What shaped your score* panel on the result screen.",
    "Evidence: `scripts/forecast.py` and `data/README.md`, which state that the index is synthetic; the forecast screen repeats this in its interpretation text.",
    "Evidence: Chapter 8 tables and figures: confusion matrices, threshold analysis, calibration bins, profile-band rates, latency and test counts.",
]


def contribution_blocks():
    out = [P("The work makes six contributions. Each is stated together with the place where the evidence for it can be inspected.")]
    out.append(N(*CONTRIBUTIONS))
    for i, note in enumerate(CONTRIB_NOTES, 1):
        out.append(P(f"*Contribution {i}.* {note}"))
    return out


# ------------------------------------------------------------------ scope, assumptions, limitations
def scope_blocks():
    return [
        P("The scope was fixed by the project abstract (identify financial profiles from demographic attributes and forecast economic trends through a web application) and then narrowed to what the available data support."),
        H2("In scope"),
        B(*SCOPE_IN),
        H2("Out of scope"),
        B(*SCOPE_OUT),
        TAB("Scope at a glance", ["Area", "Covered", "Not covered"], [
            ["Data", "UCI Adult / Census Income (public), synthetic monthly index", "Account-level transaction records, real macro series, personal data storage"],
            ["Models", "Four supervised classifiers, Holt-Winters smoothing", "Deep learning, causal models, individual-level forecasting"],
            ["Explanation", "Global and live local SHAP, what-if simulation", "Counterfactual recourse, fairness mitigation"],
            ["Product", "Flask API, React interface, sample login, tests", "Real authentication, database, cloud deployment"],
        ], widths=[1.1, 2.7, 2.5], size=9.5, align=["l", "l", "l"]),
    ]


def assumption_blocks():
    return [
        P("The results hold under the following assumptions; where one is weakened, the corresponding numbers should be re-measured."),
        B(*ASSUMPTIONS),
    ]


LIM_NOTES = [
    "Consequence: absolute income levels, occupations and the country list are dated and US-centric, so scores for a present-day user are an analogy to 1994 patterns.",
    "Consequence: nothing in this report supports lending, scoring or distress claims; the profile names (Emerging, Developing, Established) describe income-band membership only.",
    f"Consequence: the back-test (MAE {_v()['fb']['mae']:.3f} against {_v()['fb']['naive_last_value_mae']:.3f} for repeating the last value) shows the method recovers the pattern it was generated with; it is not evidence about real economies.",
    "Consequence: the model may encode historical bias, for example through the sex and marital-status effects visible in the SHAP ranking. Group metrics and mitigation are future work.",
    f"Consequence: at 0.5 the model misses {_v()['xc']['fn']:,} of the {F.TEST_POS:,} positive test records; lowering the threshold to 0.35 raises recall to {F.pct(_v()['sw'][0.35]['recall'])} at the price of precision {F.pct(_v()['sw'][0.35]['precision'])}.",
    "Consequence: reported test scores are slightly optimistic for the selected model; the cross-validation ranking (XGBoost first) agrees, but differences between models were not tested for significance.",
    "Consequence: users should read the what-if comparison as a statement about the model, not about what would happen if they changed their circumstances.",
    "Consequence: the application must not be exposed beyond a local machine or used with real personal data until real authentication, secret management and storage are added.",
    "Consequence: every screen repeats a disclaimer; the system supports exploration and education, not decisions.",
]


def limitation_blocks():
    out = [P("The limitations below are stated plainly because they change how the results may be used. Each is followed by its practical consequence.")]
    for lim, note in zip(LIMITATIONS, LIM_NOTES):
        out.append(P(lim))
        out.append(P(note))
    return out


def not_measured_blocks():
    v = _v()
    return [
        P("Several things a complete evaluation would include were not measured. They are listed so that no reader mistakes their absence for a good result."),
        TAB("Items not measured", ["Item", "Status", "Why"], [
            ["External validation on current or non-US data", "Not done", "No second dataset with the same schema was available"],
            ["Fairness audit (group error rates, equalised odds)", "Not done", f"Sex, race and marital status are inputs; mitigation is future work {n('hardt', 'mehrabi')}"],
            ["Forecast accuracy on real economic data", "Not done", f"Only the synthetic series exists; the back-test (MAPE {v['fb']['mape_pct']:.2f}%) is against its own generator"],
            ["Significance of differences between models", "Not done", f"No DeLong or paired test was run {n('delong')}"],
            ["Hyperparameter search", "Not done", "Fixed settings were used; no tuned variant was compared"],
            ["Entity-grouped or temporal validation", "Not applicable", "One row per person and no time dimension in the classification data"],
            ["Calibration beyond ten bins; recalibration", "Partly", f"Ten-bin reliability table and Brier score {F.f3(v['xc']['brier'])} only; no calibration method applied {n('guo', 'niculescu')}"],
            ["Load and concurrency testing", "Not done", f"Single-user latency only ({v['lat']['POST /api/predict']['median']:.1f} ms median)"],
            ["User-acceptance study, accessibility audit, browser matrix", "Not done", "No participants; checked only in the browser used for the screenshots"],
            ["Security testing", "Not done", "The sample login is a demo gate and was not audited"],
        ], widths=[2.4, 1.0, 2.9], size=9.5, align=["l", "c", "l"]),
    ]


# ------------------------------------------------------------------ code walkthroughs and decisions
def walkthrough_blocks():
    s = source
    return [
        P("Four pieces of code carry the method. Each is shown as it exists in the repository and explained in turn."),
        H2("1. From a probability to a profile and a risk band"),
        CODE(s("app/services/predictor.py", "def profile_from_proba", "def local_shap")),
        P("The classifier returns P(income > 50K). The application reads it as a financial-strength score and applies two fixed cut-offs, 0.60 and 0.35, to name the profile and the risk band. "
          "The cut-offs were chosen for a readable three-band output and were not tuned; the test split shows that the bands do separate people "
          f"(observed income-above-50K rates of {F.pct(_v()['rate']['Emerging'])}, {F.pct(_v()['rate']['Developing'])} and {F.pct(_v()['rate']['Established'])} for Emerging, Developing and Established)."),
        H2("2. The prediction pipeline"),
        CODE(s("app/services/predictor.py", "def predict_profile", "def build_insights")),
        P("`predict_profile` builds a one-row frame from the validated input (leaving `fnlwgt` missing so that the pipeline imputes the training median), applies the same `clean_frame` and `add_derived_features` used in training, "
          "calls `predict_proba` on the persisted pipeline and then adds the SHAP explanation and the written insights. Because imputation and one-hot encoding are inside the pipeline, no separate transformation code can drift from training."),
        H2("3. Reading SHAP values for one-hot features"),
        CODE(s("app/services/predictor.py", "        def _sentence(d, direction):", "        for d in pos:")),
        P("A one-hot column that equals 0 means the category does not apply. Saying that `occupation = Prof-specialty` weakens the score would be wrong for a person who is not a professional, so the sentence says "
          "*absence of* the category, and says *applies to you* when the value is 1. The five largest positive and five largest negative contributions are returned."),
        H2("4. The forecast"),
        CODE(s("scripts/forecast.py", "    model = ExponentialSmoothing(", "    resid_std = ")),
        P("An additive-trend, additive-seasonality Holt-Winters model with a 12-month period is fitted to the 132-month synthetic index. The 95% band is the point forecast plus or minus 1.96 times the standard deviation of the "
          "in-sample residuals, which is an approximation that ignores growth of uncertainty with the horizon."),
    ]


def decision_blocks():
    return [
        P("The main implementation decisions, with the reason for each, are collected below. Where a choice was a convenience rather than a measured improvement the table says so."),
        TAB("Implementation decisions and reasons", ["Decision", "Choice", "Reason"], [
            ["Prediction target", "Income above 50K, read as a profile signal", "The only public, large, labelled dataset with demographic and financial attributes; clearly not a credit label"],
            ["Model set", "Logistic Regression, Random Forest, Gradient Boosting, XGBoost", "Mirrors the base paper's families; the linear model is an interpretable floor, the boosted trees are the likely best"],
            ["Selection metric", "Test ROC-AUC", "Threshold-free and insensitive to the 24% positive rate; cross-validated AUC gives the same ordering"],
            ["Where preprocessing lives", "Inside each scikit-learn Pipeline", "Imputation and encoding are fitted on training data only, and identical at prediction time"],
            ["Imputation", "Median for numbers, constant 'Unknown' for categories", "The Adult data mark missing workclass, occupation and country with '?'; 'Unknown' keeps that information"],
            ["Splitting", "Stratified 80/20 plus 5-fold stratified CV", "One row per person, so no entity grouping is needed; stratification keeps the class ratio"],
            ["Explainer", "SHAP TreeExplainer, tree-path-dependent", "Exact for tree models and fast enough to run on every request"],
            ["Profile cut-offs", "0.60 and 0.35 on the probability", "Readable three bands; not tuned; checked against observed rates in Chapter 8"],
            ["Forecast data", "Synthetic index, Holt-Winters", "The census data have no time axis; the series is labelled synthetic in the code, the README and the UI"],
            ["What-if", "Re-run the same pipeline on an edited copy", "No second model to keep in step; labelled non-causal"],
            ["Interface", "React front end proxying to the Flask API; Jinja pages kept", "A modern interface without changing the working back end; both run from `run.bat`"],
            ["Login and storage", "Client-side demo gate, session storage, no database", "The product holds no personal data; real authentication was out of scope"],
        ], widths=[1.3, 2.1, 2.9], size=9, align=["l", "l", "l"]),
        P("Decisions that were made without measurement and could change the results are the fixed hyperparameters, the profile cut-offs and the choice of Holt-Winters over other smoothing or ARIMA-type models."),
    ]


# ------------------------------------------------------------------ conclusion (document 15 and chapter 9)
def _findings():
    v = _v()
    M, c = v["M"], v["c"]
    return [
        f"**{F.MODEL_LABEL[F.BEST]} is the best of the four.** On {F.N_TEST:,} held-out records it reaches accuracy {F.pct(M['accuracy'])}, precision {F.pct(M['precision'])}, recall {F.pct(M['recall'])}, F1 {F.f3(M['f1'])} and "
        f"ROC-AUC {F.f3(M['roc_auc'])}; its five-fold cross-validated AUC is {F.f3(M['cv_roc_auc_mean'])} with a standard deviation of {F.f3(M['cv_roc_auc_std'])}.",
        f"**Boosted trees beat the linear baseline, but not by a lot.** Logistic Regression reaches AUC {_auc('logistic_regression')} and F1 {F.f3(c['logistic_regression']['f1'])}; Random Forest has AUC {_auc('random_forest')} "
        f"(below the linear model) but a higher recall ({F.pct(c['random_forest']['recall'])} against {F.pct(c['logistic_regression']['recall'])}) and F1 ({F.f3(c['random_forest']['f1'])}). The ordering by AUC is XGBoost, Gradient Boosting, Logistic Regression, Random Forest, "
        "the same family ordering as in the base paper except for the position of Random Forest.",
        f"**Recall is the weak point.** At 0.5 the model finds {F.pct(M['recall'])} of the people with income above 50K. Moving the threshold to 0.35 gives recall {F.pct(v['sw'][0.35]['recall'])}, precision {F.pct(v['sw'][0.35]['precision'])} and the best F1 ({F.f3(v['sw'][0.35]['f1'])}); the choice is a business decision, not a statistical one.",
        f"**Probabilities are well calibrated on this data.** The mean prediction tracks the observed rate in nearly every one of ten bins (for example {F.f3(v['cal']['0.9-1.0']['mean_pred'])} predicted against {F.f3(v['cal']['0.9-1.0']['observed'])} observed in the top bin) and the Brier score is {F.f3(v['xc']['brier'])}; the largest gap is in the 0.4-0.5 bin ({F.f3(v['cal']['0.4-0.5']['mean_pred'])} against {F.f3(v['cal']['0.4-0.5']['observed'])}).",
        f"**The profile bands carry information.** In the test split {F.pct(v['rate']['Emerging'])} of the Emerging band, {F.pct(v['rate']['Developing'])} of the Developing band and {F.pct(v['rate']['Established'])} of the Established band actually earn more than 50K.",
        f"**What drives the model.** The five largest mean absolute SHAP values belong to {', '.join(v['top'][:4])} and {v['top'][4].lower()}. These are associations learned from 1994 census data, not causes.",
        f"**The forecast works as software, but its series is synthetic.** The 12-month Holt-Winters forecast projects a {F.FORECAST['forecast_pct_change']:+.2f}% move of the index; against its own generator the back-test error is MAPE {v['fb']['mape_pct']:.2f}%, which says nothing about real economies.",
        f"**The system is fast and tested.** A prediction takes a median of {v['lat']['POST /api/predict']['median']:.1f} ms; {v['py']} automated tests and {v['sm']} of {v['sm']} smoke checks pass.",
    ]


def conclusion_blocks():
    v = _v()
    out = [
        H1("CONCLUSION AND KEY FINDINGS"),
        P(f"FinSight AI shows that the explainable machine-learning framework of the base paper {n('base')} can be moved from organisations to individuals and wrapped in a working application: "
          f"twelve demographic and financial inputs become a profile, a risk band, a strength score, a live explanation and a forecast context in about {v['lat']['POST /api/predict']['median']:.0f} ms on a desktop CPU."),
        H2("Objectives against outcomes"),
        TAB("The six project objectives and their status", ["No.", "Objective", "Status", "Outcome"],
            [[str(i), o, st, txt] for i, (o, (st, txt)) in enumerate(zip(OBJECTIVES, OBJECTIVE_STATUS), 1)],
            widths=[0.4, 1.9, 0.8, 3.2], size=9, align=["c", "l", "c", "l"]),
        H2("Key findings"),
        B(*_findings()),
        P("These findings are bounded by the limits described in the scope and limitations: old US data, an income target, a synthetic forecast series and no fairness audit."),
    ]
    return out


def chapter9_blocks():
    v = _v()
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary"),
        P(f"The project set out to identify an individual's financial profile from demographic and financial attributes, to forecast economic conditions and to explain every result through a web application. "
          f"It delivers a Flask API and a React interface around four classifiers trained on {F.N_ROWS:,} Adult / Census Income records inside leakage-safe pipelines; "
          f"{F.MODEL_LABEL[F.BEST]} was selected by ROC-AUC. For each assessment the application returns a profile (Emerging, Developing or Established), a risk band, a financial-strength score, the SHAP factors "
          "that raised or lowered it, written insights and a 12-month forecast context, and it can compare a baseline with a changed scenario."),
        P(f"The work follows the base paper {n('base')} in structure, but changes the unit of analysis from hospitals to people, makes the explanation a per-request service and adds the forecasting and interface layers. "
          "The two studies differ in data, target and validation, so the comparison is one of approach, not of scores."),
        H2("9.2 Objectives achieved"),
        TAB("Objectives and their status", ["No.", "Objective", "Status", "Outcome"],
            [[str(i), o, st, txt] for i, (o, (st, txt)) in enumerate(zip(OBJECTIVES, OBJECTIVE_STATUS), 1)],
            widths=[0.4, 1.9, 0.8, 3.2], size=9, align=["c", "l", "c", "l"]),
        P("Three objectives (preprocessing, explainability, and evaluation with deployment) are met as stated. Three are met only in part and the report says so: the dataset has no transaction-level data, the risk output is an income-based band and not a credit or distress label, "
          "and the forecast is of an aggregate synthetic index and not of an individual's finances."),
        H2("9.3 Key findings"),
        B(*_findings()),
        FIG(F.fig("model_comparison.png"), "The four classifiers compared on the held-out test split", 5.2),
        H2("9.4 Practical applications"),
        P("Within its limits the system can serve as an educational tool and as a pattern for similar projects: it shows how a bank, a financial-literacy programme or a policy analyst could present a model-based profile together with the "
          "factors behind it, instead of a bare score. It is useful for exploring how a few inputs move a modelled profile, for teaching the difference between association and causation using the what-if screen, and as a template for "
          "wrapping a scikit-learn pipeline with a JSON API and a React interface. It is not suitable for lending, hiring, insurance or any decision about a real person."),
        H2("9.5 Known limitations"),
        P("The limitations that matter most are the following; the full list with consequences is in the scope and limitations document and in Chapter 1."),
        B("The training data are 1994 US census records and the target is income, not creditworthiness.",
          "The forecast series is synthetic and the forecast says nothing about a person's own finances.",
          "Sex, race and marital status are model inputs and no fairness audit or mitigation was performed.",
          f"Recall of the positive class is {F.pct(v['M']['recall'])} at the default threshold; the best model was chosen on the test split without a tuned search or significance tests.",
          "The sample login, absence of a database and development secret key make the application suitable only for local use."),
    ]


def future_blocks():
    return [
        H1("FUTURE SCOPE"),
        P("The most valuable next steps follow directly from the limitations."),
        N("**Real data.** Replace the synthetic index with public macroeconomic series (inflation, unemployment, benchmark rates, GDP) as the abstract proposed, and retrain on a current, non-US household survey.",
          "**Credit and distress targets.** Train on a labelled repayment or distress outcome and compare it with the income-based profile, with the base paper's entity-grouped and temporal validation.",
          "**Fairness work.** Report error rates by sex, race and age group, test removing or masking sensitive inputs and apply a mitigation such as equalised odds post-processing.",
          "**Calibration and thresholds.** Apply Platt or isotonic recalibration, add a validation set, search hyperparameters and test model differences for significance.",
          "**Personal forecasting.** Let a user enter a short income and expense history and forecast it with a state-space or machine-learning model, with prediction intervals.",
          "**Production hardening.** Real authentication, secret management, a database for optional history, containerised deployment of both services, and load and security testing."),
    ]


def chapter10_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        P("The system is a complete prototype whose limits point to its natural extensions. The ideas below are grouped by what they would change."),
        H2("10.1 Improvements"),
        B("**Better data.** Retrain on a recent household survey with credit-bureau-style attributes and an observed repayment or distress outcome, so that the target matches the claim.",
          "**Evaluation.** Add a separate validation set, a hyperparameter search, DeLong tests between models, bootstrap intervals on every metric and a temporal split once time-stamped data exist.",
          f"**Calibration and thresholds.** Apply recalibration and let the user or institution choose the threshold; the sweep shows recall of {F.pct(_v()['sw'][0.35]['recall'])} at a threshold of 0.35 for the price of lower precision ({F.pct(_v()['sw'][0.35]['precision'])}).",
          "**Explanations.** Group related one-hot features before ranking, report SHAP interaction values and add counterfactual recourse (the smallest change that would move a profile to the next band).",
          "**Robustness of what-if.** Limit scenarios to the range where the training data are dense and warn when a change moves the score by more than a set amount."),
        H2("10.2 Additional features"),
        B("**Real macroeconomic inputs.** Add inflation, employment and benchmark-rate series and let the forecast respond to them, as the project abstract describes.",
          "**Individual forecasting.** Savings and expenditure projection from a user-supplied history, with scenario bands.",
          "**Saved assessments.** Optional, consented storage of past assessments with a trend view, behind real authentication.",
          "**Reports.** Exportable PDF of a profile with its explanation, and a comparison of two people or two dates.",
          "**Localisation.** Region-specific option lists and currencies, and plain-language text in more languages."),
        H2("10.3 Scalability and deployment"),
        B("**Packaging.** Extend the Docker setup, which today serves the Flask pages only, to run the React build and the API together with a reverse proxy.",
          "**Serving.** Run the API under a production WSGI server, keep the model loaded per worker and cache the global SHAP artefacts; measure behaviour under concurrent load, which was not tested here.",
          "**Operations.** Version models and artefacts, log predictions without personal data, monitor input drift and retrain on a schedule.",
          "**Security.** Replace the demo gate with an identity provider, move secrets out of defaults, and add rate limiting and input-size limits."),
        H2("10.4 Further research"),
        B(f"**Extending the framework.** Apply the four-stage framework {n('base')} to other individual-level settings (small-business owners, students, households) and compare it with deep tabular models {n('grinsztajn')}.",
          f"**Privacy.** Combine demographic features with alternative data without sharing raw records, along the lines of privacy-preserving credit-risk learning {n('zhang')}.",
          f"**Data quality.** Measure how missing values, noise and label errors affect profile models, following the robustness methodology of {n('maurino')}.",
          f"**Responsible use.** Study fairness, explanation faithfulness and user understanding of SHAP sentences {n('mehrabi', 'doshi')}, with a user study of the kind not carried out here.",
          "**Forecasting.** Compare Holt-Winters with state-space and neural models on real household-finance series, and quantify interval coverage honestly."),
        P(RESEARCH_GAP),
    ]
