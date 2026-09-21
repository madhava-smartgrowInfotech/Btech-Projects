from datetime import date
import pytest

from auth.authentication import signup
from services.transaction_service import (
    add_transaction, update_transaction, delete_transaction, get_transactions,
)


def _make_user(username="txuser"):
    result = signup("Tx User", f"{username}@example.com", username, "Str0ng!Pass", "Str0ng!Pass")
    assert result.success
    return result.user_id


def test_add_transaction_creates_row():
    user_id = _make_user("tx1")
    txn_id = add_transaction(user_id, date.today(), "Swiggy order", "Food", 450.0, "expense")
    rows = get_transactions(user_id)
    assert len(rows) == 1
    assert rows[0]["id"] == txn_id
    assert rows[0]["amount"] == 450.0


def test_add_transaction_rejects_negative_amount():
    user_id = _make_user("tx2")
    with pytest.raises(ValueError):
        add_transaction(user_id, date.today(), "Bad", "Food", -10.0, "expense")


def test_add_transaction_rejects_invalid_type():
    user_id = _make_user("tx3")
    with pytest.raises(ValueError):
        add_transaction(user_id, date.today(), "Bad", "Food", 10.0, "transfer")


def test_update_transaction():
    user_id = _make_user("tx4")
    txn_id = add_transaction(user_id, date.today(), "Original", "Food", 100.0, "expense")
    ok = update_transaction(user_id, txn_id, description="Updated", amount=200.0)
    assert ok
    rows = get_transactions(user_id)
    assert rows[0]["description"] == "Updated"
    assert rows[0]["amount"] == 200.0


def test_delete_transaction():
    user_id = _make_user("tx5")
    txn_id = add_transaction(user_id, date.today(), "ToDelete", "Food", 50.0, "expense")
    assert delete_transaction(user_id, txn_id)
    assert get_transactions(user_id) == []


def test_delete_transaction_returns_false_for_missing():
    user_id = _make_user("tx6")
    assert delete_transaction(user_id, 99999) is False


def test_user_isolation():
    """A user must never see another user's transactions."""
    user_a = _make_user("txa")
    user_b = _make_user("txb")
    add_transaction(user_a, date.today(), "A's txn", "Food", 100.0, "expense")
    add_transaction(user_b, date.today(), "B's txn", "Food", 200.0, "expense")

    rows_a = get_transactions(user_a)
    rows_b = get_transactions(user_b)
    assert len(rows_a) == 1 and rows_a[0]["description"] == "A's txn"
    assert len(rows_b) == 1 and rows_b[0]["description"] == "B's txn"


def test_filter_by_category_and_type():
    user_id = _make_user("tx7")
    add_transaction(user_id, date.today(), "Food item", "Food", 100.0, "expense")
    add_transaction(user_id, date.today(), "Salary", "Salary", 50000.0, "income")

    food_only = get_transactions(user_id, category="Food")
    assert len(food_only) == 1
    income_only = get_transactions(user_id, transaction_type="income")
    assert len(income_only) == 1
    assert income_only[0]["category"] == "Salary"
