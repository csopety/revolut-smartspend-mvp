"""Premium Streamlit UI for the SmartSpend V2 MVP."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from smartspend.agentic_explainer import explain_recommendation
from smartspend.basket import Basket, add_product, edit_quantity, remove_product
from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database, reset_demo_data
from smartspend.favorites import (
    add_previous_list_to_favorites,
    delete_favorite,
    get_favorite_items,
    list_favorites,
    reload_favorite_as_current_basket,
    save_current_basket_as_favorite,
)
from smartspend.formatting import format_huf
from smartspend.insights import calculate_spending_insights, load_historical_months
from smartspend.models import BasketItem
from smartspend.optimizer import (
    OPTIMIZATION_BALANCED,
    OPTIMIZATION_BEST_BUDGET_FIT,
    OPTIMIZATION_CHEAPEST_BASKET,
    OPTIMIZATION_LOWEST_TOTAL_COST,
    TRANSPORT_CAR,
    TRANSPORT_PUBLIC_TRANSPORT,
    TRANSPORT_WALKING,
    PremiumOptimizationResult,
    PremiumStoreResult,
    optimize_premium_basket,
)
from smartspend.product_search import search_products
from smartspend.route_service import get_route
from smartspend.savings import list_savings_goals, simulate_save_difference_to_goal
from smartspend.transactions import (
    finalize_purchase,
    get_previous_list_items,
    get_spent_so_far,
    list_previous_lists,
    load_current_basket,
    reload_previous_list_as_current_basket,
    save_current_basket,
)
from smartspend.warnings import BudgetWarning, evaluate_budget_warnings

CONSENT_DISABLED_MESSAGE = (
    "Recommendation is disabled until you consent to using simulated supported "
    "store and price data for this planning calculation."
)


def main() -> None:
    """Run the Streamlit application."""

    st.set_page_config(page_title="SmartSpend V2 MVP", page_icon="S", layout="wide")
    apply_page_styles()
    ensure_demo_database()

    profile = load_user_profile()
    current_basket = load_current_basket()

    render_header()
    render_disclaimer()

    settings = render_user_settings(profile)
    render_spending_tracker(settings)

    consent = st.checkbox(
        "I consent to use simulated supported store, route, price, transaction, "
        "savings, and historical data for this local MVP calculation.",
        value=True,
    )
    if not consent:
        st.info(CONSENT_DISABLED_MESSAGE)

    current_basket = render_basket_builder(current_basket)

    optimization = None
    warnings = build_warnings(settings)
    if consent and current_basket.lines:
        optimization = build_recommendation(current_basket, settings)
        render_recommendation(optimization)
    elif consent:
        st.info("Add grocery products with search to estimate store recommendations.")

    render_finalization(current_basket, optimization, settings)
    render_savings_goals(optimization)
    render_previous_lists()
    render_favorites(current_basket)
    render_spending_insights()
    render_warning_messages(warnings)
    render_agentic_explanation(optimization, warnings)
    render_reset_demo_data()


def apply_page_styles() -> None:
    """Apply restrained fintech-style Streamlit CSS."""

    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        [data-testid="stMetricValue"] {font-size: 1.45rem;}
        div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the app header."""

    st.title("SmartSpend")
    st.caption(
        "Estimated grocery planning for Budapest II, based on simulated supported "
        "store and price data."
    )


def render_disclaimer() -> None:
    """Render the simulated MVP disclaimer."""

    st.warning(
        "Simulated MVP disclaimer: all banking, transactions, grocery prices, route "
        "data, savings movements, and historical spending data are simulated. This "
        "app does not connect to Revolut, banks, payment systems, retailer APIs, or "
        "real user financial accounts."
    )


