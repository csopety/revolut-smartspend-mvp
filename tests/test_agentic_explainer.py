from smartspend.agentic_explainer import explain_recommendation
from smartspend.models import BasketItem, Store
from smartspend.optimizer import (
    OPTIMIZATION_BALANCED,
    TRANSPORT_CAR,
    optimize_premium_basket,
)
from smartspend.route_service import RouteResult
from smartspend.warnings import BudgetWarning


def test_agentic_explanation_contains_all_simulated_agents() -> None:
    optimization = build_optimization()

    explanation = explain_recommendation(optimization)

    assert "Planner agent:" in explanation
    assert "Data agent:" in explanation
    assert "Optimizer agent:" in explanation
    assert "Explainer agent:" in explanation
    assert "Guardrail agent:" in explanation


def test_agentic_explanation_explains_calculated_result_and_disclaimer() -> None:
    optimization = build_optimization()

    explanation = explain_recommendation(
        optimization,
        warnings=[
            BudgetWarning(
                level="warning",
                code="budget_near_limit",
                message="Current grocery spending is between 75% and 100% of budget.",
            )
        ],
    )

    assert optimization.recommended.store.name in explanation
    assert "net total" in explanation
    assert "budget_near_limit" in explanation
    assert "simulated" in explanation.lower()
    assert "did not invent prices" in explanation
    assert "move money" in explanation


def test_agentic_explanation_does_not_change_rankings() -> None:
    optimization = build_optimization()
    before_ranking = [result.store.id for result in optimization.results]

    explain_recommendation(optimization)

    after_ranking = [result.store.id for result in optimization.results]
    assert after_ranking == before_ranking


def build_optimization():
    stores = [
        Store(
            id="usual",
            name="Usual Store",
            chain="Usual",
            neighborhood="Home",
            travel_minutes=5,
            travel_cost_huf=0,
            prices_huf={"bread": 500, "milk": 400},
        ),
        Store(
            id="better",
            name="Better Store",
            chain="Better",
            neighborhood="Near",
            travel_minutes=6,
            travel_cost_huf=0,
            prices_huf={"bread": 350, "milk": 300},
        ),
    ]
    basket = [
        BasketItem(product_id="bread", quantity=2),
        BasketItem(product_id="milk", quantity=1),
    ]
    routes = {
        "usual": RouteResult("usual", 1.0, 5, "Simulated"),
        "better": RouteResult("better", 1.2, 6, "Simulated"),
    }
    return optimize_premium_basket(
        stores=stores,
        basket=basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_BALANCED,
        transport_mode=TRANSPORT_CAR,
        travel_cost_per_km_huf=100,
        value_of_time_huf_per_min=10,
    )
