"""Investment CRUD + portfolio math. Uses yfinance for live prices when possible,
falling back gracefully to the user's manually entered current_price."""
from __future__ import annotations

from datetime import date
from sqlalchemy import and_

from database.database import get_session
from database.models import Investment

ASSET_TYPES = ["Stock", "Mutual Fund", "ETF", "Gold", "Fixed Deposit", "Other"]


def add_investment(user_id: int, asset_name: str, symbol: str, asset_type: str,
                    quantity: float, purchase_price: float, current_price: float,
                    purchase_date: date) -> int:
    if quantity <= 0 or purchase_price <= 0:
        raise ValueError("quantity and purchase_price must be greater than zero")
    with get_session() as session:
        inv = Investment(
            user_id=user_id, asset_name=asset_name.strip(), symbol=symbol.strip().upper(),
            asset_type=asset_type, quantity=quantity, purchase_price=purchase_price,
            current_price=current_price if current_price > 0 else purchase_price,
            purchase_date=purchase_date,
        )
        session.add(inv)
        session.flush()
        return inv.id


def delete_investment(user_id: int, investment_id: int) -> bool:
    with get_session() as session:
        inv = session.query(Investment).filter(
            and_(Investment.id == investment_id, Investment.user_id == user_id)
        ).first()
        if not inv:
            return False
        session.delete(inv)
        return True


def refresh_price(user_id: int, investment_id: int) -> tuple[bool, str]:
    """Attempt to refresh current_price from yfinance. Returns (success, message).
    Never raises — market data outages must degrade gracefully."""
    with get_session() as session:
        inv = session.query(Investment).filter(
            and_(Investment.id == investment_id, Investment.user_id == user_id)
        ).first()
        if not inv:
            return False, "Investment not found."
        if not inv.symbol:
            return False, "No ticker symbol on file; enter the current price manually."
        try:
            import yfinance as yf
            ticker = yf.Ticker(inv.symbol)
            price = ticker.fast_info.get("last_price") if hasattr(ticker, "fast_info") else None
            if not price:
                hist = ticker.history(period="1d")
                if hist.empty:
                    return False, "Market data unavailable for this symbol right now."
                price = float(hist["Close"].iloc[-1])
            inv.current_price = float(price)
            return True, f"Price updated to {price:.2f}."
        except Exception:
            return False, "Could not reach market data provider. Using last known price."


def get_investments(user_id: int) -> list[dict]:
    with get_session() as session:
        rows = session.query(Investment).filter(Investment.user_id == user_id).all()
        result = []
        for inv in rows:
            invested = inv.quantity * inv.purchase_price
            current_value = inv.quantity * inv.current_price
            profit_loss = current_value - invested
            return_pct = round((profit_loss / invested) * 100, 2) if invested else 0.0
            result.append({
                "id": inv.id, "asset_name": inv.asset_name, "symbol": inv.symbol,
                "asset_type": inv.asset_type, "quantity": inv.quantity,
                "purchase_price": inv.purchase_price, "current_price": inv.current_price,
                "purchase_date": inv.purchase_date, "invested_amount": invested,
                "current_value": current_value, "profit_loss": profit_loss,
                "return_percent": return_pct,
            })
        return result


def portfolio_summary(user_id: int) -> dict:
    holdings = get_investments(user_id)
    total_invested = sum(h["invested_amount"] for h in holdings)
    total_current = sum(h["current_value"] for h in holdings)
    total_pl = total_current - total_invested
    return {
        "total_invested": total_invested,
        "total_current_value": total_current,
        "total_profit_loss": total_pl,
        "total_return_percent": round((total_pl / total_invested) * 100, 2) if total_invested else 0.0,
        "holdings": holdings,
    }