def render_user_settings(profile: dict[str, int | str]) -> dict[str, int | str | bool]:
    """Render user settings and return calculation inputs."""

    st.subheader("User settings")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        monthly_budget_huf = st.number_input(
            "Monthly grocery budget",
            min_value=1,
            value=int(profile["monthly_grocery_budget_huf"]),
            step=5_000,
            format="%d",
        )
    with col2:
        max_travel_minutes = st.number_input(
            "Max travel time",
            min_value=1,
            value=int(profile["max_travel_minutes"]),
            step=1,
            format="%d",
        )
    with col3:
        travel_cost_per_km_huf = st.number_input(
            "Estimated travel cost per km",
            min_value=0,
            value=int(profile["travel_cost_per_km_huf"]),
            step=10,
            format="%d",
        )
    with col4:
        value_of_time_huf_per_min = st.number_input(
            "Estimated time value per min",
            min_value=0,
            value=35,
            step=5,
            format="%d",
        )

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        store_rows = load_store_rows()
        usual_store_options = [store["id"] for store in store_rows]
        usual_store_id = st.selectbox(
            "Usual store",
            options=usual_store_options,
            format_func=store_name_for_id,
            index=usual_store_options.index(profile["usual_store_id"]),
        )
    with col6:
        optimization_mode = st.selectbox(
            "Optimization mode",
            options=[
                OPTIMIZATION_BALANCED,
                OPTIMIZATION_LOWEST_TOTAL_COST,
                OPTIMIZATION_CHEAPEST_BASKET,
                OPTIMIZATION_BEST_BUDGET_FIT,
            ],
            format_func={
                OPTIMIZATION_BALANCED: "Balanced recommendation",
                OPTIMIZATION_LOWEST_TOTAL_COST: "Lowest total cost including travel",
                OPTIMIZATION_CHEAPEST_BASKET: "Cheapest basket only",
                OPTIMIZATION_BEST_BUDGET_FIT: "Best budget fit",
            }.get,
        )
    with col7:
        transport_mode = st.selectbox(
            "Travel mode",
            options=[TRANSPORT_WALKING, TRANSPORT_PUBLIC_TRANSPORT, TRANSPORT_CAR],
            format_func={
                TRANSPORT_WALKING: "Walking",
                TRANSPORT_PUBLIC_TRANSPORT: "Public transport",
                TRANSPORT_CAR: "Car",
            }.get,
        )
    with col8:
        use_google_maps = st.checkbox(
            "Use Google Maps if configured",
            value=False,
            help="The app falls back to simulated routes if no key exists or the API fails.",
        )

    return {
        "monthly_budget_huf": monthly_budget_huf,
        "already_spent_huf": get_spent_so_far(),
        "max_travel_minutes": max_travel_minutes,
        "travel_cost_per_km_huf": travel_cost_per_km_huf,
        "value_of_time_huf_per_min": value_of_time_huf_per_min,
        "usual_store_id": usual_store_id,
        "optimization_mode": optimization_mode,
        "transport_mode": transport_mode,
        "use_google_maps": use_google_maps,
    }


def render_spending_tracker(settings: dict[str, int | str | bool]) -> None:
    """Render spending tracker with progress and status."""

    st.subheader("Spending tracker")
    spent = int(settings["already_spent_huf"])
    budget = int(settings["monthly_budget_huf"])
    ratio = min(spent / budget, 1.0)
    remaining = budget - spent

    cols = st.columns(4)
    cols[0].metric("Simulated spent so far", format_huf(spent))
    cols[1].metric("Monthly budget", format_huf(budget))
    cols[2].metric("Estimated remaining", format_huf(remaining))
    cols[3].metric("Budget used", f"{spent / budget:.0%}")
    st.progress(ratio)
    if spent >= budget:
        st.error("Status: simulated spending appears to be at or above budget.")
    elif spent / budget >= 0.75:
        st.warning("Status: simulated spending appears to be close to budget.")
    else:
        st.success("Status: simulated spending appears to be within budget.")


def render_basket_builder(current_basket: Basket) -> Basket:
    """Render search-first grocery basket builder."""

    st.subheader("Search-first grocery basket builder")
    st.caption("No category dropdown is used. Search by English or Hungarian product terms.")

    query = st.text_input(
        "Type to search products",
        placeholder="Try cucu, ubi, tej, csir, trap...",
    )
    if query:
        for result in search_products(query, limit=6):
            cols = st.columns([4, 2, 1])
            cols[0].write(f"{result.display_name} ({result.hungarian_name})")
            cols[1].caption(f"{result.unit} - estimated catalog item")
            if cols[2].button("Add", key=f"add_{result.product_id}"):
                current_basket = add_product(current_basket, result.product_id)
                save_current_basket(current_basket)
                st.rerun()

    st.markdown("**Current planning basket**")
    if not current_basket.lines:
        st.info("Your planning basket is empty. Planning does not update spending.")
        return current_basket

    lookup = load_product_lookup()
    for line in current_basket.lines:
        product = lookup.get(line.product_id, {"name": line.product_id, "unit": ""})
        cols = st.columns([4, 2, 1, 1])
        cols[0].write(f"{product['name']} ({product['unit']})")
        new_quantity = cols[1].number_input(
            "Qty",
            min_value=1,
            max_value=50,
            value=line.quantity,
            key=f"qty_{line.product_id}",
            label_visibility="collapsed",
        )
        if cols[2].button("Update", key=f"update_{line.product_id}"):
            current_basket = edit_quantity(current_basket, line.product_id, new_quantity)
            save_current_basket(current_basket)
            st.rerun()
        if cols[3].button("Remove", key=f"remove_{line.product_id}"):
            current_basket = remove_product(current_basket, line.product_id)
            save_current_basket(current_basket)
            st.rerun()

    if st.button("Clear planning basket"):
        save_current_basket(Basket())
        st.rerun()

    return current_basket


