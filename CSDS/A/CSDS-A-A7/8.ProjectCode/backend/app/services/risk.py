import math
from datetime import datetime, timezone

TIER_WEIGHT = {"low": 1.0, "medium": 2.5, "high": 5.0}

# Night hours (local clock is not known server-side, so IST-ish 21:00-05:00 UTC+5:30
# approximated by treating 15:30-23:30 UTC as night) get an extra risk multiplier.
NIGHT_MULTIPLIER = 1.6


def _haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_district(lat, lng, districts):
    """districts: list of DistrictRisk ORM rows. Returns the closest one."""
    best, best_dist = None, float("inf")
    for d in districts:
        dist = _haversine_km(lat, lng, d.lat, d.lng)
        if dist < best_dist:
            best, best_dist = d, dist
    return best


def _is_night_utc(dt: datetime) -> bool:
    return dt.hour >= 15  # ~15:00-23:59 UTC ~ 20:30-05:30 IST


def score_route(route, districts, sample_every_n=8, now=None):
    """Sample points along the route, map each to its district's risk tier, and
    return an overall risk score (higher = riskier) plus the tier breakdown."""
    now = now or datetime.now(timezone.utc)
    night = _is_night_utc(now)
    coords = route["coordinates"]
    if not coords:
        return {"score": 0.0, "tiers": {}, "night": night}

    sampled = coords[::sample_every_n] or coords
    tier_counts = {"low": 0, "medium": 0, "high": 0}
    total_weight = 0.0
    for lat, lng in sampled:
        d = nearest_district(lat, lng, districts) if districts else None
        tier = d.risk_tier if d else "medium"
        tier_counts[tier] += 1
        w = TIER_WEIGHT[tier]
        if night:
            w *= NIGHT_MULTIPLIER
        total_weight += w

    avg_weight = total_weight / len(sampled)
    return {"score": round(avg_weight, 3), "tiers": tier_counts, "night": night}
