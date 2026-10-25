"""Second half of the CipherGuard Shield diagrams: ER, scoring flowchart, SecureChannel flowchart, model architecture."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def er_diagram():
    fig, ax = canvas(10, 8.2, 100, 82)
    ax.text(50, 79.5, "Logical entities (CipherGuard Shield keeps no database: alerts and keys live in process memory, models and reports are files)",
            ha="center", fontsize=8.0, color=NAVY, fontweight="bold")
    uml_class(ax, 2, 76, 29, "FLOW_RECORD", ["dur, spkts, dpkts, sbytes, ...", "(39 numeric features)", "proto, service, state", "label, attack_cat (CSV only)"], [], hdr=BLUE, stereotype="request payload", fs=6.6)
    uml_class(ax, 36, 76, 28, "VERDICT", ["label: normal | attack", "confidence: float 0-1", "severity: low..critical", "xgb_score, cnn_score"], [], hdr=PURPLE, stereotype="response", fs=6.6)
    uml_class(ax, 69, 76, 29, "ALERT", ["timestamp", "severity, confidence, label", "features: proto, service,", "  state, sbytes, dbytes, rate, ct_srv_src", "scores: xgb, cnn"], [], hdr=ORANGE, stereotype="in-memory list <= 500", fs=6.6)
    uml_class(ax, 2, 48, 29, "METRICS_REPORT", ["data_mode, dataset_rows, splits", "accuracy, precision, recall", "f1, roc_auc, confusion_matrix", "xgb_accuracy, cnn_accuracy", "meta_coef, meta_intercept"], [], hdr=NAVY, stereotype="reports/metrics.json", fs=6.6)
    uml_class(ax, 36, 48, 28, "MODEL_BUNDLE", ["xgb_model.joblib", "cnn_model.pt", "stacking_meta.joblib", "preprocessor.joblib", "feature_info.json"], [], hdr=NAVY, stereotype="files in models/", fs=6.6)
    uml_class(ax, 69, 48, 29, "ENVELOPE", ["ciphertext (b64, = plaintext length)", "nonce (12 B), tag (16 B)", "ephemeral_public (65 B)", "algorithm, key_exchange"], [], hdr=TEAL, stereotype="encrypt response / decrypt request", fs=6.6)
    uml_class(ax, 36, 21, 28, "CLOUD_KEYPAIR", ["private_key (P-256)", "public_key (P-256)", "one pair per server process"], [], hdr=TEAL, stereotype="mock cloud", fs=6.6)
    uml_class(ax, 69, 21, 29, "SESSION_KEY_CACHE", ["key: ephemeral_public (b64)", "value: 32-byte AES key"], [], hdr=GREY, stereotype="in-memory dict (demo shortcut)", fs=6.6)
    def line(p1, p2):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=NAVY, lw=1.6, zorder=4)
    line((31, 67.5), (36, 67.5)); ax.text(33.5, 69.3, "scored as", fontsize=6.8, ha="center", color=GREY)
    ax.text(32, 65.6, "1", fontsize=7, ha="center"); ax.text(35, 65.6, "1", fontsize=7, ha="center")
    line((64, 67.5), (69, 67.5)); ax.text(66.5, 69.3, "raises", fontsize=6.8, ha="center", color=GREY)
    ax.text(65, 65.6, "1", fontsize=7, ha="center"); ax.text(68, 65.6, "0..1", fontsize=7, ha="center")
    line((50, 59), (50, 48)); ax.text(52, 54, "scored with (n:1)", fontsize=6.8, color=GREY)
    line((31, 38), (36, 38)); ax.text(33.5, 39.8, "describes", fontsize=6.8, ha="center", color=GREY)
    ax.text(32, 36.2, "1", fontsize=7, ha="center"); ax.text(35, 36.2, "1", fontsize=7, ha="center")
    line((83.5, 29), (83.5, 21)); ax.text(85, 25, "cached for (0..1)", fontsize=6.8, color=GREY)
    line((69, 36), (60, 21)); ax.text(58.5, 25.5, "derived with (n:1)", fontsize=6.8, color=GREY, ha="right")
    ax.text(50, 3.5, "No foreign keys exist: the relations are call-time dependencies. The session-key cache is a shortcut of the demo; when it misses,\nthe cloud key pair re-derives the key from the envelope's ephemeral_public (a real ECDH).",
            ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "09_er_diagram.png")


def scoring_flowchart():
    fig, ax = canvas(10, 9.4, 100, 94)
    x = 38
    box(ax, x, 90, 26, 5, "Start: POST /api/ids/score or /score-batch", NAVY, fs=7.6, bold=True)
    diamond(ax, x, 80, 34, 8, "Engine loaded and\npayload valid?", fs=7.6)
    box(ax, 80, 80, 28, 7, "400 invalid payload / CSV error\n503 engine not ready", GREY, fs=7.2)
    box(ax, x, 69, 38, 6.2, "Fill missing features with defaults;\nmatch column names (case-insensitive)", BLUE, fs=7.4)
    box(ax, x, 59, 38, 6.2, "Cast proto, service, state to text;\nMinMaxScaler + OneHotEncoder (unknown = ignored)", BLUE, fs=7.4)
    box(ax, x - 14, 47, 20, 7.5, "XGBoost\np_xgb = P(attack)", PURPLE, fs=7.6)
    box(ax, x + 14, 47, 20, 7.5, "1D CNN (PyTorch)\np_cnn = P(attack)", PURPLE, fs=7.6)
    box(ax, x, 36.5, 38, 6.2, "Logistic-regression meta-model:\np = sigmoid(w1*p_xgb + w2*p_cnn + b)", PURPLE, fs=7.4)
    diamond(ax, x, 26, 28, 8, "p >= 0.5 ?", fs=8)
    box(ax, 12, 14, 22, 8.5, "label = attack\nseverity: p >= 0.85 critical,\n>= 0.70 high, else medium", ORANGE, fs=7.2)
    box(ax, 12, 3.8, 22, 4.8, "append alert (keep newest 500)", ORANGE, fs=7.2)
    box(ax, 64, 14, 22, 8.5, "label = normal\nseverity = low\n(no alert)", TEAL, fs=7.4)
    box(ax, 88, 3.8, 20, 4.8, "Return verdict JSON", NAVY, fs=7.6, bold=True)
    arrow(ax, (x, 87.4), (x, 84), color=NAVY)
    arrow(ax, (x + 17, 80), (66, 80), "no", lo=(0, 1.6), fs=7.4, color=NAVY)
    arrow(ax, (x, 76), (x, 72.2), "yes", lo=(2.5, 0), fs=7.4, color=NAVY)
    arrow(ax, (x, 65.9), (x, 62.2), color=NAVY)
    arrow(ax, (x - 8, 55.9), (x - 14, 50.8), color=NAVY)
    arrow(ax, (x + 8, 55.9), (x + 14, 50.8), color=NAVY)
    arrow(ax, (x - 14, 43.2), (x - 6, 39.7), color=NAVY)
    arrow(ax, (x + 14, 43.2), (x + 6, 39.7), color=NAVY)
    arrow(ax, (x, 33.4), (x, 30), color=NAVY)
    arrow(ax, (x - 14, 26), (12, 18.4), "yes", lo=(-3, 1.8), fs=7.4, color=NAVY)
    arrow(ax, (12, 9.5), (12, 6.3), color=NAVY)
    arrow(ax, (x + 14, 26), (64, 18.4), "no", lo=(3, 1.8), fs=7.4, color=NAVY)
    arrow(ax, (23, 3.8), (78, 3.8), color=NAVY)
    arrow(ax, (64, 9.7), (84, 5.8), color=NAVY)
    save(fig, OUT / "10_flowchart_scoring.png")


def securechannel_flowchart():
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 1, 3, 46, 80, "Sender side (encrypt, POST /api/crypto/encrypt)", PALE_BLUE, BLUE, fs=9)
    panel(ax, 53, 3, 46, 80, "Cloud side (decrypt, POST /api/crypto/decrypt)", PALE_TEAL, TEAL, fs=9)
    s = [("1  Plaintext non-empty and <= 1 MB?\n(files: non-empty, <= 5 MB)", 70), ("2  Generate ephemeral P-256 key pair\n(e, E) - new for every message", 58),
         ("3  ECDH:  Z = e x C_pub\n(C_pub = cloud's long-term public key)", 46), ("4  HKDF-SHA256(Z, info = cipherguard-shield-v1)\n-> 32-byte key K", 34),
         ("5  nonce = 12 random bytes;\nAES-256-GCM(K, nonce, plaintext) -> ciphertext + tag", 22), ("6  Envelope = ciphertext, nonce (12 B),\ntag (16 B), E (65 B)", 10)]
    for t, y in s:
        box(ax, 24, y, 40, 8.2, t, BLUE, fs=7.4)
    for (_, y1), (_, y2) in zip(s[:-1], s[1:]):
        arrow(ax, (24, y1 - 4.2), (24, y2 + 4.2), color=NAVY)
    c = [("7  Base64 decode; nonce 12 B, tag 16 B?\nmissing or malformed -> 400", 70), ("8  Key K: cached by E, else\nECDH(c_priv, E) + HKDF-SHA256", 58),
         ("9  AES-256-GCM decrypt and verify the tag", 46)]
    for t, y in c:
        box(ax, 76, y, 40, 8.2, t, TEAL, fs=7.4)
    arrow(ax, (76, 65.8), (76, 62.2), color=NAVY)
    arrow(ax, (76, 53.8), (76, 50.2), color=NAVY)
    diamond(ax, 76, 33, 34, 10, "Tag valid and key\ncorrect?", fs=7.8)
    arrow(ax, (76, 41.8), (76, 38), color=NAVY)
    box(ax, 65, 17, 19, 8.5, "200 plaintext,\nverified = true", NAVY, fs=7.6)
    box(ax, 88, 17, 19, 8.5, "400 Decryption failed\n(tag / key mismatch)", ORANGE, fs=7.2)
    arrow(ax, (70, 28.5), (65, 21.4), "yes", lo=(-2.5, 1.5), fs=7.4, color=NAVY)
    arrow(ax, (82, 28.5), (88, 21.4), "no", lo=(2.5, 1.5), fs=7.4, color=NAVY)
    arrow(ax, (44.2, 10), (55.8, 70), "envelope over HTTP", lo=(0, 13), fs=7.6, color=NAVY, rad=-0.12)
    save(fig, OUT / "11_flowchart_securechannel.png")


def model_architecture():
    fig, ax = canvas(10, 6.6, 100, 66)
    box(ax, 9, 33, 14, 14, "Flow record\n42 features\n(3 categorical,\n39 numeric)", BLUE, fs=7.6)
    box(ax, 28, 33, 15, 14, "Preprocess\nMinMaxScaler (39)\nOneHot (31 in the\nsynthetic bundle)\n= 70 inputs", BLUE, fs=7)
    arrow(ax, (16, 33), (20.5, 33), color=NAVY)
    box(ax, 52, 55, 28, 9, "A  XGBoost\n200 trees, depth 6, lr 0.08\nscale_pos_weight = neg/pos", PURPLE, fs=7.4)
    arrow(ax, (35.5, 38), (38, 55), color=NAVY)
    panel(ax, 38, 3, 40, 40, "B  1D CNN (PyTorch, 76,097 parameters at 70 inputs)", PALE_PURPLE, PURPLE, fs=8)
    layers = ["reshape (N, 1, 70)", "Conv1d 1->32, k=3, ReLU", "MaxPool1d(2) -> 35", "Conv1d 32->64, k=3, ReLU", "MaxPool1d(2) -> 17", "Flatten 64 x 17 = 1,088",
              "Dense 64, ReLU, Dropout 0.3", "Dense 1, sigmoid"]
    for i, t in enumerate(layers):
        box(ax, 58, 36 - i * 4.15, 32, 3.4, t, PURPLE, fs=6.9)
        if i:
            arrow(ax, (58, 36 - (i - 1) * 4.15 - 1.8), (58, 36 - i * 4.15 + 1.8), color=WHITE, lw=1.0)
    arrow(ax, (35.5, 29), (38.5, 30), color=NAVY)
    box(ax, 88, 33, 20, 14, "Stacking\nLogistic regression on\n[p_xgb, p_cnn]\n(fit on validation split)", ORANGE, fs=7.2)
    arrow(ax, (66, 55), (84, 40), "p_xgb", lo=(-1, 2), fs=7.2, color=NAVY)
    arrow(ax, (74, 25), (78, 30), "p_cnn", lo=(0.5, -2.2), fs=7.2, color=NAVY)
    box(ax, 88, 12, 20, 9, "p >= 0.5  ->  attack\nelse normal;\nseverity bands", NAVY, fs=7.4)
    arrow(ax, (88, 26), (88, 16.6), color=NAVY)
    ax.text(9, 10, "With real UNSW-NB15 the encoded\nvector has 192 inputs (more proto,\nservice and state values), so the\nflatten layer has 48 x 64 = 3,072 units.", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "12_model_architecture.png")


def main():
    er_diagram()
    scoring_flowchart()
    securechannel_flowchart()
    model_architecture()


if __name__ == "__main__":
    main()
