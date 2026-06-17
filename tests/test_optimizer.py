import pytest

from smartspend.data_generator import get_grocery_dataset
from smartspend.models import BasketItem, Store
from smartspend.optimizer import (
    calculate_basket_price,
    calculate_effective_total_cost,
    get_store_by_id,
    optimize_basket,
)


@pytest.fixture
def sample_stores() -> list[Store]:
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
            id="cheapest",
            name="Cheapest Store",
            chain="Cheapest",
            neighborhood="Nearby",
            travel_minutes=10,
            travel_cost_huf=100,
            prices_huf={"bread": 350, "milk": 300},
        ),
        Store(
            id="too_far",
            name="Far Store",
            chain="Far",
            neighborhood="Across town",
            travel_minutes=30,
            travel_cost_huf=0,
            prices_huf={"bread": 250, "milk": 250},
        ),
    ]


@pytest.fixture
def sample_basket() -> list[BasketItem]:
    return [
        BasketItem(product_id="bread", quantity=2),
        BasketItem(product_id="milk", quantity=1),
    ]


def test_calculate_basket_price_multiplies_prices_by_quantity(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    assert calculate_basket_price(sample_stores[0], sample_basket) == 1400


def test_calculate_effective_total_cost_includes_travel_cost(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    assert calculate_effective_total_cost(sample_stores[1], sample_basket) == 1100


def test_optimize_basket_ranks_cheapest_eligible_store_first(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    results = optimize_basket(
        stores=sample_stores,
        basket=sample_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=15,
        usual_store_id="usual",
    )

    assert [result.store.id for result in results] == ["cheapest", "usual", "too_far"]
    assert [result.rank for result in results] == [1, 2, 3]


def test_optimize_basket_marks_stores_over_max_travel_time_ineligible(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    results = optimize_basket(
        stores=sample_stores,
        basket=sample_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=15,
        usual_store_id="usual",
    )

    far_store = get_store_by_id([result.store for result in results], "too_far")
    far_result = next(result for result in results if result.store.id == far_store.id)

    assert far_result.is_eligible is False
    assert far_result.rank == 3


def test_optimize_basket_calculates_budget_impact_and_budget_fit(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    results = optimize_basket(
        stores=sample_stores,
        basket=sample_basket,
        monthly_budget_huf=3_000,
        already_spent_huf=2_000,
        max_travel_minutes=15,
        usual_store_id="usual",
    )

    cheapest = results[0]
    usual = results[1]

    assert cheapest.remaining_budget_huf == -100
    assert cheapest.fits_budget is False
    assert usual.remaining_budget_huf == -400
    assert usual.fits_budget is False


def test_optimize_basket_calculates_savings_against_usual_store(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    results = optimize_basket(
        stores=sample_stores,
        basket=sample_basket,
        monthly_budget_huf=10_000,
        already_spent_huf=2_000,
        max_travel_minutes=15,
        usual_store_id="usual",
    )

    cheapest = results[0]
    usual = results[1]
    far_store = results[2]

    assert cheapest.savings_vs_usual_huf == 300
    assert usual.savings_vs_usual_huf == 0
    assert far_store.savings_vs_usual_huf == 650


def test_zero_quantity_items_do_not_change_basket_total(sample_stores: list[Store]) -> None:
    basket = [
        BasketItem(product_id="bread", quantity=1),
        BasketItem(product_id="milk", quantity=0),
    ]

    assert calculate_basket_price(sample_stores[0], basket) == 500


def test_optimizer_rejects_negative_quantities(sample_stores: list[Store]) -> None:
    basket = [BasketItem(product_id="bread", quantity=-1)]

    with pytest.raises(ValueError, match="quantity"):
        calculate_basket_price(sample_stores[0], basket)


def test_optimizer_rejects_missing_product_price(sample_stores: list[Store]) -> None:
    basket = [BasketItem(product_id="eggs", quantity=1)]

    with pytest.raises(ValueError, match="no price"):
        calculate_basket_price(sample_stores[0], basket)


def test_optimizer_rejects_unknown_usual_store(
    sample_stores: list[Store],
    sample_basket: list[BasketItem],
) -> None:
    with pytest.raises(ValueError, match="No store found"):
        optimize_basket(
            stores=sample_stores,
            basket=sample_basket,
            monthly_budget_huf=10_000,
            already_spent_huf=2_000,
            max_travel_minutes=15,
            usual_store_id="missing",
        )


def test_simulated_dataset_can_be_ranked() -> None:
    dataset = get_grocery_dataset()

    results = optimize_basket(
        stores=dataset.stores,
        basket=dataset.default_basket,
        monthly_budget_huf=120_000,
        already_spent_huf=40_000,
        max_travel_minutes=15,
        usual_store_id="spar_rozsakert",
    )

    assert len(results) == 4
    assert results[0].rank == 1
    assert all(result.basket_price_huf > 0 for result in results)
    assert all(result.effective_total_cost_huf >= result.basket_price_huf for result in results)