def build_recommendation(
    current_basket: Basket,
    settings: dict[str, int | str | bool],
) -> PremiumOptimizationResult:
    """Build a premium recommendation from persisted basket inputs."""

    product_ids = [line.product_id for line in current_basket.lines]
    stores = load_stores_for_product_ids(product_ids)
    routes = {
        store.id: get_route(
            store.id,
            use_google_maps=bool(settings["use_google_maps"]),
        )
        for store in stores
    }
    basket_items = [
        BasketItem(product_id=line.product_id, quantity=line.quantity)
        for line in current_basket.lines
    ]
    return optimize_premium_basket(
        stores=stores,
        basket=basket_items,
        monthly_budget_huf=int(settings["monthly_budget_huf"]),
        already_spent_huf=int(settings["already_spent_huf"]),
        max_travel_minutes=int(settings["max_travel_minutes"]),
        usual_store_id=str(settings["usual_store_id"]),
        routes_by_store_id=routes,
        optimization_mode=str(settings["optimization_mode"]),
        transport_mode=str(settings["transport_mode"]),
        travel_cost_per_km_huf=int(settings["travel_cost_per_km_huf"]),
        value_of_time_huf_per_min=int(settings["value_of_time_huf_per_min"]),
        substitutions_accepted=False,
    )


def render_recommendation(optimization: PremiumOptimizationResult) -> None:
    """Render store recommendation and ranked alternatives."""

    st.subheader("Store recommendation")
    recommendation = optimization.recommended
    if recommendation is None:
        st.error(
            "No store appears eligible to win based on simulated supported store and "
            "price data."
        )
    else:
        st.success(
            f"Estimated recommendation: {recommendation.store.name}. This appears "
            "to be the best option for the selected mode based on simulated supported "
            "store and price data."
        )
        cols = st.columns(5)
        cols[0].metric("Product total", format_huf(recommendation.product_total_huf))
        cols[1].metric("Travel money", format_huf(recommendation.travel_monetary_cost_huf))
        cols[2].metric("Time cost", format_huf(recommendation.travel_time_cost_huf))
        cols[3].metric("Net total", format_huf(recommendation.net_total_cost_huf))
        cols[4].metric("Confidence", f"{recommendation.confidence_score}/100")

    st.dataframe(
        pd.DataFrame([premium_result_row(result) for result in optimization.results]),
        hide_index=True,
        width="stretch",
    )


