"""
KnowledgeX AI - Learn & Earn Marketplace Service
==================================================
Handles resource browsing, simulated checkout/payments, purchase history and
seller/buyer/earnings dashboards. Payments are fully simulated using an
in-app wallet balance stored on StudentProfile.wallet_balance - no real
money or external payment gateway is involved in this prototype.
"""
from datetime import datetime

from database.models import Resource, Purchase, Transaction, StudentProfile, MentorProfile, User


def get_wallet_profile(session, user: User):
    """Returns the StudentProfile or MentorProfile holding this user's simulated
    wallet, whichever applies to their role. Both expose .wallet_balance."""
    if user.role == "mentor":
        return session.query(MentorProfile).filter_by(user_id=user.id).first()
    return session.query(StudentProfile).filter_by(user_id=user.id).first()


def _credit_seller(session, author_id, amount):
    """Credits the resource author's wallet, whichever profile type they have."""
    profile = session.query(StudentProfile).filter_by(user_id=author_id).first()
    if not profile:
        profile = session.query(MentorProfile).filter_by(user_id=author_id).first()
    if profile:
        profile.wallet_balance += amount


def list_resources(session, category=None, resource_type=None, search=None, only_free=False):
    q = session.query(Resource).filter(Resource.is_approved == True)  # noqa: E712
    if category and category != "All":
        q = q.filter(Resource.category == category)
    if resource_type and resource_type != "All":
        q = q.filter(Resource.resource_type == resource_type)
    if search:
        q = q.filter(Resource.title.ilike(f"%{search}%"))
    if only_free:
        q = q.filter(Resource.price == 0)
    return q.order_by(Resource.downloads.desc()).all()


def get_author_name(session, author_id):
    u = session.query(User).get(author_id)
    return u.name if u else "Unknown"


def has_purchased(session, user_id, resource_id):
    return session.query(Purchase).filter_by(buyer_id=user_id, resource_id=resource_id).first() is not None


def purchase_resource(session, user: User, resource: Resource):
    """Simulated checkout. Returns (success: bool, message: str)."""
    if resource.author_id == user.id:
        return False, "You cannot purchase your own resource."
    if has_purchased(session, user.id, resource.id):
        return False, "You already own this resource."

    if resource.price > 0:
        buyer_profile = get_wallet_profile(session, user)
        if buyer_profile is None:
            return False, "No wallet found for this account."
        if buyer_profile.wallet_balance < resource.price:
            return False, "Insufficient wallet balance. Please top up your wallet (simulated)."
        buyer_profile.wallet_balance -= resource.price

        # Credit seller (simulated earnings, 10% platform fee)
        _credit_seller(session, resource.author_id, resource.price * 0.9)

        session.add(Transaction(user_id=user.id, amount=-resource.price, type="purchase",
                                 description=f"Purchased '{resource.title}'"))
        session.add(Transaction(user_id=resource.author_id, amount=resource.price * 0.9, type="sale",
                                 description=f"Sold '{resource.title}'"))

    session.add(Purchase(buyer_id=user.id, resource_id=resource.id, price_paid=resource.price))
    resource.downloads += 1
    session.flush()
    return True, "Purchase successful! Available in 'My Purchases'."


def get_purchase_history(session, user_id):
    purchases = session.query(Purchase).filter_by(buyer_id=user_id).order_by(Purchase.purchased_at.desc()).all()
    result = []
    for p in purchases:
        res = session.query(Resource).get(p.resource_id)
        result.append({"purchase": p, "resource": res})
    return result


def get_seller_dashboard(session, user_id):
    my_resources = session.query(Resource).filter_by(author_id=user_id).all()
    total_earnings = sum(t.amount for t in session.query(Transaction).filter_by(
        user_id=user_id, type="sale").all())
    total_sales = session.query(Purchase).join(Resource).filter(Resource.author_id == user_id).count()
    return {
        "resources": my_resources,
        "total_earnings": round(total_earnings, 2),
        "total_sales": total_sales,
    }


def upload_resource(session, user: User, title, description, category, resource_type, price, skill_tags):
    resource = Resource(
        title=title, description=description, category=category, resource_type=resource_type,
        author_id=user.id, price=max(0, float(price)), skill_tags=skill_tags,
        is_approved=True, created_at=datetime.utcnow(),
    )
    session.add(resource)
    session.flush()
    return resource


def rate_resource(session, resource: Resource, new_rating: float):
    total_score = resource.rating * resource.rating_count + new_rating
    resource.rating_count += 1
    resource.rating = round(total_score / resource.rating_count, 2)
    session.flush()
