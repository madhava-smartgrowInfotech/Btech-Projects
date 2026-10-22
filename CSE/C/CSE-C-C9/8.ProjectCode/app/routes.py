"""Flask routes for FinSight AI."""
import json
from pathlib import Path
from flask import (Blueprint, render_template, request, jsonify,
                   send_from_directory, current_app)

bp = Blueprint("main", __name__)
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def _artifact_image(name):
    return send_from_directory(str(ARTIFACTS), name)


@bp.route("/artifacts/<path:name>")
def artifacts(name):
    allowed = {"confusion_matrix.png", "roc_curve.png", "shap_bar.png", "shap_beeswarm.png"}
    if name not in allowed:
        return "Not found", 404
    return _artifact_image(name)


@bp.route("/health")
def health():
    from app.services.predictor import get_model_name, load_json_artifact
    fc = load_json_artifact("forecast.json", None)
    model_ok = (ROOT / "models" / "best_model.pkl").exists()
    return jsonify({
        "status": "ok" if model_ok else "degraded",
        "product": "FinSight AI",
        "model": get_model_name(),
        "model_loaded": model_ok,
        "forecast_available": bool(fc and fc.get("forecast")),
    })


@bp.route("/")
def index():
    from app.services.predictor import load_json_artifact, get_model_name
    metrics = load_json_artifact("metrics.json", {})
    shap_g = load_json_artifact("shap_global.json", {"features": []})
    forecast = load_json_artifact("forecast.json", {})
    comparison = load_json_artifact("model_comparison.json", {"models": {}})
    return render_template("index.html", metrics=metrics,
                           model_name=get_model_name(),
                           shap_top=(shap_g.get("features") or [])[:5],
                           forecast=forecast, comparison=comparison)


@bp.route("/assess", methods=["GET", "POST"])
def assess():
    from app.utils.validation import (WORKCLASS, EDUCATION, MARITAL, OCCUPATION,
                                      RELATIONSHIP, RACE, SEX, COUNTRIES,
                                      validate_assessment)
    ctx = dict(workclasses=WORKCLASS, educations=EDUCATION, maritals=MARITAL,
               occupations=OCCUPATION, relationships=RELATIONSHIP, races=RACE,
               sexes=SEX, countries=COUNTRIES, errors=[], form={})
    if request.method == "POST":
        data = request.form.to_dict()
        cleaned, errors = validate_assessment(data)
        if errors:
            ctx["errors"] = errors
            ctx["form"] = data
            return render_template("assess.html", **ctx), 400
        try:
            from app.services.predictor import predict_profile
            result = predict_profile(cleaned)
        except FileNotFoundError as e:
            ctx["errors"] = [str(e)]
            ctx["form"] = data
            return render_template("assess.html", **ctx), 500
        except Exception as e:
            current_app.logger.exception("Prediction failed")
            ctx["errors"] = [f"Analysis failed: {e}"]
            ctx["form"] = data
            return render_template("assess.html", **ctx), 500
        # Persist baseline for what-if convenience
        from flask import session
        session["baseline"] = cleaned
        forecast = _safe_forecast()
        return render_template("result.html", result=result, forecast=forecast)
    # Pre-fill from session baseline if present
    try:
        from flask import session
        if session.get("baseline"):
            ctx["form"] = {k: str(v) for k, v in session["baseline"].items()}
    except Exception:
        pass
    return render_template("assess.html", **ctx)


def _safe_forecast():
    try:
        from app.services.forecaster import get_forecast
        return get_forecast()
    except Exception:
        return {"available": False, "history": [], "forecast": [],
                "interpretation": "Forecast unavailable."}


@bp.route("/explain")
def explain():
    from app.services.predictor import load_json_artifact
    shap_g = load_json_artifact("shap_global.json",
                                {"features": [], "model": "unknown", "note": ""})
    return render_template("explain.html", shap=shap_g)


