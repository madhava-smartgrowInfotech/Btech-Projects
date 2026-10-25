"""Draw the CipherGuard Shield design diagrams (first half) into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: cipherguard/api/main.py (routes), cipherguard/crypto/secure_channel.py,
cipherguard/ids/*.py (ThreatSense Engine) and web/ + frontend/ (the two user interfaces).
    python scripts/docs_build/make_diagrams.py        (also runs diagrams_more.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def system_architecture():
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 2, 68, 96, 17, "Presentation tier - React 19 + Vite console (port 5305) and the original HTML dashboard (served by the API)", PALE_BLUE, BLUE)
    box(ax, 16, 74, 24, 9.5, "Pages\nLanding - Live scoring\nSecure transfer - Alerts\nModel performance", BLUE, fs=7.6)
    box(ax, 41.5, 74, 22, 9.5, "src/lib + api.js\naxios wrapper over /api\n(Vite proxy to 8305)", BLUE, fs=7.6)
    box(ax, 65.5, 74, 24, 9.5, "UI kit (V5 Kinetic Mono)\nRecharts - Framer Motion\nGSAP - three.js backdrop", BLUE, fs=7.6)
    box(ax, 88, 74, 17, 9.5, "web/index.html\nlegacy dashboard\nat GET /", GREY, fs=7.6)

    panel(ax, 2, 48, 96, 18.5, "Application tier - FastAPI + Uvicorn (cipherguard/api/main.py, 127.0.0.1:8305)", PALE_TEAL, TEAL)
    box(ax, 15, 54.5, 24, 10, "Health + metrics\nGET /api/health\nGET /api/metrics", TEAL, fs=7.6)
    box(ax, 40.5, 54.5, 24, 10, "ThreatSense routes\nPOST /api/ids/score\nPOST /api/ids/score-batch\nGET, DELETE /api/alerts", TEAL, fs=7.4)
    box(ax, 66, 54.5, 24, 10, "SecureChannel routes\nPOST /api/crypto/encrypt\nPOST /api/crypto/decrypt\nPOST /api/crypto/encrypt-file", TEAL, fs=7.4)
    box(ax, 88, 54.5, 17, 10, "Guards\n1 MB text, 5 MB file\n10 MB / 10,000-row CSV\n400 / 503 errors", TEAL, fs=7.0)

    panel(ax, 2, 24, 96, 22, "Core modules (Python packages) and in-memory state", PALE_ORANGE, ORANGE)
    box(ax, 17, 36, 28, 11, "cipherguard/crypto\nSecureChannel + KeyPair\nECDH P-256, HKDF-SHA256,\nAES-256-GCM", ORANGE, fs=7.4)
    box(ax, 50, 36, 34, 11, "cipherguard/ids  (ThreatSense Engine)\npreprocessing - XGBoost - 1D CNN (PyTorch)\nLogistic-regression stacking - inference", ORANGE, fs=7.4)
    box(ax, 82, 36, 26, 11, "In-memory state\nalerts_log (<= 500 entries)\n_last_session_keys cache\nmock cloud key pair", NAVY, fs=7.4)
    box(ax, 17, 27.5, 28, 3.6, "Mock cloud endpoint (same process)", WHITE, tc=INK, ec=ORANGE, fs=7.2)
    box(ax, 50, 27.5, 34, 3.6, "synthetic.py - features.py (42-feature schema)", WHITE, tc=INK, ec=ORANGE, fs=7.2)

    panel(ax, 2, 1.5, 96, 20, "Data tier - files on disk (no database)", LIGHT, "#B7C3D3")
    store(ax, 14, 9, 21, 10, "models/\nxgb_model.joblib\ncnn_model.pt\nstacking_meta.joblib\npreprocessor.joblib", fs=6.8)
    store(ax, 37, 9, 20, 10, "reports/\nmetrics.json\nmetrics.md\n(held-out test)", fs=7.0)
    store(ax, 59.5, 9, 21, 10, "data/raw/\nsynthetic_demo.csv\n12,000 rows,\n42-feature schema", fs=7.0)
    store(ax, 83, 9, 24, 10, "data/external + experiments/\nreal UNSW-NB15 flows and\nresults (offline study only)", fs=6.9)

    arrow(ax, (50, 68), (50, 66.5), "HTTP + JSON, multipart upload", lo=(20, 0), fs=7.4, color=NAVY)
    arrow(ax, (50, 48), (50, 46), "function calls", lo=(8, 0), fs=7.4, color=NAVY)
    arrow(ax, (50, 24), (50, 21.5), "load / read", lo=(7, 0), fs=7.4, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


def high_level_workflow():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61, "Two protections around one transfer: encrypt the payload, watch the traffic", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.text(3, 54.5, "Lane A - SecureChannel (confidentiality + integrity)", fontsize=8.6, color=TEAL, fontweight="bold")
    a = [("Payload", "text <= 1 MB or\nfile <= 5 MB", BLUE), ("Ephemeral\nkey pair", "P-256, new for\nevery message", TEAL), ("ECDH + HKDF", "shared secret ->\n32-byte AES key", TEAL),
         ("AES-256-GCM", "12-byte nonce,\n16-byte tag", TEAL), ("Envelope", "ciphertext, nonce,\ntag, ephemeral pub.", NAVY), ("Cloud decrypt", "derive key, check tag,\nplaintext or 400", ORANGE)]
    xs = [9 + i * 16.4 for i in range(6)]
    for x, (t, d, c) in zip(xs, a):
        box(ax, x, 44, 14.2, 13, f"{t}\n{d}", c, fs=7.4)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 7.2, 44), (q - 7.2, 44), color=NAVY)
    ax.text(3, 31, "Lane B - ThreatSense Engine (detect attacks in the traffic)", fontsize=8.6, color=PURPLE, fontweight="bold")
    b = [("Flow record", "42 features, one row\nor a CSV batch", BLUE), ("Preprocess", "MinMax scale,\none-hot proto/service/state", PURPLE), ("XGBoost + 1D CNN", "two attack\nprobabilities", PURPLE),
         ("LR stacking", "fused probability\nthreshold 0.5", PURPLE), ("Verdict", "label, confidence,\nseverity", NAVY), ("Alert log", "attacks appended\n(<= 500, in memory)", ORANGE)]
    for x, (t, d, c) in zip(xs, b):
        box(ax, x, 21, 14.2, 13, f"{t}\n{d}", c, fs=7.4)
    for p, q in zip(xs[:-1], xs[1:]):
        arrow(ax, (p + 7.2, 21), (q - 7.2, 21), color=NAVY)
    ax.text(50, 6.5, "The console runs both lanes side by side. The API does not gate a transfer on the verdict:\nblocking or quarantining a flagged session is left to the operator (see Scope and Limitations).",
            ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


def dfd0():
    fig, ax = canvas(10, 5.6, 100, 56)
    box(ax, 50, 28, 26, 16, "CipherGuard Shield\n(0)\nSecureChannel +\nThreatSense Engine +\nconsole", NAVY, fs=9, bold=True, r=2)
    box(ax, 10, 42, 17, 9, "Operator /\nsecurity analyst", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    box(ax, 10, 14, 17, 9, "Developer /\nadministrator", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    box(ax, 90, 42, 17, 9, "Cloud endpoint\n(mock, in-process)", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    box(ax, 90, 14, 17, 9, "UNSW-NB15 or\nsynthetic CSV", WHITE, tc=INK, ec=BLUE, fs=8.4, bold=True)
    arrow(ax, (18.5, 44), (37, 33.5), "flow record, CSV,\ntext or file, ciphertext", lo=(-2, 5), fs=7.2, color=NAVY)
    arrow(ax, (37, 30), (18.5, 40), "verdicts, alerts,\nenvelope, plaintext,\nmetrics", lo=(-1, -6.0), fs=7.2, color=TEAL, rad=0.0)
    arrow(ax, (18.5, 14), (37, 23.5), "retrain command", lo=(-4, 6.0), fs=7.2, color=NAVY)
    arrow(ax, (37, 21.5), (18.5, 12.5), "models, metrics.json", lo=(3, -6.0), fs=7.2, color=TEAL)
    arrow(ax, (63, 33.5), (81.5, 44), "envelope (ciphertext,\nnonce, tag, ephemeral key)", lo=(1, 5), fs=7.2, color=NAVY)
    arrow(ax, (81.5, 40), (63, 30), "verified plaintext /\ntag failure", lo=(0, -5), fs=7.2, color=TEAL)
    arrow(ax, (81.5, 14), (63, 23.5), "labelled flows", lo=(2, -3), fs=7.2, color=NAVY)
    ax.text(50, 4, "Level 0 (context). The mock cloud lives in the same process; it is drawn separately because a real deployment would run it elsewhere.", ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


def uml_class_diagram():
    fig, ax = canvas(10, 8.9, 100, 100)
    ax.set_ylim(11, 100)
    uml_class(ax, 35, 98, 30, "FastAPI app (main.py)", ["engine: ThreatSenseEngine", "alerts_log: list[dict]", "_last_session_keys: dict", "MODELS_DIR, REPORTS_DIR"],
              ["health(), get_metrics()", "score_single(), score_batch()", "get_alerts(), clear_alerts()", "crypto_encrypt(), crypto_decrypt()", "encrypt_file()"], hdr=NAVY, fs=6.6)
    uml_class(ax, 35, 68, 30, "Request schemas", ["IDSRecord: 42 optional features", "EncryptRequest.plaintext: str", "DecryptRequest.ciphertext, nonce,", "  tag, ephemeral_public: str"],
              ["(pydantic BaseModel)"], hdr=GREY, stereotype="pydantic", fs=6.6)
    uml_class(ax, 35, 46, 30, "Alert (dict entry)", ["timestamp: str", "severity: low|medium|high|critical", "confidence: float", "features: dict, scores: dict"], [], hdr=ORANGE, stereotype="in-memory record, appended by main.py", fs=6.6)
    uml_class(ax, 2, 90, 30, "ThreatSenseEngine", ["models_dir: Path", "preprocessor, xgb_model, cnn_model", "meta_model, input_dim", "cnn_backend, loaded: bool"],
              ["load()", "predict_proba(df) : dict", "score_single(record) : dict", "get_metrics() : dict", "_cnn_predict(X) : ndarray"], hdr=PURPLE, fs=6.6)
    uml_class(ax, 2, 60, 30, "CNN1D_Torch", ["conv1: Conv1d(1, 32, 3)", "conv2: Conv1d(32, 64, 3)", "fc1: Linear(flat, 64)", "dropout 0.3, fc2: Linear(64, 1)"],
              ["forward(x) : sigmoid prob"], hdr=PURPLE, stereotype="torch.nn.Module", fs=6.6)
    uml_class(ax, 2, 39, 30, "Training pipeline (train.py)", ["XGBClassifier (200 trees, depth 6)", "LogisticRegression meta-model", "ColumnTransformer: MinMax + OneHot"],
              ["train_pipeline(data_dir, ...)", "train_cnn_torch(X, y, ...)", "generate_synthetic(n, seed)"], hdr=ORANGE, fs=6.6)
    uml_class(ax, 68, 90, 30, "SecureChannel", [],
              ["derive_session_key(priv, peer_pub)", "encrypt(plaintext, key) : dict", "decrypt(ct, nonce, tag, key)", "encrypt_with_ephemeral(pt, pub)", "encrypt_b64 / decrypt_b64"], hdr=TEAL, stereotype="static methods", fs=6.6)
    uml_class(ax, 68, 66, 30, "KeyPair", ["private_key: EllipticCurvePrivateKey", "public_key: EllipticCurvePublicKey"],
              ["generate() : KeyPair", "public_bytes_raw() : bytes", "load_public_from_bytes(b) : key"], hdr=TEAL, stereotype="dataclass", fs=6.6)
    arrow(ax, (35, 83), (32, 83), "uses", lo=(0, 1.6), fs=7, color=NAVY)
    arrow(ax, (65, 83), (68, 83), "uses", lo=(0, 1.6), fs=7, color=NAVY)
    arrow(ax, (83, 70.8), (83, 66.2), "creates", lo=(5, 0), fs=7, color=NAVY)
    arrow(ax, (17, 64.8), (17, 60.2), "owns", lo=(4, 0), fs=7, color=NAVY)
    arrow(ax, (50, 72.8), (50, 68.2), "validates", lo=(5, 0), fs=7, color=NAVY)
    arrow(ax, (17, 43.4), (17, 39.2), "", color=NAVY, ls="--")
    ax.text(50, 16.5, "Training pipeline (offline) writes models/*.joblib and cnn_model.pt;\nThreatSenseEngine.load() reads them at start-up.\nThe engine redefines the CNN layer stack in inference.py,\nidentical to CNN1D_Torch in train.py.",
            ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


def sequence():
    fig, ax = canvas(10, 8.4, 100, 84)
    names = ["Console\n(browser)", "FastAPI\nmain.py", "ThreatSense\nEngine", "SecureChannel\n+ KeyPair", "Mock cloud\nkey pair", "alerts_log /\nkey cache"]
    xs = [8, 24, 41, 58, 75, 92]
    for x, n in zip(xs, names):
        box(ax, x, 80, 13.5, 6.5, n, NAVY, fs=7.4, bold=True)
        ax.plot([x, x], [77, 3], color="#9AA7B8", lw=1, ls="--", zorder=1)
    y = 73

    def msg(i, j, text, y, color=NAVY, ls="-", dy=1.6):
        arrow(ax, (xs[i], y), (xs[j], y), text, color=color, ls=ls, lo=(0, dy), fs=7)
    msg(0, 1, "POST /api/ids/score {flow record}", y)
    msg(1, 2, "score_single(merged 42 features)", y - 4.2)
    ax.text(41, y - 7.6, "preprocess -> XGBoost p1, CNN p2 -> LR stack", fontsize=6.8, ha="center", color=INK, style="italic")
    msg(2, 1, "label, confidence, severity", y - 10.4, ls="--")
    msg(1, 5, "if attack: insert alert", y - 14.2)
    msg(1, 0, "200 {verdict (+alert)}", y - 18.2, ls="--")
    msg(0, 1, "POST /api/crypto/encrypt {plaintext}", y - 23.5)
    msg(1, 3, "KeyPair.generate(); derive_session_key(eph_priv, cloud_pub)", y - 27.7)
    ax.text(66, y - 30.9, "cloud_pub from get_cloud_public_key()", fontsize=6.8, ha="center", color=INK, style="italic")
    msg(3, 1, "AES-256-GCM encrypt -> ciphertext, nonce, tag", y - 34.6, ls="--")
    msg(1, 5, "cache session key by ephemeral_public", y - 38.6)
    msg(1, 0, "200 {ciphertext, nonce, tag, ephemeral_public}", y - 42.6, ls="--")
    msg(0, 1, "POST /api/crypto/decrypt {envelope}", y - 48)
    msg(1, 5, "key cached?  else ECDH(cloud_priv, eph_pub)", y - 52.2)
    msg(1, 4, "cloud private key (cache miss only)", y - 56.2)
    msg(1, 3, "decrypt(ct, nonce, tag, key)", y - 60.4)
    msg(3, 1, "plaintext, or InvalidTag", y - 64.4, ls="--")
    msg(1, 0, "200 {plaintext, verified: true}  |  400 on tag mismatch", y - 68.4, ls="--")
    save(fig, OUT / "07_sequence_flow.png")


def use_case():
    fig, ax = canvas(10, 6.8, 100, 68)
    ax.add_patch(Rectangle((22, 3), 56, 62, fc="#F7F9FC", ec=GREY, lw=1.3, zorder=0))
    ax.text(50, 62.3, "CipherGuard Shield", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    cases = [(50, 55, "Score one traffic record"), (50, 47, "Score a CSV batch"), (50, 39, "Review and clear alerts"), (50, 31, "Encrypt text or file"),
             (50, 23, "Decrypt and verify at cloud"), (50, 15, "Run a tamper test"), (50, 7.5, "View model performance")]
    for x, y, t in cases:
        ellipse(ax, x, y, 36, 6.2, t, PALE_BLUE, BLUE, fs=8.2)
    box(ax, 9, 38, 14, 12, "Operator /\nsecurity\nanalyst", WHITE, tc=INK, ec=NAVY, fs=8.2, bold=True)
    box(ax, 91, 23, 14, 10, "Cloud\nendpoint\n(mock)", WHITE, tc=INK, ec=NAVY, fs=8.2, bold=True)
    box(ax, 91, 52, 14, 12, "Developer /\nadministrator\n(CLI)", WHITE, tc=INK, ec=NAVY, fs=8.2, bold=True)
    ellipse(ax, 68.5, 61, 18, 4, "Retrain models", PALE_ORANGE, ORANGE, fs=7.2)
    for _, y, _t in cases:
        arrow(ax, (16, 38), (32, y), color=GREY, lw=1.0, style="-")
    arrow(ax, (84, 23), (68, 23), "", color=GREY, lw=1.0, style="-")
    arrow(ax, (84, 55), (73, 61), "", color=GREY, lw=1.0, style="-")
    ax.text(50, 0.8, "Tamper test = flip a ciphertext byte, then decrypt (includes Decrypt and verify). Retraining is a command-line action (python -m cipherguard.ids.train).", ha="center", fontsize=6.9, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


if __name__ == "__main__":
    system_architecture(); high_level_workflow(); dfd0(); uml_class_diagram(); sequence(); use_case()
    import diagrams_dfd
    diagrams_dfd.main()
    try:
        import diagrams_more
        diagrams_more.main()
    except ImportError:
        pass
