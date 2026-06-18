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
                   transaction_count, notes
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
    """Build deterministic weekly spending pattern data from historical totals."""

    week_weights = [
        ("Week 1", 0.24),
        ("Week 2", 0.28),
        ("Week 3", 0.22),
        ("Week 4", 0.26),
    ]
    rows = []
    for label, weight in week_weights:
        rows.append(
            {
                "week": label,
                "estimated_spend_huf": round(
                    sum(int(month["grocery_spend_huf"]) * weight for month in historical_months)
                    / len(historical_months)
                ),
            }
        )

    return rows


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

    average_monthly = round(
        sum(int(month["grocery_spend_huf"]) for month in historical_months)
        / len(historical_months)
    )
    split = [
        ("Lidl", 0.31),
        ("Aldi", 0.27),
        ("SPAR", 0.24),
        ("Tesco", 0.18),
    ]
    return [
        {"store": store, "spend_huf": round(average_monthly * weight)}
        for store, weight in split
    ]