@bp.route("/forecast")
def forecast():
    return render_template("forecast.html", forecast=_safe_forecast())


@bp.route("/whatif", methods=["GET", "POST"])
def whatif():
    from app.utils.validation import (WORKCLASS, EDUCATION, MARITAL, OCCUPATION,
                                      RELATIONSHIP, RACE, SEX, COUNTRIES,
                                      validate_assessment, EDU_NUM_MAP)
    ctx = dict(workclasses=WORKCLASS, educations=EDUCATION, maritals=MARITAL,
               occupations=OCCUPATION, relationships=RELATIONSHIP, races=RACE,
               sexes=SEX, countries=COUNTRIES, errors=[], form={}, result=None)
    from flask import session
    if session.get("baseline"):
        ctx["form"] = {k: str(v) for k, v in session["baseline"].items()}
    if request.method == "POST":
        data = request.form.to_dict()
        cleaned, errors = validate_assessment(data)
        if errors:
            ctx["errors"] = errors
            ctx["form"] = data
            return render_template("whatif.html", **ctx), 400
        # Scenario overrides (empty = keep baseline)
        overrides = {}
        try:
            sg = data.get("scenario_capital_gain", "").strip()
            sl = data.get("scenario_capital_loss", "").strip()
            sh = data.get("scenario_hours", "").strip()
            se = data.get("scenario_education", "").strip()
            if sg != "":
                v = float(sg)
                if v < 0 or v > 1000000:
                    raise ValueError("Scenario investment gains out of range.")
                overrides["capital-gain"] = v
            if sl != "":
                v = float(sl)
                if v < 0 or v > 1000000:
                    raise ValueError("Scenario investment losses out of range.")
                overrides["capital-loss"] = v
            if sh != "":
                v = int(sh)
                if v < 1 or v > 99:
                    raise ValueError("Scenario hours out of range.")
                overrides["hours-per-week"] = v
            if se != "":
                if se not in EDU_NUM_MAP:
                    raise ValueError("Scenario education is invalid.")
                overrides["education"] = se
                overrides["education-num"] = EDU_NUM_MAP[se]
        except ValueError as e:
            ctx["errors"] = [str(e)]
            ctx["form"] = data
            return render_template("whatif.html", **ctx), 400
        if not overrides:
            ctx["errors"] = ["Change at least one scenario field to compare."]
            ctx["form"] = data
            return render_template("whatif.html", **ctx), 400
        try:
            from app.services.whatif import run_whatif
            ctx["result"] = run_whatif(cleaned, overrides)
            ctx["form"] = data
        except Exception as e:
            current_app.logger.exception("What-if failed")
            ctx["errors"] = [f"Scenario analysis failed: {e}"]
            ctx["form"] = data
            return render_template("whatif.html", **ctx), 500
    return render_template("whatif.html", **ctx)


@bp.route("/performance")
def performance():
    from app.services.predictor import load_json_artifact
    comparison = load_json_artifact("model_comparison.json", {"models": {}})
    validation = load_json_artifact("validation_report.json", {})
    stats = load_json_artifact("stats_report.json", {})
    summary = load_json_artifact("training_summary.json", {})
    return render_template("performance.html", comparison=comparison,
                           validation=validation, stats=stats, summary=summary)


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or {}
    from app.utils.validation import validate_assessment
    cleaned, errors = validate_assessment(payload)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    try:
        from app.services.predictor import predict_profile
        return jsonify({"ok": True, "result": predict_profile(cleaned)})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "errors": [str(e)]}), 500
    except Exception as e:
        current_app.logger.exception("API prediction failed")
        return jsonify({"ok": False, "errors": [f"Prediction failed: {e}"]}), 500


@bp.route("/api/forecast")
def api_forecast():
    fc = _safe_forecast()
    return jsonify(fc)


@bp.app_errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="The page you requested was not found."), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500,
                           message="Something went wrong on our side. Please try again."), 500
