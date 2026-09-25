"""Seeds demo accounts, towns and marketplace activity so the app is
immediately explorable after setup. Run with:  python scripts/seed_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.ml.price.features import REGIONS
from app.models.crop import CropListing, QualityGrade
from app.models.market import Town
from app.models.order import Order
from app.models.user import User

TOWN_COORDS = {
    "Sunridge Valley": (28.61, 77.20),
    "Palmgrove Delta": (22.57, 88.36),
    "Amberfield Plains": (19.08, 72.88),
    "Cedarbrook Hills": (12.97, 77.59),
    "Millstone Basin": (23.03, 72.58),
    "Harborview Coast": (13.08, 80.27),
    "Stonegate Highlands": (26.85, 80.95),
    "Clearwater Flats": (17.39, 78.49),
}

DEMO_PASSWORD = "cropsight123"


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded — skipping.")
            return

        for region, (lat, lon) in TOWN_COORDS.items():
            db.add(Town(name=f"{region} Market", region=region, lat=lat, lon=lon, is_market=True))

        farmer = User(
            name="Asha Menon",
            email="farmer@cropsight.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="farmer",
            region=REGIONS[0],
            phone="+91 90000 00001",
            reliability_score=4.7,
        )
        distributor = User(
            name="Vikram Rao",
            email="distributor@cropsight.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="distributor",
            region=REGIONS[2],
            phone="+91 90000 00002",
            reliability_score=4.6,
        )
        admin = User(
            name="Platform Admin",
            email="admin@cropsight.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="admin",
            region=REGIONS[0],
            reliability_score=5.0,
        )
        db.add_all([farmer, distributor, admin])

        buyer_names = ["Riverstone Foods", "GreenMart Wholesale", "Coastal Fresh Distributors", "Harvest & Co."]
        buyers = []
        for i, name in enumerate(buyer_names):
            buyer = User(
                name=name,
                email=f"buyer{i+1}@cropsight.dev",
                hashed_password=hash_password(DEMO_PASSWORD),
                role="buyer",
                region=REGIONS[(i + 1) % len(REGIONS)],
                phone=f"+91 90000 000{10 + i}",
                reliability_score=round(3.8 + i * 0.3, 1),
            )
            buyers.append(buyer)
        db.add_all(buyers)
        db.commit()

        listing = CropListing(
            farmer_id=farmer.id,
            crop_type="Tomato",
            region=farmer.region,
            quantity_kg=480,
            image_path="",
            status="listed",
            asking_price=1950,
        )
        db.add(listing)
        db.commit()

        quality = QualityGrade(
            listing_id=listing.id,
            grade="A",
            confidence=0.91,
            probabilities={"A": 0.91, "B": 0.07, "C": 0.02, "Reject": 0.0},
            features={},
            shap_explanation={"top_features": []},
        )
        db.add(quality)
        db.commit()

        print("Seed complete.")
        print(f"  Farmer login:      farmer@cropsight.dev / {DEMO_PASSWORD}")
        print(f"  Buyer login:       buyer1@cropsight.dev / {DEMO_PASSWORD}")
        print(f"  Distributor login: distributor@cropsight.dev / {DEMO_PASSWORD}")
        print(f"  Admin login:       admin@cropsight.dev / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
