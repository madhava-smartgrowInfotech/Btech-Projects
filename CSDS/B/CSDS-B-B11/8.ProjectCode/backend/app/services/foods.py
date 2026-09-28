"""Food database: loading, safety filtering, search, nutrient maths and swap-model features."""
import difflib
import math
import re
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from ..config import FOODS_CSV, MODEL_PATH

NUTRIENTS = ["kcal", "protein", "carbs", "fat", "fibre", "sugar", "sodium"]
PLAN_ROLES = ["bf", "bev", "staple", "curry", "onedish", "side", "snack"]
ALLERGENS = ["peanut", "tree_nut", "dairy", "gluten", "egg", "soy", "fish", "shellfish", "sesame"]
DIETS = ["vegetarian", "eggetarian", "non_vegetarian", "vegan"]
FEATURES = ["p_share", "c_share", "f_share", "fibre_100kcal", "sugar_100kcal", "log_sodium_100kcal", "log_density"]


def feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Nutrient-composition features used by the K-Means swap model (independent of portion size)."""
    kcal = df["kcal"].clip(lower=1.0)
    energy = (4 * df["protein"] + 4 * df["carbs"] + 9 * df["fat"]).clip(lower=1.0)
    return pd.DataFrame({
        "p_share": 4 * df["protein"] / energy,
        "c_share": 4 * df["carbs"] / energy,
        "f_share": 9 * df["fat"] / energy,
        "fibre_100kcal": 100 * df["fibre"] / kcal,
        "sugar_100kcal": 100 * df["sugar"] / kcal,
        "log_sodium_100kcal": np.log1p(100 * df["sodium"] / kcal),
        "log_density": np.log1p(df["kcal"]),
    })


def normalise(text: str) -> str:
    s = re.sub(r"\(.*?\)", " ", text.lower())
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class FoodDB:
    def __init__(self):
        df = pd.read_csv(FOODS_CSV)
        df["alt_names"] = df["alt_names"].fillna("")
        df["allergens"] = df["allergens"].fillna("")
        df["typical_minutes"] = pd.to_numeric(df["typical_minutes"], errors="coerce")
        feats = feature_frame(df)
        self.model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
        if self.model is not None:
            self.scaled = self.model["scaler"].transform(feats[FEATURES].values)
            df["cluster"] = self.model["kmeans"].predict(self.scaled)
        else:
            self.scaled = ((feats - feats.mean()) / feats.std()).values
            df["cluster"] = -1
        self.df = df
        self.foods = {}
        for i, r in enumerate(df.to_dict("records")):
            r["allergen_set"] = set(a for a in r["allergens"].split("|") if a)
            r["row"] = i
            r["norm"] = normalise(r["name"])
            r["search_text"] = normalise(r["name"] + " " + r["alt_names"])
            self.foods[int(r["food_id"])] = r

    def get(self, food_id: int):
        return self.foods.get(int(food_id))

    # ------------------------------------------------------------------ safety
    @staticmethod
    def allowed(food, prefs) -> bool:
        """Hard filter: diet type, allergens and condition exclusions. Used by planning, swaps and search flags."""
        diet = prefs.get("diet_type", "non_vegetarian")
        if diet == "vegan" and not food["vegan"]:
            return False
        if diet == "vegetarian" and food["diet"] != "vegetarian":
            return False
        if diet == "eggetarian" and food["diet"] == "non_vegetarian":
            return False
        if food["allergen_set"] & set(prefs.get("allergies", [])):
            return False
        if "high_cholesterol" in prefs.get("conditions", []) and (food["fried"] or food["rich"]):
            return False
        return True

    @staticmethod
    def warnings_for(food, prefs):
        out = []
        hit = food["allergen_set"] & set(prefs.get("allergies", []))
        if hit:
            out.append("Contains or may contain: " + ", ".join(sorted(a.replace("_", " ") for a in hit)))
        diet = prefs.get("diet_type")
        if diet == "vegetarian" and food["diet"] != "vegetarian":
            out.append("Not vegetarian")
        if diet == "vegan" and not food["vegan"]:
            out.append("Not vegan")
        if diet == "eggetarian" and food["diet"] == "non_vegetarian":
            out.append("Contains meat or fish")
        if "high_cholesterol" in prefs.get("conditions", []) and (food["fried"] or food["rich"]):
            out.append("Fried or rich - not advised for high cholesterol")
        return out

    # ------------------------------------------------------------------ nutrients
    @staticmethod
    def nutrients(food, grams: float) -> dict:
        f = grams / 100.0
        out = {n: round(float(food[n]) * f, 1) for n in NUTRIENTS}
        out["gl"] = round(food["gi"] / 100.0 * float(food["carbs"]) * f, 1)
        return out

    # ------------------------------------------------------------------ search
    def search(self, query: str, limit: int = 15, prefs=None):
        q = normalise(query)
        if not q:
            return []
        q_tokens = q.split()
        scored = []
        for food in self.foods.values():
            text = food["search_text"]
            if q in text:
                score = 1.0 + (0.3 if food["norm"].startswith(q) else 0) - len(food["norm"]) / 400
            else:
                tokens = text.split()
                hits = sum(1 for t in q_tokens if any(tok.startswith(t) or difflib.SequenceMatcher(None, t, tok).ratio() > 0.8 for tok in tokens))
                overlap = hits / len(q_tokens)
                ratio = difflib.SequenceMatcher(None, q, food["norm"]).ratio()
                score = 0.6 * overlap + 0.4 * ratio
            if score > 0.45:
                scored.append((score, food))
        scored.sort(key=lambda x: -x[0])
        return [self.public(f, prefs, score=round(s, 3)) for s, f in scored[:limit]]

    def public(self, food, prefs=None, grams=None, score=None):
        grams = grams or food["serving_g"]
        out = {
            "food_id": int(food["food_id"]),
            "name": food["name"],
            "alt_names": food["alt_names"],
            "role": food["role"],
            "diet": food["diet"],
            "cuisine": food["cuisine"],
            "allergens": sorted(food["allergen_set"]),
            "serving_g": float(food["serving_g"]),
            "per_100g": {n: float(food[n]) for n in NUTRIENTS},
            "grams": float(grams),
            "nutrients": self.nutrients(food, grams),
            "cluster": int(food["cluster"]),
        }
        if prefs is not None:
            out["warnings"] = self.warnings_for(food, prefs)
        if score is not None:
            out["score"] = score
        return out

    # ------------------------------------------------------------------ swaps
    def similar(self, food, candidates):
        """Rank candidate foods by nutrient-profile similarity: same K-Means cluster first, then distance."""
        base = self.scaled[food["row"]]
        ranked = []
        for c in candidates:
            dist = float(np.linalg.norm(self.scaled[c["row"]] - base))
            same = c["cluster"] == food["cluster"]
            ranked.append((0 if same else 1, dist, c))
        ranked.sort(key=lambda x: (x[0], x[1]))
        return [(c, d, s == 0) for s, d, c in ranked]


@lru_cache(maxsize=1)
def food_db() -> FoodDB:
    return FoodDB()


def round_to(x: float, step: float) -> float:
    return float(step * math.floor(x / step + 0.5))
