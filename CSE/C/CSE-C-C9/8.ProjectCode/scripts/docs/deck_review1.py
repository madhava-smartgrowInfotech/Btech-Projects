"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K
from . import shared as SH
from .refs import TEXT, n, num

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    # layout footer text carries the template's deck title
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n_ for n_, _ in F.STUDENTS)
    cp.keywords = "financial identification, demographic analytics, economic forecasting, XGBoost, SHAP"
    cp.comments = ""
    cp.category = ""
    cp.last_modified_by = ""


def set_title(slide, text):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors):
    cols = 3
    w, h, gx, gy = 3.85, 1.45, 0.29, 0.3
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, review_label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle)
        elif nm == "review label":
            K.replace_text(sh, review_label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"Guide: {F.GUIDE}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def ref_lines(keys):
    return [(f"[{num(k)}] {TEXT[k]}", {"space_after": 5}) for k in keys]


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}

    # ---- 1 title
    title_slide(S[0], "An explainable machine-learning system that profiles an individual's financial position from demographic and financial inputs, explains every result with SHAP and forecasts economic conditions",
                "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: we build a web tool that takes a person's demographic and financial details, "
                "returns a financial profile and risk band, shows which factors drove it, and gives a 12-month economic outlook.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey"), ("04", "Existing approaches and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work, not yet about results."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: a financial profile that explains itself")
    wipe(s)
    W, H = 3.85, 4.6
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "Financial decisions rest on a narrow set of financial parameters and a static score. Non-linear interactions between demographic and financial factors are missed, the present is described but the future is not, and an unexplained decision cannot be defended.", K.ORANGE, "!"),
        ("Our idea", "Learn the interactions with tree-ensemble models (Logistic Regression, Random Forest, Gradient Boosting, XGBoost), explain every assessment with SHAP, and add a Holt-Winters forecast and a what-if scenario.", K.BLUE, "i"),
        ("The deliverable", "A Flask API with a React web interface: enter a profile, receive a profile class (Emerging, Developing or Established), a risk band, the factors behind it and a 12-month economic outlook.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=17)
    notes[3] = "Three sentences: the problem, our idea, the deliverable. Emphasise explanation: every number comes with the factors that produced it."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.1, fill=K.CARD)
    K.text(s, 0.82, 1.48, 11.7, 0.95, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Framework", "Four stages: domain-adaptive feature engineering, multi-model training (Logistic Regression, Random Forest, Gradient Boosting, XGBoost, MLP), SHAP global and local interpretation, and domain-specific validation (hospital-level Group K-Fold, temporal hold-out).", K.BLUE, "F"),
        ("Data and reported results", "165 Korean hospitals, 825 hospital-year rows (2019-2023), 236 line items reduced to 11 features; target is a deficit (net income below zero). XGBoost AUC 0.842, Gradient Boosting 0.840, Random Forest 0.831, Logistic Regression 0.776; 2023 hold-out 0.780.", K.GREEN, "R"),
        ("Limits stated by the authors", "SHAP shows associations, not causes; compositional cost ratios make single attributions unstable; ensembles cannot extrapolate beyond training values; the setting is organisations with structured disclosures, not individuals.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.75, cw, 4.0, t, b_, col, gl, body_size=14)
    notes[4] = ("Read the citation. The base paper extends explainable ML to organisations (hospitals). The gap, and our project, is extending the same approach to "
                "individual profiling where demographic context carries much of the signal.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Approach", "Data", "Reported result"]]
    for r in SH.LIT_TABLE:
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3]])
    K.table(s, 0.6, 1.3, [2.2, 3.7, 2.7, 3.53], rows, font_size=10.5, row_h=0.6, header_size=12)
    notes[5] = ("The pattern: explainable and ensemble models for organisations, sovereigns and firms; robustness and privacy studies on credit data; benchmarks showing trees beat deep models on tabular data. "
                "Results marked as summarised in the base paper are quoted from its own related-work section. Three further entries of the batch survey (financial cycles, "
                "a 2024 editorial and a multimodal system) could not be verified and are listed only in the report's reference list.")

    # ---- 6 supporting evidence (chart)
    s = S[5]
    set_title(s, "Supporting evidence: ensembles beat linear baselines")
    wipe(s)
    K.bar_chart(s, 0.6, 1.4, 7.6, 5.2, ["Altman Z''\nscore", "Logistic\nRegression", "Random\nForest", "Gradient\nBoosting", "XGBoost"],
                [("AUC", [0.680, 0.776, 0.831, 0.840, 0.842])], colors=[K.BLUE], number_format="0.000", font_size=12, max_value=1.0)
    K.card(s, 8.5, 1.5, 4.23, 2.45, "Takeaway", "On the base paper's hospital data, nonlinear ensembles lift AUC by about 0.07 over Logistic Regression and 0.16 over the classic Altman score.", K.GREEN, "↑", body_size=14)
    K.card(s, 8.5, 4.15, 4.23, 2.45, "Caveat", "The three ensembles are not significantly different from one another (DeLong tests), so the choice among them rests on practicality and explainability.", K.ORANGE, "!", body_size=14)
    notes[6] = ("Values are the base paper's AUC under hospital-level Group K-Fold: Z'' 0.680, LR 0.776, RF 0.831, GB 0.840, XGBoost 0.842. "
                "This is evidence from a different dataset and motivates our model families; our own numbers come in later reviews.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.55, 12.13, 1.1, [("Applicant data collected", K.NAVY), ("Few parameters scored", K.NAVY), ("Single static score", K.NAVY), ("Decision, rarely explained", K.NAVY)], size=16, gap=0.5)
    K.card(s, 0.6, 3.1, 5.95, 3.55, "Traditional scoring", "Linear and rule-based scores such as the Altman Z-score or logistic scorecards use a handful of financial ratios. They are transparent but cannot capture non-linear interactions, and ignore demographic context.", K.BLUE, "1", body_size=17)
    K.card(s, 6.78, 3.1, 5.95, 3.55, "Research models", "Papers train ensembles and deep networks and report an AUC. Code is usually a notebook: no per-person explanation, no forecast and no interface that a user or analyst can open.", K.ORANGE, "2", body_size=17)
    notes[7] = "Describe today's typical path. Static scores describe the present and are hard to defend; research models stop at a number in a notebook."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    items = [
        ("Narrow parameters", "A limited set of financial ratios misses demographic factors such as age, occupation, education and region.", K.ORANGE, "1"),
        ("Linear structure", "Statistical scores assume additive effects and miss non-linear interactions that tree ensembles capture.", K.BLUE, "2"),
        ("Present only", "A static score describes where someone is today; it gives no view of how conditions may change.", K.GREEN, "3"),
        ("No explanation", "A bare score cannot be justified to the customer or a regulator, and research code has no usable interface.", K.PURPLE, "4"),
    ]
    for i, (t, b_, col, gl) in enumerate(items):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.5 + r * 2.7, 5.95, 2.5, t, b_, col, gl, body_size=17)
    notes[8] = "These four limitations restate the problem statement from the batch documents. Each maps to a design decision: more inputs, tree ensembles, forecast, SHAP."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    gaps = [("Population", "Explainable ML for financial distress targets organisations and sovereigns; individual profiling from demographics is far less covered."),
            ("Explanation", "Accuracy is the usual headline; a per-person explanation that a non-expert can read is rarely part of the tool."),
            ("Future view", "Models describe the present position; a forecast of economic conditions is seldom combined with the profile."),
            ("Usability", "Few works deliver the model as a reproducible, tested application with a validated input form."),
            ("Honest scope", "Claims about credit or distress are often made from proxy data without saying so; limits must be stated.")]
    for i, (k, v) in enumerate(gaps):
        y = 1.45 + i * 1.08
        K.box(s, 0.6, y, 2.6, 0.9, fill=K.NAVY, line=None, radius=0.06)
        K.text(s, 0.6, y, 2.6, 0.9, k, size=16, color=K.WHITE, bold=True, align="c", anchor="m")
        K.text(s, 3.5, y, 9.2, 0.9, v, size=17, color=K.INK, anchor="m")
    notes[9] = SH.RESEARCH_GAP

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 2.75, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.5, "Given an individual's demographic and financial details, **identify a financial profile and risk band**, show **which factors drove the assessment**, and **forecast how economic conditions may move**, through a web interface, with output a non-expert can read and a regulator can question.", size=20, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "Age, education, occupation, household, country, hours, gains and losses (12 fields)"), ("Output", "Profile class, risk band, strength score, SHAP drivers, insights"), ("Context", "12-month forecast and what-if comparison")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.5, 3.85, 1.7)
        K.text(s, x + 0.25, 4.62, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.1, 3.4, 1.0, b_, size=14, color=K.TXT)
    notes[10] = "Read the statement slowly. Three parts: identify the profile, explain it, put it in an economic context."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 5.3, [(f"{i}.  {o}", {"space_after": 11}) for i, o in enumerate(SH.OBJECTIVES, 1)], size=22, color=K.INK)
    notes[11] = "The six objectives from the project proposal: dataset, preprocessing, classification and risk, forecasting, explainability, evaluation and deployment."

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Prepare", "UCI Adult / Census Income (48,842 individuals); missing values imputed; categories one-hot encoded; 12 derived features.", K.BLUE, "1"),
        ("Model", "Compare Logistic Regression, Random Forest, Gradient Boosting and XGBoost; select by ROC-AUC with stratified cross-validation.", K.GREEN, "2"),
        ("Explain", "SHAP TreeExplainer: global importance and live per-person contributions in plain language.", K.ORANGE, "3"),
        ("Forecast", "Holt-Winters model for a 12-month economic index; what-if scenarios for a changed profile.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.4, t, b_, col, gl, body_size=14)
    K.box(s, 0.6, 5.1, 12.13, 1.5)
    K.circle(s, 0.85, 5.4, 0.7, K.NAVY, "W", 18)
    K.text(s, 1.8, 5.3, 10.7, 0.5, "Web application", size=17, color=K.INK, bold=True)
    K.text(s, 1.8, 5.8, 10.7, 0.75, "Flask JSON API (validation, prediction, what-if, forecast) behind a React interface with a sample login, dashboard, explainability, forecast and performance screens.", size=15, color=K.TXT)
    notes[12] = "Four stages and the application around them. The forecast uses a documented synthetic series, because the census data has no time dimension; this is stated again in later reviews."

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 8.1, 5.5)
    K.text(s, 9.0, 1.5, 3.8, 5.2, [
        ("**Four tiers**", {"space_after": 8}),
        ("Presentation: React single-page app.", {"bullet": True}),
        ("Application: Flask routes, JSON API and input validation.", {"bullet": True}),
        ("Model and service tier: predictor, SHAP, what-if, forecast.", {"bullet": True}),
        ("Data: model files, JSON artifacts and the UCI Adult data.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[13] = "Follow the diagram left to right: the user interface, the Flask routes, the services that load the model and run SHAP, and the stored artifacts."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    outs = [("Working classifier", "A trained model selected from four candidates on a held-out test split.", K.BLUE, "1"),
            ("Visible reasoning", "SHAP drivers and plain-language insights for every assessment.", K.GREEN, "2"),
            ("Honest evaluation", "Metrics stated with their protocol, including limits and weak points.", K.ORANGE, "3"),
            ("Usable system", "Web application with validated input, dashboard and what-if screen.", K.PURPLE, "4"),
            ("Economic context", "A 12-month forecast with an interval, labelled with its data source.", K.BLUE, "5"),
            ("Quality", "Automated tests for the API, validation and feature code.", K.GREEN, "6")]
    for i, (t, b_, col, gl) in enumerate(outs):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=16)
    notes[14] = "These are expected outcomes, not results. We will report whatever the held-out test split shows, including weaknesses."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    K.text(s, 0.6, 1.3, 12.13, 5.6, ref_lines(["base", "abid", "maurino", "zhang", "xgboost", "shap", "treeshap", "uci", "winters"]), size=13, color=K.INK)
    notes[15] = "Full references are in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = "Likely questions: why income as the target (public individual-level data); why XGBoost; why a synthetic forecast series; what about fairness (a stated limitation)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
