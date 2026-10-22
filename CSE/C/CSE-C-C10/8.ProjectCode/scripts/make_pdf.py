"""Build VenturePulse_Documentation.pdf from actual artifacts (fpdf2)."""
import json
from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).resolve().parent.parent
res = json.loads((BASE / "models" / "evaluation_results.json").read_text(encoding="utf-8"))
meta = json.loads((BASE / "models" / "metadata.json").read_text(encoding="utf-8"))

def f(x):
    return f"{x:.3f}"

def S(t: str) -> str:
    return (t.replace("\u2014", "-").replace("\u2013", "-").replace("\u2022", "-")
             .replace("\u00b1", "+/-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"'))


class Doc(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(90)
        self.cell(0, 8, S("VenturePulse - Product Documentation"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def h1(self, t):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(15, 23, 42)
        self.multi_cell(0, 9, S(t), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def h2(self, t):
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(37, 99, 235)
        self.multi_cell(0, 8, S(t), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, t):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30)
        self.multi_cell(0, 6, S(t), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def bullets(self, items):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30)
        for b in items:
            self.multi_cell(0, 6, S("-  " + b), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def img(self, p, w=170):
        try:
            self.image(str(p), w=w)
            self.ln(2)
        except Exception as e:
            self.body(f"[image unavailable: {Path(p).name}]")

pdf = Doc()
pdf.set_auto_page_break(True, 20)

# cover
pdf.add_page()
pdf.ln(30)
pdf.set_font("Helvetica", "B", 34)
pdf.set_text_color(37, 99, 235)
pdf.multi_cell(0, 14, "VenturePulse", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(60)
pdf.multi_cell(0, 8, "Early-stage startup outcome analytics", new_x="LMARGIN", new_y="NEXT")
pdf.multi_cell(0, 8, "Product documentation", new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)
pdf.set_font("Helvetica", "", 11)
pdf.multi_cell(0, 7, f"Historical startups: {meta['n_train']}  |  Best model: {meta['best_model']}  |  "
                     f"Balanced accuracy: {f(res['models'][meta['best_model']]['balanced_accuracy']['mean'])}  |  "
                     f"F1: {f(res['models'][meta['best_model']]['f1']['mean'])}", new_x="LMARGIN", new_y="NEXT")
pdf.multi_cell(0, 7, "Local web app at http://localhost:8000. All numbers in this document were produced by the local pipeline.",
               new_x="LMARGIN", new_y="NEXT")
if meta["dataset_meta"].get("synthetic_fallback"):
    pdf.multi_cell(0, 7, "Data note: public download unavailable; results use the realistic synthetic fallback dataset (same schema).",
                   new_x="LMARGIN", new_y="NEXT")

pdf.add_page()
pdf.h1("1. VenturePulse overview")
pdf.body("VenturePulse helps investors, founders and analysts estimate whether an early-stage startup resembles historically "
         "successful or failed companies. Users enter structured signals (funding, rounds, milestones, relationships, industry, "
         "state, investor indicators) plus a free-text business description. The system builds a fused representation of "
         "structured features and transformer text embeddings, retrieves comparable historical startups with cosine similarity, "
         "and predicts with the best validated classifier. Every prediction ships with evidence: similar cases, similarity "
         "scores, key features and confidence.")
pdf.h1("2. Problem being addressed")
pdf.body("Early-stage outcomes are uncertain and data is scattered across funding, team, market and narrative signals. "
         "VenturePulse unifies these views so a user can compare a new venture against comparable historical cases instead "
         "of relying on gut feel alone. Outputs are analytical estimates, not guarantees or investment advice.")
pdf.h1("3. Product features")
pdf.bullets(["Outcome prediction (SUCCESS / FAILURE) with calibrated probabilities and confidence.",
             "Similar-case retrieval (k = 10/20/30/50, default 50) with class-balanced evidence and similarity scores.",
             "Four validated models with a live comparison table, confusion matrix and charts.",
             "Startup insights: industry success rates, funding distributions, correlations, top features.",
             "JSON APIs for health, metrics, insights and prediction; clean validation and error handling.",
             "Local-first: no accounts, no external prediction services, no required API keys."])
pdf.h1("4. User workflow")
pdf.bullets(["Open the dashboard to review data coverage and the best validated model.",
             "Go to Predict Startup, fill funding/traction/profile fields and write a business description.",
             "Press Predict Startup Success and read the estimated outcome, confidence and risk note.",
             "Inspect key contributing features and the ranked table of similar historical startups.",
             "Cross-check on Model Performance and Startup Insights before forming a view."])
pdf.h1("5. Technology stack")
pdf.body("Python, FastAPI, Jinja2, HTML5/CSS3, pandas, scikit-learn, XGBoost, sentence-transformers "
         "(all-MiniLM-L6-v2, 384-d), torch, joblib, matplotlib, uvicorn, pytest, Playwright. Embeddings backend in this "
         f"deployment: {meta['embedding_backend']}.")
pdf.h1("6. System architecture")
pdf.body("Browser UI (Jinja2 templates + static CSS) talks to a FastAPI backend. The backend loads cached artifacts "
         "(preprocessor, best model, fused training matrix, training frame, metadata) from models/ at startup; the first "
         "start trains them via scripts/train.py. Prediction flows through validation, structured transform, embedding, "
         "fusion, cosine retrieval and classification. Charts are precomputed into app/static/img/.")
pdf.h1("7. Data pipeline")
pdf.body("Load public CSV from data/raw/ when available, else generate the realistic synthetic fallback (same schema, "
         f"seed 42). Map acquired to SUCCESS and closed to FAILURE. Deduplicate, coerce numerics, normalize categoricals, "
         f"median/most-frequent imputation, log1p funding feature, clean descriptions and mask company names. Split with "
         f"StratifiedShuffleSplit (5 x 80/20, seed 42); preprocessing is fit on train only. Dataset: {meta['n_train']} "
         f"records ({meta['class_counts']['SUCCESS']} SUCCESS / {meta['class_counts']['FAILURE']} FAILURE).")
pdf.h1("8. Machine-learning pipeline")
pdf.bullets(["LogisticRegression (lbfgs, balanced, C=1.0, max_iter=1000).",
             "DecisionTreeClassifier (max_depth=8, min_samples_split=10, min_samples_leaf=5, balanced).",
             "RandomForestClassifier (300 trees, balanced, min_samples_leaf=2).",
             "XGBClassifier (400 trees, depth 6, lr 0.05, subsample/colsample 0.8, reg_lambda 1.0).",
             "Primary metric: balanced accuracy; also accuracy, precision, recall, F1, confusion matrix (mean +/- std)."])
pdf.h1("9. Similarity retrieval mechanism")
pdf.body("Structured features are scaled (StandardScaler + one-hot) then L2-normalized; text embeddings are L2-normalized; "
         "the fused vector is concat(0.5 * structured, 0.5 * text) with a final L2 normalization (alpha = 0.5). Cosine "
         "similarity is computed against training records only, sorted descending, and filled to approximately half SUCCESS "
         "and half FAILURE (graceful fallback when a class is short). Scores are shown unmodified; the target label is "
         "never used during retrieval.")
pdf.h1("10. Model comparison")
for m, v in res["models"].items():
    mark = "  [SELECTED]" if m == res["best_model"] else ""
    pdf.body(f"{m}{mark}: balanced_acc={f(v['balanced_accuracy']['mean'])} +/- {f(v['balanced_accuracy']['std'])}, "
             f"acc={f(v['accuracy']['mean'])}, prec={f(v['precision']['mean'])}, rec={f(v['recall']['mean'])}, "
             f"f1={f(v['f1']['mean'])}.")
pdf.body("Representation study (balanced accuracy): " + ", ".join(
    f"{k}={f(v['mean'])} +/- {f(v['std'])}" for k, v in res["representations"].items()) +
    ". Combining structured and textual information performs best. Similar-case weighted vote: " + ", ".join(
    f"{k}={f(v['mean'])}" for k, v in res["retrieval_k"].items()) + " (default k=50).")
pdf.h1("11. Evaluation methodology")
pdf.body("StratifiedShuffleSplit, 5 repetitions, 80% train / 20% test, seed 42. Metrics computed from actual predictions on "
         "held-out splits; reported as mean +/- standard deviation. No target leakage: outcome columns are excluded from "
         "features, preprocessing is fit on train only, and retrieval never sees test records.")
pdf.h1("12. Actual results and metrics")
pdf.body(f"Best model: {meta['best_model']} with balanced accuracy "
         f"{f(res['models'][meta['best_model']]['balanced_accuracy']['mean'])} +/- "
         f"{f(res['models'][meta['best_model']]['balanced_accuracy']['std'])} and F1 "
         f"{f(res['models'][meta['best_model']]['f1']['mean'])}. Held-out confusion matrix (last split, "
         f"rows actual FAILURE/SUCCESS, cols predicted): {res['models'][meta['best_model']]['confusion_matrix_last']}.")
pdf.h1("13. Screenshots")
pdf.body("Captured from the running application at http://localhost:8000.")
for img in ["01-dashboard.png", "02-predict-form.png", "03-prediction-result.png",
            "06-similar-startups.png", "04-model-performance.png", "05-insights.png"]:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, img, new_x="LMARGIN", new_y="NEXT")
    pdf.img(BASE / "screenshots" / img)
pdf.h1("14. API overview")
pdf.bullets(["GET /api/health -> {status, app, records, best_model}.",
             "GET /api/model-metrics -> full evaluation results JSON.",
             "GET /api/insights -> dataset insights JSON.",
             "POST /predict (JSON) -> {outcome, probability_success, confidence, model, similar[], explanation[]}.",
             "Pages: GET /, /dashboard, /predict, /performance, /insights; form posts to POST /predict-form."])
pdf.h1("15. Installation and execution")
pdf.body("See HOW_TO_RUN.md. Fastest path: double-click run.bat, wait for dependency install and first-run training, use "
         "http://localhost:8000, stop with Ctrl+C. Docker alternative: run-docker.bat (Recommended if Docker Desktop is "
         "installed) or docker build/run commands. Manual: create venv, pip install -r requirements.txt, "
         "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000.")
pdf.h1("16. Limitations")
pdf.bullets(["Estimates reflect historical correlations, not causal guarantees; not investment advice.",
             "Description input capped at 2000 characters; CPU embeddings.",
             "Synthetic fallback used when the public CSV is unavailable (recorded in metadata).",
             "Rare industries/states have small samples; treat their rates cautiously."])
pdf.h1("17. Practical interpretation")
pdf.body("Use the predicted outcome together with confidence and the similar-case table. High confidence with similar "
         "cases pointing the same way is more convincing than a bare label. Disagreement between the model and the "
         "retrieved evidence is itself informative: inspect the key-feature notes and the funding/milestone profile "
         "before deciding what to investigate next.")

pdf.output(BASE / "VenturePulse_Documentation.pdf")
print("PDF written")
