import pytest

from smartspend.models import BasketItem, Store
from smartspend.optimizer import (
    OPTIMIZATION_BEST_BUDGET_FIT,
    OPTIMIZATION_CHEAPEST_BASKET,
    OPTIMIZATION_LOWEST_TOTAL_COST,
    TRANSPORT_CAR,
    TRANSPORT_WALKING,
    optimize_premium_basket,
)
from smartspend.route_service import RouteResult


@pytest.fixture
def premium_stores() -> list[Store]:
    return [
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
            id="cheap_far",
            name="Cheap Far Store",
            chain="Cheap",
            neighborhood="Far",
            travel_minutes=25,
            travel_cost_huf=0,
            prices_huf={"bread": 250, "milk": 300},
        ),
        Store(
            id="missing",
            name="Missing Store",
            chain="Missing",
            neighborhood="Near",
            travel_minutes=4,
            travel_cost_huf=0,
            prices_huf={"bread": 100},
        ),
    ]


@pytest.fixture
def premium_basket() -> list[BasketItem]:
    return [
        BasketItem(product_id="bread", quantity=2),
        BasketItem(product_id="milk", quantity=1),
    ]


@pytest.fixture
def routes() -> dict[str, RouteResult]:
    return {
        "usual": RouteResult("usual", distance_km=1.0, travel_minutes=5, route_source="Simulated"),
        "cheap_far": RouteResult(
            "cheap_far",
            distance_km=8.0,
            travel_minutes=25,
            route_source="Google Maps",
        ),
        "missing": RouteResult(
            "missing",
            distance_km=0.5,
            travel_minutes=4,
            route_source="Simulated",
        ),
    }


def test_premium_optimizer_calculates_required_fields(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_LOWEST_TOTAL_COST,
        transport_mode=TRANSPORT_CAR,
        travel_cost_per_km_huf=100,
        value_of_time_huf_per_min=20,
    )

    usual = next(item for item in result.results if item.store.id == "usual")

    assert usual.product_total_huf == 1400
    assert usual.travel_monetary_cost_huf == 100
    assert usual.travel_time_cost_huf == 100
    assert usual.net_total_cost_huf == 1600
    assert usual.remaining_budget_after_purchase_huf == 6600
    assert usual.overspend_amount_huf == 0
    assert usual.route_source == "Simulated"
    assert usual.confidence_score == 95


def test_walking_travel_monetary_cost_is_zero(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        transport_mode=TRANSPORT_WALKING,
        travel_cost_per_km_huf=999,
        value_of_time_huf_per_min=0,
    )

    assert all(item.travel_monetary_cost_huf == 0 for item in result.results)


def test_optimizer_uses_openrouteservice_distance_and_time(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    routes = {
        **routes,
        "usual": RouteResult(
            "usual",
            distance_km=3.4,
            travel_minutes=11,
            route_source="OpenRouteService",
        ),
    }

    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=20,
        usual_store_id="usual",
        routes_by_store_id=routes,
        transport_mode=TRANSPORT_CAR,
        travel_cost_per_km_huf=100,
        value_of_time_huf_per_min=5,
    )

    usual = next(item for item in result.results if item.store.id == "usual")

    assert usual.route_source == "OpenRouteService"
    assert usual.distance_km == 3.4
    assert usual.travel_time_min == 11
    assert usual.travel_monetary_cost_huf == 340
    assert usual.travel_time_cost_huf == 55


def test_stores_over_max_travel_time_remain_visible_but_cannot_win(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_CHEAPEST_BASKET,
    )

    far = next(item for item in result.results if item.store.id == "cheap_far")

    assert far.within_max_travel_time is False
    assert far.can_win is False
    assert far in result.results
    assert result.recommended.store.id == "usual"


def test_unavailable_required_items_cannot_win_without_substitutions(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_CHEAPEST_BASKET,
    )

    missing = next(item for item in result.results if item.store.id == "missing")

    assert missing.unavailable_items == ("milk",)
    assert missing.can_win is False
    assert result.recommended.store.id == "usual"


def test_unavailable_store_can_win_when_substitutions_are_accepted(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_CHEAPEST_BASKET,
        substitutions_accepted=True,
    )

    assert result.recommended.store.id == "missing"


def test_best_budget_fit_prefers_largest_remaining_budget_that_can_win(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=30,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode=OPTIMIZATION_BEST_BUDGET_FIT,
    )

    assert result.recommended.store.id == "cheap_far"


def test_premium_optimizer_requires_routes_for_all_stores(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    routes.pop("missing")

    with pytest.raises(ValueError, match="Missing routes"):
        optimize_premium_basket(
            stores=premium_stores,
            basket=premium_basket,
            monthly_budget_huf=10_000,
            already_spent_huf=2_000,
            max_travel_minutes=30,
            usual_store_id="usual",
            routes_by_store_id=routes,
        )


def test_premium_optimizer_accepts_human_labels_and_brief_field_names(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        optimization_mode="Lowest total cost including travel",
        transport_mode="Car",
        travel_cost_per_km_huf=100,
        value_of_time_huf_per_min=20,
    )

    recommended = result.recommended

    assert result.mode == OPTIMIZATION_LOWEST_TOTAL_COST
    assert recommended.product_total == recommended.product_total_huf
    assert recommended.travel_monetary_cost == recommended.travel_monetary_cost_huf
    assert recommended.travel_time_cost == recommended.travel_time_cost_huf
    assert recommended.net_total_cost == recommended.net_total_cost_huf
    assert (
        recommended.remaining_budget_after_purchase
        == recommended.remaining_budget_after_purchase_huf
    )
    assert recommended.overspend_amount == recommended.overspend_amount_huf
    assert recommended.savings_vs_usual_store == recommended.savings_vs_usual_store_huf
    assert (
        recommended.savings_vs_most_expensive_store
        == recommended.savings_vs_most_expensive_store_huf
    )


def test_premium_optimizer_balanced_mode_keeps_travel_time_as_comparison_cost_only(
    premium_stores: list[Store],
    premium_basket: list[BasketItem],
    routes: dict[str, RouteResult],
) -> None:
    result = optimize_premium_basket(
        stores=premium_stores,
        basket=premium_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
        travel_cost_per_km_huf=100,
        value_of_time_huf_per_min=40,
    )

    usual = next(item for item in result.results if item.store.id == "usual")

    assert result.recommended.store.id == "usual"
    assert usual.travel_time_cost_huf == 200
    assert usual.net_total_cost_huf == (
        usual.product_total_huf
        + usual.travel_monetary_cost_huf
        + usual.travel_time_cost_huf
    )
    assert usual.remaining_budget_after_purchase_huf == 6600
