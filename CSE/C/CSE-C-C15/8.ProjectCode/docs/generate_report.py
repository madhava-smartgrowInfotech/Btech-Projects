"""Generate docs/SentinelFlow_Product_Report.pdf from actual build artifacts.

Only real training metrics, real plots, and real screenshots are used.
Usage: python docs/generate_report.py
"""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BASE, "results")
SHOTS = os.path.join(BASE, "screenshots")
OUT = os.path.join(BASE, "docs", "SentinelFlow_Product_Report.pdf")


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default if default is not None else {}


def main():
    from fpdf import FPDF

    metrics = load_json(os.path.join(RESULTS, "metrics.json"))
    importance = load_json(os.path.join(RESULTS, "feature_importance.json"))
    cm = load_json(os.path.join(RESULTS, "confusion_matrix.json"))
    try:
        with open(os.path.join(RESULTS, "classification_report.txt"), "r", encoding="utf-8") as fh:
            class_report = fh.read()
    except Exception:
        class_report = "Classification report unavailable."

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)

    def title_page():
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 28)
        pdf.cell(0, 14, "SentinelFlow", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 9, "Real-Time DDoS Detection & Adaptive Mitigation", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, (
            "Product documentation report. SentinelFlow is a defensive network-monitoring "
            "application that detects suspicious / DDoS-like traffic with a Random Forest "
            "classifier, assesses threat severity, monitors network health, and applies "
            "adaptive mitigation with automatic recovery."
        ))
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Measured model performance (this build)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for label, key in [("Accuracy", "accuracy"), ("Precision", "precision"),
                           ("Recall", "recall"), ("F1-score", "f1"), ("ROC-AUC", "roc_auc")]:
            val = metrics.get(key)
            text = "n/a" if val is None else "%.4f" % val
            pdf.cell(0, 6, "%s: %s" % (label, text), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "Test samples: %s" % metrics.get("test_samples", "n/a"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "Dataset: %s" % metrics.get("dataset_provenance", "n/a"),
                 new_x="LMARGIN", new_y="NEXT")

    def heading(text):
        pdf.set_font("Helvetica", "B", 14)
        pdf.ln(2)
        pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)

    def body(text):
        pdf.multi_cell(0, 6, text)
        pdf.ln(1)

    def image(path, width=170):
        if os.path.exists(path):
            pdf.image(path, w=width)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 6, "[Figure unavailable: %s]" % os.path.basename(path),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)

    title_page()

    pdf.add_page()
    heading("1. SentinelFlow overview")
    body("SentinelFlow is a standalone defensive network-security product. It watches a selected "
         "network interface (or a safe local simulator), aggregates traffic into monitoring windows, "
         "classifies each window with a trained Random Forest, scores distributed-traffic risk, assigns "
         "an explainable severity, and triggers adaptive mitigation with automatic recovery.")
    heading("2. Problem being addressed")
    body(" volumetric and distributed denial-of-service traffic can overwhelm hosts and links. Operators "
         "need a lightweight, explainable, always-on monitor that flags suspicious windows within seconds, "
         "explains why they look suspicious, and takes proportionate defensive action without manual triage.")
    heading("3. Key product features")
    body("- Real-time DDoS detection (Random Forest)\n- 10-second rolling monitoring windows\n"
         "- Distributed / carpet-bombing-aware risk scoring\n- Explainable Low/Medium/High/Critical severity\n"
         "- Adaptive mitigation: application-level quarantine with ~40 s auto-recovery\n"
         "- Network health monitoring (CPU, memory, throughput)\n- Simulation Mode for permission-free demos\n"
         "- SQLite-backed detection, mitigation, and health history")
    heading("4. User workflow")
    body("1. Launch SentinelFlow and open http://localhost:5000.\n2. Pick a capture interface or press "
         "\"Start Simulation\".\n3. Watch summary cards, health charts, and the detection table.\n"
         "4. Click a row for threat detail and severity factors.\n5. Review the Mitigation Center; "
         "quarantines recover automatically.")
    heading("5. System architecture")
    body("Modular Python application: monitoring/ (Scapy capture, aggregation, simulator), ml/ (features, "
         "training, inference), security/ (detector, distributed analysis, severity, mitigation), database/ "
         "(SQLite), config/, Flask app.py serving server-rendered templates plus a JSON REST API, with a "
         "vanilla-JS dashboard using Chart.js (CDN with numeric fallback).")
    heading("6. ML architecture")
    body("RandomForestClassifier (200 trees, class_weight=balanced, seed 42) over a compact 10-feature "
         "interface-level schema. No LLM is used for detection. Feature names and ordering are validated "
         "before every predict() call via the shared ml/features.py module.")
    heading("7. CICIDS2017 data pipeline")
    body("The trainer first looks for local CICIDS2017 CSVs in data/raw/, then attempts documented public "
         "mirrors. In this build the dataset was unreachable, so a schema-compatible synthetic fallback was "
         "generated (clearly labelled in metadata). Raw flow fields are normalized, cleaned of infinite/missing "
         "values, and mapped forward->sent / backward->received with rates from flow duration. A documented "
         "window-scale augmentation (6000 aggregated windows through the real monitoring pipeline) keeps the "
         "model calibrated across flow scale and window scale. Provenance: " +
         str(metrics.get("dataset_provenance", "n/a")))
    heading("8. Random Forest implementation")
    body("Stratified 80/20 train/test split, reproducible seed 42, class-balanced weights. Artifacts: persisted "
         "model (joblib), feature list, metadata, metrics JSON, classification report, confusion matrix, ROC "
         "curve, and feature importance.")
    heading("9. Scapy monitoring")
    body("Scapy sniff() captures per-window packets on the chosen interface (default 10 s). Packets are grouped "
         "into received (inbound/local-destination) vs sent (outbound) using local interface addresses, then "
         "reduced to the 10 common features. Permission/driver failures surface clear errors and the UI offers "
         "Simulation Mode as a safe alternative.")
    heading("10. Network Health Monitoring")
    body("psutil samples CPU, memory, and interface throughput into a rolling buffer plus SQLite history; the "
         "dashboard charts CPU/memory and inbound/outbound byte series.")
    heading("11. Threat Severity Analysis")
    body("Severity blends model confidence, packet-rate pressure, distributed-risk score, source/destination "
         "spread, and cross-window persistence into Low/Medium/High/Critical, always listing the contributing "
         "factors next to the verdict.")
    heading("12. Adaptive Mitigation")
    body("High/Critical windows quarantine the top suspicious sources inside SentinelFlow (default ~40 s, "
         "doubled for Critical) with automatic expiry and recovery history; Medium recommends rate limiting; "
         "Low keeps monitoring. OS firewall changes are never made automatically.")
    heading("13. Simulation Mode")
    body("A safe local generator produces benign plus flood / carpet-bombing / slow-style windows, aggregates "
         "them through the identical inference pipeline, and labels the UI banner as Simulation Mode. It never "
         "emits network traffic.")
    heading("14. Technology stack")
    body("Python 3.11/3.12, Flask, scikit-learn, pandas, numpy, joblib, Scapy, psutil, matplotlib, SQLite; "
         "HTML5 + modern CSS + vanilla JS + Chart.js frontend; Docker support.")
    heading("15. How to run")
    body("Automatic: double-click run.bat and open http://localhost:5000. Docker: docker build -t sentinelflow . "
         "then docker run --rm -p 5000:5000 sentinelflow (or run-docker.bat). Manual: create a venv, "
         "pip install -r requirements.txt, python ml/train_model.py, python app.py. Full steps in HOW_TO_RUN.md.")
    heading("16. Actual evaluation metrics (this build)")
    lines = []
    for label, key in [("Accuracy", "accuracy"), ("Precision", "precision"), ("Recall", "recall"),
                       ("F1-score", "f1"), ("ROC-AUC", "roc_auc")]:
        val = metrics.get(key)
        lines.append("%s: %s" % (label, "n/a" if val is None else "%.4f" % val))
    lines.append("Test samples: %s | Train samples: %s" % (metrics.get("test_samples"), metrics.get("train_samples")))
    lines.append("Class totals: benign=%s attack=%s" % (metrics.get("benign_total"), metrics.get("attack_total")))
    body("\n".join(lines))
    body("Classification report:\n" + class_report)
    heading("17. Actual confusion matrix")
    if isinstance(cm, dict) and "matrix" in cm:
        body("Rows = actual [Benign, Attack]; columns = predicted [Benign, Attack]: %s" % (cm["matrix"],))
    image(os.path.join(RESULTS, "confusion_matrix.png"))
    heading("18. Actual ROC-AUC")
    body("ROC-AUC: %s" % ("n/a" if metrics.get("roc_auc") is None else "%.4f" % metrics.get("roc_auc")))
    image(os.path.join(RESULTS, "roc_curve.png"))
    heading("19. Actual feature importance")
    if importance:
        ranked = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)
        body("\n".join(" - %s: %.4f" % (k, v) for k, v in ranked))
    image(os.path.join(RESULTS, "feature_importance.png"))
    heading("20. Limitations and responsible-use notes")
    body("- Defensive monitoring only: no attack generation, no external scanning, no automatic firewall edits.\n"
         "- Live capture needs elevated privileges and Npcap on Windows; otherwise use Simulation Mode.\n"
         "- This build trained on documented synthetic fallback data (CICIDS2017 unreachable offline); metrics "
         "describe that data, not CICIDS2017 captures, and the dashboard labels this.\n"
         "- Window aggregates differ in scale from single flows; window-scale augmentation addresses this but "
         "operators should re-train on their own labelled captures for production use.\n"
         "- Binds to 127.0.0.1 only; localhost dashboard.")
    dash = os.path.join(SHOTS, "01_dashboard.png")
    if os.path.exists(dash):
        pdf.add_page()
        heading("Appendix: SentinelFlow dashboard (running application)")
        image(dash)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pdf.output(OUT)
    print("Wrote %s" % OUT)


if __name__ == "__main__":
    main()
