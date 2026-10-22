"""Generate FinSight AI product documentation PDF with real training metrics."""
import json
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def load(name, default=None):
    p = ART / name
    if not p.exists():
        return default if default is not None else {}
    return json.loads(p.read_text())


def safe(text: str) -> str:
    """Strip characters the core Helvetica font cannot render."""
    return (text.replace("\u2014", "-").replace("\u2013", "-")
                .replace("\u2192", "->").replace("\u2022", "-")
                .replace("\u2265", ">=").replace("\u2264", "<=")
                .replace("\u00b1", "+/-").replace("\u2605", "*"))


class Doc(FPDF):
    def mc(self, h, t):
        self.multi_cell(0, h, safe(t), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"FinSight AI Product Documentation  |  Page {self.page_no()}",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def h1(self, t):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(15, 23, 42)
        self.mc(9, t)
        self.ln(1)

    def h2(self, t):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(37, 99, 235)
        self.mc(8, t)
        self.ln(1)

    def body(self, t):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 41, 59)
        self.mc(6, t)
        self.ln(1)

    def bullets(self, items):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 41, 59)
        for it in items:
            self.mc(6, "-  " + it)
        self.ln(1)


summary = load("training_summary.json")
comp = load("model_comparison.json", {"models": {}})
valid = load("validation_report.json")
shap_g = load("shap_global.json", {"features": []})
fc = load("forecast.json")
stats = load("stats_report.json")

pdf = Doc()
pdf.set_auto_page_break(True, 20)

pdf.add_page()
pdf.set_font("Helvetica", "B", 26)
pdf.set_text_color(15, 23, 42)
pdf.mc(12, "FinSight AI")
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(37, 99, 235)
pdf.mc(8, "AI-Based Financial Identification and Forecasting")
pdf.ln(2)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(71, 85, 105)
pdf.mc(6, "Product documentation  |  Version 1.0  |  Local-first Flask application")
pdf.ln(4)
pdf.set_font("Helvetica", "", 10.5)
pdf.set_text_color(30, 41, 59)
pdf.mc(6, "FinSight AI analyzes an individual's demographic and financial information "
          "to produce a financial profile, a risk assessment, a future economic forecast, "
          "and explainable ML insights with visualizations and actionable, non-prescriptive guidance.")

pdf.h2("1. Product overview")
pdf.body("FinSight AI is a standalone commercial-style web application. A user completes a financial "
         "assessment; the system validates the input, engineers interpretable features, runs a trained "
         "classifier, explains the prediction with SHAP, shows an economic forecast, and optionally "
         "compares what-if scenarios side-by-side.")

pdf.h2("2. Problem statement")
pdf.body("Individuals lack clear, data-driven feedback on their financial position and on which factors "
         "matter most. FinSight AI converts factors such as age, occupation, education, income signals, "
         "location, and economic indicators into an interpretable profile with honest, model-based insights.")

pdf.h2("3. Key features")
pdf.bullets([
    "Financial assessment with full server-side validation.",
    "Financial profile classification (Emerging / Developing / Established) with confidence and Low / Moderate / High risk bands.",
    "Four-model comparison (Logistic Regression, Random Forest, Gradient Boosting, XGBoost) with best-model selection by ROC-AUC.",
    "SHAP global importance plus live per-person local explanations.",
    "Holt-Winters 12-month economic forecast with intervals and trend interpretation.",
    "What-if scenario comparison (baseline vs scenario, labelled as simulation).",
    "Stratified 5-fold validation, leakage-safe pipelines, statistical summaries.",
])

pdf.h2("4. User workflow")
pdf.bullets([
    "Dashboard: product summary, model snapshot, Start Financial Assessment CTA.",
    "Assessment: enter age, employment type, education, marital status, occupation, household relationship, race, sex, country, investment gains/losses, hours per week.",
    "Result: profile, risk band, strength score, SHAP drivers, insights, forecast mini-chart, inputs.",
    "Explainability: global SHAP bar + beeswarm + ranked table + reading guide.",
    "Forecast: history, 12-month forecast, intervals, values table.",
    "What-If: baseline + scenario overrides, side-by-side comparison with delta.",
    "Performance: real model comparison, confusion matrix, ROC, validation, statistics.",
])

pdf.h2("5. Technology stack")
pdf.body("Python, pandas, NumPy, scikit-learn, XGBoost, SHAP, statsmodels, Flask, Jinja2 templates, "
         "HTML/CSS/vanilla JavaScript, Plotly.js charts, matplotlib (training plots), joblib persistence, "
         "pytest. Lightweight: runs locally on an ordinary Windows laptop with no GPU.")

pdf.h2("6. Architecture summary")
pdf.body("data ingestion -> preprocessing -> feature engineering -> model training -> evaluation -> "
         "persisted model artifacts -> Flask prediction API -> dashboard frontend. Training is offline "
         "(scripts/train.py); Flask loads persisted artifacts at startup so predictions are fast. "
         "Modules: app/__init__.py, app/routes.py, app/services/predictor.py, forecaster.py, whatif.py, "
         "app/utils/validation.py, scripts/feature_engineering.py, models.py, forecast.py, train.py, evaluate.py.")

