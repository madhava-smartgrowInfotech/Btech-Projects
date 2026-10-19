"""Stripe test-mode helper with offline demo fallback."""
from __future__ import annotations
import uuid
from . import config

try:
    import stripe as _stripe
except Exception:  # pragma: no cover
    _stripe = None


def stripe_configured() -> bool:
    return bool(config.STRIPE_SECRET_KEY) and _stripe is not None


def create_checkout(amount: float, reservation_id: int, email: str) -> dict:
    """Return {'url', 'session_id', 'provider'}. Uses Stripe when keys exist, else demo."""
    if stripe_configured():
        _stripe.api_key = config.STRIPE_SECRET_KEY
        session = _stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {"currency": "usd", "unit_amount": int(round(amount * 100)),
                               "product_data": {"name": f"ParkSure reservation #{reservation_id}"}},
                "quantity": 1}],
            customer_email=email,
            success_url=f"{config.APP_BASE_URL}/?paid={reservation_id}",
            cancel_url=f"{config.APP_BASE_URL}/?cancelled={reservation_id}",
            metadata={"reservation_id": str(reservation_id)},
        )
        return {"url": session.url, "session_id": session.id, "provider": "stripe"}
    sid = f"demo_{uuid.uuid4().hex[:12]}"
    return {"url": f"/api/payments/demo-confirm?session_id={sid}&reservation_id={reservation_id}",
            "session_id": sid, "provider": "demo"}
