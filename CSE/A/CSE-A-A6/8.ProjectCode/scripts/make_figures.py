r"""Collects the measurement charts into docs/figures and draws two more from real data.

    .venv\Scripts\python.exe scripts\make_figures.py --cew C:\ceww\d1\dataset_B_FacialImages
Needs experiments/cew_ear, experiments/rule_engine and experiments/api_latency to exist (run the measure_*.py scripts first).
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FIG = ROOT / 'docs' / 'figures'
EXP = ROOT / 'experiments'


def landmark_examples(cew):
    """Real CEW faces with the six EAR points per eye drawn, open (top row) and closed (bottom row), via the shipped Vision."""
    from vision import Vision
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = list(csv.DictReader((EXP / 'cew_ear' / 'per_image.csv').open()))
    rng = np.random.default_rng(7)
    v = Vision()
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.0), dpi=150)
    t = 0.0
    for row, (label, sub, lo, hi) in enumerate(((0, 'OpenFace', 0.26, 0.34), (1, 'ClosedFace', 0.02, 0.09))):
        pool = [r for r in rows if r['closed_truth'] == str(label) and r['quality'] == 'Good' and lo < float(r['ear']) < hi]
        col = 0
        for i in rng.permutation(len(pool)):
            if col == 3:
                break
            r = pool[i]
            img = cv2.imread(str(Path(cew) / sub / r['file']))
            img = cv2.resize(img, (480, 480), interpolation=cv2.INTER_CUBIC)
            canvas = np.empty((480, 640, 3), np.uint8)
            canvas[:] = img.reshape(-1, 3).mean(axis=0).astype(np.uint8)
            canvas[:, 80:560] = img
            v.previous = None
            t += 0.1
            o = v.process(canvas, t)     # draws the eye points on the canvas
            if o.quality != 'Good':      # VIDEO-mode tracking makes a few stills flip between runs; show assessed ones only
                continue
            ax = axes[row, col]
            ax.imshow(cv2.cvtColor(canvas[:, 80:560], cv2.COLOR_BGR2RGB))
            ax.set_title(f"{'Open' if label == 0 else 'Closed'} (truth)  EAR {o.ear:.3f}", fontsize=8)
            ax.axis('off')
            col += 1
    v.close()
    fig.suptitle('Six-point eye landmarks on real CEW faces (green dots) and the EAR they give', fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / 'landmark_examples.png')


def robustness_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    conds = json.loads((EXP / 'cew_ear' / 'metrics.json').read_text())['robustness']['conditions']
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=150)
    names = [c['condition'] for c in conds]
    ypos = np.arange(len(names))
    good = np.array([c['good_rate'] * 100 for c in conds])
    ax.barh(ypos, good, color='#2a9d8f', label='Assessed (quality Good)')
    ax.barh(ypos, 100 - good, left=good, color='#adb5bd', label='Unable to assess')
    ax.set_yticks(ypos); ax.set_yticklabels(names, fontsize=7); ax.invert_yaxis()
    ax.set(xlabel='% of images', title='Quality gating on degraded open-eye faces (n = 272)')
    ax.legend(frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=2)
    fig.tight_layout(); fig.savefig(FIG / 'robustness.png')


def latency_chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a = json.loads((EXP / 'api_latency' / 'metrics.json').read_text())
    names = ['GET /api/health', 'POST tick (simulation, monitoring on)', 'GET /api/history (limit 500)',
             'POST frame (real face JPEG 640x480, monitoring on)']
    labels = ['health', 'simulation tick', 'history (500 rows)', 'camera frame']
    p50 = [a[n]['p50_ms'] for n in names]
    p95 = [a[n]['p95_ms'] for n in names]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
    ax.bar(x - 0.18, p50, 0.36, label='median', color='#2a9d8f')
    ax.bar(x + 0.18, p95, 0.36, label='95th percentile', color='#e76f51')
    for i, (m, q) in enumerate(zip(p50, p95)):
        ax.text(i - 0.18, m + 0.8, f'{m:.1f}', ha='center', fontsize=7)
        ax.text(i + 0.18, q + 0.8, f'{q:.1f}', ha='center', fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set(ylabel='milliseconds', title='API latency on 127.0.0.1 (i5-12500, CPU only)')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / 'api_latency.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cew', required=True)
    args = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)
    for src in ('cew_ear/ear_histogram.png', 'cew_ear/threshold_sweep.png', 'cew_ear/roc.png',
                'rule_engine/closure_vs_warning.png', 'rule_engine/parameter_tradeoff.png'):
        shutil.copy(EXP / src, FIG / Path(src).name)
    landmark_examples(args.cew)
    robustness_chart()
    latency_chart()
    print('figures:', sorted(p.name for p in FIG.glob('*.png')))


if __name__ == '__main__':
    main()