def render_finalization(
    current_basket: Basket,
    optimization: PremiumOptimizationResult | None,
    settings: dict[str, int | str | bool],
) -> None:
    """Render simulated purchase finalization."""

    st.subheader("Finalize grocery purchase")
    st.caption(
        "Finalization is simulated. Planning and recommendation runs do not update "
        "spending; only this action updates simulated spent so far."
    )
    if optimization is None or optimization.recommended is None or not current_basket.lines:
        st.button("Finalize simulated purchase", disabled=True)
        return

    recommendation = optimization.recommended
    include_travel = st.checkbox(
        "Count estimated travel monetary cost as real grocery spending for this simulation",
        value=False,
    )
    if st.button("Finalize simulated purchase", type="primary"):
        try:
            result = finalize_purchase(
                store_id=recommendation.store.id,
                basket=current_basket,
                travel_monetary_cost_huf=recommendation.travel_monetary_cost_huf,
                travel_time_cost_huf=recommendation.travel_time_cost_huf,
                include_travel_monetary_cost=include_travel,
                route_source=recommendation.route_source,
                list_name=f"{recommendation.store.chain} simulated purchase",
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.success(result.success_message)
            st.caption(
                "Travel-time opportunity cost was not counted as real spending. "
                "No external payment action occurred."
            )
            st.rerun()


def render_savings_goals(optimization: PremiumOptimizationResult | None) -> None:
    """Render simulated savings goals."""

    st.subheader("Simulated savings goals")
    goals = list_savings_goals()
    goal_cols = st.columns(3)
    for index, goal in enumerate(goals):
        with goal_cols[index % 3]:
            st.metric(goal.name, format_huf(goal.current_amount_huf))
            st.progress(min(goal.current_amount_huf / goal.target_amount_huf, 1.0))

    positive_savings = 0
    if optimization and optimization.recommended:
        positive_savings = max(optimization.recommended.savings_vs_usual_store_huf, 0)

    selected_goal_id = st.selectbox(
        "Select simulated savings goal",
        options=[goal.id for goal in goals],
        format_func=lambda goal_id: next(goal.name for goal in goals if goal.id == goal_id),
    )
    if st.button(
        "Simulate saving the SmartSpend difference",
        disabled=positive_savings <= 0,
    ):
        movement = simulate_save_difference_to_goal(selected_goal_id, positive_savings)
        st.success(
            f"Simulated savings movement: {format_huf(movement.amount_huf)} to "
            f"{movement.goal_name}. This is not a real money movement."
        )
        st.rerun()


def render_previous_lists() -> None:
    """Render previous grocery lists."""

    st.subheader("Previous grocery lists")
    previous_lists = list_previous_lists()
    if not previous_lists:
        st.info("No finalized simulated grocery lists yet.")
        return

    for previous in previous_lists:
        with st.expander(f"{previous.name} - {previous.created_at}"):
            items = get_previous_list_items(previous.id)
            st.dataframe(
                pd.DataFrame([basket_line_row(line) for line in items]),
                hide_index=True,
                width="stretch",
            )
            cols = st.columns(2)
            if cols[0].button("Reload as current basket", key=f"reload_prev_{previous.id}"):
                reload_previous_list_as_current_basket(previous.id)
                st.success("Previous list reloaded for planning. Spending was not updated.")
                st.rerun()
            if cols[1].button("Add to favorites", key=f"fav_prev_{previous.id}"):
                add_previous_list_to_favorites(previous.id)
                st.success("Previous list saved as a simulated favorite.")
                st.rerun()


def render_favorites(current_basket: Basket) -> None:
    """Render favorite grocery lists."""

    st.subheader("Favorite grocery lists")
    favorite_name = st.text_input("Favorite name", placeholder="Weekend basics")
    if st.button("Save current basket as favorite", disabled=not current_basket.lines):
        try:
            save_current_basket_as_favorite(current_basket, favorite_name)
        except ValueError as error:
            st.error(str(error))
        else:
            st.success("Current planning basket saved as simulated favorite.")
            st.rerun()

    favorites = list_favorites()
    if not favorites:
        st.info("No simulated favorite lists yet.")
        return

    for favorite in favorites:
        with st.expander(f"{favorite.name} - {favorite.created_at}"):
            items = get_favorite_items(favorite.id)
            st.dataframe(
                pd.DataFrame([basket_line_row(line) for line in items]),
                hide_index=True,
                width="stretch",
            )
            cols = st.columns(2)
            if cols[0].button("Reload favorite", key=f"reload_fav_{favorite.id}"):
                reload_favorite_as_current_basket(favorite.id)
                st.success("Favorite reloaded for planning. Spending was not updated.")
                st.rerun()
            if cols[1].button("Delete favorite", key=f"delete_fav_{favorite.id}"):
                delete_favorite(favorite.id)
                st.success("Favorite deleted. Spending was not updated.")
                st.rerun()


def render_spending_insights() -> None:
    """Render spending insights and Plotly charts."""

    st.subheader("Spending insights")
    historical_months = load_historical_months()
    selected_month = st.selectbox(
        "Selected historical month",
        options=[str(month["month"]) for month in historical_months],
        index=len(historical_months) - 1,
    )
    insights = calculate_spending_insights(selected_month=selected_month)

    cols = st.columns(4)
    cols[0].metric(
        "Average monthly groceries",
        format_huf(insights.average_monthly_grocery_spending_huf),
    )
    cols[1].metric("Average basket", format_huf(insights.average_basket_value_huf))
    cols[2].metric("Avg trips/month", f"{insights.average_grocery_trips_per_month:.1f}")
    cols[3].metric(
        "Selected month",
        format_huf(int(insights.selected_month_summary["grocery_spend_huf"])),
    )

    st.caption(
        f"Highest simulated month: {insights.highest_spending_month['month']} "
        f"({format_huf(int(insights.highest_spending_month['grocery_spend_huf']))}). "
        f"Lowest simulated month: {insights.lowest_spending_month['month']} "
        f"({format_huf(int(insights.lowest_spending_month['grocery_spend_huf']))})."
    )

    monthly_df = pd.DataFrame(insights.monthly_spending_vs_budget_chart_data)
    weekly_df = pd.DataFrame(insights.weekly_spending_pattern_chart_data)
    store_df = pd.DataFrame(insights.store_split_chart_data)

    chart_cols = st.columns(3)
    chart_cols[0].plotly_chart(
        px.line(
            monthly_df,
            x="month",
            y=["grocery_spend_huf", "planned_budget_huf"],
            markers=True,
            title="Monthly spending versus budget",
        ),
        width="stretch",
    )
    chart_cols[1].plotly_chart(
        px.bar(
            weekly_df,
            x="week",
            y="estimated_spend_huf",
            title="Weekly spending pattern",
        ),
        width="stretch",
    )
    chart_cols[2].plotly_chart(
        px.pie(store_df, names="store", values="spend_huf", title="Store split"),
        width="stretch",
    )


def render_warning_messages(warnings: list[BudgetWarning]) -> None:
    """Render deterministic warning messages."""

    st.subheader("Warning messages")
    if not warnings:
        st.success("No deterministic simulated budget warnings were triggered.")
        return

    for warning in warnings:
        message = f"{warning.code}: {warning.message}"
        if warning.level == "danger":
            st.error(message)
        elif warning.level == "warning":
            st.warning(message)
        else:
            st.info(message)


def render_agentic_explanation(
    optimization: PremiumOptimizationResult | None,
    warnings: list[BudgetWarning],
) -> None:
    """Render agentic-style explanation."""

    st.subheader("Agentic explanation")
    if optimization is None:
        st.info("Run an eligible simulated recommendation to generate the explanation.")
        return

    st.text(explain_recommendation(optimization, warnings))


def render_reset_demo_data() -> None:
    """Render reset demo data control."""

    st.subheader("Reset demo data")
    st.caption(
        "Resetting restores simulated prices, profile, goals, historical data, "
        "favorites, previous lists, and transactions."
    )
    if st.button("Reset simulated demo data"):
        reset_demo_data()
        st.success("Simulated demo data reset.")
        st.rerun()


def build_warnings(settings: dict[str, int | str | bool]) -> list[BudgetWarning]:
    """Build deterministic warnings for the current settings."""

    spent = int(settings["already_spent_huf"])
    budget = int(settings["monthly_budget_huf"])
    historical_months = load_historical_months()
    projected = round(spent / max(date.today().day, 1) * 30)
    return evaluate_budget_warnings(
        current_spent_huf=spent,
        monthly_budget_huf=budget,
        historical_months=historical_months,
        day_of_month=date.today().day,
        projected_month_end_spend_huf=projected,
    )


def load_user_profile() -> dict[str, int | str]:
    """Load the simulated user profile."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        row = connection.execute(
            """
            SELECT monthly_grocery_budget_huf, already_spent_current_month_huf,
                   usual_store_id, max_travel_minutes, travel_cost_per_km_huf
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()
    return dict(row)


def load_store_rows() -> list[dict[str, int | str]]:
    """Load store rows for selectors."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT id, name, chain
            FROM stores
            ORDER BY chain
            """
        ).fetchall()
    return [dict(row) for row in rows]


