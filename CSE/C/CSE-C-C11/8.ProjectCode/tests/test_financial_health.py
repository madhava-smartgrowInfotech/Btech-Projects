from ml.financial_health import (
    calculate_financial_health, score_savings_rate, score_expense_ratio,
)


def test_score_savings_rate_bounds():
    assert score_savings_rate(-10) == 0.0
    assert score_savings_rate(20) == 100.0
    assert score_savings_rate(100) == 100.0  # clipped
    assert score_savings_rate(10) == 50.0


def test_score_expense_ratio_bounds():
    assert score_expense_ratio(0, 100) == 0.0  # no income -> 0
    assert score_expense_ratio(10000, 5000) == 100.0  # spending half income -> full marks
    assert score_expense_ratio(10000, 10000) == 0.0  # spending it all -> 0


def test_healthy_user_scores_well():
    result = calculate_financial_health(
        monthly_income=100000, monthly_expenses=40000, savings_rate=60,
        total_balance=300000, budget_status=[{"percent_used": 50}],
        holdings=[{"asset_type": "Stock"}, {"asset_type": "Gold"}, {"asset_type": "ETF"}],
        goals=[{"percent_complete": 80}],
    )
    assert result["score"] >= 75
    assert result["rating"] in ("Good", "Excellent")


def test_struggling_user_scores_poorly():
    result = calculate_financial_health(
        monthly_income=30000, monthly_expenses=32000, savings_rate=-6.7,
        total_balance=1000, budget_status=[{"percent_used": 150}, {"percent_used": 120}],
        holdings=[], goals=[{"percent_complete": 5}],
    )
    assert result["score"] < 60
    assert result["rating"] in ("Needs Improvement", "Critical", "Fair")


def test_score_is_bounded_0_to_100():
    result = calculate_financial_health(
        monthly_income=0, monthly_expenses=0, savings_rate=0,
        total_balance=0, budget_status=[], holdings=[], goals=[],
    )
    assert 0 <= result["score"] <= 100


def test_result_contains_explanation_and_weakest_area():
    result = calculate_financial_health(
        monthly_income=50000, monthly_expenses=45000, savings_rate=10,
        total_balance=5000, budget_status=[], holdings=[], goals=[],
    )
    assert "weakest_area" in result
    assert result["weakest_area"] in result["components"]
    assert isinstance(result["explanation"], str) and result["explanation"]
