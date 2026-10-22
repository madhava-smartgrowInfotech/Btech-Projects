"""Generate LearnPathIQ_Documentation.pdf from real local artifacts (no fabricated values)."""
import json
from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).resolve().parent.parent
M = json.loads((BASE / "artifacts" / "metrics" / "model_metrics.json").read_text())

class Doc(FPDF):
    pass
    def h1(self, t):
        self.set_font("Helvetica", "B", 14); self.set_text_color(20, 20, 40)
        self.multi_cell(0, 8, t, new_x="LMARGIN", new_y="NEXT"); self.ln(1)
    def h2(self, t):
        self.set_font("Helvetica", "B", 11); self.set_text_color(40, 40, 70)
        self.multi_cell(0, 7, t, new_x="LMARGIN", new_y="NEXT")
    def body(self, t):
        self.set_font("Helvetica", "", 10); self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, t, new_x="LMARGIN", new_y="NEXT"); self.ln(1)

pdf = Doc()
pdf.set_auto_page_break(True, 20)
pdf.add_page()
pdf.h1("LearnPathIQ - Intelligent Personalized E-Learning Recommendations")
pdf.body("LearnPathIQ helps learners find the right courses and the most useful next learning action. Learners describe their background, interests, topics and goals; the platform combines profile matching, learning behavior, and predictive models to rank courses with plain-language reasons. Interaction history continuously refines future suggestions.")
pdf.h2("1. Product overview"); pdf.body("Accounts, learner profiles, course catalog, ranked recommendations with explanations, ordered learning paths, engagement insights, and a transparency/analytics view with real model metrics.")
pdf.h2("2. Problem being solved"); pdf.body("Learners face too many course options and unclear next steps. LearnPathIQ narrows choices to a short ranked list matched to profile and behavior, plus one clear recommended action (review content, take a quiz, join a discussion, review resources, or continue the path).")
pdf.h2("3. Key features"); pdf.body("- Profile-aware hybrid ranking with explanations\n- Behavior-driven personalization loop\n- Success-probability estimates with contributing features\n- Personalized action scores (estimated benefit, observational)\n- Learning path, insights, activity history\n- Offline evaluation and fairness audit reporting")
pdf.h2("4. User workflow"); pdf.body("Register -> complete learner profile -> view dashboard and recommendations -> open/start courses -> log quizzes, content reviews, discussions -> recommendations adapt -> follow the ordered learning path -> review insights.")
pdf.h2("5. System architecture"); pdf.body("FastAPI + Jinja2 frontend, SQLAlchemy/SQLite persistence, recommender service, trained model bundle (scaler, selected predictor, T-learner action models), metrics JSON and plots served to the analytics page. Binds to 127.0.0.1:8000.")
pdf.h2("6. Technology stack"); pdf.body("Python, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic, pandas, NumPy, scikit-learn, XGBoost, joblib, matplotlib, Jinja2.")
pdf.h2("7. Data pipeline"); pdf.body(f"Dataset source: {M.get('dataset_source')}. Weekly learner-state features ({', '.join(M.get('features', []))}), learner-level 80/10/10 split (train {M.get('train_samples')}, val {M.get('val_samples')}, test {M.get('test_samples')}). Categorical encoding, missing-value imputation, scaling; cached artifacts avoid reprocessing per request.")
pdf.h2("8. Recommendation engine"); pdf.body("Weighted hybrid: TF-IDF cosine content similarity (30%), skill compatibility (15%), topic fit (15%), predicted success (12%), behavioral signals (10%), goal fit (8%), rating and engagement (10%). Scores computed dynamically; catalog metadata is static but rankings are not.")
pdf.h2("9. ML models"); pdf.body("Logistic Regression, Random Forest, XGBoost trained to predict learner success from learner-state features. Best by validation AUC is promoted. Confusion matrices, ROC curves, calibration (Brier) and feature importance are generated from the local run.")
pdf.h2("10. Personalization mechanism"); pdf.body("Events (view/open/start/quiz/content/forum/complete/dismiss/save) are stored in SQLite and shift behavioral boosts, engagement scores and state vectors, so rankings differ as history grows (verified live).")
pdf.h2("11. Adaptive action recommendation"); pdf.body("One-vs-rest T-learner estimates uplift(state, action) = P(success|action) - P(success|no action) where data supports it, else a predictive fallback. Policy selects argmax estimated benefit. UI wording is conservative: estimated benefit / personalized action score / based on observed patterns.")
pdf.h2("12. Evaluation methodology"); pdf.body("Held-out learner-level test set; AUC/F1 primary; Brier for calibration. Offline policy value via behavior-policy estimation (multinomial logistic), propensity clipping, IPS/SNIPS/DR on logged data. No live A/B testing claims.")
pdf.h2("13. Actual model metrics (this training run)")
for name, v in M.get("models", {}).items():
    pdf.body(f"{name}: AUC={v.get('roc_auc')} acc={v.get('accuracy')} prec={v.get('precision')} rec={v.get('recall')} F1={v.get('f1')} Brier={v.get('brier')} cm={v.get('confusion_matrix')}")
pe = M.get("policy_evaluation", {})
pdf.body(f"Selected model: {M.get('selected_model')}. Offline policy: IPS={pe.get('ips')} SNIPS={pe.get('snips')} DR={pe.get('doubly_robust')} ({pe.get('limitation', pe.get('reason',''))}).")
pdf.h2("14. Charts")
for img, cap in [("roc_curve.png","ROC curves"),("confusion_matrix.png","Confusion matrix"),("feature_importance.png","Feature importance")]:
    p = BASE / "artifacts" / "plots" / img
    if p.exists():
        try:
            pdf.body(cap + ":"); pdf.image(str(p), w=150); pdf.ln(2)
        except Exception as e:
            pdf.body(f"{cap}: (chart unavailable: {e})")
pdf.h2("15. Fairness audit"); pdf.body(json.dumps(M.get("fairness", {}), indent=1)[:2500] + "\nAudit-only reporting; no claim of perfect fairness.")
pdf.h2("16. Installation"); pdf.body("Double-click run.bat (Windows), or: pip install -r requirements.txt. Optional: docker build -t learnpathiq .")
pdf.h2("17. Running instructions"); pdf.body("run.bat starts http://localhost:8000 automatically. Manual: python scripts/train_pipeline.py, then python -m uvicorn app.main:app --host 127.0.0.1 --port 8000. Docker: docker run --rm -p 8000:8000 learnpathiq.")
pdf.h2("18. Limitations"); pdf.body("Synthetic fallback data when the public dataset is unreachable; observational action scores are not causal proof; offline policy values are not live results; demo-grade auth; single-node SQLite.")
pdf.h2("19. Privacy/security"); pdf.body("Local-first: all data in learnpathiq.db. Hashed passwords (pbkdf2_sha256), HttpOnly token cookie, validated inputs, parameterized queries, no secrets committed.")

out = BASE / "LearnPathIQ_Documentation.pdf"
pdf.output(str(out))
print("wrote", out)
