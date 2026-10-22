"""What-if scenario comparison for FinSight AI (model simulation, not causal)."""
from copy import deepcopy
from .predictor import predict_profile


def run_whatif(baseline_cleaned: dict, overrides: dict) -> dict:
    """Run baseline vs scenario predictions.

    overrides: subset of keys (capital-gain, capital-loss, hours-per-week,
    education + education-num, age, etc.) with new values.
    """
    base = predict_profile(baseline_cleaned)
    scenario_inputs = deepcopy(baseline_cleaned)
    changed = []
    for k, v in overrides.items():
        if v is None:
            continue
        if k in scenario_inputs and scenario_inputs[k] != v:
            changed.append({"field": k, "from": scenario_inputs[k], "to": v})
            scenario_inputs[k] = v
    scen = predict_profile(scenario_inputs)
    delta = round(scen["proba"] - base["proba"], 4)
    if delta > 0.02:
        verdict = "The scenario improves the modelled financial-strength score."
    elif delta < -0.02:
        verdict = "The scenario lowers the modelled financial-strength score."
    else:
        verdict = "The scenario leaves the modelled score roughly unchanged."
    # Largest-effect hint: attribute delta to changed fields qualitatively
    effect_notes = []
    for c in changed:
        effect_notes.append(f"{c['field']}: {c['from']} → {c['to']}")
    return {
        "baseline": base,
        "scenario": scen,
        "scenario_inputs": scenario_inputs,
        "changed": changed,
        "effect_notes": effect_notes,
        "delta": delta,
        "delta_pct": round(delta * 100, 2),
        "verdict": verdict + " This is a model what-if simulation, not a causal prediction.",
        "profile_changed": base["profile"] != scen["profile"],
        "risk_changed": base["risk"] != scen["risk"],
    }
