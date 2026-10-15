"""Admin panel."""
from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_db, require, iso
from database.models import User, MentorProfile, Resource, Report
from services.analytics_service import platform_overview

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require("admin")


@router.get("/overview")
def overview(user: User = Depends(admin_only), db=Depends(get_db)):
    return platform_overview(db)


@router.get("/users")
def users(user: User = Depends(admin_only), db=Depends(get_db)):
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": bool(u.is_active),
             "created_at": iso(u.created_at)} for u in db.query(User).order_by(User.id).all()]


@router.post("/users/{user_id}/toggle")
def toggle(user_id: int, user: User = Depends(admin_only), db=Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found.")
    if u.role == "admin":
        raise HTTPException(422, "Admin accounts can't be deactivated.")
    u.is_active = not u.is_active
    return {"id": u.id, "is_active": u.is_active}


@router.get("/mentors/pending")
def pending_mentors(user: User = Depends(admin_only), db=Depends(get_db)):
    out = []
    for mp in db.query(MentorProfile).filter_by(is_verified=False).all():
        mu = db.get(User, mp.user_id)
        out.append({"id": mp.id, "name": mu.name, "email": mu.email, "domain": mp.domain,
                    "expertise": mp.expertise, "experience_years": mp.experience_years})
    return out


@router.post("/mentors/{mentor_id}/verify")
def verify(mentor_id: int, user: User = Depends(admin_only), db=Depends(get_db)):
    mp = db.get(MentorProfile, mentor_id)
    if not mp:
        raise HTTPException(404, "Mentor not found.")
    mp.is_verified = True
    mu = db.get(User, mp.user_id)
    return {"message": f"{mu.name if mu else 'Mentor'} verified."}


@router.get("/resources")
def resources(user: User = Depends(admin_only), db=Depends(get_db)):
    return [{"id": r.id, "title": r.title, "price": r.price, "category": r.category,
             "is_reported": bool(r.is_reported), "is_approved": bool(r.is_approved)}
            for r in db.query(Resource).order_by(Resource.id).all()]


@router.delete("/resources/{resource_id}")
def remove_resource(resource_id: int, user: User = Depends(admin_only), db=Depends(get_db)):
    r = db.get(Resource, resource_id)
    if not r:
        raise HTTPException(404, "Resource not found.")
    db.delete(r)
    return {"message": "Resource removed."}


@router.get("/reports")
def reports(user: User = Depends(admin_only), db=Depends(get_db)):
    return [{"id": r.id, "reason": r.reason, "resource_id": r.resource_id, "created_at": iso(r.created_at)}
            for r in db.query(Report).filter_by(status="open").all()]


@router.post("/reports/{report_id}/resolve")
def resolve(report_id: int, user: User = Depends(admin_only), db=Depends(get_db)):
    r = db.get(Report, report_id)
    if not r:
        raise HTTPException(404, "Report not found.")
    r.status = "resolved"
    return {"message": "Report resolved."}
