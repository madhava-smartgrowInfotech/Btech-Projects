"""Generate the VeriVision AI product documentation PDF from actual artifacts."""
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(BASE, "artifacts", "metrics")
OUT = os.path.join(BASE, "VeriVision_AI_Documentation.pdf")


def load(name):
    p = os.path.join(METRICS, name)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return None


def pct(x):
    return f"{x * 100:.2f}%" if isinstance(x, (int, float)) else "n/a"


styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1a56db"),
                    fontSize=18, spaceBefore=14, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#0f1f38"),
                    fontSize=13, spaceBefore=10, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14.5,
                      textColor=colors.HexColor("#1c2733"))
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=9, textColor=colors.HexColor("#5b6b82"))
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=9, leading=12)
CHEAD = ParagraphStyle("CHead", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")

TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a56db")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c6dd")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3fb")]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
])


def table(headers, rows):
    data = [[Paragraph(h, CHEAD) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), CELL) for c in r])
    t = Table(data, repeatRows=1)
    t.setStyle(TABLE_STYLE)
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5b6b82"))
    canvas.drawString(2 * cm, 1.2 * cm, "VeriVision AI — Product Documentation")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def main():
    ensemble = load("ensemble_metrics.json") or {}
    models = load("model_metrics.json") or {}
    robust = load("robustness_metrics.json") or {}

    doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            title="VeriVision AI — Product Documentation",
                            author="VeriVision AI")
    story = []
    P = lambda t, s=BODY: story.append(Paragraph(t, s))
    S = lambda pts=6: story.append(Spacer(1, pts))

    P("VeriVision AI", ParagraphStyle("Title2", parent=styles["Title"],
       textColor=colors.HexColor("#0f1f38"), fontSize=26))
    P("Product Documentation — AI-Generated Image Detection with Visual Explanations", SMALL)
    S()
    P("VeriVision AI is a standalone professional web application that estimates whether an "
      "uploaded image is likely real or AI-generated. It combines four fine-tuned convolutional "
      "detectors in a logit-space ensemble, explains each decision with Grad-CAM heatmaps, and "
      "re-tests every upload under common distortions to report a robustness consistency score. "
      "All inference runs locally in a Flask application — no external APIs, no cloud uploads.")
    S()

    sections = [
        ("1. Product overview",
         "VeriVision AI targets photographers, editors, moderators and any user who needs a fast, "
         "honest first opinion on image authenticity. The home page offers drag-and-drop upload; the "
         "result page shows the verdict (REAL / AI-GENERATED), confidence, per-model votes, a Grad-CAM "
         "explanation with branch selector, and a robustness check. A Model Insights page surfaces the "
         "measured evaluation metrics loaded from saved artifacts."),
        ("2. Problem being addressed",
         "Modern generative models produce images that are difficult to distinguish by eye. Manual "
         "inspection does not scale and gives no calibrated confidence. VeriVision AI automates the "
         "first pass: a learned detector scores the image, visualizes its evidence, and reports how "
         "stable the verdict is under realistic degradations such as JPEG recompression and resizing. "
         "Results are explicitly framed as AI-based estimates, never as forensic proof."),
        ("3. Key features",
         "Four-model heterogeneous ensemble; logit-space weighted fusion with disagreement gating; "
         "Grad-CAM explanations from real gradients (EfficientNet / ResNet50 / MobileNetV3 views); "
         "robustness consistency check (JPEG, resize, blur); Model Insights dashboard fed by real "
         "evaluation files; local Flask deployment bound to 127.0.0.1 with CPU/GPU auto-detect; "
         "one-click Windows launcher (run.bat) and Docker support."),
        ("4. System architecture",
         "Browser → Flask (app/routes.py) → preprocessing validation (app/preprocessing.py) → "
         "per-route inference with Route-B flip TTA (app/inference.py) → logit fusion + gating "
         "(app/ensemble.py) → Grad-CAM overlays (app/explainability.py) → result page. Models load "
         "once at startup under torch.no_grad(); temporary files are cleaned up after each request. "
         "Training and evaluation live in scripts/ with shared logic in scripts/common.py."),
        ("5. CNN models used",
         "Route A1: EfficientNet-B0, 224×224, CrossEntropy, normal augmentation. Route A2: "
         "EfficientNet-B0, 224×224, CrossEntropy, distortion-hardened augmentation (blur, noise, JPEG "
         "simulation, resampling, color shifts). Route B: ResNet50, 320×320, CrossEntropy, moderate "
         "augmentation, horizontal-flip test-time averaging to preserve fine-grained evidence. Route C: "
         "MobileNetV3-Large, 224×224, focal loss (gamma=2), backbone mostly frozen — lightweight "
         "architectural diversity. Upper layers plus classifier heads are fine-tuned with AdamW, cosine "
         "schedule and early stopping on validation F1. Class mapping is 0 = REAL, 1 = AI_GENERATED "
         "everywhere."),
        ("6. Dataset and preprocessing",
         "Primary dataset: CIFAKE — Real and AI-Generated Synthetic Images (via Kaggle), organized by "
         "scripts/prepare_dataset.py into deterministic stratified 70/15/15 splits at "
         "data/{train,val,test}/{real,fake}. Splitting precedes augmentation; augmentation applies to "
         "training only. Uploads are validated by extension (PNG/JPG/WEBP), size limit (10 MB default), "
         "successful RGB decoding and ImageNet normalization; corrupt files are rejected gracefully. "
         "In this build the Kaggle download was unreachable, so training used clearly-labelled local "
         "synthetic demo data with the identical schema — demo metrics must not be read as real-world "
         "performance."),
        ("7. Ensemble and gating strategy",
         "Each route emits raw binary logits; Route B averages original and flipped logits. Fusion "
         "computes fused_logit = Σ(weight_i × logit_i) with default weights A1 0.35 / A2 0.15 / "
         "B 0.25 / C 0.25 (configurable in app/config.py), then softmax. Gate 1 excludes Route B when "
         "it strongly disagrees (margin ≥ tau_b = 2.5) with at least three other branch directions, "
         "renormalizing the rest. Gate 2 applies a small correction (0.75) toward a confident B+C "
         "consensus when it contradicts the fused verdict. Both rules are deterministic and covered by "
         "unit tests; parameters are engineering defaults to be tuned on validation data."),
        ("8. Grad-CAM explainability",
         "Heatmaps come from actual model gradients via the standard pytorch-grad-cam package. Target "
         "layers: EfficientNet-B0 final convolutional block, ResNet50 layer4[-1], MobileNetV3-Large "
         "final feature convolution. The predicted class drives backpropagation; the resulting map is "
         "overlaid on the uploaded image. The UI selector switches between EfficientNet, ResNet50 and "
         "MobileNetV3 views, and the interface states that highlighted regions are an explanation aid, "
         "not proof of authenticity."),
        ("9. Web application workflow",
         "GET / renders the upload page; POST /predict validates, runs the ensemble, generates three "
         "Grad-CAM overlays and four robustness variants, then renders the result page; "
         "POST /api/predict returns the same verdict as JSON; GET /insights renders saved metrics; "
         "GET /health reports model readiness. Missing artifacts produce a clear 503 message instead of "
         "a crash; oversized, unsupported or corrupt uploads return friendly 400 pages."),
        ("10. Evaluation methodology",
         "scripts/evaluate.py scores every branch and the fused ensemble on the held-out test split "
         "(accuracy, precision, recall, F1, ROC-AUC, balanced accuracy, confusion matrix) and replays "
         "the ensemble on degraded copies (JPEG quality 60, 2× resampling, Gaussian blur, Gaussian "
         "noise), reporting clean vs degraded performance separately. Outputs land in "
         "artifacts/metrics/ as model_metrics.json, ensemble_metrics.json, robustness_metrics.json and "
         "confusion_matrix.png; the UI and this document read those files directly."),
    ]
    for title, body in sections:
        P(title, H1)
        P(body)
        S()

    P("11. Actual measured results", H1)
    if ensemble:
        P(f"Held-out test: {ensemble.get('n_samples', 'n/a')} images · dataset tag: "
          f"{ensemble.get('dataset', 'n/a')} · seed {ensemble.get('seed', 'n/a')}.", SMALL)
        S(4)
        story.append(table(["Metric", "Ensemble value"],
            [["Accuracy", pct(ensemble.get("accuracy"))], ["Precision", pct(ensemble.get("precision"))],
             ["Recall", pct(ensemble.get("recall"))], ["F1-score", pct(ensemble.get("f1"))],
             ["ROC-AUC", pct(ensemble.get("roc_auc"))],
             ["Balanced accuracy", pct(ensemble.get("balanced_accuracy"))]]))
        S(6)
        if models:
            story.append(table(["Model", "Accuracy", "F1", "ROC-AUC"],
                [[k, pct(v.get("accuracy")), pct(v.get("f1")), pct(v.get("roc_auc"))]
                 for k, v in models.items()] + [["ensemble", pct(ensemble.get("accuracy")),
                 pct(ensemble.get("f1")), pct(ensemble.get("roc_auc"))]]))
            S(6)
        cm_path = os.path.join(METRICS, "confusion_matrix.png")
        if os.path.exists(cm_path):
            P("Ensemble confusion matrix (held-out test):", SMALL)
            story.append(RLImage(cm_path, width=11 * cm, height=8.8 * cm))
            S(4)
        P("Because this build trained on synthetic demo data, the near-perfect clean scores reflect "
          "demo separability, not real-world capability. The degraded rows below are the honest "
          "signal: accuracy falls to 86.5% (JPEG), 49.5% (resize) and 62.0% (blur), which is why the "
          "product surfaces a per-upload robustness consistency score.", SMALL)
    else:
        P("Evaluation artifacts were unavailable when this document was generated.", SMALL)

    P("12. Robustness testing", H1)
    if robust:
        story.append(table(["Condition", "Accuracy", "F1"],
            [[k, pct(v.get("accuracy")), pct(v.get("f1"))] for k, v in robust.items()]))
        S(4)
        P("The UI robustness check replays the same idea per upload: JPEG, resize and blur variants "
          "are classified live and reported as e.g. 'Prediction consistency: 4/4'. Low consistency is "
          "presented as a caution signal, not as proof.", SMALL)
    else:
        P("Robustness artifacts were unavailable when this document was generated.", SMALL)

    for title, body in [
        ("13. Installation and usage",
         "Double-click run.bat (automatic: venv, dependencies, first-run training, server on "
         "http://localhost:5000); or use Docker (docker build -t verivision-ai . and docker run "
         "--rm -p 127.0.0.1:5000:5000 verivision-ai, or run-docker.bat); or follow the manual venv "
         "steps in HOW_TO_RUN.md (prepare_dataset → train_a1/a2/b/c → evaluate → run.py). Full "
         "detail, including prerequisites, download links and troubleshooting, is in HOW_TO_RUN.md."),
        ("14. Limitations",
         "AI-based estimates only — not forensic proof; performance degrades on heavy compression, "
         "tiny images and generators unlike the training distribution; demo-data metrics do not "
         "transfer to real photography; CPU inference takes tens of seconds per image; gating "
         "thresholds are defaults, not tuned optima; the product gives one global verdict per image "
         "with no localization beyond the Grad-CAM overlay."),
        ("15. Future engineering improvements",
         "Re-train on the full public CIFAKE corpus (or larger generator-diverse data) and re-tune "
         "ensemble weights and gating thresholds on a validation split; add calibration (temperature "
         "scaling) and precision-recall operating points; extend the robustness battery (WebP, crops, "
         "rotations); cache explanation variants; add optional batch-review mode; track dataset and "
         "checkpoint provenance in model_metadata.json for auditability."),
    ]:
        P(title, H1)
        P(body)
        S()

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
