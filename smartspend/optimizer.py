"""Rule-based grocery basket optimizers for the SmartSpend MVP."""

from dataclasses import dataclass

from smartspend.models import BasketItem, Store, StoreResult
from smartspend.route_service import RouteResult

OPTIMIZATION_CHEAPEST_BASKET = "cheapest_basket"
OPTIMIZATION_LOWEST_TOTAL_COST = "lowest_total_cost"
OPTIMIZATION_BEST_BUDGET_FIT = "best_budget_fit"
OPTIMIZATION_BALANCED = "balanced"
OPTIMIZATION_MODE_ALIASES = {
    OPTIMIZATION_CHEAPEST_BASKET: OPTIMIZATION_CHEAPEST_BASKET,
    "Cheapest basket only": OPTIMIZATION_CHEAPEST_BASKET,
    OPTIMIZATION_LOWEST_TOTAL_COST: OPTIMIZATION_LOWEST_TOTAL_COST,
    "Lowest total cost including travel": OPTIMIZATION_LOWEST_TOTAL_COST,
    OPTIMIZATION_BEST_BUDGET_FIT: OPTIMIZATION_BEST_BUDGET_FIT,
    "Best budget fit": OPTIMIZATION_BEST_BUDGET_FIT,
    OPTIMIZATION_BALANCED: OPTIMIZATION_BALANCED,
    "Balanced recommendation": OPTIMIZATION_BALANCED,
}

TRANSPORT_WALKING = "walking"
TRANSPORT_PUBLIC_TRANSPORT = "public_transport"
TRANSPORT_CAR = "car"
TRANSPORT_MODE_ALIASES = {
    TRANSPORT_WALKING: TRANSPORT_WALKING,
    "Walking": TRANSPORT_WALKING,
    TRANSPORT_PUBLIC_TRANSPORT: TRANSPORT_PUBLIC_TRANSPORT,
    "Public transport": TRANSPORT_PUBLIC_TRANSPORT,
    TRANSPORT_CAR: TRANSPORT_CAR,
    "Car": TRANSPORT_CAR,
}


@dataclass(frozen=True)
class PremiumStoreResult:
    """Detailed deterministic recommendation result for one store."""

    store: Store
    rank: int
    product_total_huf: int
    unavailable_items: tuple[str, ...]
    confidence_score: int
    travel_monetary_cost_huf: int
    travel_time_cost_huf: int
    net_total_cost_huf: int
    remaining_budget_after_purchase_huf: int
    overspend_amount_huf: int
    savings_vs_usual_store_huf: int
    savings_vs_most_expensive_store_huf: int
    within_max_travel_time: bool
    route_source: str
    distance_km: float
    travel_time_min: int
    can_win: bool
    mode_score: int

    @property
    def product_total(self) -> int:
        return self.product_total_huf

    @property
    def travel_monetary_cost(self) -> int:
        return self.travel_monetary_cost_huf

    @property
    def travel_time_cost(self) -> int:
        return self.travel_time_cost_huf

    @property
    def net_total_cost(self) -> int:
        return self.net_total_cost_huf

    @property
    def remaining_budget_after_purchase(self) -> int:
        return self.remaining_budget_after_purchase_huf

    @property
    def overspend_amount(self) -> int:
        return self.overspend_amount_huf

    @property
    def savings_vs_usual_store(self) -> int:
        return self.savings_vs_usual_store_huf

    @property
    def savings_vs_most_expensive_store(self) -> int:
        return self.savings_vs_most_expensive_store_huf


@dataclass(frozen=True)
class PremiumOptimizationResult:
    """Ranked premium recommendation output."""

    mode: str
    results: tuple[PremiumStoreResult, ...]
    recommended: PremiumStoreResult | None


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


