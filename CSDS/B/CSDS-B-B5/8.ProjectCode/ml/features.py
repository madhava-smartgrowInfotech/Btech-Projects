"""Landmark -> feature conversion shared by training, evaluation and the live backend.

Words: every frame keeps 7 upper-body pose points + 21 left-hand + 21 right-hand points
(x, y only), in body coordinates (origin = shoulder centre, unit = shoulder width).
A sign is a sequence of such frames, trimmed to the hands-visible part and resampled to T frames.

Letters: one frame, up to two hands, described by their shape (relative to the wrist) and
the offset between the two hands.
"""
import numpy as np

T = 32  # frames per word sample
POSE_IDX = [0, 11, 12, 13, 14, 15, 16]  # nose, shoulders, elbows, wrists
POSE_MIRROR = [0, 2, 1, 4, 3, 6, 5]  # left/right swap inside POSE_IDX
N_POINTS = len(POSE_IDX) + 42  # 49
WORD_DIM = 14 + 42 + 42 + 42 + 42 + 2  # 184
LETTER_DIM = 42 + 42 + 3  # 87


# ---------------------------------------------------------------- words
def body_frame(pose, left, right, aspect):
    """pose (33,2+) / left (21,2+) / right (21,2+) in normalised image coords, NaN or None when missing.
    Returns (49, 2) float32 in body coordinates (NaN where missing)."""
    pts = np.full((N_POINTS, 2), np.nan, np.float32)
    if pose is not None:
        pts[: len(POSE_IDX)] = np.asarray(pose, np.float32)[POSE_IDX, :2]
    if left is not None:
        pts[7:28] = np.asarray(left, np.float32)[:, :2]
    if right is not None:
        pts[28:49] = np.asarray(right, np.float32)[:, :2]
    pts[:, 0] *= aspect  # make x and y the same unit
    ls, rs = pts[1], pts[2]
    if np.isfinite(ls).all() and np.isfinite(rs).all() and np.linalg.norm(ls - rs) > 1e-3:
        centre, scale = (ls + rs) / 2, np.linalg.norm(ls - rs)
    else:  # no body found: assume a centred signer
        centre, scale = np.array([0.5 * aspect, 0.55], np.float32), 0.35
    return (pts - centre) / scale


def has_hand(frame):
    return np.isfinite(frame[7:49, 0]).any()


def resample_sequence(frames, t=T, margin=2):
    """frames (n, 49, 2) -> (t, 49, 2): keep the hands-visible span, pick t evenly spaced frames."""
    frames = np.asarray(frames, np.float32)
    active = np.where([has_hand(f) for f in frames])[0]
    if len(active):
        frames = frames[max(active[0] - margin, 0): active[-1] + margin + 1]
    idx = np.linspace(0, len(frames) - 1, t).round().astype(int)
    return frames[idx]


def _hand_local(h):
    """(21,2) body coords -> shape relative to wrist, scaled by wrist->middle-knuckle length."""
    size = np.linalg.norm(h[9] - h[0]) + 1e-6
    return (h - h[0]) / size


def word_features(seq, mirror=False):
    """seq (T, 49, 2) body coords -> (T, 184) float32 model input."""
    seq = np.array(seq, np.float32)
    if mirror:
        seq[..., 0] *= -1
        pose = seq[:, :7][:, POSE_MIRROR]
        seq = np.concatenate([pose, seq[:, 28:49], seq[:, 7:28]], axis=1)
    out = np.zeros((len(seq), WORD_DIM), np.float32)
    for i, f in enumerate(seq):
        pose, lh, rh = f[:7], f[7:28], f[28:49]
        out[i, :14] = np.nan_to_num(pose).ravel()
        for k, h in enumerate((lh, rh)):
            if np.isfinite(h).all():
                out[i, 14 + 42 * k: 56 + 42 * k] = h.ravel()
                out[i, 98 + 42 * k: 140 + 42 * k] = _hand_local(h).ravel()
                out[i, 182 + k] = 1.0
    return out


# ---------------------------------------------------------------- letters
def letter_features(hands, mirror=False):
    """hands: list of (21,2) arrays in aspect-corrected image coords (x already * aspect).
    Returns (87,) float32. Hands are ordered left-to-right in the image."""
    hands = [np.array(h, np.float32)[:, :2] for h in hands][:2]
    if mirror:
        for h in hands:
            h[:, 0] *= -1
    hands.sort(key=lambda h: h[0, 0])
    out = np.zeros(LETTER_DIM, np.float32)
    if not hands:
        return out
    out[:42] = _hand_local(hands[0]).ravel()
    if len(hands) > 1:
        out[42:84] = _hand_local(hands[1]).ravel()
        size = np.linalg.norm(hands[0][9] - hands[0][0]) + 1e-6
        out[84:86] = (hands[1][0] - hands[0][0]) / size
        out[86] = 1.0
    return out
