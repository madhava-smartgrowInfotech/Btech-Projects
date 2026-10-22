"""Prediction + SHAP local explanation services for FinSight AI."""
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
ARTIFACTS_DIR = ROOT / "artifacts"

_model = None
_model_name = "unknown"
_feature_names = None
_explainer = None


def _load_feature_names():
    global _feature_names
    if _feature_names is not None:
        return _feature_names
    p = MODELS_DIR / "feature_names.pkl"
    if p.exists():
        try:
            _feature_names = list(joblib.load(p))
            return _feature_names
        except Exception as e:
            log.warning("Could not load feature names: %s", e)
    return None


def get_model():
    global _model, _model_name
    if _model is not None:
        return _model
    p = MODELS_DIR / "best_model.pkl"
    if not p.exists():
        raise FileNotFoundError(
            "Trained model not found (models/best_model.pkl). "
            "Run the training pipeline: python scripts/train.py")
    try:
        _model = joblib.load(p)
    except Exception as e:
        raise RuntimeError(f"Model artifact is corrupt and could not be loaded: {e}")
    name_file = MODELS_DIR / "best_model_name.txt"
    if name_file.exists():
        _model_name = name_file.read_text().strip()
    return _model


def get_model_name() -> str:
    try:
        get_model()
    except Exception:
        pass
    return _model_name


def get_explainer():
    """Lazily build a TreeExplainer (tree_path_dependent: fast, no background)."""
    global _explainer
    if _explainer is not None:
        return _explainer
    import shap
    model = get_model()
    step = model.named_steps["model"]
    cname = type(step).__name__
    if cname in ("XGBClassifier", "RandomForestClassifier", "GradientBoostingClassifier"):
        _explainer = shap.TreeExplainer(step, feature_perturbation="tree_path_dependent")
    else:
        _explainer = None
    return _explainer


