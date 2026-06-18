"""Agentic-style explanation layer for calculated SmartSpend results."""

from __future__ import annotations

from smartspend.formatting import format_huf
from smartspend.optimizer import PremiumOptimizationResult, PremiumStoreResult
from smartspend.warnings import BudgetWarning

SIMULATED_DATA_DISCLAIMER = (
    "All prices, routes, savings, warnings, and spending figures are simulated "
    "for this local MVP."
)


def explain_recommendation(
    optimization: PremiumOptimizationResult,
    warnings: list[BudgetWarning] | None = None,
) -> str:
    """Explain calculated results through simulated agent roles."""

    warning_list = warnings or []
    recommendation = optimization.recommended
    if recommendation is None:
        recommendation_text = "No store can win under the current hard constraints."
    else:
        recommendation_text = build_recommendation_summary(recommendation)

    warning_text = build_warning_summary(warning_list)
    guardrail_text = (
        "Guardrail agent: I did not invent prices, change rankings, move money, "
        "or make real financial recommendations. I only explain deterministic "
        "calculations already produced by the optimizer."
    )

    return "\n".join(
        [
            "Planner agent: Compared the requested basket across visible stores "
            f"using optimization mode '{optimization.mode}'.",
            "Data agent: Used the supplied product prices, route distance, travel "
            "time, availability, and budget inputs only.",
            f"Optimizer agent: {recommendation_text}",
            f"Explainer agent: {warning_text}",
            guardrail_text,
            f"Disclaimer: {SIMULATED_DATA_DISCLAIMER}",
        ]
    )


def build_recommendation_summary(result: PremiumStoreResult) -> str:
    """Build the deterministic recommendation sentence."""

    unavailable_text = (
        "no unavailable required items"
        if not result.unavailable_items
        else f"unavailable items: {', '.join(result.unavailable_items)}"
    )
    return (
        f"Recommended {result.store.name} with net total "
        f"{format_huf(result.net_total_cost_huf)}, product total "
        f"{format_huf(result.product_total_huf)}, travel monetary cost "
        f"{format_huf(result.travel_monetary_cost_huf)}, travel-time cost "
        f"{format_huf(result.travel_time_cost_huf)}, confidence "
        f"{result.confidence_score}/100, route source {result.route_source}, and "
        f"{unavailable_text}."
    )


def build_warning_summary(warnings: list[BudgetWarning]) -> str:
    """Summarize deterministic warnings without adding new advice."""

    if not warnings:
        return "No deterministic budget warnings were triggered."

    warning_bits = [
        f"{warning.level}:{warning.code}" for warning in warnings
    ]
    return "Triggered deterministic warnings: " + ", ".join(warning_bits) + "."
