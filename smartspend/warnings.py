"""Deterministic warning rules for SmartSpend V2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetWarning:
    """One deterministic warning or insight."""

    level: str
    code: str
    message: str


def evaluate_budget_warnings(
    current_spent_huf: int,
    monthly_budget_huf: int,
    historical_months: list[dict[str, int | str]],
    day_of_month: int,
    projected_month_end_spend_huf: int | None = None,
) -> list[BudgetWarning]:
    """Evaluate budget warnings using deterministic rule thresholds."""

    if monthly_budget_huf <= 0:
        raise ValueError("Monthly budget must be positive.")
    if current_spent_huf < 0:
        raise ValueError("Current spent amount cannot be negative.")
    if day_of_month < 1 or day_of_month > 31:
        raise ValueError("Day of month must be between 1 and 31.")

    warnings: list[BudgetWarning] = []
    spent_ratio = current_spent_huf / monthly_budget_huf

    if spent_ratio >= 1:
        warnings.append(
            BudgetWarning(
                level="danger",
                code="budget_used",
                message="Current grocery spending is at or above 100% of budget.",
            )
        )
    elif spent_ratio >= 0.75:
        warnings.append(
            BudgetWarning(
                level="warning",
                code="budget_near_limit",
                message="Current grocery spending is between 75% and 100% of budget.",
            )
        )

    if historical_months:
        historical_average = round(
            sum(int(month["grocery_spend_huf"]) for month in historical_months)
            / len(historical_months)
        )
        if historical_average > monthly_budget_huf:
            warnings.append(
                BudgetWarning(
                    level="warning",
                    code="historical_average_above_budget",
                    message="Historical average grocery spending is above current budget.",
                )
            )

        recent_months = historical_months[-6:]
        months_over_budget = sum(
            int(month["grocery_spend_huf"]) > int(month["planned_budget_huf"])
            for month in recent_months
        )
        if months_over_budget >= 3:
            warnings.append(
                BudgetWarning(
                    level="warning",
                    code="three_recent_months_over_budget",
                    message="At least 3 of the last 6 months were over budget.",
                )
            )

    if day_of_month <= 14 and spent_ratio > 0.6:
        warnings.append(
            BudgetWarning(
                level="insight",
                code="early_month_spend_high",
                message="Spending is above 60% of monthly budget in the first two weeks.",
            )
        )

    if (
        projected_month_end_spend_huf is not None
        and projected_month_end_spend_huf > monthly_budget_huf
    ):
        warnings.append(
            BudgetWarning(
                level="warning",
                code="projected_month_end_overspend",
                message="Projected month-end spending is above budget.",
            )
        )

    return warnings
