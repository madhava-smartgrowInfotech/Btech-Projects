"""Component-level measurements of the shipped vision pipeline on the public CEW dataset.

CEW = Closed Eyes in the Wild (Song et al., Pattern Recognition 2014): 1192 faces with both eyes closed and 1231
faces with eyes open (from LFW), 100x100 warped crops. This measures ONE component of Smart Rider: how well
vision.Vision (MediaPipe landmarks + six-point EAR + quality gates) tells closed from open eyes in still images.
It says nothing about alcohol or about impairment over time.

Run in the project venv:
    .venv\\Scripts\\python.exe scripts\\measure_cew.py --cew C:\\ceww\\d1\\dataset_B_FacialImages

Writes experiments/cew_ear/{metrics.json, per_image.csv, *.png}. The dataset itself is never copied into the repo.
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from vision import Vision, LEFT, RIGHT  # noqa: E402

OUT = ROOT / 'experiments' / 'cew_ear'
DEFAULT_THRESHOLD = 0.21
CANVAS = (640, 480)


def to_canvas(path):
    """100x100 face -> 480x480 on a 640x480 canvas (the size Smart Rider's camera path uses)."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return None
    img = cv2.resize(img, (480, 480), interpolation=cv2.INTER_CUBIC)
    canvas = np.empty((CANVAS[1], CANVAS[0], 3), np.uint8)
    canvas[:] = img.reshape(-1, 3).mean(axis=0).astype(np.uint8)
    canvas[:, 80:560] = img
    return canvas


class Runner:
    """One Vision instance fed independent stills (frame-to-frame motion check disabled per image)."""

    def __init__(self):
        self.v = Vision()
        self.t = 0.0

    def run(self, frame):
        self.v.previous = None
        self.t += 0.1
        start = time.perf_counter()
        o = self.v.process(frame.copy(), self.t)
        return o, (time.perf_counter() - start) * 1000

    def close(self):
        self.v.close()


def eye_boxes(locator, frame):
    """Landmark-based boxes (x0, y0, x1, y1) of each eye on a 640x480 frame, or None if no single face."""
    locator.t += 0.1
    ms = max(locator.v.last_ms + 1, int(locator.t * 1000))
    locator.v.last_ms = ms
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = locator.v.detector.detect_for_video(
        locator.v.mp.Image(image_format=locator.v.mp.ImageFormat.SRGB, data=rgb), ms)
    if len(res.face_landmarks) != 1:
        return None
    h, w = frame.shape[:2]
    pts = np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]])
    boxes = []
    for idx in (LEFT, RIGHT):
        e = pts[idx]
        boxes.append((int(e[:, 0].min()) - 14, int(e[:, 1].min()) - 16, int(e[:, 0].max()) + 14, int(e[:, 1].max()) + 16))
    return boxes


def landmark_ear(locator, frame):
    """Geometry-only EAR: same landmarks and eye_aspect_ratio() as Vision, first detected face, NO quality gates.

    Used to separate 'is EAR informative?' from 'did the sharpness/size gates let the image through?'
    (100x100 crops upscaled 4.8x are soft and trip the Laplacian-variance gate).
    """
    from core import eye_aspect_ratio
    locator.t += 0.1
    ms = max(locator.v.last_ms + 1, int(locator.t * 1000))
    locator.v.last_ms = ms
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = locator.v.detector.detect_for_video(
        locator.v.mp.Image(image_format=locator.v.mp.ImageFormat.SRGB, data=rgb), ms)
    if not res.face_landmarks:
        return None
    h, w = frame.shape[:2]
    pts = np.array([(p.x * w, p.y * h) for p in res.face_landmarks[0]])
    return float(np.mean([eye_aspect_ratio(pts[LEFT]), eye_aspect_ratio(pts[RIGHT])]))


def experiment_geometry(cew_dir, locator):
    rows = []
    for label, sub in ((1, 'ClosedFace'), (0, 'OpenFace')):
        for p in sorted((cew_dir / sub).glob('*.jpg')):
            frame = to_canvas(p)
            if frame is None:
                continue
            e = landmark_ear(locator, frame)
            rows.append((label, e))
    found = [(l, e) for l, e in rows if e is not None]
    ear = np.array([e for _, e in found])
    truth = np.array([l for l, _ in found])
    sweep = [confusion(ear, truth, t) for t in np.round(np.arange(0.10, 0.341, 0.01), 2)]
    youden = max(sweep, key=lambda c: c['recall'] + c['specificity'] - 1)
    return {'note': 'Geometry only: same landmarks/EAR as Vision, first detected face, no quality gates.',
            'images_total': len(rows), 'face_found': len(found),
            'closed_found': int(truth.sum()), 'open_found': int((1 - truth).sum()),
            'auc_ear_closed_vs_open': auc(-ear, truth), 'default_threshold_0.21': confusion(ear, truth, DEFAULT_THRESHOLD),
            'best_threshold_in_sample_youden': youden, 'threshold_sweep': sweep,
            'ear_mean_closed': float(ear[truth == 1].mean()), 'ear_mean_open': float(ear[truth == 0].mean())}


