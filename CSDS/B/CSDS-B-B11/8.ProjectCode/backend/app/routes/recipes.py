import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Profile, RecipeCache, get_db
from ..services.foods import food_db
from ..services.gemini import GeminiUnavailable, generate_json
from ..services.guardrails import diet_scan, scan
from ..deps import require_profile

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

PROMPT = """You are a careful Indian home cook and nutrition coach.
Write a home recipe for the dish "{name}" ({cuisine} cuisine) that makes ONE portion of about {grams:.0f} g.
The person's diet: {diet}. Allergies (must NEVER appear as an ingredient, garnish, oil or derivative): {allergies}.
Health conditions: {conditions}. {condition_rules}
Keep ingredients that are easy to find in India. Use metric or Indian household measures.
Return JSON only, with this shape:
{{"ingredients": [{{"item": "string", "quantity": "string"}}], "steps": ["string"], "prep_minutes": 0, "cook_minutes": 0,
  "health_tips": ["string"]}}
{extra}"""

RULES = {
    "diabetes": "Diabetes: no added sugar or jaggery; prefer whole grains, more vegetables and legumes.",
    "hypertension": "Hypertension: at most 1/4 teaspoon salt, no papad, pickle or stock cubes.",
    "high_cholesterol": "High cholesterol: at most 1 teaspoon of oil, no ghee, butter, cream or deep frying.",
}


@router.get("/{food_id}")
def recipe(food_id: int, grams: float | None = None, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    fdb = food_db()
    food = fdb.get(food_id)
    if food is None:
        raise HTTPException(404, "Dish not found.")
    grams = grams or food["serving_g"]
    allergies = sorted(p.allergies or [])
    conditions = sorted(p.conditions or [])
    sig = f"{food_id}|{round(grams / 25) * 25}|{p.diet_type}|{','.join(allergies)}|{','.join(conditions)}"
    key = hashlib.sha1(sig.encode()).hexdigest()
    cached = db.scalar(select(RecipeCache).where(RecipeCache.key == key))
    if cached:
        return {**cached.content, "cached": True}

    base = dict(name=food["name"], cuisine=food["cuisine"].replace("_", "-"), grams=grams,
                diet=p.diet_type.replace("_", "-"),
                allergies=", ".join(a.replace("_", " ") for a in allergies) or "none",
                conditions=", ".join(c.replace("_", " ") for c in conditions) or "none",
                condition_rules=" ".join(RULES[c] for c in conditions if c in RULES))
    extra, warnings, model, data = "", [], None, None
    for attempt in range(2):
        try:
            data, model = generate_json(PROMPT.format(**base, extra=extra))
        except GeminiUnavailable as e:
            raise HTTPException(503, str(e))
        text = " ".join(f"{i.get('item', '')} {i.get('quantity', '')}" for i in data.get("ingredients", [])) + " " + " ".join(data.get("steps", []))
        hits = scan(text, allergies) + diet_scan(text, p.diet_type)
        if not hits:
            break
        extra = f"IMPORTANT: your previous answer used {', '.join(hits)}, which this person cannot eat. Replace them with safe alternatives."
    else:
        # still unsafe after a retry: drop offending lines and warn
        data["ingredients"] = [i for i in data.get("ingredients", []) if not (scan(i.get("item", ""), allergies) + diet_scan(i.get("item", ""), p.diet_type))]
        data["steps"] = [s for s in data.get("steps", []) if not (scan(s, allergies) + diet_scan(s, p.diet_type))]
        warnings.append("Some AI-suggested ingredients conflicted with your allergies or diet and were removed. Review before cooking.")

    content = {
        "food_id": food_id, "name": food["name"], "grams": grams,
        "nutrients": fdb.nutrients(food, grams),
        "ingredients": data.get("ingredients", []), "steps": data.get("steps", []),
        "prep_minutes": data.get("prep_minutes"), "cook_minutes": data.get("cook_minutes"),
        "health_tips": data.get("health_tips", []),
        "typical_minutes_dataset": None if food["typical_minutes"] != food["typical_minutes"] else int(food["typical_minutes"]),
        "warnings": warnings, "model": model,
    }
    db.add(RecipeCache(key=key, food_id=food_id, content=content))
    db.commit()
    return {**content, "cached": False}
