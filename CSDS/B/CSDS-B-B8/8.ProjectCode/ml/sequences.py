"""Seeded keypoint-sequence builder used by train.py and eval.py.

The public datasets are still images, so motion is added here from real extracted poses:
each sequence starts from a real YOLO11n-pose skeleton (normal, dimmed or dimmed+enhanced image) and
applies a simple kinematic model (sway, gait, bending, falling) plus jitter, keypoint dropout and
occlusion. Recorded own clips (data/own_clips/<label>/*.json) are real sequences and are used as-is.
Everything is deterministic for a given seed.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.features import VIS, WINDOW, body_geometry  # noqa: E402

POSES = ROOT / "data" / "keypoints" / "poses.npz"
CLIPS = ROOT / "data" / "own_clips"
FLIP = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]
UPPER = list(range(0, 11))
LOWER = [13, 14, 15, 16]


def load_poses():
    d = np.load(POSES)
    return {k: d[k] for k in d.files}


def pose_pool(d, label, split, variants=None, min_vis=6, sources=None):
    m = (d["label"] == label) & (d["split"] == split)
    if variants is not None:
        m &= np.isin(d["variant"], variants)
    if sources is not None:
        m &= np.isin(d["source"], sources)
    ks = [k for k in d["kpts"][m] if (k[:, 2] > VIS).sum() >= min_vis and body_geometry(k) is not None]
    return ks


def canon(k):
    """Centre on the body and scale to unit size."""
    c, s, *_ = body_geometry(k)
    out = k.copy()
    out[:, :2] = (k[:, :2] - c) / s
    return out


def flip(k):
    out = k[FLIP].copy()
    out[:, 0] = -out[:, 0]
    return out


class Builder:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
        self.force_block = None  # e.g. LOWER to test occlusion of the legs

    # --- helpers -------------------------------------------------------------------------------------
    def place(self, kc, size, pos):
        out = kc.copy()
        out[:, :2] = kc[:, :2] * size + pos
        return out

    def base(self, pool):
        k = canon(pool[self.rng.integers(len(pool))])
        return flip(k) if self.rng.random() < 0.5 else k

    def times(self, n, fps=None):
        fps = fps or self.rng.uniform(7, 14)
        return np.cumsum(np.r_[0, self.rng.uniform(0.8, 1.2, n - 1) / fps])

    def noisy(self, frames, size, occl=True):
        """Jitter, keypoint dropout and occlusion (F4 robustness)."""
        r = self.rng
        drop_p = r.uniform(0, 0.12)
        block = None
        if occl:
            u = r.random()
            block = LOWER if u < 0.15 else ([7, 9] if u < 0.22 else ([8, 10] if u < 0.29 else None))
        if self.force_block is not None:
            block = self.force_block
        out = []
        for k in frames:
            k = k.copy()
            k[:, :2] += r.normal(0, 0.012 * size, (17, 2))
            k[r.random(17) < drop_p, 2] = 0.0
            if block:
                k[block, 2] = 0.0
            out.append(k)
        return out

    def scene(self):
        size = self.rng.uniform(120, 380)
        pos = np.array([self.rng.uniform(150, 490), self.rng.uniform(150, 330)])
        return size, pos

    # --- activities ----------------------------------------------------------------------------------
    def still(self, pool, n=WINDOW, amp=0.004):
        kc = self.base(pool)
        size, pos = self.scene()
        drift = np.cumsum(self.rng.normal(0, amp * size, (n, 2)), 0)
        frames = [self.place(kc, size, pos + drift[i]) for i in range(n)]
        return self.times(n), self.noisy(frames, size)

    def walking(self, pool, n=WINDOW):
        kc = self.base(pool)
        size, pos = self.scene()
        t = self.times(n)
        speed = self.rng.uniform(0.35, 1.3) * size
        if self.rng.random() < 0.7:   # across the view
            ang = self.rng.uniform(-0.4, 0.4) + (np.pi if self.rng.random() < 0.5 else 0)
            v = speed * np.array([np.cos(ang), np.sin(ang)])
            grow = 0.0
        else:                          # towards / away from the camera
            v = speed * np.array([self.rng.uniform(-0.2, 0.2), self.rng.choice([-0.35, 0.35])])
            grow = np.sign(v[1]) * self.rng.uniform(0.05, 0.2)
        f = self.rng.uniform(0.7, 1.2)
        a = self.rng.uniform(0.08, 0.16)
        ph0 = self.rng.uniform(0, 2 * np.pi)
        frames = []
        for i, ti in enumerate(t):
            ph = 2 * np.pi * f * ti + ph0
            k = kc.copy()
            sgn = 1 if grow == 0 else 0
            for idx, side in ((15, 1), (13, 0.5), (16, -1), (14, -0.5)):
                k[idx, 0] += sgn * a * side * np.sin(ph)
                k[idx, 1] -= 0.03 * max(0, side * np.sin(ph))
            for idx, side in ((9, -0.5), (10, 0.5)):
                k[idx, 0] += a * side * np.sin(ph)
            k[:, 1] += 0.01 * np.sin(2 * ph)
            s = size * (1 + grow * ti)
            frames.append(self.place(k, s, pos + v * ti))
        return t, self.noisy(frames, size)

    def drinking(self, pool, n=WINDOW):
        kc = self.base(pool)
        size, pos = self.scene()
        t = self.times(n)
        f = self.rng.uniform(0.2, 0.6)
        frames = []
        for ti in t:
            k = kc.copy()
            w = 9 if k[9, 1] < k[10, 1] else 10  # hand nearest the face
            k[w, 1] += 0.04 * np.sin(2 * np.pi * f * ti)
            k[w - 2, 1] += 0.02 * np.sin(2 * np.pi * f * ti)
            frames.append(self.place(k, size, pos + self.rng.normal(0, 0.003 * size, 2)))
        return t, self.noisy(frames, size)

    def bend(self, kc, b, side, frontal):
        """Pose bent forward by fraction b (0 upright .. 1 fully bent, hand at the floor)."""
        k = kc.copy()
        hips = [i for i in (11, 12) if k[i, 2] > VIS]
        hip = k[hips, :2].mean(0) if hips else k[:, :2].mean(0)
        ank = [i for i in (15, 16) if k[i, 2] > VIS]
        floor = k[ank, 1].max() if ank else hip[1] + 0.5
        if frontal:
            k[UPPER, 1] = hip[1] + (k[UPPER, 1] - hip[1]) * (1 - 0.65 * b)
            k[UPPER, 1] += 0.15 * b
            for w in (9, 10):
                k[w, 1] = (1 - b) * k[w, 1] + b * (floor - 0.05)
                k[w - 2, 1] = (k[w - 4, 1] + k[w, 1]) / 2
        else:
            a = side * np.radians(self.rng.uniform(55, 90)) * b
            ca, sa = np.cos(a), np.sin(a)
            for i in UPPER:
                x, y = k[i, :2] - hip
                k[i, :2] = hip + [x * ca - y * sa, x * sa + y * ca]
            for w in (9, 10):
                target = np.array([k[w - 4, 0] + side * 0.05, floor - 0.05])
                k[w, :2] = (1 - b) * k[w, :2] + b * (k[w - 4, :2] + (target - k[w - 4, :2]) * 0.95)
                k[w - 2, :2] = (k[w - 4, :2] + k[w, :2]) / 2
        for kn in (13, 14):
            k[kn, 0] += side * 0.06 * b
        k[[11, 12], 1] += 0.08 * b
        return k

    def picking_up(self, pool, n=WINDOW):
        kc = self.base(pool)
        size, pos = self.scene()
        t = self.times(n)
        side = self.rng.choice([-1, 1])
        frontal = self.rng.random() < 0.35
        dur = t[-1]
        start = self.rng.uniform(-0.3, 0.3) * dur
        frames = []
        for ti in t:
            u = (ti - start) / dur
            b = np.clip(np.sin(np.pi * np.clip(u * 1.1, 0, 1)) * 1.2, 0, 1)
            frames.append(self.place(self.bend(kc, b, side, frontal), size, pos))
        return t, self.noisy(frames, size)

    # --- transitions for fall evaluation --------------------------------------------------------------
    def transition(self, k_from, k_to, size, pos, dur, n_before, n_after, fps, ease="gravity",
                   floor_to=True, target_scale=1.0):
        """Standing pose -> target pose over `dur` seconds. Returns (t, frames, t_end_of_transition)."""
        a = k_from.copy()
        b = k_to.copy()
        if floor_to:  # put the target pose on the floor under the standing feet
            vis_a = a[:, 2] > VIS
            vis_b = b[:, 2] > VIS
            floor = a[vis_a, 1].max() if vis_a.any() else 0.5
            ext = b[vis_b, :2]
            L = max(np.ptp(ext[:, 0]), np.ptp(ext[:, 1]), 1e-3)
            b[:, :2] = b[:, :2] / L * target_scale
            b[:, 1] += floor - b[vis_b, 1].max() - 0.02
            b[:, 0] += self.rng.uniform(-0.2, 0.2)
        self.last_target = b.copy()
        dt = 1.0 / fps
        n_tr = max(2, int(round(dur * fps)))
        frames, times = [], []
        tt = 0.0
        for _ in range(n_before):
            frames.append(self.place(a, size, pos))
            times.append(tt)
            tt += dt
        for i in range(1, n_tr + 1):
            u = i / n_tr
            u = u * u if ease == "gravity" else 0.5 - 0.5 * np.cos(np.pi * u)
            k = a.copy()
            k[:, :2] = (1 - u) * a[:, :2] + u * b[:, :2]
            k[:, 2] = np.minimum(a[:, 2], b[:, 2]) if i < n_tr else b[:, 2]
            frames.append(self.place(k, size, pos))
            times.append(tt)
            tt += dt
        t_end = times[-1]
        for _ in range(n_after):
            frames.append(self.place(b, size, pos + self.rng.normal(0, 0.002 * size, 2)))
            times.append(tt)
            tt += dt
        return np.array(times), self.noisy(frames, size, occl=False), t_end


def own_clip_windows(split_seed=42, stride=5):
    """Sliding windows from recorded clips: list of (label, split, (t, frames))."""
    out = []
    rng = np.random.default_rng(split_seed)
    for f in sorted(CLIPS.glob("*/*.json")):
        clip = json.loads(f.read_text())
        label = clip["label"]
        ts = np.array([fr["t"] for fr in clip["frames"]])
        ks = [np.array(fr["kpts"], dtype=np.float32) if fr["kpts"] else None for fr in clip["frames"]]
        split = "test" if rng.random() < 0.25 else "train"
        for s in range(0, max(1, len(ks) - WINDOW + 1), stride):
            out.append((label, split, (ts[s:s + WINDOW], ks[s:s + WINDOW])))
    return out