def auc(scores, labels):
    """Rank-based ROC AUC; labels 1 = closed. Higher score = more likely closed."""
    s = np.asarray(scores, float)
    y = np.asarray(labels, int)
    order = s.argsort(kind='mergesort')
    ranks = np.empty(len(s))
    sorted_s = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n1, n0 = int(y.sum()), int((1 - y).sum())
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def confusion(ear, closed_truth, thr):
    pred = np.asarray(ear) < thr
    t = np.asarray(closed_truth).astype(bool)
    tp, fp = int((pred & t).sum()), int((pred & ~t).sum())
    fn, tn = int((~pred & t).sum()), int((~pred & ~t).sum())
    n = tp + fp + fn + tn
    div = lambda a, b: a / b if b else None
    return {'threshold': float(thr), 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'accuracy': div(tp + tn, n), 'precision': div(tp, tp + fp), 'recall': div(tp, tp + fn),
            'specificity': div(tn, tn + fp), 'f1': div(2 * tp, 2 * tp + fp + fn)}


def experiment_cew(cew_dir, runner):
    closed = sorted(p for p in (cew_dir / 'ClosedFace').glob('*.jpg'))
    opened = sorted(p for p in (cew_dir / 'OpenFace').glob('*.jpg'))
    rows = []
    for label, files in ((1, closed), (0, opened)):
        for p in files:
            frame = to_canvas(p)
            if frame is None:
                continue
            o, ms = runner.run(frame)
            rows.append({'file': p.name, 'closed_truth': label, 'quality': o.quality,
                         'ear': round(o.ear, 5), 'roll': round(o.roll, 3), 'ms': round(ms, 2)})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'per_image.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    good = [r for r in rows if r['quality'] == 'Good']
    ear = np.array([r['ear'] for r in good])
    truth = np.array([r['closed_truth'] for r in good])
    by_class = {}
    for label, name in ((1, 'closed'), (0, 'open')):
        sub = [r for r in rows if r['closed_truth'] == label]
        reasons = {}
        for r in sub:
            reasons[r['quality']] = reasons.get(r['quality'], 0) + 1
        gear = np.array([r['ear'] for r in sub if r['quality'] == 'Good'])
        by_class[name] = {'images': len(sub), 'assessed_good': int(len(gear)),
                          'coverage': len(gear) / len(sub), 'quality_breakdown': reasons,
                          'ear_mean': float(gear.mean()), 'ear_std': float(gear.std()),
                          'ear_median': float(np.median(gear)),
                          'ear_p5_p95': [float(np.percentile(gear, 5)), float(np.percentile(gear, 95))]}
    sweep = [confusion(ear, truth, t) for t in np.round(np.arange(0.10, 0.341, 0.01), 2)]
    youden = max(sweep, key=lambda c: c['recall'] + c['specificity'] - 1)
    at_default = confusion(ear, truth, DEFAULT_THRESHOLD)
    # unassessed images count as errors for an "end-to-end" view of the default threshold
    total = len(rows)
    correct = at_default['tp'] + at_default['tn']
    ms = np.array([r['ms'] for r in rows])
    result = {
        'dataset': 'CEW (Closed Eyes in the Wild), 100x100 warped faces, public research dataset',
        'images_total': total, 'closed_images': len(closed), 'open_images': len(opened),
        'assessed_good': len(good), 'coverage': len(good) / total, 'by_class': by_class,
        'auc_ear_closed_vs_open': auc(-ear, truth), 'default_threshold_0.21': at_default,
        'end_to_end_accuracy_unassessed_counted_wrong': correct / total,
        'best_threshold_in_sample_youden': youden, 'threshold_sweep': sweep,
        'latency_ms_vision_process_640x480': {'mean': float(ms.mean()), 'p50': float(np.percentile(ms, 50)),
                                              'p95': float(np.percentile(ms, 95)), 'max': float(ms.max()),
                                              'n': int(len(ms))},
        'caveats': ['Closed-eye images come from the Internet, open-eye images from LFW: the two classes differ in '
                    'source and image conditions, so separation may be easier than within-source separation.',
                    'Still images only: blink dynamics, persistence rules and head motion are not exercised.',
                    'Best threshold is chosen on the same images (in-sample) and is reported for context only.']}
    return rows, result


