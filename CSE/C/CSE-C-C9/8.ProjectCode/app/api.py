"""Thin read-only JSON API for the React frontend.

Every route here only wraps functions and artifacts that already exist
(validation lists, artifact JSON files, ``run_whatif``); no logic is duplicated
except the what-if override parsing that mirrors the ``/whatif`` form route.
"""
from flask import Blueprint, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _artifact(name, default):
    from app.services.predictor import load_json_artifact
    return load_json_artifact(name, default)


@api_bp.route("/options")
def options():
    from app.utils import validation as v
    return jsonify({
        "workclass": v.WORKCLASS, "education": v.EDUCATION,
        "marital-status": v.MARITAL, "occupation": v.OCCUPATION,
        "relationship": v.RELATIONSHIP, "race": v.RACE, "sex": v.SEX,
        "native-country": v.COUNTRIES,
        "limits": {
            "age": [16, 100], "capital-gain": [0, 1000000],
            "capital-loss": [0, 1000000], "hours-per-week": [1, 99],
        },
    })


@api_bp.route("/dashboard")
def dashboard():
    from app.services.predictor import get_model_name
    shap_g = _artifact("shap_global.json", {"features": []})
    forecast = _artifact("forecast.json", {})
    return jsonify({
        "model": get_model_name(),
        "metrics": _artifact("metrics.json", {}),
        "shap_top": (shap_g.get("features") or [])[:5],
        "outlook": {
            "interpretation": forecast.get("interpretation"),
            "trend_direction": forecast.get("trend_direction"),
            "forecast_pct_change": forecast.get("forecast_pct_change"),
        },
        "training": _artifact("training_summary.json", {}),
    })


@api_bp.route("/explain")
def explain():
    return jsonify(_artifact("shap_global.json",
                             {"features": [], "model": "unknown", "note": ""}))


@api_bp.route("/performance")
def performance():
    return jsonify({
        "comparison": _artifact("model_comparison.json", {"models": {}}),
        "validation": _artifact("validation_report.json", {}),
        "stats": _artifact("stats_report.json", {}),
        "summary": _artifact("training_summary.json", {}),
    })


def _parse_overrides(data):
    """Same rules as the /whatif form route. Returns (overrides, error)."""
    from app.utils.validation import EDU_NUM_MAP
    overrides = {}
    try:
        sg = str(data.get("scenario_capital_gain", "")).strip()
        sl = str(data.get("scenario_capital_loss", "")).strip()
        sh = str(data.get("scenario_hours", "")).strip()
        se = str(data.get("scenario_education", "")).strip()
        if sg != "":
            val = float(sg)
            if val < 0 or val > 1000000:
                raise ValueError("Scenario investment gains out of range.")
            overrides["capital-gain"] = val
        if sl != "":
            val = float(sl)
            if val < 0 or val > 1000000:
                raise ValueError("Scenario investment losses out of range.")
            overrides["capital-loss"] = val
        if sh != "":
            val = int(sh)
            if val < 1 or val > 99:
                raise ValueError("Scenario hours out of range.")
            overrides["hours-per-week"] = val
        if se != "":
            if se not in EDU_NUM_MAP:
                raise ValueError("Scenario education is invalid.")
            overrides["education"] = se
            overrides["education-num"] = EDU_NUM_MAP[se]
    except ValueError as e:
        return None, str(e)
    if not overrides:
        return None, "Change at least one scenario field to compare."
    return overrides, None


@api_bp.route("/whatif", methods=["POST"])
def whatif():
    from app.utils.validation import validate_assessment
    payload = request.get_json(silent=True) or {}
    cleaned, errors = validate_assessment(payload)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    overrides, err = _parse_overrides(payload)
    if err:
        return jsonify({"ok": False, "errors": [err]}), 400
    try:
        from app.services.whatif import run_whatif
        return jsonify({"ok": True, "result": run_whatif(cleaned, overrides)})
    except Exception as e:
        current_app.logger.exception("API what-if failed")
        return jsonify({"ok": False, "errors": [f"Scenario analysis failed: {e}"]}), 500