def optimize_premium_basket(
    stores: list[Store],
    basket: list[BasketItem],
    monthly_budget_huf: int,
    already_spent_huf: int,
    max_travel_minutes: int,
    usual_store_id: str,
    routes_by_store_id: dict[str, RouteResult],
    optimization_mode: str = OPTIMIZATION_BALANCED,
    transport_mode: str = TRANSPORT_WALKING,
    travel_cost_per_km_huf: int = 0,
    value_of_time_huf_per_min: int = 0,
    substitutions_accepted: bool = False,
) -> PremiumOptimizationResult:
    """Calculate detailed deterministic store rankings for V2."""

    normalized_optimization_mode = normalize_optimization_mode(optimization_mode)
    normalized_transport_mode = normalize_transport_mode(transport_mode)
    validate_premium_inputs(
        stores=stores,
        basket=basket,
        monthly_budget_huf=monthly_budget_huf,
        already_spent_huf=already_spent_huf,
        max_travel_minutes=max_travel_minutes,
        routes_by_store_id=routes_by_store_id,
        optimization_mode=normalized_optimization_mode,
        transport_mode=normalized_transport_mode,
        travel_cost_per_km_huf=travel_cost_per_km_huf,
        value_of_time_huf_per_min=value_of_time_huf_per_min,
    )

    usual_store = get_store_by_id(stores, usual_store_id)
    raw_results = [
        calculate_premium_store_result(
            store=store,
            basket=basket,
            monthly_budget_huf=monthly_budget_huf,
            already_spent_huf=already_spent_huf,
            max_travel_minutes=max_travel_minutes,
            route=routes_by_store_id[store.id],
            transport_mode=normalized_transport_mode,
            travel_cost_per_km_huf=travel_cost_per_km_huf,
            value_of_time_huf_per_min=value_of_time_huf_per_min,
            substitutions_accepted=substitutions_accepted,
        )
        for store in stores
    ]

    usual_result = next(result for result in raw_results if result.store.id == usual_store.id)
    most_expensive_net_total = max(result.net_total_cost_huf for result in raw_results)
    enriched_results = [
        replace_savings(
            result=result,
            savings_vs_usual_store_huf=usual_result.net_total_cost_huf
            - result.net_total_cost_huf,
            savings_vs_most_expensive_store_huf=most_expensive_net_total
            - result.net_total_cost_huf,
        )
        for result in raw_results
    ]

    ranked_results = rank_premium_results(enriched_results, normalized_optimization_mode)
    return PremiumOptimizationResult(
        mode=normalized_optimization_mode,
        results=tuple(ranked_results),
        recommended=next((result for result in ranked_results if result.can_win), None),
    )


def calculate_premium_store_result(
    store: Store,
    basket: list[BasketItem],
    monthly_budget_huf: int,
    already_spent_huf: int,
    max_travel_minutes: int,
    route: RouteResult,
    transport_mode: str,
    travel_cost_per_km_huf: int,
    value_of_time_huf_per_min: int,
    substitutions_accepted: bool,
) -> PremiumStoreResult:
    """Calculate all premium fields for one store."""

    product_total_huf = 0
    unavailable_items = []
    for item in basket:
        if item.quantity < 0:
            raise ValueError("Basket item quantity cannot be negative.")

        item_price = store.prices_huf.get(item.product_id)
        if item_price is None:
            unavailable_items.append(item.product_id)
            continue

        product_total_huf += item_price * item.quantity

    travel_monetary_cost_huf = calculate_travel_monetary_cost(
        distance_km=route.distance_km,
        transport_mode=transport_mode,
        travel_cost_per_km_huf=travel_cost_per_km_huf,
    )
    travel_time_cost_huf = route.travel_minutes * value_of_time_huf_per_min
    net_total_cost_huf = (
        product_total_huf + travel_monetary_cost_huf + travel_time_cost_huf
    )
    remaining_budget_huf = monthly_budget_huf - already_spent_huf - product_total_huf
    overspend_amount_huf = max(0, -remaining_budget_huf)
    within_max_travel_time = route.travel_minutes <= max_travel_minutes
    can_win = within_max_travel_time and (
        substitutions_accepted or len(unavailable_items) == 0
    )

    return PremiumStoreResult(
        store=store,
        rank=0,
        product_total_huf=product_total_huf,
        unavailable_items=tuple(unavailable_items),
        confidence_score=calculate_confidence_score(
            unavailable_count=len(unavailable_items),
            within_max_travel_time=within_max_travel_time,
            route_source=route.route_source,
        ),
        travel_monetary_cost_huf=travel_monetary_cost_huf,
        travel_time_cost_huf=travel_time_cost_huf,
        net_total_cost_huf=net_total_cost_huf,
        remaining_budget_after_purchase_huf=remaining_budget_huf,
        overspend_amount_huf=overspend_amount_huf,
        savings_vs_usual_store_huf=0,
        savings_vs_most_expensive_store_huf=0,
        within_max_travel_time=within_max_travel_time,
        route_source=route.route_source,
        distance_km=route.distance_km,
        travel_time_min=route.travel_minutes,
        can_win=can_win,
        mode_score=0,
    )


