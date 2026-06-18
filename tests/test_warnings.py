import pytest

from smartspend.warnings import evaluate_budget_warnings


def test_spent_at_or_above_budget_gives_danger() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=100_000,
        monthly_budget_huf=100_000,
        historical_months=[],
        day_of_month=20,
    )

    assert warnings[0].level == "danger"
    assert warnings[0].code == "budget_used"


def test_spent_between_75_and_100_percent_gives_warning() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=80_000,
        monthly_budget_huf=100_000,
        historical_months=[],
        day_of_month=20,
    )

    assert warnings[0].level == "warning"
    assert warnings[0].code == "budget_near_limit"


def test_historical_average_above_budget_gives_warning() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=20_000,
        monthly_budget_huf=100_000,
        historical_months=[
            {"grocery_spend_huf": 120_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 125_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 130_000, "planned_budget_huf": 100_000},
        ],
        day_of_month=20,
    )

    codes = {warning.code for warning in warnings}

    assert "historical_average_above_budget" in codes


def test_three_of_last_six_months_over_budget_gives_warning() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=20_000,
        monthly_budget_huf=150_000,
        historical_months=[
            {"grocery_spend_huf": 90_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 110_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 95_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 120_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 130_000, "planned_budget_huf": 100_000},
            {"grocery_spend_huf": 80_000, "planned_budget_huf": 100_000},
        ],
        day_of_month=20,
    )

    codes = {warning.code for warning in warnings}

    assert "three_recent_months_over_budget" in codes


def test_first_two_weeks_above_60_percent_gives_insight() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=61_000,
        monthly_budget_huf=100_000,
        historical_months=[],
        day_of_month=12,
    )

    assert warnings[0].level == "insight"
    assert warnings[0].code == "early_month_spend_high"


def test_projected_month_end_overspend_gives_warning() -> None:
    warnings = evaluate_budget_warnings(
        current_spent_huf=50_000,
        monthly_budget_huf=100_000,
        historical_months=[],
        day_of_month=12,
        projected_month_end_spend_huf=125_000,
    )

    codes = {warning.code for warning in warnings}

    assert "projected_month_end_overspend" in codes


def test_warning_inputs_are_validated() -> None:
    with pytest.raises(ValueError, match="positive"):
        evaluate_budget_warnings(0, 0, [], 10)

    with pytest.raises(ValueError, match="Day"):
        evaluate_budget_warnings(0, 100_000, [], 32)
