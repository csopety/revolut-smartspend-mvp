from pathlib import Path

from smartspend.database import reset_demo_data
from smartspend.insights import calculate_spending_insights


def test_spending_insights_calculate_required_metrics(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    insights = calculate_spending_insights(db_path=db_path)

    assert insights.average_monthly_grocery_spending_huf > 0
    assert insights.average_basket_value_huf > 0
    assert insights.average_grocery_trips_per_month > 0
    assert insights.highest_spending_month["month"] == "2026-05"
    assert insights.lowest_spending_month["month"] == "2026-01"


def test_spending_insights_selected_month_summary(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    insights = calculate_spending_insights(selected_month="2026-03", db_path=db_path)

    assert insights.selected_month_summary["month"] == "2026-03"
    assert insights.selected_month_summary["grocery_spend_huf"] == 149_600


def test_spending_insights_return_chart_ready_data(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    insights = calculate_spending_insights(db_path=db_path)

    assert len(insights.monthly_spending_vs_budget_chart_data) >= 6
    assert len(insights.weekly_spending_pattern_chart_data) == 4
    assert len(insights.store_split_chart_data) == 4
    assert {
        "month",
        "grocery_spend_huf",
        "planned_budget_huf",
    }.issubset(insights.monthly_spending_vs_budget_chart_data[0])
    assert {"week", "estimated_spend_huf"}.issubset(
        insights.weekly_spending_pattern_chart_data[0]
    )
    assert {"store", "spend_huf"}.issubset(insights.store_split_chart_data[0])