def calculate_travel_monetary_cost(
    distance_km: float,
    transport_mode: str,
    travel_cost_per_km_huf: int,
) -> int:
    """Calculate monetary route cost from the selected transport mode."""

    if transport_mode == TRANSPORT_WALKING:
        return 0

    if transport_mode in {TRANSPORT_PUBLIC_TRANSPORT, TRANSPORT_CAR}:
        return round(distance_km * travel_cost_per_km_huf)

    raise ValueError(f"Unknown transport mode '{transport_mode}'.")


def calculate_confidence_score(
    unavailable_count: int,
    within_max_travel_time: bool,
    route_source: str,
) -> int:
    """Calculate an explainable confidence score from deterministic factors."""

    score = 100
    score -= unavailable_count * 25
    if not within_max_travel_time:
        score -= 10
    if route_source == "Simulated":
        score -= 5

    return max(0, min(100, score))


def rank_premium_results(
    results: list[PremiumStoreResult],
    optimization_mode: str,
) -> list[PremiumStoreResult]:
    """Rank stores by the selected deterministic optimization mode."""

    scored_results = [
        set_mode_score(result, calculate_mode_score(result, optimization_mode))
        for result in results
    ]
    sorted_results = sorted(
        scored_results,
        key=lambda result: (
            not result.can_win,
            result.mode_score,
            result.net_total_cost_huf,
            result.travel_time_min,
            result.store.name,
        ),
    )
    return [
        set_rank(result, rank)
        for rank, result in enumerate(sorted_results, start=1)
    ]


def calculate_mode_score(
    result: PremiumStoreResult,
    optimization_mode: str,
) -> int:
    """Return the primary score for one optimization mode."""

    if optimization_mode == OPTIMIZATION_CHEAPEST_BASKET:
        return result.product_total_huf
    if optimization_mode == OPTIMIZATION_LOWEST_TOTAL_COST:
        return result.net_total_cost_huf
    if optimization_mode == OPTIMIZATION_BEST_BUDGET_FIT:
        return result.overspend_amount_huf * 10_000 - result.remaining_budget_after_purchase_huf
    if optimization_mode == OPTIMIZATION_BALANCED:
        return (
            result.net_total_cost_huf
            + result.overspend_amount_huf * 2
            + max(0, 100 - result.confidence_score) * 100
        )

    raise ValueError(f"Unknown optimization mode '{optimization_mode}'.")


def replace_savings(
    result: PremiumStoreResult,
    savings_vs_usual_store_huf: int,
    savings_vs_most_expensive_store_huf: int,
) -> PremiumStoreResult:
    """Return a result copy with savings fields filled in."""

    return PremiumStoreResult(
        store=result.store,
        rank=result.rank,
        product_total_huf=result.product_total_huf,
        unavailable_items=result.unavailable_items,
        confidence_score=result.confidence_score,
        travel_monetary_cost_huf=result.travel_monetary_cost_huf,
        travel_time_cost_huf=result.travel_time_cost_huf,
        net_total_cost_huf=result.net_total_cost_huf,
        remaining_budget_after_purchase_huf=result.remaining_budget_after_purchase_huf,
        overspend_amount_huf=result.overspend_amount_huf,
        savings_vs_usual_store_huf=savings_vs_usual_store_huf,
        savings_vs_most_expensive_store_huf=savings_vs_most_expensive_store_huf,
        within_max_travel_time=result.within_max_travel_time,
        route_source=result.route_source,
        distance_km=result.distance_km,
        travel_time_min=result.travel_time_min,
        can_win=result.can_win,
        mode_score=result.mode_score,
    )