pdf.h2("7. ML pipeline")
pdf.body("Load Adult data -> schema validation -> cleaning (? to missing, numeric coercion) -> derived "
         "features (net-capital, log scales, bands, tiers, region, employment-stability, capital-position) "
         "-> stratified 80/20 split -> 4 candidate pipelines (scaling only for Logistic Regression) -> "
         "5-fold stratified CV (ROC-AUC) -> test evaluation -> best-model selection -> SHAP artifacts -> "
         "confusion matrix / ROC plots -> persist model + preprocessor -> metrics, validation, stats, "
         "forecast artifacts. random_state=42 throughout.")

pdf.h2("8. Dataset and preprocessing")
pdf.body(f"Classification dataset: {summary.get('dataset', 'UCI Adult / Census Income (public)')}; "
         f"source: {summary.get('source_url', 'https://archive.ics.uci.edu/dataset/20/census+income')}; "
         f"rows: {summary.get('rows', 'n/a')}. Target: income >50K vs <=50K adapted as a financial-profile "
         "signal (probability of >50K = financial-strength score; NOT a credit score or approval). "
         "Missing values: median imputation (numeric) and 'Unknown' constant (categorical) inside the "
         "pipeline. Forecasting uses a separate monthly Household Financial Conditions Index series "
         "(documented synthetic illustrative series, 132 months 2015-2025) because the classification data "
         "is cross-sectional. See data/README.md for full provenance.")

pdf.h2("9. Model comparison (actual results)")
if comp.get("models"):
    for name, m in comp["models"].items():
        star = "  [BEST]" if name == comp.get("best_model") else ""
        pdf.body(f"{name}{star}: accuracy={m['accuracy']}, precision={m['precision']}, "
                 f"recall={m['recall']}, F1={m['f1']}, ROC-AUC={m['roc_auc']}, "
                 f"CV AUC={m['cv_roc_auc_mean']} +/- {m['cv_roc_auc_std']}")
else:
    pdf.body("Metrics unavailable.")
for img in ["confusion_matrix.png", "roc_curve.png", "shap_bar.png", "shap_beeswarm.png"]:
    p = ART / img
    if p.exists():
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, img, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.image(str(p), w=170)
        pdf.ln(2)

pdf.h2("10. Explainability / SHAP")
pdf.body("SHAP TreeExplainer (tree-path-dependent) on the selected tree model. Global importance is "
         "precomputed over a 500-row sample; local contributions are computed live per prediction with "
         "positive (strengthening) vs negative (weakening) contributors, values, and plain-language "
         "sentences. The UI and this document state that SHAP describes learned associations, not causation.")
for f in (shap_g.get("features") or [])[:10]:
    pdf.body(f"- {f.get('label')}: mean|SHAP| = {f.get('mean_abs_shap')}")

pdf.h2("11. Forecasting")
pdf.body(f"Method: {fc.get('method', 'Holt-Winters')}. Horizon: {fc.get('horizon_months', 12)} months. "
         f"Trend: {fc.get('trend_direction')}. {fc.get('interpretation', '')} "
         f"Residual std: {fc.get('residual_std')}.")

pdf.h2("12. What-if scenario analysis")
pdf.body("Users override gains, losses, hours, and/or education; the persisted model re-runs on baseline "
         "and scenario; the UI reports both scores, the delta, profile/risk changes, and changed fields. "
         "Labelled everywhere as a scenario simulation, not a causal prediction.")

pdf.h2("13. Validation methodology")
pdf.body(f"Protocol: {valid.get('protocol', '')} Why: {valid.get('why', '')} "
         f"Train size: {valid.get('train_size', 'n/a')}, test size: {valid.get('test_size', 'n/a')}.")
if stats.get("correlations_with_target"):
    pdf.body("Statistical associations (complementary, not causal):")
    for k, v in stats["correlations_with_target"].items():
        pdf.body(f"- {k}: r={v}, logit coef={stats.get('logit_coefficients', {}).get(k)}, "
                 f"p={stats.get('logit_pvalues', {}).get(k)}")

pdf.h2("14. Actual model results and metrics")
best = comp.get("best_model", summary.get("best_model", ""))
pdf.body(f"Best model: {best}. Test metrics: {json.dumps(summary.get('metrics', {}))}. "
         "Every number above was generated by the training run in artifacts/ (metrics.json, "
         "model_comparison.json, training_summary.json); no benchmark values are invented.")

pdf.h2("15. How to run the product")
pdf.body("Automatic (recommended): double-click run.bat (checks Python, creates .venv, installs "
         "requirements, trains if needed, starts Flask on http://localhost:5000, opens the browser). "
         "Docker (recommended if Docker Desktop is installed): docker build -t finsight-ai . and "
         "docker run --rm -p 5000:5000 finsight-ai, or double-click run-docker.bat. Manual: "
         "python -m venv .venv; activate; pip install -r requirements.txt; python scripts/train.py; "
         "python run.py; open http://localhost:5000. Full details in HOW_TO_RUN.md.")

pdf.h2("16. Limitations and responsible-use notes")
pdf.bullets([
    "Informational estimates from historical patterns; not professional financial advice.",
    "No guarantee of income, returns, credit, or loan approval.",
    "Training data reflects historical census patterns and may encode societal biases.",
    "SHAP shows associations, not causation; what-if runs are simulations, not causal.",
    "The economic index is illustrative; forecasts extrapolate past patterns.",
])

out = ROOT / "FinSight_Documentation.pdf"
pdf.output(str(out))
print(f"Wrote {out}")
