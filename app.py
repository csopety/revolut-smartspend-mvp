"""Streamlit UI for the SmartSpend MVP."""

from dataclasses import replace

import pandas as pd
import streamlit as st

from smartspend.data_generator import get_grocery_dataset
from smartspend.models import BasketItem, Product, Store, StoreResult
from smartspend.optimizer import optimize_basket

AVERAGE_CITY_SPEED_KM_PER_MINUTE = 0.25


def format_huf(amount: int) -> str:
    """Format Hungarian forint values for display."""

    return f"{amount:,.0f} HUF".replace(",", " ")


def estimate_distance_km(store: Store) -> float:
    """Estimate distance from travel time for the simulated demo."""

    return round(store.travel_minutes * AVERAGE_CITY_SPEED_KM_PER_MINUTE, 1)


def apply_travel_cost_per_km(stores: list[Store], travel_cost_per_km_huf: int) -> list[Store]:
    """Return store copies with travel cost recalculated from the UI input."""

    adjusted_stores = []
    for store in stores:
        travel_cost_huf = round(estimate_distance_km(store) * travel_cost_per_km_huf)
        adjusted_stores.append(replace(store, travel_cost_huf=travel_cost_huf))

    return adjusted_stores


def build_basket(products: list[Product], quantities: dict[str, int]) -> list[BasketItem]:
    """Create a basket from UI quantities, skipping zero-quantity products."""

    return [
        BasketItem(product_id=product.id, quantity=quantities[product.id])
        for product in products
        if quantities[product.id] > 0
    ]


def result_table_rows(results: list[StoreResult]) -> list[dict[str, str | int]]:
    """Convert optimizer results into table-ready rows."""

    return [
        {
            "Rank": result.rank,
            "Store": result.store.name,
            "Area": result.store.neighborhood,
            "Travel": f"{result.store.travel_minutes} min",
            "Eligible": "Yes" if result.is_eligible else "No",
            "Basket price": format_huf(result.basket_price_huf),
            "Travel cost": format_huf(result.travel_cost_huf),
            "Effective total": format_huf(result.effective_total_cost_huf),
            "Savings vs usual": format_huf(result.savings_vs_usual_huf),
            "Budget status": "Fits" if result.fits_budget else "Over budget",
        }
        for result in results
    ]


def product_price_rows(products: list[Product], stores: list[Store]) -> list[dict[str, str]]:
    """Create a simple product price comparison table."""

    rows = []
    for product in products:
        row = {
            "Product": f"{product.name} ({product.unit})",
            "Category": product.category,
        }
        for store in stores:
            row[store.chain] = format_huf(store.prices_huf[product.id])
        rows.append(row)

    return rows


def find_recommended_result(results: list[StoreResult]) -> StoreResult | None:
    """Return the first eligible result, if one exists."""

    return next((result for result in results if result.is_eligible), None)


def render_recommendation(recommendation: StoreResult) -> None:
    """Display the recommended store summary."""

    st.subheader("Recommended store")

    st.success(f"{recommendation.store.name} in {recommendation.store.neighborhood}")

    metric_columns = st.columns(4)
    metric_columns[0].metric("Basket price", format_huf(recommendation.basket_price_huf))
    metric_columns[1].metric("Travel cost", format_huf(recommendation.travel_cost_huf))
    metric_columns[2].metric(
        "Effective total",
        format_huf(recommendation.effective_total_cost_huf),
    )
    metric_columns[3].metric(
        "Expected savings",
        format_huf(max(recommendation.savings_vs_usual_huf, 0)),
    )

    budget_message = (
        f"After this basket, estimated remaining grocery budget is "
        f"{format_huf(recommendation.remaining_budget_huf)}."
    )
    if recommendation.fits_budget:
        st.info(budget_message)
    else:
        st.warning(budget_message)