def store_name_for_id(store_id: str) -> str:
    """Return display name for one store ID."""

    for store in load_store_rows():
        if store["id"] == store_id:
            return str(store["name"])
    return store_id


def load_product_lookup() -> dict[str, dict[str, str]]:
    """Load product labels for basket tables."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT id, english_name, hungarian_name, unit
            FROM products
            """
        ).fetchall()
    return {
        row["id"]: {
            "name": row["english_name"],
            "hungarian_name": row["hungarian_name"],
            "unit": row["unit"],
        }
        for row in rows
    }


def load_stores_for_product_ids(product_ids: list[str]):
    """Load stores with available prices for selected product IDs."""

    from smartspend.database import load_stores_for_optimizer

    return load_stores_for_optimizer(product_ids)


def premium_result_row(result: PremiumStoreResult) -> dict[str, str | int]:
    """Convert one premium optimizer result into a table row."""

    return {
        "Rank": result.rank,
        "Store": result.store.name,
        "Product total": format_huf(result.product_total_huf),
        "Travel money": format_huf(result.travel_monetary_cost_huf),
        "Time cost": format_huf(result.travel_time_cost_huf),
        "Net total": format_huf(result.net_total_cost_huf),
        "Savings vs usual": format_huf(result.savings_vs_usual_store_huf),
        "Within max travel": "Yes" if result.within_max_travel_time else "No",
        "Unavailable": ", ".join(result.unavailable_items) or "None",
        "Route source": result.route_source,
        "Can win": "Yes" if result.can_win else "No",
    }


def basket_line_row(line) -> dict[str, str | int]:
    """Convert a basket line into a table row."""

    lookup = load_product_lookup()
    product = lookup.get(line.product_id, {"name": line.product_id, "unit": ""})
    return {
        "Product": product["name"],
        "Unit": product["unit"],
        "Quantity": line.quantity,
    }


if __name__ == "__main__":
    main()
