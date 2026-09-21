import pandas as pd
from datetime import date, timedelta

from ml.expense_classifier import predict_category
from ml.spending_prediction import predict_next_month_expense, predict_category_spending


def test_predict_category_food():
    assert predict_category("Swiggy order") == "Food"


def test_predict_category_transport():
    assert predict_category("Uber ride") == "Transport"


def test_predict_category_entertainment():
    assert predict_category("Netflix subscription") == "Entertainment"


def test_predict_category_empty_description():
    assert predict_category("") == "Other"


def test_predict_category_unknown_falls_back_gracefully():
    # Nonsense text with no keyword match should not crash, should return a string
    result = predict_category("xyzabc123 qqq")
    assert isinstance(result, str) and result


def _build_expense_df(months: int, amounts: list[float]) -> pd.DataFrame:
    rows = []
    today = date.today()
    for i, amount in enumerate(amounts):
        d = today.replace(day=1) - timedelta(days=30 * (months - i))
        rows.append({"date": d, "amount": amount, "transaction_type": "expense", "category": "Food"})
    return pd.DataFrame(rows)


def test_spending_prediction_requires_minimum_history():
    df = _build_expense_df(2, [1000, 1100])  # only 2 data points
    result = predict_next_month_expense(df)
    assert result["available"] is False
    assert "months" in result["message"].lower()


def test_spending_prediction_with_enough_history():
    df = _build_expense_df(4, [1000, 1100, 1200, 1300])
    result = predict_next_month_expense(df)
    assert result["available"] is True
    assert result["predicted_next_month_expense"] >= 0
    assert result["trend"] in ("increasing", "decreasing", "stable")


def test_spending_prediction_never_negative():
    df = _build_expense_df(4, [1000, 500, 100, 10])  # sharply decreasing trend
    result = predict_next_month_expense(df)
    assert result["available"] is True
    assert result["predicted_next_month_expense"] >= 0


def test_category_spending_prediction_empty_df():
    df = pd.DataFrame(columns=["date", "amount", "transaction_type", "category"])
    result = predict_category_spending(df)
    assert result["available"] is False
