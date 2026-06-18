"""Spending insights for the SmartSpend V2 demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database


@dataclass(frozen=True)
class SpendingInsights:
    """Calculated grocery spending insights and chart-ready data."""

    average_monthly_grocery_spending_huf: int
    average_basket_value_huf: int
    average_grocery_trips_per_month: float
    highest_spending_month: dict[str, int | str]
    lowest_spending_month: dict[str, int | str]
    selected_month_summary: dict[str, int | str]
    monthly_spending_vs_budget_chart_data: list[dict[str, int | str]]
    weekly_spending_pattern_chart_data: list[dict[str, int | str]]
    store_split_chart_data: list[dict[str, int | str]]


@dataclass(frozen=True)
class CurrentMonthTrackPrediction:
    """Explainable current-month grocery budget prediction."""

    status: str
    severity: str
    projected_spend_huf: int
    over_under_budget_huf: int
    likelihood_percentage: int
    explanation_points: tuple[str, ...]


def calculate_spending_insights(
    selected_month: str | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> SpendingInsights:
    """Calculate deterministic spending insights from seeded/local data."""

    historical_months = load_historical_months(db_path)
    if not historical_months:
        raise ValueError("Historical monthly spending data is required.")

    total_spend = sum(int(month["grocery_spend_huf"]) for month in historical_months)
    total_trips = sum(int(month["transaction_count"]) for month in historical_months)
    average_monthly = round(total_spend / len(historical_months))
    average_trips = round(total_trips / len(historical_months), 1)
    average_basket = round(total_spend / total_trips) if total_trips else 0
    highest_month = max(historical_months, key=lambda month: int(month["grocery_spend_huf"]))
    lowest_month = min(historical_months, key=lambda month: int(month["grocery_spend_huf"]))
    selected_summary = find_selected_month(historical_months, selected_month)

    return SpendingInsights(
        average_monthly_grocery_spending_huf=average_monthly,
        average_basket_value_huf=average_basket,
        average_grocery_trips_per_month=average_trips,
        highest_spending_month=highest_month,
        lowest_spending_month=lowest_month,
        selected_month_summary=selected_summary,
        monthly_spending_vs_budget_chart_data=build_monthly_spending_chart_data(
            historical_months
        ),
        weekly_spending_pattern_chart_data=build_weekly_spending_pattern_data(
            historical_months
        ),
        store_split_chart_data=build_store_split_chart_data(db_path, historical_months),
    )


def load_historical_months(
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[dict[str, int | str]]:
    """Load historical monthly grocery spending rows."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT month, grocery_spend_huf, planned_budget_huf,
                   transaction_count,
                   week_1_spend_huf, week_2_spend_huf,
                   week_3_spend_huf, week_4_spend_huf,
                   lidl_spend_huf, aldi_spend_huf,
                   spar_spend_huf, tesco_spend_huf,
                   highest_purchase_huf, most_used_store,
                   notes
            FROM historical_monthly_spending
            ORDER BY month
            """
        ).fetchall()

    return [dict(row) for row in rows]


def find_selected_month(
    historical_months: list[dict[str, int | str]],
    selected_month: str | None,
) -> dict[str, int | str]:
    """Return a selected month or the most recent month when not provided."""

    if selected_month is None:
        return historical_months[-1]

    for month in historical_months:
        if month["month"] == selected_month:
            return month

    raise ValueError(f"No historical month found for '{selected_month}'.")


def build_monthly_spending_chart_data(
    historical_months: list[dict[str, int | str]],
) -> list[dict[str, int | str]]:
    """Build chart data for monthly spending versus budget."""

    return [
        {
            "month": month["month"],
            "grocery_spend_huf": int(month["grocery_spend_huf"]),
            "planned_budget_huf": int(month["planned_budget_huf"]),
        }
        for month in historical_months
    ]


def build_weekly_spending_pattern_data(
    historical_months: list[dict[str, int | str]],
) -> list[dict[str, int | str]]:
    """Build deterministic weekly spending pattern data from enriched history."""

    week_columns = [
        ("Week 1", "week_1_spend_huf"),
        ("Week 2", "week_2_spend_huf"),
        ("Week 3", "week_3_spend_huf"),
        ("Week 4", "week_4_spend_huf"),
    ]
    return [
        {
            "week": label,
            "estimated_spend_huf": round(
                sum(int(month[column]) for month in historical_months)
                / len(historical_months)
            ),
        }
        for label, column in week_columns
    ]


def build_store_split_chart_data(
    db_path: Path | str,
    historical_months: list[dict[str, int | str]],
) -> list[dict[str, int | str]]:
    """Build store split data from transactions or deterministic simulated split."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT s.chain AS store, SUM(t.product_total_huf) AS spend_huf
            FROM transactions t
            JOIN stores s ON s.id = t.store_id
            GROUP BY s.chain
            ORDER BY spend_huf DESC
            """
        ).fetchall()

    if rows:
        return [
            {"store": row["store"], "spend_huf": int(row["spend_huf"])}
            for row in rows
        ]

    return [
        {
            "store": store,
            "spend_huf": round(
                sum(int(month[column]) for month in historical_months)
                / len(historical_months)
            ),
        }
        for store, column in [
            ("Lidl", "lidl_spend_huf"),
            ("Aldi", "aldi_spend_huf"),
            ("SPAR", "spar_spend_huf"),
            ("Tesco", "tesco_spend_huf"),
        ]
    ]


def calculate_current_month_track_prediction(
    current_spend_huf: int,
    monthly_budget_huf: int,
    day_of_month: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> CurrentMonthTrackPrediction:
    """Predict whether current grocery spending appears on track."""

    if current_spend_huf < 0:
        raise ValueError("Current spend cannot be negative.")
    if monthly_budget_huf <= 0:
        raise ValueError("Monthly budget must be positive.")
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("Day of month must be between 1 and 31.")

    historical_months = load_historical_months(db_path)
    historical_average = round(
        sum(int(month["grocery_spend_huf"]) for month in historical_months)
        / len(historical_months)
    )
    over_budget_count = sum(
        int(month["grocery_spend_huf"]) > int(month["planned_budget_huf"])
        for month in historical_months
    )
    over_budget_frequency = over_budget_count / len(historical_months)
    elapsed_spend_share = calculate_elapsed_historical_share(
        historical_months=historical_months,
        day_of_month=day_of_month,
    )
    run_rate_projection = round(current_spend_huf / elapsed_spend_share)
    projected_spend = round(run_rate_projection * 0.65 + historical_average * 0.35)
    over_under_budget = monthly_budget_huf - projected_spend

    likelihood = calculate_on_track_likelihood(
        projected_spend_huf=projected_spend,
        monthly_budget_huf=monthly_budget_huf,
        over_budget_frequency=over_budget_frequency,
    )
    status, severity = classify_track_prediction(
        projected_spend_huf=projected_spend,
        monthly_budget_huf=monthly_budget_huf,
        likelihood_percentage=likelihood,
    )

    explanation_points = (
        (
            f"Current simulated grocery spend is {current_spend_huf:,} HUF "
            f"against a {monthly_budget_huf:,} HUF monthly budget."
        ),
        (
            f"Historical average monthly grocery spend is "
            f"{historical_average:,} HUF."
        ),
        (
            f"By day {day_of_month}, historical weekly distribution usually "
            f"accounts for about {round(elapsed_spend_share * 100)}% of "
            "monthly grocery spend."
        ),
        (
            f"{over_budget_count} of the last {len(historical_months)} "
            "simulated months finished over budget."
        ),
        (
            f"Projected month-end spend is {projected_spend:,} HUF, "
            f"which is {abs(over_under_budget):,} HUF "
            f"{'under' if over_under_budget >= 0 else 'over'} budget."
        ),
    )

    return CurrentMonthTrackPrediction(
        status=status,
        severity=severity,
        projected_spend_huf=projected_spend,
        over_under_budget_huf=over_under_budget,
        likelihood_percentage=likelihood,
        explanation_points=explanation_points,
    )


def calculate_elapsed_historical_share(
    historical_months: list[dict[str, int | str]],
    day_of_month: int,
) -> float:
    """Return the historical monthly spend share elapsed by the given day."""

    total_historical_spend = sum(
        int(month["grocery_spend_huf"]) for month in historical_months
    )
    week_columns = weekly_columns_elapsed_by_day(day_of_month)
    elapsed_historical_spend = sum(
        int(month[column])
        for month in historical_months
        for column in week_columns
    )
    if total_historical_spend <= 0:
        return max(day_of_month / 31, 0.1)

    return max(elapsed_historical_spend / total_historical_spend, 0.1)


def weekly_columns_elapsed_by_day(day_of_month: int) -> tuple[str, ...]:
    """Map a calendar day to completed simulated weekly snapshot columns."""

    if day_of_month <= 7:
        return ("week_1_spend_huf",)
    if day_of_month <= 14:
        return ("week_1_spend_huf", "week_2_spend_huf")
    if day_of_month <= 21:
        return ("week_1_spend_huf", "week_2_spend_huf", "week_3_spend_huf")
    return (
        "week_1_spend_huf",
        "week_2_spend_huf",
        "week_3_spend_huf",
        "week_4_spend_huf",
    )


def calculate_on_track_likelihood(
    projected_spend_huf: int,
    monthly_budget_huf: int,
    over_budget_frequency: float,
) -> int:
    """Convert deterministic budget signals into an on-track likelihood."""

    margin_ratio = (monthly_budget_huf - projected_spend_huf) / monthly_budget_huf
    if projected_spend_huf <= monthly_budget_huf:
        likelihood = 72 + min(18, round(margin_ratio * 100))
    else:
        likelihood = 54 + max(-34, round(margin_ratio * 140))

    likelihood -= round(over_budget_frequency * 18)
    return max(5, min(95, likelihood))


def classify_track_prediction(
    projected_spend_huf: int,
    monthly_budget_huf: int,
    likelihood_percentage: int,
) -> tuple[str, str]:
    """Return display-safe status and severity labels."""

    if projected_spend_huf > monthly_budget_huf * 1.1:
        return "Likely over budget", "danger"
    if projected_spend_huf > monthly_budget_huf:
        return "Likely over budget", "warning"
    if likelihood_percentage < 65:
        return "Watch closely", "warning"
    return "On track", "success"