def experiment_robustness(rows, cew_dir, runner, locator, n=300, seed=2026):
    rng = np.random.default_rng(seed)
    pool = [r for r in rows if r['closed_truth'] == 0 and r['quality'] == 'Good']
    picks = [pool[i] for i in rng.choice(len(pool), size=min(n, len(pool)), replace=False)]
    frames, boxes = [], []
    for r in picks:
        fr = to_canvas(cew_dir / 'OpenFace' / r['file'])
        b = eye_boxes(locator, fr)
        if b is not None:
            frames.append(fr)
            boxes.append(b)

    def rect(img, box, value=0, alpha=1.0):
        x0, y0, x1, y1 = [max(0, v) for v in box]
        x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
        region = img[y0:y1, x0:x1].astype(np.float32)
        img[y0:y1, x0:x1] = (region * (1 - alpha) + value * alpha).astype(np.uint8)

    def both(b):
        return (min(b[0][0], b[1][0]), min(b[0][1], b[1][1]), max(b[0][2], b[1][2]), max(b[0][3], b[1][3]))

    def p_dark(k):
        return lambda im, b: np.clip(im.astype(np.float32) * k, 0, 255).astype(np.uint8)

    def p_bright(k):
        return lambda im, b: np.clip(im.astype(np.float32) * k + 25, 0, 255).astype(np.uint8)

    def p_blur(s):
        return lambda im, b: cv2.GaussianBlur(im, (0, 0), s)

    def p_noise(s):
        def f(im, b):
            return np.clip(im.astype(np.float32) + rng.normal(0, s, im.shape), 0, 255).astype(np.uint8)
        return f

    def p_dark_glasses(im, b):
        out = im.copy()
        rect(out, both(b), 0, 1.0)
        return out

    def p_tinted(im, b):
        out = im.copy()
        rect(out, both(b), 0, 0.55)
        return out

    def p_one_eye(im, b):
        out = im.copy()
        rect(out, b[0], 0, 1.0)
        return out

    def p_mask(im, b):
        out = im.copy()
        out[int(0.66 * out.shape[0]):, :] = 90
        return out

    perturbations = [
        ('baseline (unmodified)', lambda im, b: im),
        ('brightness x0.50', p_dark(0.50)), ('brightness x0.25', p_dark(0.25)), ('brightness x0.12', p_dark(0.12)),
        ('over-exposed (x1.8 + 25)', p_bright(1.8)),
        ('Gaussian blur sigma 2 px', p_blur(2)), ('Gaussian blur sigma 5 px', p_blur(5)),
        ('Gaussian noise sd 20', p_noise(20)),
        ('opaque sunglasses over both eyes', p_dark_glasses), ('tinted lenses (55% dark)', p_tinted),
        ('one eye covered', p_one_eye), ('lower face masked', p_mask),
    ]
    results = []
    for name, fn in perturbations:
        qual, ears = {}, []
        for im, b in zip(frames, boxes):
            o, _ = runner.run(fn(im.copy(), b))
            qual[o.quality] = qual.get(o.quality, 0) + 1
            if o.quality == 'Good':
                ears.append(o.ear)
        good = len(ears)
        ears = np.array(ears)
        results.append({'condition': name, 'n': len(frames), 'good': good, 'good_rate': good / len(frames),
                        'unable_to_assess_rate': 1 - good / len(frames), 'quality_breakdown': qual,
                        'false_closure_rate_among_good': float((ears < DEFAULT_THRESHOLD).mean()) if good else None,
                        'mean_ear_good': float(ears.mean()) if good else None})
    base = results[0]['mean_ear_good']
    for r in results:
        r['mean_ear_shift_vs_baseline'] = None if r['mean_ear_good'] is None else r['mean_ear_good'] - base
    return {'source': 'open-eye CEW faces that were Good at baseline, seeded sample', 'n_images': len(frames),
            'conditions': results}


