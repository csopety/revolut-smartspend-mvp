"""Rule-based grocery basket optimizer for the SmartSpend MVP."""

from smartspend.models import BasketItem, Store, StoreResult


def calculate_basket_price(store: Store, basket: list[BasketItem]) -> int:
    """Calculate the grocery basket price for one store in HUF."""

    total_huf = 0

    for item in basket:
        if item.quantity < 0:
            raise ValueError("Basket item quantity cannot be negative.")

        if item.product_id not in store.prices_huf:
            raise ValueError(
                f"Store '{store.name}' has no price for product '{item.product_id}'."
            )

        total_huf += store.prices_huf[item.product_id] * item.quantity

    return total_huf


def calculate_effective_total_cost(store: Store, basket: list[BasketItem]) -> int:
    """Calculate basket price plus travel cost for one store."""

    return calculate_basket_price(store, basket) + store.travel_cost_huf


def get_store_by_id(stores: list[Store], store_id: str) -> Store:
    """Find one store by ID or raise a clear error."""

    for store in stores:
        if store.id == store_id:
            return store

    raise ValueError(f"No store found with id '{store_id}'.")


def rank_store_results(results: list[StoreResult]) -> list[StoreResult]:
    """Rank eligible stores first, then by effective cost and travel time."""

    sorted_results = sorted(
        results,
        key=lambda result: (
            not result.is_eligible,
            result.effective_total_cost_huf,
            result.store.travel_minutes,
            result.store.name,
        ),
    )

    return [
        StoreResult(
            store=result.store,
            basket_price_huf=result.basket_price_huf,
            travel_cost_huf=result.travel_cost_huf,
            effective_total_cost_huf=result.effective_total_cost_huf,
            remaining_budget_huf=result.remaining_budget_huf,
            savings_vs_usual_huf=result.savings_vs_usual_huf,
            is_eligible=result.is_eligible,
            fits_budget=result.fits_budget,
            rank=index,
        )
        for index, result in enumerate(sorted_results, start=1)
    ]


def optimize_basket(
    stores: list[Store],
    basket: list[BasketItem],
    monthly_budget_huf: int,
    already_spent_huf: int,
    max_travel_minutes: int,
    usual_store_id: str,
) -> list[StoreResult]:
    """Compare stores and return ranked grocery basket results.

    The calculation is transparent and rule-based:
    effective total cost = basket price + travel cost.
    Stores over the user's maximum travel time are marked ineligible and ranked
    after eligible stores.
    """

    if monthly_budget_huf < 0:
        raise ValueError("Monthly budget cannot be negative.")
    if already_spent_huf < 0:
        raise ValueError("Already spent amount cannot be negative.")
    if max_travel_minutes < 0:
        raise ValueError("Maximum travel time cannot be negative.")
    if not stores:
        raise ValueError("At least one store is required.")

    usual_store = get_store_by_id(stores, usual_store_id)
    usual_effective_cost_huf = calculate_effective_total_cost(usual_store, basket)

    results = []
    for store in stores:
        basket_price_huf = calculate_basket_price(store, basket)
        effective_total_cost_huf = basket_price_huf + store.travel_cost_huf
        remaining_budget_huf = (
            monthly_budget_huf - already_spent_huf - effective_total_cost_huf
        )

        results.append(
            StoreResult(
                store=store,
                basket_price_huf=basket_price_huf,
                travel_cost_huf=store.travel_cost_huf,
                effective_total_cost_huf=effective_total_cost_huf,
                remaining_budget_huf=remaining_budget_huf,
                savings_vs_usual_huf=usual_effective_cost_huf
                - effective_total_cost_huf,
                is_eligible=store.travel_minutes <= max_travel_minutes,
                fits_budget=remaining_budget_huf >= 0,
                rank=0,
            )
        )

    return rank_store_results(results)
