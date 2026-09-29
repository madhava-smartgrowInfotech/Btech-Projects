"""Keypoint features shared by training (ml/) and the live pipeline.

Keypoints are COCO-17 (x, y, confidence) in pixels, as produced by YOLO11n-pose.
A window is a list of (timestamp_seconds, keypoints[17,3] or None).
"""
import numpy as np

NOSE, L_EYE, R_EYE, L_EAR, R_EAR = 0, 1, 2, 3, 4
L_SH, R_SH, L_EL, R_EL, L_WR, R_WR = 5, 6, 7, 8, 9, 10
L_HIP, R_HIP, L_KN, R_KN, L_AN, R_AN = 11, 12, 13, 14, 15, 16

SKELETON = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]

VIS = 0.3          # keypoint confidence treated as visible
WINDOW = 20        # frames per classification window (~2 s at 10 fps)
FRAME_DIM = 57


def _mid(k, a, b):
    va, vb = k[a, 2] > VIS, k[b, 2] > VIS
    if va and vb:
        return (k[a, :2] + k[b, :2]) / 2
    if va:
        return k[a, :2]
    if vb:
        return k[b, :2]
    return None


def body_geometry(k):
    """Centre (px), scale (px), torso angle from vertical (deg), height ratio of the keypoint box."""
    vis = k[:, 2] > VIS
    if vis.sum() < 3:
        return None
    pts = k[vis, :2]
    core = [i for i in (L_SH, R_SH, L_HIP, R_HIP) if k[i, 2] > VIS]
    centre = k[core, :2].mean(0) if core else pts.mean(0)
    w, h = np.ptp(pts[:, 0]), np.ptp(pts[:, 1])
    scale = max(w, h, 1.0)
    sh, hp = _mid(k, L_SH, R_SH), _mid(k, L_HIP, R_HIP)
    if sh is not None and hp is not None and np.linalg.norm(sh - hp) > 1:
        v = sh - hp
        angle = float(np.degrees(np.arctan2(abs(v[0]), -v[1])))  # 0 = upright, 90 = horizontal
        angle = min(max(angle, 0.0), 180.0)
    else:
        angle = 90.0 if w > h else 0.0
    return centre, scale, angle, h / (w + h + 1e-6), w, h


def frame_features(k):
    """57-dim per-frame posture vector; zeros when no usable person."""
    g = body_geometry(k) if k is not None else None
    if g is None:
        return np.zeros(FRAME_DIM, dtype=np.float32), None
    centre, scale, angle, aspect, _, _ = g
    vis = (k[:, 2] > VIS).astype(np.float32)
    xy = (k[:, :2] - centre) / scale * vis[:, None]

    sh, hp = _mid(k, L_SH, R_SH), _mid(k, L_HIP, R_HIP)
    torso = np.linalg.norm(sh - hp) if sh is not None and hp is not None else scale * 0.35
    torso = max(torso, 1.0)
    head = k[NOSE, :2] if k[NOSE, 2] > VIS else _mid(k, L_EAR, R_EAR)
    wrist_head = 3.0
    if head is not None:
        d = [np.linalg.norm(k[w, :2] - head) / torso for w in (L_WR, R_WR) if k[w, 2] > VIS]
        if d:
            wrist_head = min(min(d), 3.0)
    knee_ang = []
    for h_, kn, an in ((L_HIP, L_KN, L_AN), (R_HIP, R_KN, R_AN)):
        if k[h_, 2] > VIS and k[kn, 2] > VIS and k[an, 2] > VIS:
            a, b = k[h_, :2] - k[kn, :2], k[an, :2] - k[kn, :2]
            c = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-6)
            knee_ang.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
    knee = (np.mean(knee_ang) if knee_ang else 150.0) / 180.0
    kn = _mid(k, L_KN, R_KN)
    hip_knee_dy = ((kn[1] - hp[1]) / torso) if kn is not None and hp is not None else 1.0
    wr = _mid(k, L_WR, R_WR)
    wrist_low = ((wr[1] - hp[1]) / torso) if wr is not None and hp is not None else 0.0
    extra = [angle / 90.0, aspect, wrist_head, knee, np.clip(hip_knee_dy, -3, 3), np.clip(wrist_low, -3, 3)]
    f = np.concatenate([xy.ravel(), vis, np.array(extra, dtype=np.float32)]).astype(np.float32)
    return f, (centre, scale, angle)


def window_features(window):
    """Feature vector for a window of (t, keypoints) - posture statistics plus motion."""
    feats, geos, ts, kps = [], [], [], []
    for t, k in window:
        f, g = frame_features(k)
        if g is None:
            continue
        feats.append(f)
        geos.append(g)
        ts.append(t)
        kps.append(k)
    n_total = max(len(window), 1)
    if len(feats) < 3:
        return None
    F = np.stack(feats)
    ts = np.array(ts)
    centres = np.stack([g[0] for g in geos])
    scale = float(np.median([g[1] for g in geos]))
    angles = np.array([g[2] for g in geos])
    dt = np.clip(np.diff(ts), 1e-3, None)

    vel = np.diff(centres, axis=0) / scale / dt[:, None]
    speed = np.linalg.norm(vel, axis=1)

    def rel_speed(idxs):
        out = []
        for a in range(1, len(kps)):
            s = []
            for i in idxs:
                if kps[a][i, 2] > VIS and kps[a - 1][i, 2] > VIS:
                    d = (kps[a][i, :2] - centres[a]) - (kps[a - 1][i, :2] - centres[a - 1])
                    s.append(np.linalg.norm(d) / scale / dt[a - 1])
            out.append(np.mean(s) if s else 0.0)
        return float(np.mean(out)) if out else 0.0

    motion = [
        speed.mean(), speed.max(), np.abs(vel[:, 0]).mean(), np.abs(vel[:, 1]).mean(),
        (centres[-1, 1] - centres[0, 1]) / scale,
        rel_speed([L_WR, R_WR]), rel_speed([L_AN, R_AN, L_KN, R_KN]),
        (angles.max() - angles.min()) / 90.0, len(feats) / n_total,
    ]
    return np.concatenate([F.mean(0), F.std(0), np.array(motion, dtype=np.float32)]).astype(np.float32)