def charts(res_cew, res_rob, rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    good = [r for r in rows if r['quality'] == 'Good']
    ce = np.array([r['ear'] for r in good if r['closed_truth'] == 1])
    oe = np.array([r['ear'] for r in good if r['closed_truth'] == 0])
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    bins = np.linspace(0, 0.5, 51)
    ax.hist(oe, bins=bins, alpha=.75, label=f'Open eyes (n={len(oe)})', color='#2a9d8f')
    ax.hist(ce, bins=bins, alpha=.75, label=f'Closed eyes (n={len(ce)})', color='#e76f51')
    ax.axvline(DEFAULT_THRESHOLD, color='k', ls='--', lw=1.2, label='Default threshold 0.21')
    ax.set(xlabel='Eye aspect ratio (mean of both eyes)', ylabel='Images', title='EAR on CEW faces, assessed images only')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / 'ear_histogram.png'); plt.close(fig)

    sweep = res_cew['threshold_sweep']
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    x = [c['threshold'] for c in sweep]
    ax.plot(x, [c['accuracy'] for c in sweep], label='Accuracy', color='#264653')
    ax.plot(x, [c['recall'] for c in sweep], label='Closed-eye recall', color='#e76f51')
    ax.plot(x, [c['specificity'] for c in sweep], label='Open-eye specificity', color='#2a9d8f')
    ax.axvline(DEFAULT_THRESHOLD, color='k', ls='--', lw=1.0)
    ax.set(xlabel='EAR threshold', ylabel='Rate', ylim=(0, 1.02), title='Threshold sweep on CEW (assessed images)')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / 'threshold_sweep.png'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    thr = np.linspace(0.0, 0.6, 300)
    tpr = [(ce < t).mean() for t in thr]
    fpr = [(oe < t).mean() for t in thr]
    ax.plot(fpr, tpr, color='#264653')
    ax.plot([0, 1], [0, 1], color='grey', ls=':')
    ax.set(xlabel='False closed rate (open eyes below threshold)', ylabel='Closed-eye recall',
           title=f"ROC of EAR on CEW, AUC = {res_cew['auc_ear_closed_vs_open']:.3f}")
    fig.tight_layout(); fig.savefig(OUT / 'roc.png'); plt.close(fig)

    conds = res_rob['conditions']
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
    names = [c['condition'] for c in conds]
    ypos = np.arange(len(names))
    ax.barh(ypos, [c['good_rate'] * 100 for c in conds], color='#2a9d8f', label='Assessed (Good)')
    ax.barh(ypos, [c['unable_to_assess_rate'] * 100 for c in conds],
            left=[c['good_rate'] * 100 for c in conds], color='#adb5bd', label='Unable to assess')
    ax.set_yticks(ypos); ax.set_yticklabels(names, fontsize=7); ax.invert_yaxis()
    ax.set(xlabel='% of images', title='Quality gating under degraded conditions (open-eye faces)')
    ax.legend(frameon=False, fontsize=8, loc='lower right')
    fig.tight_layout(); fig.savefig(OUT / 'robustness.png'); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cew', required=True, help='folder containing ClosedFace/ and OpenFace/ (100x100 CEW faces)')
    ap.add_argument('--skip-robustness', action='store_true')
    ap.add_argument('--geometry-only', action='store_true',
                    help='add the gate-free geometry experiment to an existing metrics.json')
    args = ap.parse_args()
    cew_dir = Path(args.cew)
    runner, locator = Runner(), Runner()
    if args.geometry_only:
        try:
            path = OUT / 'metrics.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            data['cew_geometry_only'] = experiment_geometry(cew_dir, locator)
            path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            print(json.dumps({k: v for k, v in data['cew_geometry_only'].items() if k != 'threshold_sweep'}, indent=1))
        finally:
            runner.close()
            locator.close()
        return
    try:
        rows, res_cew = experiment_cew(cew_dir, runner)
        print(json.dumps({k: v for k, v in res_cew.items() if k not in ('threshold_sweep',)}, indent=1)[:3000])
        res_rob = None
        if not args.skip_robustness:
            res_rob = experiment_robustness(rows, cew_dir, runner, locator)
            print(json.dumps(res_rob, indent=1)[:4000])
        res_geo = experiment_geometry(cew_dir, locator)
        (OUT / 'metrics.json').write_text(
            json.dumps({'cew': res_cew, 'cew_geometry_only': res_geo, 'robustness': res_rob}, indent=2),
            encoding='utf-8')
        if res_rob:
            charts(res_cew, res_rob, rows)
    finally:
        runner.close()
        locator.close()


if __name__ == '__main__':
    main()
