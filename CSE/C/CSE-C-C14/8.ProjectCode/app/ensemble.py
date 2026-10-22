"""Logit-space weighted fusion with lightweight disagreement gating.

Gate 1 (high-resolution outlier suppression): if Route B strongly disagrees
with at least three other branch directions, exclude Route B and renormalize.
Gate 2 (independent-route consensus correction): if B and C strongly agree on
a class while the fused prediction strongly points the other way, nudge the
fused logits toward the B+C consensus by a small configurable correction.

All logic is deterministic and operates on raw logits (never on probabilities).
"""
import math

from . import config


def normalize_weights(weights):
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Ensemble weights must sum to a positive value.")
    return {k: v / total for k, v in weights.items()}


def fuse_logits(logits, weights):
    """Weighted sum of per-branch [real_logit, fake_logit] pairs.

    logits: dict branch -> [l_real, l_fake]
    weights: dict branch -> float (need not be normalized)
    """
    w = normalize_weights(weights)
    fused = [0.0, 0.0]
    for branch, pair in logits.items():
        weight = w.get(branch, 0.0)
        fused[0] += weight * pair[0]
        fused[1] += weight * pair[1]
    return fused


def softmax(logits):
    m = max(logits)
    exps = [math.exp(v - m) for v in logits]
    s = sum(exps)
    return [e / s for e in exps]


def branch_direction(pair):
    """Predicted class direction of a logit pair: 0 (REAL) or 1 (AI_GENERATED)."""
    return 0 if pair[0] >= pair[1] else 1


def apply_gate1(logits, weights, tau_b=None):
    """Possibly exclude Route B as an outlier.

    Returns (active_branches, excluded_branch_or_None, reason).
    """
    tau = config.GATE_TAU_B if tau_b is None else tau_b
    if "b" not in logits:
        return dict(weights), None, "route B unavailable"
    b_dir = branch_direction(logits["b"])
    b_margin = abs(logits["b"][1] - logits["b"][0])
    others = [k for k in logits.keys() if k != "b"]
    disagreeing = sum(1 for k in others if branch_direction(logits[k]) != b_dir)
    if b_margin >= tau and disagreeing >= 3 and len(others) >= 3:
        # Note: with 4 branches, disagreeing>=3 means every other branch
        # points the other way while B is very confident.
        remaining = {k: v for k, v in weights.items() if k != "b" and k in logits}
        return remaining, "b", (
            f"Route B excluded: strong disagreement (margin {b_margin:.2f} >= {tau}) "
            f"with {disagreeing} other branches."
        )
    return {k: v for k, v in weights.items() if k in logits}, None, "all branches active"


def apply_gate2(fused, logits, tau_b=None, tau_c=None, correction=None):
    """Possibly nudge fused logits toward a B+C consensus.

    Returns (adjusted_fused, applied_bool, reason).
    """
    tb = config.GATE_TAU_B if tau_b is None else tau_b
    tc = config.GATE_TAU_C if tau_c is None else tau_c
    corr = config.GATE_CORRECTION if correction is None else correction
    if "b" not in logits or "c" not in logits:
        return list(fused), False, "B+C consensus unavailable"
    b_dir = branch_direction(logits["b"])
    c_dir = branch_direction(logits["c"])
    b_margin = abs(logits["b"][1] - logits["b"][0])
    c_margin = abs(logits["c"][1] - logits["c"][0])
    fused_dir = branch_direction(fused)
    fused_margin = abs(fused[1] - fused[0])
    if b_dir == c_dir and b_dir != fused_dir and b_margin >= tb and c_margin >= tc:
        adjusted = list(fused)
        # Nudge both logits: strengthen consensus class, weaken the other.
        if b_dir == 1:
            adjusted[1] += corr
            adjusted[0] -= corr * 0.5
        else:
            adjusted[0] += corr
            adjusted[1] -= corr * 0.5
        return adjusted, True, (
            f"B+C consensus correction applied toward {config.CLASS_NAMES[b_dir]} "
            f"(B margin {b_margin:.2f}, C margin {c_margin:.2f}, fused margin {fused_margin:.2f})."
        )
    return list(fused), False, "no consensus correction"


def ensemble_predict(logits, weights=None, tau_b=None, tau_c=None, correction=None):
    """Full fusion pipeline. Returns a dict with fused logits, probs, gates."""
    w = dict(config.ENSEMBLE_WEIGHTS) if weights is None else dict(weights)
    active_w, excluded, gate1_reason = apply_gate1(logits, w, tau_b=tau_b)
    fused = fuse_logits(logits, active_w)
    fused_adj, gate2_applied, gate2_reason = apply_gate2(
        fused, logits, tau_b=tau_b, tau_c=tau_c, correction=correction
    )
    probs = softmax(fused_adj)
    pred = 0 if fused_adj[0] >= fused_adj[1] else 1
    branch_dirs = {k: branch_direction(v) for k, v in logits.items()}
    agreement = sum(1 for d in branch_dirs.values() if d == pred)
    return {
        "fused_logits": fused_adj,
        "probabilities": probs,
        "predicted_class": pred,
        "predicted_label": config.CLASS_NAMES[pred],
        "excluded_branch": excluded,
        "gate1_reason": gate1_reason,
        "gate2_applied": gate2_applied,
        "gate2_reason": gate2_reason,
        "branch_directions": branch_dirs,
        "agreement_count": agreement,
        "active_weights": normalize_weights(active_w),
    }