def _ensure_scripts_path():
    import sys
    p = str(ROOT / "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)


def _label_for(feature: str) -> str:
    _ensure_scripts_path()
    from feature_engineering import human_label
    return human_label(feature)


def build_input_frame(cleaned: dict) -> pd.DataFrame:
    row = {
        "age": cleaned["age"],
        "workclass": cleaned["workclass"],
        "fnlwgt": np.nan,  # imputed with training median inside the pipeline
        "education": cleaned["education"],
        "education-num": cleaned["education-num"],
        "marital-status": cleaned["marital-status"],
        "occupation": cleaned["occupation"],
        "relationship": cleaned["relationship"],
        "race": cleaned["race"],
        "sex": cleaned["sex"],
        "capital-gain": cleaned["capital-gain"],
        "capital-loss": cleaned["capital-loss"],
        "hours-per-week": cleaned["hours-per-week"],
        "native-country": cleaned["native-country"],
    }
    return pd.DataFrame([row])


def profile_from_proba(p: float) -> tuple:
    """Map P(income>50K) to (profile, risk_level)."""
    if p >= 0.60:
        return "Established", "Low"
    if p >= 0.35:
        return "Developing", "Moderate"
    return "Emerging", "High"


def local_shap(pipe, frame: pd.DataFrame, max_items: int = 8) -> dict:
    """Compute live SHAP contributions for one row.

    Returns dict with positives/negatives lists and base info.
    Never raises: failures return an explanatory fallback.
    """
    out = {"positives": [], "negatives": [], "expected_value": None,
           "available": False, "note": ""}
    try:
        explainer = get_explainer()
        if explainer is None:
            out["note"] = "Local explanations are unavailable for this model type."
            return out
        pre = pipe.named_steps["preprocess"]
        Xt = pre.transform(frame)
        names = _load_feature_names()
        if names is None:
            try:
                _ensure_scripts_path()
                from feature_engineering import get_output_feature_names
                names = get_output_feature_names(pre)
            except Exception:
                names = [f"feature_{i}" for i in range(Xt.shape[1])]
        sv = np.asarray(explainer.shap_values(Xt[:1]))
        if sv.ndim == 3:  # some explainers return (1, features, classes)
            sv = sv[:, :, -1]
        vals = sv[0]
        row_vals = np.asarray(Xt[:1])[0]
        try:
            ev = explainer.expected_value
            if isinstance(ev, (list, np.ndarray)):
                ev = ev[-1] if len(ev) else float(ev)
            out["expected_value"] = round(float(ev), 4)
        except Exception:
            pass
        order = np.argsort(vals)
        _ensure_scripts_path()
        from feature_engineering import human_label as _hl
        items = []
        for i in list(order[:max_items]) + list(order[-max_items:][::-1]):
            fname = names[i] if i < len(names) else f"f{i}"
            fval = float(row_vals[i]) if i < len(row_vals) else float("nan")
            items.append({
                "feature": fname,
                "label": _hl(fname),
                "shap": round(float(vals[i]), 4),
                "value": round(fval, 4) if fval == fval else None,
            })
        pos = sorted([x for x in items if x["shap"] > 0],
                     key=lambda d: -d["shap"])[:5]
        neg = sorted([x for x in items if x["shap"] <= 0],
                     key=lambda d: d["shap"])[:5]
        # Attach human-readable direction sentences; for one-hot encoded
        # features a value of 0 means "this category does not apply", so say so.
        def _sentence(d, direction):
            base = d["label"]
            v = d.get("value")
            if v is not None and abs(v) < 1e-9 and "=" in base:
                state = "absence of " + base
            elif v is not None and abs(v - 1.0) < 1e-9 and "=" in base:
                state = base + " (applies to you)"
            else:
                state = base
            verb = ("pushes the prediction toward a stronger financial profile."
                    if direction == "up" else
                    "pulls the prediction toward a weaker financial profile.")
            return f"{state} {verb}"
        for d in pos:
            d["sentence"] = _sentence(d, "up")
        for d in neg:
            d["sentence"] = _sentence(d, "down")
        out.update({"positives": pos, "negatives": neg, "available": True})
    except Exception as e:
        log.exception("SHAP local explanation failed")
        out["note"] = f"Local explanation could not be computed: {e}"
    return out


def predict_profile(cleaned: dict) -> dict:
    """Full prediction pipeline for one validated input dict."""
    _ensure_scripts_path()
    from feature_engineering import clean_frame, add_derived_features
    pipe = get_model()
    frame = build_input_frame(cleaned)
    frame = add_derived_features(clean_frame(frame))
    try:
        proba = float(pipe.predict_proba(frame)[0, 1])
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {e}")
    profile, risk = profile_from_proba(proba)
    shap_local = local_shap(pipe, frame)
    insights = build_insights(cleaned, proba, profile, risk, shap_local)
    return {
        "proba": round(proba, 4),
        "strength_pct": round(proba * 100, 1),
        "risk_pct": round((1 - proba) * 100, 1),
        "profile": profile,
        "risk": risk,
        "model": get_model_name(),
        "inputs": cleaned,
        "shap": shap_local,
        "insights": insights,
    }


def build_insights(cleaned, proba, profile, risk, shap_local) -> list:
    tips = []
    if profile == "Established":
        tips.append("Your supplied factors resemble higher-earning profiles in the training data. "
                    "Maintaining steady work hours and continued skill development supports this position.")
    elif profile == "Developing":
        tips.append("Your supplied factors place you near the middle of the modelled range. "
                    "Small, steady improvements in skills, hours, or investment position are associated "
                    "with stronger modelled outcomes.")
    else:
        tips.append("Your supplied factors resemble lower-earning profiles in the training data. "
                    "Focus on factors you can influence over time, such as education, stable employment, "
                    "and consistent work hours.")
    h = cleaned.get("hours-per-week", 40) or 40
    if h < 35:
        tips.append(f"Working {h} hours per week is below full-time; the model generally associates "
                    "full-time, stable employment with stronger profiles (association, not a guarantee).")
    if (cleaned.get("capital-gain", 0) or 0) > 0:
        tips.append("Reported investment gains are a positive signal in the model — they are among the "
                    "stronger financial indicators it learned.")
    if (cleaned.get("capital-loss", 0) or 0) > 0:
        tips.append("Reported investment losses weigh against the modelled score. Reducing loss-making "
                    "exposure, where possible, is worth reviewing.")
    edu = cleaned.get("education", "")
    if edu in ("Preschool", "1st-4th", "5th-6th", "7th-8th", "9th", "10th", "11th", "12th", "HS-grad"):
        tips.append("Higher education levels are associated with stronger modelled profiles. "
                    "Further qualifications are the most commonly influential longer-term lever.")
    if shap_local.get("available"):
        tops = (shap_local.get("positives", [])[:2] + shap_local.get("negatives", [])[:2])
        if tops:
            tips.append("Top modelled drivers for your specific case: " +
                        "; ".join(f"{t['label']} ({t['shap']:+.3f})" for t in tops[:4]) + ".")
    tips.append("These are informational model insights, not professional financial advice, and they "
                "describe patterns in historical data — not certainties about your future.")
    return tips


def load_json_artifact(name: str, default):
    p = ARTIFACTS_DIR / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text())
    except Exception:
        return default