def main() -> None:
    """Run the Streamlit application."""

    st.set_page_config(
        page_title="SmartSpend MVP",
        page_icon="S",
        layout="wide",
    )

    dataset = get_grocery_dataset()
    default_quantities = {
        item.product_id: item.quantity for item in dataset.default_basket
    }

    if "smartspend_pocket_huf" not in st.session_state:
        st.session_state.smartspend_pocket_huf = 0

    st.title("SmartSpend Grocery Optimizer")
    st.caption(
        "Presentation MVP using simulated Budapest II grocery prices, travel times, "
        "and distances. No banking, payment, maps, or retailer integrations are used."
    )

    with st.sidebar:
        st.header("Budget")
        monthly_budget_huf = st.number_input(
            "Monthly grocery budget",
            min_value=0,
            value=120_000,
            step=5_000,
            format="%d",
        )
        already_spent_huf = st.number_input(
            "Already spent this month",
            min_value=0,
            value=40_000,
            step=5_000,
            format="%d",
        )

        st.header("Trip")
        usual_store_id = st.selectbox(
            "Usual store",
            options=[store.id for store in dataset.stores],
            format_func=lambda store_id: next(
                store.name for store in dataset.stores if store.id == store_id
            ),
            index=2,
        )
        max_travel_minutes = st.slider(
            "Maximum travel time",
            min_value=5,
            max_value=30,
            value=15,
            step=1,
        )
        travel_cost_per_km_huf = st.number_input(
            "Travel cost per km",
            min_value=0,
            value=120,
            step=10,
            format="%d",
        )

    adjusted_stores = apply_travel_cost_per_km(
        stores=dataset.stores,
        travel_cost_per_km_huf=travel_cost_per_km_huf,
    )

    st.subheader("Basket")
    quantities = {}
    for category in sorted({product.category for product in dataset.products}):
        st.markdown(f"**{category}**")
        columns = st.columns(2)
        category_products = [
            product for product in dataset.products if product.category == category
        ]

        for index, product in enumerate(category_products):
            with columns[index % 2]:
                quantities[product.id] = st.number_input(
                    f"{product.name} ({product.unit})",
                    min_value=0,
                    max_value=20,
                    value=default_quantities.get(product.id, 0),
                    step=1,
                    key=f"quantity_{product.id}",
                )

    basket = build_basket(dataset.products, quantities)

    if not basket:
        st.warning("Add at least one basket item to compare stores.")
        return

    results = optimize_basket(
        stores=adjusted_stores,
        basket=basket,
        monthly_budget_huf=monthly_budget_huf,
        already_spent_huf=already_spent_huf,
        max_travel_minutes=max_travel_minutes,
        usual_store_id=usual_store_id,
    )
    recommendation = find_recommended_result(results)

    if recommendation is None:
        st.error("No store is within the selected maximum travel time.")
    else:
        render_recommendation(recommendation)

        savings_to_move_huf = max(recommendation.savings_vs_usual_huf, 0)
        if st.button(
            "Move savings to SmartSpend Pocket",
            disabled=savings_to_move_huf == 0,
            type="primary",
        ):
            st.session_state.smartspend_pocket_huf += savings_to_move_huf
            st.success(
                f"Moved {format_huf(savings_to_move_huf)} to SmartSpend Pocket."
            )

    st.metric(
        "SmartSpend Pocket balance",
        format_huf(st.session_state.smartspend_pocket_huf),
    )

    st.subheader("Ranked alternatives")
    st.dataframe(
        pd.DataFrame(result_table_rows(results)),
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("Store prices and travel assumptions"):
        st.dataframe(
            pd.DataFrame(product_price_rows(dataset.products, adjusted_stores)),
            hide_index=True,
            use_container_width=True,
        )

        travel_rows = [
            {
                "Store": store.name,
                "Area": store.neighborhood,
                "Estimated distance": f"{estimate_distance_km(store)} km",
                "Travel time": f"{store.travel_minutes} min",
                "Travel cost": format_huf(store.travel_cost_huf),
            }
            for store in adjusted_stores
        ]
        st.dataframe(pd.DataFrame(travel_rows), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