def set_mode_score(result: PremiumStoreResult, mode_score: int) -> PremiumStoreResult:
    """Return a result copy with its mode score set."""

    return PremiumStoreResult(
        store=result.store,
        rank=result.rank,
        product_total_huf=result.product_total_huf,
        unavailable_items=result.unavailable_items,
        confidence_score=result.confidence_score,
        travel_monetary_cost_huf=result.travel_monetary_cost_huf,
        travel_time_cost_huf=result.travel_time_cost_huf,
        net_total_cost_huf=result.net_total_cost_huf,
        remaining_budget_after_purchase_huf=result.remaining_budget_after_purchase_huf,
        overspend_amount_huf=result.overspend_amount_huf,
        savings_vs_usual_store_huf=result.savings_vs_usual_store_huf,
        savings_vs_most_expensive_store_huf=result.savings_vs_most_expensive_store_huf,
        within_max_travel_time=result.within_max_travel_time,
        route_source=result.route_source,
        distance_km=result.distance_km,
        travel_time_min=result.travel_time_min,
        can_win=result.can_win,
        mode_score=mode_score,
    )


def set_rank(result: PremiumStoreResult, rank: int) -> PremiumStoreResult:
    """Return a result copy with its final rank set."""

    return PremiumStoreResult(
        store=result.store,
        rank=rank,
        product_total_huf=result.product_total_huf,
        unavailable_items=result.unavailable_items,
        confidence_score=result.confidence_score,
        travel_monetary_cost_huf=result.travel_monetary_cost_huf,
        travel_time_cost_huf=result.travel_time_cost_huf,
        net_total_cost_huf=result.net_total_cost_huf,
        remaining_budget_after_purchase_huf=result.remaining_budget_after_purchase_huf,
        overspend_amount_huf=result.overspend_amount_huf,
        savings_vs_usual_store_huf=result.savings_vs_usual_store_huf,
        savings_vs_most_expensive_store_huf=result.savings_vs_most_expensive_store_huf,
        within_max_travel_time=result.within_max_travel_time,
        route_source=result.route_source,
        distance_km=result.distance_km,
        travel_time_min=result.travel_time_min,
        can_win=result.can_win,
        mode_score=result.mode_score,
    )


def validate_premium_inputs(
    stores: list[Store],
    basket: list[BasketItem],
    monthly_budget_huf: int,
    already_spent_huf: int,
    max_travel_minutes: int,
    routes_by_store_id: dict[str, RouteResult],
    optimization_mode: str,
    transport_mode: str,
    travel_cost_per_km_huf: int,
    value_of_time_huf_per_min: int,
) -> None:
    """Validate premium optimizer inputs with clear deterministic errors."""

    if not stores:
        raise ValueError("At least one store is required.")
    if not basket:
        raise ValueError("At least one basket item is required.")
    if monthly_budget_huf < 0:
        raise ValueError("Monthly budget cannot be negative.")
    if already_spent_huf < 0:
        raise ValueError("Already spent amount cannot be negative.")
    if max_travel_minutes < 0:
        raise ValueError("Maximum travel time cannot be negative.")
    if travel_cost_per_km_huf < 0:
        raise ValueError("Travel cost per km cannot be negative.")
    if value_of_time_huf_per_min < 0:
        raise ValueError("Value of time cannot be negative.")
    if optimization_mode not in set(OPTIMIZATION_MODE_ALIASES.values()):
        raise ValueError(f"Unknown optimization mode '{optimization_mode}'.")
    if transport_mode not in set(TRANSPORT_MODE_ALIASES.values()):
        raise ValueError(f"Unknown transport mode '{transport_mode}'.")

    missing_routes = [store.id for store in stores if store.id not in routes_by_store_id]
    if missing_routes:
        raise ValueError(f"Missing routes for stores: {', '.join(missing_routes)}.")


def normalize_optimization_mode(optimization_mode: str) -> str:
    """Map human-readable mode labels to stable internal constants."""

    if optimization_mode in OPTIMIZATION_MODE_ALIASES:
        return OPTIMIZATION_MODE_ALIASES[optimization_mode]

    raise ValueError(f"Unknown optimization mode '{optimization_mode}'.")


def normalize_transport_mode(transport_mode: str) -> str:
    """Map human-readable transport labels to stable internal constants."""

    if transport_mode in TRANSPORT_MODE_ALIASES:
        return TRANSPORT_MODE_ALIASES[transport_mode]

    raise ValueError(f"Unknown transport mode '{transport_mode}'.")
