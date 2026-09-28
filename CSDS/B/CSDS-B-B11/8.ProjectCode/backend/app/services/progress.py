"""Adherence scoring and the weekly adaptive target recalculation."""
from datetime import date, timedelta

import numpy as np

from .targets import GOAL_RATE_KG_WEEK

KCAL_PER_KG = 7700
MAX_STEP = 250      # kcal/day change allowed per recalculation
MAX_TOTAL = 500     # total adaptive correction allowed
DAMPING = 0.5       # apply half of the measured gap per week, so noisy weigh-ins are not chased


def day_score(kcal: float, protein: float, target_kcal: float, target_protein: float) -> float:
    """0-100: calories within 5 % score full marks, falling linearly to 0 at 55 % off; protein adds 30 %."""
    err = abs(kcal - target_kcal) / max(target_kcal, 1)
    kcal_score = max(0.0, 1 - max(0.0, err - 0.05) * 2)
    protein_score = min(1.0, protein / max(target_protein, 1))
    return round(100 * (0.7 * kcal_score + 0.3 * protein_score), 1)


def adherence(daily: dict, target_for, protein_target: float, end: date, window: int = 7):
    """daily: {date: {"kcal":..,"protein":..}}. Unlogged days score 0."""
    scores, logged = [], 0
    for i in range(window):
        d = end - timedelta(days=i)
        if d in daily:
            logged += 1
            scores.append(day_score(daily[d]["kcal"], daily[d]["protein"], target_for(d), protein_target))
        else:
            scores.append(0.0)
    return {"score": round(float(np.mean(scores)), 1), "days_logged": logged, "window_days": window}


def weight_trend(points):
    """points: list of (date, kg). Returns slope in kg/week by least squares, or None."""
    if len(points) < 2:
        return None
    d0 = points[0][0]
    x = np.array([(d - d0).days for d, _ in points], dtype=float)
    y = np.array([w for _, w in points], dtype=float)
    if x.max() - x.min() < 1:
        return None
    slope = np.polyfit(x, y, 1)[0]
    return float(slope * 7)


def recalculation(points, goal: str, prev_adjust: float):
    """Given >= 3 weights spanning >= 6 days (ideally the last 14 days), return the new adaptive adjustment and an explanation."""
    points = sorted(points)
    if len(points) < 3 or (points[-1][0] - points[0][0]).days < 6:
        return None
    observed = weight_trend(points)
    expected = GOAL_RATE_KG_WEEK.get(goal, 0.0)
    gap = observed - expected                      # kg/week faster gain (or slower loss) than planned
    step = float(np.clip(-DAMPING * gap * KCAL_PER_KG / 7, -MAX_STEP, MAX_STEP))
    new_adjust = float(np.clip(prev_adjust + step, -MAX_TOTAL, MAX_TOTAL))
    reason = (f"Weekly recalculation: weight trend {observed:+.2f} kg/week vs planned {expected:+.2f} kg/week; "
              f"calorie correction {step:+.0f} kcal/day; latest weight {points[-1][1]:.1f} kg.")
    return {"observed_kg_week": round(observed, 2), "expected_kg_week": expected, "step": round(step),
            "adaptive_adjust": round(new_adjust), "latest_weight": points[-1][1], "as_of": points[-1][0], "reason": reason}
