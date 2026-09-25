"""Deterministic generator for the Nuvara demo dataset.

Produces the catalogue, the review corpus, the synthetic shopper population
with hidden latent taste vectors, and a behaviour stream biased by those
vectors. Everything is derived from a single fixed seed so intelligence
metrics stay reproducible between restarts.
"""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import catalog_data as cd
from .config import CATALOG_SIZE, DEFAULT_WEIGHTS, POPULATION_SIZE, RANDOM_SEED
from .models import Event, Product, Review, StrategyState, User, WeightHistory

# The behaviour stream is anchored to the moment the database is seeded, so the
# trending agent's recency decay always sees a live 90-day window. The random
# stream is unaffected by this anchor, so which shopper touched which product
# stays identical between environments; only the absolute timestamps shift.
NOW = datetime.utcnow()
HISTORY_DAYS = 90


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _price(rng: random.Random, low: float, high: float) -> float:
    """Draw a price with a log-ish skew so cheap items outnumber flagships."""
    raw = low + (high - low) * (rng.random() ** 1.7)
    if raw < 60:
        return round(raw) - 0.05 + 1
    return round(raw / 5) * 5 - 1


def build_products(rng: random.Random) -> list[dict]:
    per_category = CATALOG_SIZE // len(cd.CATEGORIES)
    remainder = CATALOG_SIZE - per_category * len(cd.CATEGORIES)
    products: list[dict] = []
    used_slugs: set[str] = set()
    pid = 1

    for idx, (category, spec) in enumerate(cd.CATEGORIES.items()):
        count = per_category + (1 if idx < remainder else 0)
        for n in range(count):
            line = cd.LINES[(idx * 7 + n * 3) % len(cd.LINES)]
            noun = spec["nouns"][n % len(spec["nouns"])]
            name = f"{line} {noun}"
            slug = _slugify(name)
            suffix = 2
            while slug in used_slugs:
                slug = f"{_slugify(name)}-{suffix}"
                suffix += 1
            used_slugs.add(slug)

            colorway = cd.COLORWAYS[(pid * 5) % len(cd.COLORWAYS)]
            material = spec["materials"][n % len(spec["materials"])]
            subcategory = spec["subcategories"][n % len(spec["subcategories"])]

            low, high = spec["price_range"]
            price = _price(rng, low, high)
            on_sale = rng.random() < 0.32
            compare_at = round(price * rng.uniform(1.15, 1.45) / 5) * 5 - 1 if on_sale else None

            tag_pool = spec["tags"]
            tags = sorted(rng.sample(tag_pool, k=rng.randint(3, 5)))
            tags.append(spec["slug"])

            phrase_a, phrase_b = rng.sample(spec["phrases"], 2)
            short_description = (
                f"{subcategory} built around {phrase_a}."
            )
            description = (
                f"The {name} is the {colorway.lower()} entry in our {line} range, made in "
                f"{material}. It is built around {phrase_a}, and finished with {phrase_b}. "
                f"We designed it for people who use one thing often rather than five things "
                f"occasionally, so the parts that wear are the parts you can replace. "
                f"Ships with a two-year warranty and a spares list that stays stocked for six years."
            )

            # Rating is drawn so the catalogue has a realistic left tail rather
            # than every item sitting at 4.6.
            rating = round(min(5.0, max(2.9, rng.gauss(4.32, 0.36))), 1)
            review_count = int(max(3, rng.lognormvariate(4.1, 0.95)))

            products.append(
                {
                    "id": pid,
                    "slug": slug,
                    "name": name,
                    "category": category,
                    "subcategory": subcategory,
                    "price": float(price),
                    "compare_at_price": float(compare_at) if compare_at else None,
                    "currency": "USD",
                    "description": description,
                    "short_description": short_description,
                    "image_seed": f"{slug}-{pid}",
                    "colorway": colorway,
                    "rating": rating,
                    "review_count": review_count,
                    "stock": rng.choice([0, 3, 7, 12, 18, 25, 40, 64, 90, 140]),
                    "tags": tags,
                    "attributes": {
                        "colorway": colorway,
                        "material": material,
                        "subcategory": subcategory,
                        "warranty": "2 years",
                        "ships_from": rng.choice(["Rotterdam", "Newark", "Osaka"]),
                        "weight_g": rng.randrange(80, 4200, 20),
                    },
                    "created_at": NOW - timedelta(days=rng.randint(20, 900)),
                }
            )
            pid += 1
    return products


