from datetime import date as Date
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import FoodLog, Profile, get_db
from ..deps import profile_dict, require_profile, targets_for
from ..services import usda
from ..services.foods import NUTRIENTS, food_db
from ..services.gemini import GeminiUnavailable, generate_json

router = APIRouter(prefix="/api/logs", tags=["logs"])


def log_out(row: FoodLog):
    return {"id": row.id, "date": row.date.isoformat(), "meal": row.meal, "food_id": row.food_id, "name": row.name,
            "grams": row.grams, "source": row.source, **{n: round(getattr(row, n), 1) for n in NUTRIENTS}}


class LogIn(BaseModel):
    date: Date | None = None
    meal: Literal["breakfast", "lunch", "snack", "dinner"]
    grams: float = Field(gt=0, le=3000)
    food_id: int | None = None
    fdc_id: int | None = None
    source: Literal["database", "photo", "usda"] = "database"


@router.get("")
def list_logs(date: Date | None = None, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    d = date or Date.today()
    rows = db.scalars(select(FoodLog).where(FoodLog.user_id == p.user_id, FoodLog.date == d).order_by(FoodLog.id)).all()
    totals = {n: round(sum(getattr(r, n) for r in rows), 1) for n in NUTRIENTS}
    t = targets_for(p)
    return {"date": d.isoformat(), "entries": [log_out(r) for r in rows], "totals": totals,
            "targets": {"kcal": t["kcal"], "protein": t["protein_g"], "carbs": t["carbs_g"], "fat": t["fat_g"],
                        "fibre": t["fibre_g"], "sodium": t["sodium_max_mg"], "sugar": t["sugar_max_g"]}}


@router.post("")
def add_log(body: LogIn, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    source = body.source
    if body.food_id is not None:
        f = food_db().get(body.food_id)
        if f is None:
            raise HTTPException(404, "Dish not found.")
        name, n = f["name"], food_db().nutrients(f, body.grams)
    elif body.fdc_id is not None:
        try:
            u = usda.get_food(body.fdc_id)
        except usda.USDAError as e:
            raise HTTPException(503, str(e))
        name = u["name"]
        n = {k: round(u["per_100g"][k] * body.grams / 100, 1) for k in NUTRIENTS}
        source = "usda"
    else:
        raise HTTPException(400, "Choose a dish or an ingredient to log.")
    row = FoodLog(user_id=p.user_id, date=body.date or Date.today(), meal=body.meal, food_id=body.food_id, name=name,
                  grams=body.grams, source=source, **{k: n[k] for k in NUTRIENTS})
    db.add(row)
    db.commit()
    return log_out(row)


@router.delete("/{log_id}")
def delete_log(log_id: int, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    row = db.get(FoodLog, log_id)
    if row is None or row.user_id != p.user_id:
        raise HTTPException(404, "Entry not found.")
    db.delete(row)
    db.commit()
    return {"ok": True}


PHOTO_PROMPT = """Look at this meal photo. Identify each distinct Indian (or other) dish visible.
For each dish give its common name as used in India (e.g. "Masala dosa", "Chapati", "Dal tadka", "Vegetable pulao"),
your confidence from 0 to 1, and an estimate of the portion weight in grams.
If the image does not show food, return an empty list.
Return JSON only: {"items": [{"dish": "string", "confidence": 0.0, "estimated_grams": 0, "description": "string"}]}"""


@router.post("/photo")
async def photo(file: UploadFile = File(...), p: Profile = Depends(require_profile)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
        raise HTTPException(400, "Upload a JPG, PNG or WEBP photo.")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "Photo is too large (max 8 MB).")
    try:
        result, model = generate_json(PHOTO_PROMPT, image=data, mime_type=file.content_type, temperature=0.2)
    except GeminiUnavailable as e:
        raise HTTPException(503, str(e))
    prefs = profile_dict(p)
    fdb = food_db()
    items = []
    for it in (result.get("items") or [])[:4]:
        dish = str(it.get("dish", "")).strip()
        if not dish:
            continue
        grams = float(it.get("estimated_grams") or 0) or None
        matches = fdb.search(dish, limit=4, prefs=prefs)
        for m in matches:
            g = grams or m["serving_g"]
            m["grams"] = round(g)
            m["nutrients"] = fdb.nutrients(fdb.get(m["food_id"]), g)
        items.append({"detected": dish, "confidence": it.get("confidence"), "estimated_grams": grams,
                      "description": it.get("description", ""), "matches": matches})
    return {"items": items, "model": model}
