"""DFD level 1 and level 2 for CipherGuard Shield (see make_diagrams.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def dfd1():
    fig, ax = canvas(10, 7.8, 100, 78)
    P = [(17, 60, "1.0\nValidate and\nparse request"), (46, 60, "2.0\nScore flow(s)\n(ThreatSense)"), (75, 60, "3.0\nReport verdicts,\nlog alerts"),
         (17, 34, "4.0\nEncrypt payload\n(SecureChannel)"), (46, 34, "5.0\nDecrypt and\nverify at cloud"), (75, 34, "6.0\nServe model\nmetrics"), (46, 9, "7.0\nTrain models\n(offline CLI)")]
    for x, y, t in P:
        ellipse(ax, x, y, 21, 12.5, t, PALE_BLUE, BLUE, fs=8)
    store(ax, 46, 74, 22, 4.8, "D4  models/ artefacts", fs=7.4)
    store(ax, 75, 47, 22, 4.8, "D1  alerts_log (memory)", fs=7.4)
    store(ax, 17, 18, 22, 4.8, "D2  session-key cache", fs=7.4)
    store(ax, 75, 20, 22, 4.8, "D3  reports/metrics.json", fs=7.4)
    store(ax, 75, 5, 22, 4.8, "D4  models/ artefacts", fs=7.4)
    store(ax, 17, 5, 22, 4.8, "D5  training CSV", fs=7.4)
    box(ax, 5, 49, 8.5, 6, "Operator", WHITE, tc=INK, ec=BLUE, fs=7.4, bold=True)
    box(ax, 94, 52, 9.5, 6, "Operator", WHITE, tc=INK, ec=BLUE, fs=7.4, bold=True)
    box(ax, 46, 21.5, 12, 5, "Operator", WHITE, tc=INK, ec=BLUE, fs=7.4, bold=True)
    arrow(ax, (7.5, 52), (11.5, 54.5), "requests", lo=(-1.5, 2.8), fs=7, color=NAVY)
    arrow(ax, (27.5, 60), (35.5, 60), "valid record", lo=(0, 1.8), fs=7, color=NAVY)
    arrow(ax, (46, 71.6), (46, 66.3), "weights, scaler", lo=(8.5, 0), fs=7, color=TEAL)
    arrow(ax, (56.5, 60), (64.5, 60), "scores", lo=(0, 1.8), fs=7, color=NAVY)
    arrow(ax, (73.5, 53.8), (73.5, 49.5), "", color=NAVY)
    arrow(ax, (76.5, 49.5), (76.5, 53.8), "", color=NAVY, ls="--")
    arrow(ax, (83, 57), (89.5, 54.5), "verdicts, alerts", lo=(1, 3.2), fs=7, color=TEAL)
    arrow(ax, (17, 53.7), (17, 40.3), "text / file", lo=(-5, 0), fs=7, color=NAVY)
    arrow(ax, (17, 27.7), (17, 20.5), "session key", lo=(6.5, 0), fs=7, color=NAVY)
    arrow(ax, (27.5, 34), (35.5, 34), "envelope", lo=(0, 1.8), fs=7, color=NAVY)
    arrow(ax, (28, 20), (40, 28.5), "key lookup", lo=(-2, -2.5), fs=7, color=TEAL)
    arrow(ax, (46, 27.7), (46, 24), "plaintext / 400", lo=(9.5, 0), fs=7, color=TEAL)
    arrow(ax, (75, 22.4), (75, 27.7), "", color=TEAL)
    arrow(ax, (82, 38.5), (91, 49), "metrics", lo=(5.5, -1), fs=7, color=TEAL)
    arrow(ax, (54.5, 11), (64, 18.5), "metrics", lo=(-1, 2.6), fs=7, color=NAVY)
    arrow(ax, (56.5, 8), (63.5, 6), "weights, scaler", lo=(-0.5, -2.8), fs=7, color=NAVY)
    arrow(ax, (28, 5.5), (35.5, 8), "labelled flows", lo=(-1, -2.8), fs=7, color=NAVY)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71.2, "DFD level 2 - process 2.0 Score flow(s) (ThreatSenseEngine.predict_proba / score_single)", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    for x, y, t in [(16, 48, "2.1\nFill defaults\nand align\nfeature names"), (50, 48, "2.2\nPreprocess\nMinMax + one-hot"), (84, 48, "2.3\nXGBoost\nattack probability"),
                    (84, 25, "2.4\n1D CNN\nattack probability"), (50, 25, "2.5\nLogistic-regression\nstacking"), (16, 25, "2.6\nThreshold 0.5 and\nseverity band")]:
        ellipse(ax, x, y, 26, 14, t, PALE_BLUE, BLUE, fs=8)
    store(ax, 50, 63.5, 22, 4.6, "D4a preprocessor.joblib", fs=7.2)
    store(ax, 84, 63.5, 22, 4.6, "D4b xgb_model.joblib", fs=7.2)
    store(ax, 84, 7.5, 22, 4.6, "D4c cnn_model.pt", fs=7.2)
    store(ax, 50, 7.5, 22, 4.6, "D4d stacking_meta.joblib", fs=7.2)
    box(ax, 12, 64, 20, 6.5, "From 1.0:\nvalid record (dict)", WHITE, tc=INK, ec=BLUE, fs=7.2, bold=True)
    box(ax, 16, 7.5, 28, 6.5, "To 3.0: label, confidence,\nseverity, xgb and cnn scores", WHITE, tc=INK, ec=BLUE, fs=7.2, bold=True)
    arrow(ax, (14, 60.7), (15, 55.2), "", color=NAVY)
    arrow(ax, (29, 48), (37, 48), "42 columns", lo=(0, 2.2), fs=7, color=NAVY)
    arrow(ax, (50, 61.1), (50, 55.2), "", color=TEAL)
    arrow(ax, (63, 48), (71, 48), "X (70 or\n192 dims)", lo=(0, 3.8), fs=7, color=NAVY)
    arrow(ax, (84, 61.1), (84, 55.2), "", color=TEAL)
    arrow(ax, (84, 40.8), (84, 32.2), "X as (N, 1, F)", lo=(8.5, 0), fs=7, color=NAVY)
    arrow(ax, (84, 9.8), (84, 17.8), "", color=TEAL)
    arrow(ax, (71, 25), (63, 25), "p_cnn", lo=(0, 2), fs=7, color=NAVY)
    arrow(ax, (72, 43), (58, 31.5), "p_xgb", lo=(2, 2.2), fs=7, color=NAVY)
    arrow(ax, (50, 9.8), (50, 17.8), "", color=TEAL)
    arrow(ax, (37, 25), (29, 25), "fused p", lo=(0, 2), fs=7, color=NAVY)
    arrow(ax, (16, 17.8), (16, 11), "", color=NAVY)
    save(fig, OUT / "05_dfd_level2.png")


def main():
    dfd1()
    dfd2()


if __name__ == "__main__":
    main()
