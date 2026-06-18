from pathlib import Path

from smartspend.database import reset_demo_data
from smartspend.insights import (
    calculate_current_month_track_prediction,
    calculate_spending_insights,
)


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


def test_spending_insights_use_enriched_weekly_and_store_snapshots(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    insights = calculate_spending_insights(db_path=db_path)

    weekly_spend = {
        row["week"]: row["estimated_spend_huf"]
        for row in insights.weekly_spending_pattern_chart_data
    }
    store_split = {
        row["store"]: row["spend_huf"]
        for row in insights.store_split_chart_data
    }

    assert weekly_spend["Week 1"] > 0
    assert weekly_spend["Week 4"] > weekly_spend["Week 1"]
    assert set(store_split) == {"Lidl", "Aldi", "SPAR", "Tesco"}
    assert store_split["Lidl"] > store_split["Tesco"]


def test_current_month_track_prediction_returns_explainable_on_track_result(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    prediction = calculate_current_month_track_prediction(
        current_spend_huf=55000,
        monthly_budget_huf=170000,
        day_of_month=14,
        db_path=db_path,
    )

    assert prediction.status == "On track"
    assert prediction.severity == "success"
    assert prediction.projected_spend_huf < 170000
    assert prediction.over_under_budget_huf > 0
    assert 0 <= prediction.likelihood_percentage <= 100
    assert len(prediction.explanation_points) >= 4
    assert any("Historical average" in point for point in prediction.explanation_points)
    assert any("weekly distribution" in point for point in prediction.explanation_points)


def test_current_month_track_prediction_flags_likely_overspend(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    prediction = calculate_current_month_track_prediction(
        current_spend_huf=140000,
        monthly_budget_huf=120000,
        day_of_month=14,
        db_path=db_path,
    )

    assert prediction.status == "Likely over budget"
    assert prediction.severity == "danger"
    assert prediction.projected_spend_huf > 120000
    assert prediction.over_under_budget_huf < 0