def build_reviews(rng: random.Random, products: list[dict]) -> list[dict]:
    """Write reviews for roughly half the catalogue, 15-20 each."""
    reviews: list[dict] = []
    rid = 1
    reviewed = rng.sample(products, k=int(len(products) * 0.55))

    for product in reviewed:
        n = rng.randint(15, 20)
        # Rating mix is anchored on the product's own average score so the
        # written reviews agree with the headline number.
        mean = product["rating"]
        for _ in range(n):
            score = int(min(5, max(1, round(rng.gauss(mean, 0.85)))))
            title, body = rng.choice(cd.REVIEW_TEMPLATES[score])
            body = body.format(
                place=rng.choice(cd.REVIEW_PLACES),
                material=product["attributes"]["material"],
                weeks=rng.randint(3, 40),
                detail=rng.choice(cd.REVIEW_DETAILS),
            )
            reviews.append(
                {
                    "id": rid,
                    "product_id": product["id"],
                    "user_name": rng.choice(cd.REVIEW_NAMES),
                    "rating": score,
                    "title": title,
                    "body": body,
                    "helpful_count": int(rng.lognormvariate(1.6, 1.0)),
                    "created_at": NOW - timedelta(days=rng.randint(1, 420), hours=rng.randint(0, 23)),
                }
            )
            rid += 1
    return reviews


def build_users(rng: random.Random) -> list[dict]:
    """Create the shopper population and its hidden latent taste vectors."""
    users: list[dict] = []
    categories = list(cd.CATEGORIES.keys())
    all_tags = sorted({t for spec in cd.CATEGORIES.values() for t in spec["tags"]})

    for i in range(POPULATION_SIZE):
        segment = cd.SEGMENTS[i % len(cd.SEGMENTS)]
        first = cd.FIRST_NAMES[i % len(cd.FIRST_NAMES)]
        last = cd.LAST_NAMES[(i * 3 + 1) % len(cd.LAST_NAMES)]

        # Latent category affinities: segment bias plus individual jitter, so
        # two shoppers in one segment are related but not identical.
        cat_latent = {}
        for c in categories:
            base = segment["bias"].get(c, 0.12)
            cat_latent[c] = round(min(1.0, max(0.02, rng.gauss(base, 0.16))), 4)

        tag_latent = {}
        for t in all_tags:
            base = segment["tag_bias"].get(t, 0.15)
            tag_latent[t] = round(min(1.0, max(0.01, rng.gauss(base, 0.13))), 4)

        price_affinity = round(
            min(0.95, max(0.05, rng.gauss(segment["price_affinity"], 0.12))), 4
        )

        roll = rng.random()
        if roll < 0.16:
            activity = "power"
        elif roll < 0.62:
            activity = "regular"
        else:
            activity = "light"

        users.append(
            {
                "id": f"u_{i + 1:03d}",
                "name": f"{first} {last}",
                "segment": segment["name"],
                "avatar_seed": f"{first.lower()}-{last.lower()}",
                "blurb": cd.PERSONA_BLURBS[segment["name"]],
                "is_demo_persona": False,
                "activity_level": activity,
                "latent": {
                    "categories": cat_latent,
                    "tags": tag_latent,
                    "price_affinity": price_affinity,
                },
            }
        )

    # One demo persona per segment, chosen as the most active representative so
    # the persona switcher always lands on a shopper with real signal behind it.
    activity_rank = {"power": 0, "regular": 1, "light": 2}
    for segment in cd.SEGMENTS:
        members = [u for u in users if u["segment"] == segment["name"]]
        members.sort(key=lambda u: (activity_rank[u["activity_level"]], u["id"]))
        members[0]["is_demo_persona"] = True
        # Demo personas are guaranteed an active history.
        members[0]["activity_level"] = "power"
    return users


