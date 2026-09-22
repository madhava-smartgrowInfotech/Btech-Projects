"""Live inference + explanations (LIME for category words, SHAP for priority / time factors)."""
import threading

import joblib
import numpy as np
import shap
from lime.lime_text import LimeTextExplainer

from .taxonomy import CATEGORIES, PRIORITIES
from .textutil import CUE_NAMES, cue_hits
from .training import (DEPTS, PRIORITY_PATH, RESOLUTION_PATH, TEXT_PATH, priority_features,
                       resolution_features)

SEPARATORS = r"[\s\.,!?।:;()\[\]\"'/\-|]+"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _group(name):
    return "Category" if name.startswith("Category: ") else name


class Predictor:
    def __init__(self):
        self.lock = threading.Lock()
        self.load()

    def load(self):
        text = joblib.load(TEXT_PATH)
        prio = joblib.load(PRIORITY_PATH)
        res = joblib.load(RESOLUTION_PATH)
        prio_exp = shap.TreeExplainer(prio["model"])
        res_exp = shap.TreeExplainer(res["model"])
        with self.lock:
            self.text, self.prio, self.res = text, prio, res
            self.prio_exp, self.res_exp = prio_exp, res_exp
        self.lime = LimeTextExplainer(class_names=CATEGORIES, split_expression=SEPARATORS, bow=True,
                                      random_state=42)

    @property
    def version(self):
        return self.text.get("version")

    # ---- predictions ----
    def _cat_proba(self, texts):
        return self.text["category"].predict_proba(self.text["vectorizer"].transform(texts))

    def expected_days(self, category, priority, created_at):
        R = resolution_features([category], [PRIORITIES.index(priority)], [created_at])
        return max(float(self.res["model"].predict(R)[0]), 0.1), R

    def predict(self, text, created_at, explain=True):
        X = self.text["vectorizer"].transform([text])
        cat_p = self.text["category"].predict_proba(X)[0]
        dept_p = self.text["department"].predict_proba(X)[0]
        category, department = CATEGORIES[int(cat_p.argmax())], DEPTS[int(dept_p.argmax())]
        urg = self.text["urgency"].predict_proba(X)
        P = priority_features([text], [category], urg)
        prio_p = self.prio["model"].predict_proba(P)[0]
        plevel = int(prio_p.argmax())
        days, R = self.expected_days(category, PRIORITIES[plevel], created_at)
        out = {
            "category": category, "category_confidence": round(float(cat_p.max()), 3),
            "category_top3": [{"label": CATEGORIES[i], "p": round(float(cat_p[i]), 3)}
                              for i in cat_p.argsort()[::-1][:3]],
            "department": department, "department_confidence": round(float(dept_p.max()), 3),
            "department_top3": [{"label": DEPTS[i], "p": round(float(dept_p[i]), 3)}
                                for i in dept_p.argsort()[::-1][:3]],
            "priority": PRIORITIES[plevel], "priority_confidence": round(float(prio_p.max()), 3),
            "priority_proba": {PRIORITIES[i]: round(float(p), 3) for i, p in enumerate(prio_p)},
            "expected_days": round(days, 1),
            "model_version": self.version,
        }
        if explain:
            out["explanations"] = {
                "category_words": self.lime_words(text, CATEGORIES.index(category)),
                "priority_factors": self.priority_factors(P, plevel, text),
                "time_factors": self.time_factors(R),
            }
        return out

    # ---- explanations ----
    def lime_words(self, text, label, num_features=8):
        exp = self.lime.explain_instance(text, self._cat_proba, labels=(label,), num_features=num_features,
                                         num_samples=400)
        return [{"word": w, "weight": round(float(v), 4)} for w, v in exp.as_list(label=label)]

    def priority_factors(self, P, plevel, text):
        sv = np.asarray(self.prio_exp.shap_values(P))
        # shap returns (rows, features, classes) for multi-class XGBoost
        vals = sv[0, :, plevel] if sv.ndim == 3 else sv[plevel][0]
        names = self.prio["features"]
        hits = cue_hits(text)
        groups = {}
        for name, v, x in zip(names, vals, P[0]):
            g = _group(name)
            groups.setdefault(g, {"factor": g, "impact": 0.0, "value": None})
            groups[g]["impact"] += float(v)
            if g == "Category" and x:
                groups[g]["value"] = name.split(": ", 1)[1]
            elif g in CUE_NAMES:
                groups[g]["value"] = ", ".join(hits.get(g, [])[:4]) or "none found"
            elif g.startswith("Text model"):
                groups[g]["value"] = f"{x:.2f}"
            elif g == "Length (words)":
                groups[g]["value"] = str(int(x))
        rows = sorted(groups.values(), key=lambda r: -abs(r["impact"]))[:7]
        for r in rows:
            r["impact"] = round(r["impact"], 4)
        return {"target": PRIORITIES[plevel], "factors": rows}

    def time_factors(self, R):
        vals = np.asarray(self.res_exp.shap_values(R))[0]
        base = float(np.ravel(self.res_exp.expected_value)[0])
        names = self.res["features"]
        groups = {}
        for name, v, x in zip(names, vals, R[0]):
            g = _group(name)
            groups.setdefault(g, {"factor": g, "impact": 0.0, "value": None})
            groups[g]["impact"] += float(v)
            if g == "Category" and x:
                groups[g]["value"] = name.split(": ", 1)[1]
            elif g == "Priority level":
                groups[g]["value"] = PRIORITIES[int(x)]
            elif g == "Day of week":
                groups[g]["value"] = WEEKDAYS[int(x)]
            elif g == "Hour filed":
                groups[g]["value"] = f"{int(x):02d}:00"
        rows = sorted(groups.values(), key=lambda r: -abs(r["impact"]))
        for r in rows:
            r["impact"] = round(r["impact"], 3)  # days added (+) or removed (-) from the baseline
        return {"baseline_days": round(base, 2), "factors": rows}


_predictor = None
_init_lock = threading.Lock()


def get_predictor() -> Predictor:
    global _predictor
    with _init_lock:
        if _predictor is None:
            _predictor = Predictor()
    return _predictor

