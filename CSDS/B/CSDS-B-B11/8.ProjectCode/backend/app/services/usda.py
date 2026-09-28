"""USDA FoodData Central lookups (per-100 g nutrients for raw ingredients)."""
import httpx

from ..config import USDA_API_KEY

BASE = "https://api.nal.usda.gov/fdc/v1"
# nutrient ids -> our names (energy has several ids depending on the data type)
IDS = {1008: "kcal", 2047: "kcal", 2048: "kcal", 1003: "protein", 1005: "carbs", 1004: "fat",
       1079: "fibre", 1093: "sodium", 2000: "sugar", 1063: "sugar"}


class USDAError(Exception):
    pass


def _extract(nutrients):
    out = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fibre": 0.0, "sodium": 0.0, "sugar": 0.0}
    seen = set()
    for n in nutrients:
        nid = n.get("nutrientId") or (n.get("nutrient") or {}).get("id")
        val = n.get("value", n.get("amount"))
        unit = (n.get("unitName") or (n.get("nutrient") or {}).get("unitName") or "").upper()
        name = IDS.get(int(nid)) if nid else None
        if name is None or val is None or name in seen:
            continue
        if name == "kcal" and unit == "KJ":
            continue
        out[name] = round(float(val), 2)
        seen.add(name)
    return out


def search(query: str, limit: int = 10):
    try:
        r = httpx.get(f"{BASE}/foods/search", params={"api_key": USDA_API_KEY, "query": query, "pageSize": limit,
                                                      "dataType": "Foundation,SR Legacy"}, timeout=20)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise USDAError(f"USDA FoodData Central is unavailable right now ({e.__class__.__name__}).")
    return [{"fdc_id": f["fdcId"], "name": f["description"].capitalize(), "data_type": f.get("dataType"),
             "per_100g": _extract(f.get("foodNutrients", []))} for f in r.json().get("foods", [])]


def get_food(fdc_id: int):
    try:
        r = httpx.get(f"{BASE}/food/{int(fdc_id)}", params={"api_key": USDA_API_KEY}, timeout=20)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise USDAError(f"USDA FoodData Central is unavailable right now ({e.__class__.__name__}).")
    f = r.json()
    return {"fdc_id": f["fdcId"], "name": f["description"].capitalize(), "per_100g": _extract(f.get("foodNutrients", []))}