def affinity(latent: dict, product: dict) -> float:
    """Hidden ground-truth preference of a shopper for a product, in [0, 1].

    This is the single source of truth the behaviour generator and the digital
    twin's response model both read from, which is what makes simulated results
    internally consistent with the historical data the agents train on.
    """
    cat = latent["categories"].get(product["category"], 0.1)
    tags = product["tags"]
    tag_scores = [latent["tags"][t] for t in tags if t in latent["tags"]]
    tag_mean = sum(tag_scores) / len(tag_scores) if tag_scores else 0.15

    # Price fit: a shopper with high price_affinity tolerates premium items, a
    # low-affinity shopper is pulled towards cheaper stock.
    norm_price = min(1.0, product["price"] / 700.0)
    price_fit = 1.0 - abs(norm_price - latent["price_affinity"] * 0.8)

    quality = (product["rating"] - 2.9) / 2.1

    return max(0.0, min(1.0, 0.46 * cat + 0.28 * tag_mean + 0.14 * price_fit + 0.12 * quality))


def build_events(rng: random.Random, users: list[dict], products: list[dict]) -> list[dict]:
    """Generate a behaviour stream whose shape follows each shopper's latent vector."""
    volume = {"power": (140, 240), "regular": (45, 110), "light": (10, 34)}
    events: list[dict] = []
    eid = 1

    for user in users:
        lo, hi = volume[user["activity_level"]]
        n_events = rng.randint(lo, hi)

        # Sampling weights: exponential tilt on the latent affinity so the
        # shopper concentrates on their taste without ever being exclusive.
        weights = [max(0.004, affinity(user["latent"], p) ** 3.2) for p in products]
        session_id = f"seed-{user['id']}"

        for _ in range(n_events):
            day_offset = int(HISTORY_DAYS * (rng.random() ** 0.6))
            ts = NOW - timedelta(
                days=day_offset, hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
            )

            roll = rng.random()
            if roll < 0.055:
                events.append(
                    {
                        "id": eid,
                        "session_id": session_id,
                        "user_id": user["id"],
                        "product_id": None,
                        "type": "search",
                        "query": rng.choice(cd.SEARCH_TERMS),
                        "value": None,
                        "rec_id": None,
                        "source_agent": None,
                        "created_at": ts,
                    }
                )
                eid += 1
                continue

            product = rng.choices(products, weights=weights, k=1)[0]
            aff = affinity(user["latent"], product)

            # Funnel: a view always happens; deeper actions need stronger fit.
            if roll < 0.055 + 0.50:
                etype, value = "view", None
            elif roll < 0.055 + 0.74:
                etype, value = "click", None
            elif roll < 0.055 + 0.86:
                etype = "add_to_cart" if aff > 0.42 else "click"
                value = None
            elif roll < 0.055 + 0.94:
                if aff > 0.52:
                    etype, value = "purchase", product["price"]
                else:
                    etype, value = "view", None
            else:
                if aff > 0.45:
                    etype = "rating"
                    value = float(min(5, max(2, round(rng.gauss(2.6 + 2.6 * aff, 0.6)))))
                else:
                    etype, value = "view", None

            events.append(
                {
                    "id": eid,
                    "session_id": session_id,
                    "user_id": user["id"],
                    "product_id": product["id"],
                    "type": etype,
                    "query": None,
                    "value": value,
                    "rec_id": None,
                    "source_agent": None,
                    "created_at": ts,
                }
            )
            eid += 1

    events.sort(key=lambda e: e["created_at"])
    return events


def seed_database(db: Session) -> None:
    """Populate an empty database. Idempotent: returns immediately if seeded."""
    if db.query(Product).count() > 0:
        _ensure_strategy_row(db)
        return

    rng = random.Random(RANDOM_SEED)

    products = build_products(rng)
    reviews = build_reviews(rng, products)
    users = build_users(rng)
    events = build_events(rng, users, products)

    db.bulk_insert_mappings(Product, products)
    db.bulk_insert_mappings(Review, reviews)
    db.bulk_insert_mappings(User, users)
    db.bulk_insert_mappings(Event, events)
    db.commit()

    _ensure_strategy_row(db)


def _ensure_strategy_row(db: Session) -> None:
    state = db.get(StrategyState, 1)
    if state is None:
        state = StrategyState(id=1, weights=dict(DEFAULT_WEIGHTS), step=0)
        db.add(state)
        db.add(
            WeightHistory(
                step=0,
                weights=dict(DEFAULT_WEIGHTS),
                trigger_action="initial_strategy",
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
