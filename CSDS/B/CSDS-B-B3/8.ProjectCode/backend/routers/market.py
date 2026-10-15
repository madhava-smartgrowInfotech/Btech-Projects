"""Learn & Earn marketplace (students and mentors)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_db, require, iso
from database.models import User, Resource
from services.marketplace_service import (
    list_resources, get_author_name, purchase_resource, get_purchase_history, get_seller_dashboard,
    upload_resource, has_purchased, get_wallet_profile,
)
from services.gamification_service import award_xp, grant_badge

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
member = require("student", "mentor")

CATEGORIES = ["Notes", "Projects", "Interview Prep", "Courses", "Cheat Sheets", "Practice Questions",
              "Coding Templates"]
RESOURCE_TYPES = ["Notes", "Study Material", "Project Report", "Coding Template",
                  "Interview Preparation Material", "Course", "Cheat Sheet",
                  "Practice Questions", "Mini Project"]


def resource_dict(db, r: Resource, user_id: int, owned: Optional[bool] = None):
    return {
        "id": r.id, "title": r.title, "description": r.description, "category": r.category,
        "resource_type": r.resource_type, "price": r.price, "rating": r.rating, "rating_count": r.rating_count,
        "downloads": r.downloads, "skill_tags": r.skill_tags, "author": get_author_name(db, r.author_id),
        "owned": has_purchased(db, user_id, r.id) if owned is None else owned,
        "is_own": r.author_id == user_id, "created_at": iso(r.created_at),
    }


def wallet(db, user):
    p = get_wallet_profile(db, user)
    return p.wallet_balance if p else 0


@router.get("/meta")
def meta(user: User = Depends(member), db=Depends(get_db)):
    return {"categories": CATEGORIES, "resource_types": RESOURCE_TYPES, "wallet_balance": wallet(db, user)}


@router.get("/resources")
def resources(category: str = "All", search: str = "", only_free: bool = False,
              user: User = Depends(member), db=Depends(get_db)):
    rows = list_resources(db, category=category, search=search or None, only_free=only_free)
    return {"wallet_balance": wallet(db, user), "resources": [resource_dict(db, r, user.id) for r in rows]}


@router.post("/resources/{resource_id}/purchase")
def purchase(resource_id: int, user: User = Depends(member), db=Depends(get_db)):
    r = db.get(Resource, resource_id)
    if not r or not r.is_approved:
        raise HTTPException(404, "Resource not found.")
    ok, msg = purchase_resource(db, user, r)
    if not ok:
        raise HTTPException(422, msg)
    award_xp(db, user.id, "resource_purchased")
    return {"message": msg, "wallet_balance": wallet(db, user)}


@router.get("/purchases")
def purchases(user: User = Depends(member), db=Depends(get_db)):
    out = []
    for item in get_purchase_history(db, user.id):
        r, p = item["resource"], item["purchase"]
        if r is None:  # removed by an admin after purchase
            continue
        out.append({**resource_dict(db, r, user.id, owned=True), "purchased_at": iso(p.purchased_at),
                    "price_paid": p.price_paid})
    return out


class UploadIn(BaseModel):
    title: str
    description: str
    category: str
    resource_type: str
    price: float = 0
    skill_tags: str = ""


@router.post("/resources")
def upload(body: UploadIn, user: User = Depends(member), db=Depends(get_db)):
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(422, "Title and description are required.")
    if not 0 <= body.price <= 5000:
        raise HTTPException(422, "Price must be between 0 and 5000.")
    r = upload_resource(db, user, body.title.strip(), body.description.strip(), body.category,
                        body.resource_type, body.price, body.skill_tags)
    award_xp(db, user.id, "resource_uploaded")
    if body.price > 0:
        grant_badge(db, user.id, "Knowledge Seller", "Published a paid resource")
    else:
        grant_badge(db, user.id, "Knowledge Sharer", "Shared a free resource")
    return resource_dict(db, r, user.id, owned=False)


@router.get("/seller")
def seller(user: User = Depends(member), db=Depends(get_db)):
    d = get_seller_dashboard(db, user.id)
    return {"total_sales": d["total_sales"], "total_earnings": d["total_earnings"],
            "resources": [resource_dict(db, r, user.id, owned=False) for r in d["resources"]]}
