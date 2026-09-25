"""Heuristic buyer / route / best-time-to-sell recommendation engine.

This is intentionally not a trained model: it combines the price model's
output with distance, buyer reliability and a perishability-aware
spoilage risk into a transparent weighted score, so every ranking can be
explained in plain terms in the UI without a second black-box model.
"""

from __future__ import annotations

import hashlib
import math
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.ml.price.infer import predict_price
from app.models.market import Town
from app.models.user import User

PERISHABLE_CROPS = {"Tomato", "Mango", "Onion", "Potato"}

WEIGHTS = {
    "price": 0.38,
    "distance": 0.22,
    "quality_fit": 0.18,
    "reliability": 0.14,
    "spoilage_risk": 0.08,
}


def _hash_unit(*parts: str) -> float:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _town_for_region(db: Session, region: str) -> Town | None:
    return db.query(Town).filter(Town.region == region).first()


def recommend(db: Session, crop_type: str, region: str, grade: str, quantity_kg: float) -> dict:
    origin_town = _town_for_region(db, region)
    buyers = db.query(User).filter(User.role == "buyer").all()

    price_info = predict_price(crop_type, region, grade)
    base_price = price_info["current_price"]

    is_perishable = crop_type in PERISHABLE_CROPS
    spoilage_span = 5 if is_perishable else 21

    scored = []
    for buyer in buyers:
        buyer_town = _town_for_region(db, buyer.region) or origin_town
        if origin_town and buyer_town:
            distance_km = _haversine_km(origin_town.lat, origin_town.lon, buyer_town.lat, buyer_town.lon)
        else:
            distance_km = 50 + _hash_unit(buyer.email, "dist") * 400

        price_variance = 0.9 + _hash_unit(buyer.email, crop_type) * 0.28
        offered_price = base_price * price_variance

        price_norm = min(offered_price / (base_price * 1.2), 1.0)
        distance_norm = max(0.0, 1.0 - min(distance_km, 500) / 500)
        quality_fit = {"A": 1.0, "B": 0.85, "C": 0.6, "Reject": 0.1}.get(grade, 0.5)
        reliability_norm = min(buyer.reliability_score / 5.0, 1.0)
        transit_days = distance_km / 380 + 0.5
        spoilage_risk = min(transit_days / spoilage_span, 1.0)

        score = (
            WEIGHTS["price"] * price_norm
            + WEIGHTS["distance"] * distance_norm
            + WEIGHTS["quality_fit"] * quality_fit
            + WEIGHTS["reliability"] * reliability_norm
            + WEIGHTS["spoilage_risk"] * (1 - spoilage_risk)
        )

        scored.append(
            {
                "buyer_id": buyer.id,
                "buyer_name": buyer.name,
                "region": buyer.region,
                "offered_price": round(offered_price, 2),
                "distance_km": round(distance_km, 1),
                "transit_days": round(transit_days, 1),
                "reliability_score": buyer.reliability_score,
                "spoilage_risk": round(spoilage_risk, 2),
                "match_score": round(score * 100, 1),
            }
        )

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    top_buyers = scored[:5]

    best_route = None
    if top_buyers and origin_town:
        best = top_buyers[0]
        dest_town = _town_for_region(db, best["region"])
        best_route = {
            "origin": origin_town.name,
            "destination": dest_town.name if dest_town else best["region"],
            "distance_km": best["distance_km"],
            "estimated_transit_days": best["transit_days"],
            "buyer_name": best["buyer_name"],
        }

    return {
        "ranked_buyers": {"buyers": top_buyers},
        "best_route": best_route or {},
        "best_sell_day": price_info["best_sell_day"],
        "reference_price": base_price,
    }
