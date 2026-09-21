from datetime import date
import pytest

from auth.authentication import signup
from services.transaction_service import add_transaction
from services.budget_service import set_budget, get_budget_status, delete_budget, check_and_raise_alerts


def _make_user(username="buduser"):
    result = signup("Bud User", f"{username}@example.com", username, "Str0ng!Pass", "Str0ng!Pass")
    assert result.success
    return result.user_id


def test_set_budget_and_get_status():
    user_id = _make_user("bud1")
    today = date.today()
    set_budget(user_id, "Food", 5000.0, today.month, today.year)
    add_transaction(user_id, today, "Groceries", "Food", 2000.0, "expense")

    status = get_budget_status(user_id, today.month, today.year)
    assert len(status) == 1
    assert status[0]["category"] == "Food"
    assert status[0]["actual_spent"] == 2000.0
    assert status[0]["remaining"] == 3000.0
    assert status[0]["percent_used"] == 40.0


def test_set_budget_rejects_non_positive_amount():
    user_id = _make_user("bud2")
    today = date.today()
    with pytest.raises(ValueError):
        set_budget(user_id, "Food", 0, today.month, today.year)


def test_set_budget_updates_existing():
    user_id = _make_user("bud3")
    today = date.today()
    set_budget(user_id, "Food", 3000.0, today.month, today.year)
    set_budget(user_id, "Food", 4000.0, today.month, today.year)
    status = get_budget_status(user_id, today.month, today.year)
    assert len(status) == 1
    assert status[0]["budget_amount"] == 4000.0


def test_delete_budget():
    user_id = _make_user("bud4")
    today = date.today()
    budget_id = set_budget(user_id, "Food", 3000.0, today.month, today.year)
    assert delete_budget(user_id, budget_id)
    assert get_budget_status(user_id, today.month, today.year) == []


def test_budget_overrun_alert_created():
    user_id = _make_user("bud5")
    today = date.today()
    set_budget(user_id, "Food", 1000.0, today.month, today.year)
    add_transaction(user_id, today, "Big spend", "Food", 1200.0, "expense")

    alerts = check_and_raise_alerts(user_id, today.month, today.year)
    assert any("exceeded" in a.lower() for a in alerts)


def test_no_alert_when_under_threshold():
    user_id = _make_user("bud6")
    today = date.today()
    set_budget(user_id, "Food", 1000.0, today.month, today.year)
    add_transaction(user_id, today, "Small spend", "Food", 100.0, "expense")

    alerts = check_and_raise_alerts(user_id, today.month, today.year)
    assert alerts == []
