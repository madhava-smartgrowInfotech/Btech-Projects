from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.ml.price.features import FEATURE_COLUMNS as PRICE_FEATURES
from app.ml.price.infer import load_artifact as load_price_artifact, readable_label
from app.ml.quality.infer import load_artifact as load_quality_artifact
from app.models.crop import CropListing
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    users_by_role = {}
    for role in ["farmer", "buyer", "distributor", "admin"]:
        users_by_role[role] = db.query(User).filter(User.role == role).count()

    total_listings = db.query(CropListing).count()
    listed = db.query(CropListing).filter(CropListing.status == "listed").count()
    sold = db.query(CropListing).filter(CropListing.status == "sold").count()
    orders = db.query(Order).count()
    gmv = sum(o.agreed_price * o.quantity_kg for o in db.query(Order).all())

    return {
        "users_by_role": users_by_role,
        "total_listings": total_listings,
        "listed": listed,
        "sold": sold,
        "orders": orders,
        "gross_volume": round(gmv, 2),
    }


@router.get("/model-insights")
def model_insights(user: User = Depends(require_roles("admin"))):
    quality_artifact = load_quality_artifact()
    price_artifact = load_price_artifact()

    q_model = quality_artifact["model"]
    quality_importance = sorted(
        [
            {"feature": name, "importance": float(imp)}
            for name, imp in zip(quality_artifact["feature_names"], q_model.feature_importances_)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )

    p_model = price_artifact["point_model"]
    grouped: dict[str, float] = {}
    for col, imp in zip(PRICE_FEATURES, p_model.feature_importances_):
        label = readable_label(col)
        grouped[label] = grouped.get(label, 0.0) + float(imp)
    price_importance = sorted(
        [{"feature": k, "importance": v} for k, v in grouped.items()],
        key=lambda x: x["importance"],
        reverse=True,
    )

    return {
        "quality_model": {
            "algorithm": "Random Forest classifier",
            "test_accuracy": quality_artifact["test_accuracy"],
            "feature_importance": quality_importance,
            "training_data": "Synthetically generated, distribution-based labeled feature vectors "
            "(color, texture, edge and blemish statistics per grade) — no proprietary or "
            "real-world labeled image dataset was used.",
        },
        "price_model": {
            "algorithm": "Gradient Boosted Regression Trees (point estimate + quantile bands)",
            "test_mae": price_artifact["test_mae"],
            "test_r2": price_artifact["test_r2"],
            "feature_importance": price_importance,
            "training_data": "Synthetically generated multi-year market series combining seasonality, "
            "weather, demand/supply and quality-grade effects — no live market data feed is connected.",
        },
    }
