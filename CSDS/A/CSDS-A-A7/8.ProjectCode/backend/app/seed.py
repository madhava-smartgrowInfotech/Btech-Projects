import csv

from sqlalchemy.orm import Session

from . import config, models


def seed_district_risk(db: Session):
    """Load the ML-generated district_risk.csv into the DB once, if empty."""
    if db.query(models.DistrictRisk).first() is not None:
        return

    csv_path = config.DATA_DIR / "district_risk.csv"
    if not csv_path.exists():
        print(f"[seed] {csv_path} not found - run ml/train_risk_model.py to generate it.")
        return

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(models.DistrictRisk(
                state=row["state"],
                district=row["district"],
                lat=float(row["lat"]),
                lng=float(row["lng"]),
                crime_rate=float(row["crime_rate"]),
                risk_score=float(row["risk_score"]),
                risk_tier=row["risk_tier"],
            ))
    db.add_all(rows)
    db.commit()
    print(f"[seed] loaded {len(rows)} district risk rows")
