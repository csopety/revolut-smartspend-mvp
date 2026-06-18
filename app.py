"""Premium phone-style Streamlit UI for the SmartSpend V2 MVP."""

from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from smartspend.agentic_explainer import explain_recommendation
from smartspend.basket import Basket, BasketLine, add_product, edit_quantity, remove_product
from smartspend.database import (
    DEFAULT_DB_PATH,
    DEFAULT_ORIGIN_ADDRESS,
    connect,
    ensure_demo_database,
    reset_demo_data,
    update_user_profile,
)
from smartspend.favorites import (
    add_previous_list_to_favorites,
    delete_favorite,
    get_favorite_items,
    list_favorites,
    reload_favorite_as_current_basket,
    save_current_basket_as_favorite,
)
from smartspend.formatting import format_huf
from smartspend.insights import (
    calculate_current_month_track_prediction,
    calculate_spending_insights,
    load_historical_months,
)
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
from smartspend.route_service import get_openrouteservice_api_key, get_route
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
SCREEN_NAMES = ("Home", "Plan", "History", "Setup")
MODE_LABELS = {
    OPTIMIZATION_BALANCED: "Balanced recommendation",
    OPTIMIZATION_LOWEST_TOTAL_COST: "Lowest total cost including travel",
    OPTIMIZATION_CHEAPEST_BASKET: "Cheapest basket only",
    OPTIMIZATION_BEST_BUDGET_FIT: "Best budget fit",
}
TRANSPORT_LABELS = {
    TRANSPORT_WALKING: "Walking",
    TRANSPORT_PUBLIC_TRANSPORT: "Public transport",
    TRANSPORT_CAR: "Car",
}


def main() -> None:
    """Run the Streamlit application."""

    st.set_page_config(page_title="SmartSpend V2 MVP", page_icon="S", layout="wide")
    apply_page_styles()
    ensure_demo_database()
    initialize_ui_state()

    profile = load_user_profile()
    current_basket = load_current_basket()
    settings = build_settings(profile)
    warnings = build_warnings(settings)

    render_app_header()
    render_phone_navigation()
    render_persistent_notice()
    render_finalization_verification()

    active_screen = st.session_state["active_screen"]
    if active_screen == "Home":
        render_home_screen(settings, current_basket, warnings)
    elif active_screen == "Plan":
        render_plan_screen(current_basket, settings, warnings)
    elif active_screen == "History":
        render_history_screen(current_basket, settings)
    else:
        render_setup_screen(profile)


def initialize_ui_state() -> None:
    """Initialize UI-only state without touching spending."""

    st.session_state.setdefault("active_screen", "Home")
    st.session_state.setdefault("consent_enabled", True)
    st.session_state.setdefault("use_live_routes", False)
    st.session_state.setdefault("optimization_mode", OPTIMIZATION_BALANCED)
    st.session_state.setdefault("transport_mode", TRANSPORT_WALKING)
    st.session_state.setdefault("value_of_time_huf_per_min", 35)
    st.session_state.setdefault("comparison_requested", False)
    st.session_state.setdefault("last_success_message", "")
    st.session_state.setdefault("last_finalization_receipt", None)


def apply_page_styles() -> None:
    """Apply dark phone-frame fintech styling."""

    st.markdown(
        """
        <style>
        :root {
            --smart-bg: #040711;
            --smart-panel: rgba(13, 18, 35, 0.78);
            --smart-panel-soft: rgba(23, 30, 54, 0.62);
            --smart-border: rgba(140, 151, 255, 0.24);
            --smart-border-hot: rgba(111, 82, 255, 0.74);
            --smart-text: #f7f8ff;
            --smart-muted: #9aa3b9;
            --smart-blue: #00c2ff;
            --smart-purple: #7c3cff;
            --smart-pink: #db43ff;
        }
        .stApp {
            background:
                radial-gradient(circle at 18% 0%, rgba(124, 60, 255, 0.34), transparent 28rem),
                radial-gradient(circle at 88% 12%, rgba(0, 194, 255, 0.22), transparent 24rem),
                linear-gradient(180deg, #02040b 0%, #07101f 100%);
            color: var(--smart-text);
        }
        .block-container {
            max-width: 460px;
            padding: 1.05rem 1rem 2.2rem;
            margin-top: 1.15rem;
            margin-bottom: 1.15rem;
            background:
                linear-gradient(180deg, rgba(14, 20, 38, 0.92), rgba(5, 8, 18, 0.96)),
                radial-gradient(circle at 50% 0%, rgba(124, 60, 255, 0.18), transparent 16rem);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 36px;
            box-shadow: 0 30px 100px rgba(0, 0, 0, 0.62), 0 0 42px rgba(0, 194, 255, 0.16);
        }
        .block-container::before {
            content: "";
            display: block;
            width: 5.3rem;
            height: 0.28rem;
            margin: 0 auto 0.95rem auto;
            border-radius: 99px;
            background: rgba(255, 255, 255, 0.23);
        }
        h1, h2, h3, h4, p, label, span, div { color: var(--smart-text); letter-spacing: 0; }
        h1 { font-size: 1.7rem; margin-bottom: 0.15rem; }
        h2 { font-size: 1.28rem; margin-top: 1.15rem; }
        h3 { font-size: 1.05rem; margin-top: 0.9rem; }
        .stCaption, [data-testid="stCaptionContainer"], .muted { color: var(--smart-muted) !important; }
        .smart-subtle { color: var(--smart-muted); font-size: 0.88rem; line-height: 1.45; margin: 0.15rem 0 0; }
        .smart-kicker {
            color: #b8c3ff;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .glass-card, .hero-card, .recommendation-card {
            border: 1px solid var(--smart-border);
            background: linear-gradient(145deg, rgba(19, 26, 50, 0.82), rgba(9, 13, 27, 0.72));
            border-radius: 24px;
            padding: 1rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07), 0 18px 44px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(18px);
            margin: 0.85rem 0;
        }
        .hero-card {
            border-color: rgba(0, 194, 255, 0.36);
            background:
                linear-gradient(135deg, rgba(124, 60, 255, 0.72), rgba(0, 194, 255, 0.24)),
                linear-gradient(145deg, rgba(19, 26, 50, 0.90), rgba(9, 13, 27, 0.82));
            box-shadow: 0 0 34px rgba(124, 60, 255, 0.28), 0 20px 50px rgba(0, 0, 0, 0.34);
        }
        .recommendation-card {
            border-color: var(--smart-border-hot);
            background:
                linear-gradient(135deg, rgba(124, 60, 255, 0.45), rgba(0, 194, 255, 0.18)),
                rgba(10, 14, 29, 0.86);
            box-shadow: 0 0 34px rgba(124, 60, 255, 0.36), 0 0 26px rgba(0, 194, 255, 0.15);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.85rem;
        }
        .mini-metric {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 0.78rem;
            background: rgba(255, 255, 255, 0.045);
        }
        .mini-label { color: var(--smart-muted); font-size: 0.74rem; }
        .mini-value { font-size: 1.05rem; font-weight: 750; margin-top: 0.2rem; }
        .journey-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.55rem;
            margin: 0.85rem 0;
        }
        .journey-step {
            min-height: 5rem;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 0.74rem;
            background: rgba(255, 255, 255, 0.045);
        }
        .journey-step b { display: block; font-size: 0.82rem; margin-bottom: 0.25rem; }
        .journey-step span { color: var(--smart-muted); font-size: 0.72rem; line-height: 1.25; }
        .nav-row div[data-testid="stButton"] > button,
        div[data-testid="stButton"] > button {
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.13);
            background: rgba(255, 255, 255, 0.055);
            color: #f7f8ff;
            min-height: 2.5rem;
            box-shadow: none;
        }
        div[data-testid="stButton"] > button:hover {
            border-color: rgba(0, 194, 255, 0.65);
            box-shadow: 0 0 22px rgba(0, 194, 255, 0.18);
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #7c3cff, #00c2ff);
            border: 0;
            box-shadow: 0 0 26px rgba(124, 60, 255, 0.34);
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 0.8rem;
            background: rgba(255, 255, 255, 0.045);
        }
        [data-testid="stMetricLabel"] p { color: var(--smart-muted) !important; font-size: 0.74rem; }
        [data-testid="stMetricValue"] { color: var(--smart-text); font-size: 1.2rem; }
        div[data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; }
        div[data-testid="stExpander"] {
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.035);
        }
        .stTabs [data-baseweb="tab-list"] { gap: 0.35rem; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.45rem 0.78rem;
            background: rgba(255, 255, 255, 0.045);
            color: var(--smart-muted);
        }
        input, textarea, [data-baseweb="select"] > div {
            border-radius: 16px !important;
            background-color: rgba(255, 255, 255, 0.07) !important;
            color: var(--smart-text) !important;
        }
        .stAlert {
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.07);
        }
        @media (max-width: 540px) {
            .block-container {
                max-width: 100%;
                min-height: 100vh;
                margin: 0;
                border-radius: 0;
                border-left: 0;
                border-right: 0;
            }
            .metric-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    """Render the app header."""

    st.markdown(
        """
        <div class="hero-card">
            <div class="smart-kicker">Simulated SmartSpend MVP</div>
            <h1>SmartSpend</h1>
            <p class="smart-subtle">
                Estimated grocery planning for Budapest II based on simulated
                supported store, route, price, and spending data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_phone_navigation() -> None:
    """Render four-screen phone-style navigation."""

    st.markdown('<div class="nav-row">', unsafe_allow_html=True)
    cols = st.columns(4)
    for index, screen_name in enumerate(SCREEN_NAMES):
        label = f"{screen_name}" if st.session_state["active_screen"] != screen_name else f"{screen_name}."
        if cols[index].button(label, key=f"nav_{screen_name}", use_container_width=True):
            st.session_state["active_screen"] = screen_name
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_persistent_notice() -> None:
    """Render success and simulation notices that matter across screens."""

    if st.session_state.get("last_success_message"):
        st.success(st.session_state["last_success_message"])
        if st.button("Dismiss", key="dismiss_success"):
            st.session_state["last_success_message"] = ""
            st.rerun()


def render_finalization_verification() -> None:
    """Render closed-loop simulated savings verification after finalization."""

    receipt = st.session_state.get("last_finalization_receipt")
    if not receipt:
        return

    saved_huf = int(receipt["estimated_verified_saving_huf"])
    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="smart-kicker">Simulated savings verification</div>
            <h2>You saved an estimated {escape(format_huf(saved_huf))}</h2>
            <p class="smart-subtle">
                This is a simulated comparison against the usual-store estimate.
                No payment, receipt OCR, banking action, or real money transfer occurred.
            </p>
            <div class="metric-grid">
                <div class="mini-metric"><div class="mini-label">Finalized basket</div><div class="mini-value">{escape(format_huf(int(receipt["finalized_basket_total_huf"])))}</div></div>
                <div class="mini-metric"><div class="mini-label">Usual-store estimate</div><div class="mini-value">{escape(format_huf(int(receipt["usual_store_estimate_huf"])))}</div></div>
                <div class="mini-metric"><div class="mini-label">Counted toward budget</div><div class="mini-value">{escape(format_huf(int(receipt["amount_counted_toward_budget_huf"])))}</div></div>
                <div class="mini-metric"><div class="mini-label">Remaining budget</div><div class="mini-value">{escape(format_huf(int(receipt["remaining_budget_huf"])))}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if receipt.get("savings_goal_name"):
        st.success(
            f"Simulated movement: {format_huf(saved_huf)} to "
            f"{receipt['savings_goal_name']}. This is not a real money transfer."
        )
    else:
        st.caption("No simulated savings goal movement was selected.")

    with st.expander("View simulated verification details"):
        st.write(f"Store actually visited: {receipt['visited_store_name']}")
        st.write(
            f"Finalized basket total: "
            f"{format_huf(int(receipt['finalized_basket_total_huf']))}"
        )
        st.write(
            f"Usual-store estimate: "
            f"{format_huf(int(receipt['usual_store_estimate_huf']))}"
        )
        st.write(f"Estimated verified saving: {format_huf(saved_huf)}")
        st.write(
            f"Amount counted toward budget: "
            f"{format_huf(int(receipt['amount_counted_toward_budget_huf']))}"
        )
        st.write(
            f"Remaining budget: {format_huf(int(receipt['remaining_budget_huf']))}"
        )
        if receipt.get("savings_goal_name"):
            st.write(f"Selected simulated savings goal: {receipt['savings_goal_name']}")
        st.caption(
            "Simulated only: no confirmed payment, receipt OCR, external account "
            "update, or real transfer."
        )

    if st.button("Dismiss simulated verification", key="dismiss_finalization_receipt"):
        st.session_state["last_finalization_receipt"] = None
        st.rerun()


def build_settings(profile: dict[str, int | str]) -> dict[str, int | str | bool]:
    """Build calculation settings from persisted profile and UI-only choices."""

    return {
        "monthly_budget_huf": int(profile["monthly_grocery_budget_huf"]),
        "already_spent_huf": get_spent_so_far(),
        "max_travel_minutes": int(profile["max_travel_minutes"]),
        "travel_cost_per_km_huf": int(profile["travel_cost_per_km_huf"]),
        "value_of_time_huf_per_min": int(st.session_state["value_of_time_huf_per_min"]),
        "usual_store_id": str(profile["usual_store_id"]),
        "origin_address": str(profile.get("origin_address") or DEFAULT_ORIGIN_ADDRESS),
        "optimization_mode": str(st.session_state["optimization_mode"]),
        "transport_mode": str(st.session_state["transport_mode"]),
        "use_live_routes": bool(st.session_state["use_live_routes"]),
        "consent_enabled": bool(st.session_state["consent_enabled"]),
    }


def render_home_screen(
    settings: dict[str, int | str | bool],
    current_basket: Basket,
    warnings: list[BudgetWarning],
) -> None:
    """Render budget overview, journey, goals, and quick actions."""

    st.subheader("Home")
    prediction = calculate_current_month_track_prediction(
        current_spend_huf=int(settings["already_spent_huf"]),
        monthly_budget_huf=int(settings["monthly_budget_huf"]),
        day_of_month=date.today().day,
    )
    render_budget_hero(settings, prediction)
    render_priority_status(warnings, prediction)
    render_journey_strip()
    render_savings_goals_preview()
    render_quick_actions(current_basket)


def render_budget_hero(settings: dict[str, int | str | bool], prediction) -> None:
    """Render budget hero card."""

    spent = int(settings["already_spent_huf"])
    budget = int(settings["monthly_budget_huf"])
    remaining = budget - spent
    ratio = min(spent / budget, 1.0)

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="smart-kicker">Current month</div>
            <h2>{escape(format_huf(remaining))} remaining</h2>
            <p class="smart-subtle">
                {escape(format_huf(spent))} spent from a simulated
                {escape(format_huf(budget))} grocery budget.
            </p>
            <div class="metric-grid">
                <div class="mini-metric">
                    <div class="mini-label">On-track likelihood</div>
                    <div class="mini-value">{prediction.likelihood_percentage}%</div>
                </div>
                <div class="mini-metric">
                    <div class="mini-label">Projected month-end</div>
                    <div class="mini-value">{escape(format_huf(prediction.projected_spend_huf))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(ratio)


def render_priority_status(
    warnings: list[BudgetWarning],
    prediction,
) -> None:
    """Render the top warning or track prediction."""

    if warnings:
        priority = sorted(
            warnings,
            key=lambda warning: {"danger": 0, "warning": 1, "info": 2}.get(warning.level, 3),
        )[0]
        if priority.level == "danger":
            st.error(f"{priority.message} Based on simulated spending data.")
        elif priority.level == "warning":
            st.warning(f"{priority.message} Based on simulated spending data.")
        else:
            st.info(f"{priority.message} Based on simulated spending data.")
        return

    st.success(
        f"{prediction.status}: projected spend appears to be "
        f"{format_huf(abs(prediction.over_under_budget_huf))} "
        f"{'under' if prediction.over_under_budget_huf >= 0 else 'over'} budget."
    )


def render_journey_strip() -> None:
    """Render Before / During / After journey."""

    st.markdown(
        """
        <div class="journey-strip">
            <div class="journey-step">
                <b>Before</b><span>Check budget risk and plan a basket.</span>
            </div>
            <div class="journey-step">
                <b>During</b><span>Compare supported stores before purchase.</span>
            </div>
            <div class="journey-step">
                <b>After</b><span>Finalize only when the simulated shop is done.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_savings_goals_preview() -> None:
    """Render compact simulated goals preview."""

    st.markdown('<div class="glass-card"><div class="smart-kicker">Simulated savings goals</div>', unsafe_allow_html=True)
    goals = list_savings_goals()
    for goal in goals[:3]:
        st.caption(f"{goal.name}: {format_huf(goal.current_amount_huf)} of {format_huf(goal.target_amount_huf)}")
        st.progress(min(goal.current_amount_huf / goal.target_amount_huf, 1.0))
    st.markdown("</div>", unsafe_allow_html=True)


def render_quick_actions(current_basket: Basket) -> None:
    """Render quick navigation actions."""

    st.markdown('<div class="glass-card"><div class="smart-kicker">Quick actions</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if col1.button("Plan grocery basket", use_container_width=True):
        st.session_state["active_screen"] = "Plan"
        st.rerun()
    if col2.button("View history", use_container_width=True):
        st.session_state["active_screen"] = "History"
        st.rerun()
    if st.button("Load investor demo scenario", type="primary", use_container_width=True):
        load_investor_demo_scenario()
        st.rerun()
    st.caption(f"Current planning basket: {len(current_basket.lines)} item types. Planning does not update spending.")
    st.markdown("</div>", unsafe_allow_html=True)


def load_investor_demo_scenario() -> None:
    """Load a deterministic investor demo without finalizing purchase."""

    update_user_profile(
        monthly_grocery_budget_huf=165000,
        usual_store_id="spar_rozsakert",
        max_travel_minutes=16,
        travel_cost_per_km_huf=120,
        origin_address=DEFAULT_ORIGIN_ADDRESS,
    )
    save_current_basket(
        Basket(
            lines=(
                BasketLine("milk", 2),
                BasketLine("bread_loaf", 1),
                BasketLine("cucumber", 2),
                BasketLine("chicken_breast", 1),
                BasketLine("trappista_cheese", 1),
                BasketLine("apples", 1),
            )
        )
    )
    st.session_state["optimization_mode"] = OPTIMIZATION_BALANCED
    st.session_state["transport_mode"] = TRANSPORT_PUBLIC_TRANSPORT
    st.session_state["value_of_time_huf_per_min"] = 35
    st.session_state["use_live_routes"] = False
    st.session_state["consent_enabled"] = True
    st.session_state["comparison_requested"] = True
    st.session_state["last_finalization_receipt"] = None
    st.session_state["last_success_message"] = (
        "Investor demo scenario loaded. No purchase was finalized, no transaction "
        "was created, and no savings goal was updated."
    )
    st.session_state["active_screen"] = "Plan"


def render_plan_screen(
    current_basket: Basket,
    settings: dict[str, int | str | bool],
    warnings: list[BudgetWarning],
) -> None:
    """Render basket, recommendation, receipt, and finalization."""

    st.subheader("Plan")
    st.caption(
        "Build a simulated grocery basket and compare supported stores. Planning and comparison do not update spending."
    )
    current_basket = render_basket_builder(current_basket)

    optimization = None
    st.markdown('<div class="glass-card"><div class="smart-kicker">Compare stores</div>', unsafe_allow_html=True)
    if not settings["consent_enabled"]:
        st.info(CONSENT_DISABLED_MESSAGE)
        st.button("Compare supported stores", disabled=True, use_container_width=True)
    elif not current_basket.lines:
        st.info("Add grocery products with search to estimate supported store recommendations.")
        st.button("Compare supported stores", disabled=True, use_container_width=True)
    else:
        if st.button("Compare supported stores", type="primary", use_container_width=True):
            st.session_state["comparison_requested"] = True
        if st.session_state.get("comparison_requested"):
            optimization = build_recommendation(current_basket, settings)
    st.markdown("</div>", unsafe_allow_html=True)

    if optimization is not None:
        render_recommendation(optimization)
        render_why_not_other_stores(optimization)
        render_calculation_receipt(optimization)
        render_agentic_explanation(optimization, warnings)

    render_finalization(current_basket, optimization)


def render_basket_builder(current_basket: Basket) -> Basket:
    """Render search-first grocery basket builder."""

    st.markdown('<div class="glass-card"><div class="smart-kicker">Typeahead basket builder</div>', unsafe_allow_html=True)
    query = st.text_input(
        "Search products",
        placeholder="Try cucu, ubi, tej, csir, trap...",
    )
    if query:
        for result in search_products(query, limit=6):
            cols = st.columns([3.8, 1.2])
            cols[0].write(f"{result.display_name} ({result.hungarian_name})")
            cols[0].caption(f"{result.unit} - simulated supported catalog item")
            if cols[1].button("Add", key=f"add_{result.product_id}", use_container_width=True):
                current_basket = add_product(current_basket, result.product_id)
                save_current_basket(current_basket)
                st.session_state["comparison_requested"] = False
                st.rerun()

    st.markdown("**Current basket**")
    if not current_basket.lines:
        st.info("Your planning basket is empty. Planning does not update spending.")
        st.markdown("</div>", unsafe_allow_html=True)
        return current_basket

    lookup = load_product_lookup()
    for line in current_basket.lines:
        product = lookup.get(line.product_id, {"name": line.product_id, "unit": ""})
        cols = st.columns([3, 1.1, 1.2])
        cols[0].write(f"{product['name']}")
        cols[0].caption(str(product["unit"]))
        new_quantity = cols[1].number_input(
            "Qty",
            min_value=1,
            max_value=50,
            value=line.quantity,
            key=f"qty_{line.product_id}",
            label_visibility="collapsed",
        )
        if cols[2].button("Update", key=f"update_{line.product_id}", use_container_width=True):
            current_basket = edit_quantity(current_basket, line.product_id, new_quantity)
            save_current_basket(current_basket)
            st.session_state["comparison_requested"] = False
            st.rerun()
        if cols[2].button("Remove", key=f"remove_{line.product_id}", use_container_width=True):
            current_basket = remove_product(current_basket, line.product_id)
            save_current_basket(current_basket)
            st.session_state["comparison_requested"] = False
            st.rerun()

    if st.button("Clear planning basket", use_container_width=True):
        save_current_basket(Basket())
        st.session_state["comparison_requested"] = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
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
            origin=str(settings["origin_address"]),
            use_live_routes=bool(settings["use_live_routes"]),
            transport_mode=str(settings["transport_mode"]),
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
            "No store appears eligible to win based on simulated supported store and price data."
        )
        return

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="smart-kicker">Estimated recommendation</div>
            <h2>{escape(recommendation.store.name)}</h2>
            <p class="smart-subtle">
                This appears to be the best fit for {escape(MODE_LABELS.get(optimization.mode, optimization.mode))}
                using simulated supported store, price, and route data.
            </p>
            <div class="metric-grid">
                <div class="mini-metric"><div class="mini-label">Basket</div><div class="mini-value">{escape(format_huf(recommendation.product_total_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Estimated total</div><div class="mini-value">{escape(format_huf(recommendation.net_total_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Savings vs usual</div><div class="mini-value">{escape(format_huf(recommendation.savings_vs_usual_store_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Confidence</div><div class="mini-value">{recommendation.confidence_score}/100</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Ranked alternatives**")
    for result in optimization.results:
        render_store_result_card(result, is_recommended=result == recommendation)


def render_store_result_card(result: PremiumStoreResult, is_recommended: bool) -> None:
    """Render one compact ranked store card."""

    border_class = "recommendation-card" if is_recommended else "glass-card"
    unavailable = ", ".join(result.unavailable_items) or "None"
    st.markdown(
        f"""
        <div class="{border_class}">
            <div class="smart-kicker">Rank {result.rank}{' - selected' if is_recommended else ''}</div>
            <h3>{escape(result.store.name)}</h3>
            <p class="smart-subtle">
                Route source: {escape(result.route_source)} · Distance: {result.distance_km:.1f} km ·
                Travel time: {result.travel_time_min} min · Can win: {'Yes' if result.can_win else 'No'}
            </p>
            <div class="metric-grid">
                <div class="mini-metric"><div class="mini-label">Basket</div><div class="mini-value">{escape(format_huf(result.product_total_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Travel money</div><div class="mini-value">{escape(format_huf(result.travel_monetary_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Time cost</div><div class="mini-value">{escape(format_huf(result.travel_time_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Net total</div><div class="mini-value">{escape(format_huf(result.net_total_cost_huf))}</div></div>
            </div>
            <p class="smart-subtle">Unavailable required items: {escape(unavailable)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_why_not_other_stores(optimization: PremiumOptimizationResult) -> None:
    """Explain why non-winning stores did not win."""

    st.subheader("Why not other stores?")
    if optimization.recommended is None:
        st.info("No winning store is available to compare against.")
        return

    winner = optimization.recommended
    for result in optimization.results:
        if result.store.id == winner.store.id:
            continue
        reason = explain_non_winning_store(result, winner)
        st.caption(f"{result.store.chain}: {reason}")


def explain_non_winning_store(
    result: PremiumStoreResult,
    winner: PremiumStoreResult,
) -> str:
    """Return deterministic non-winner explanation."""

    if result.unavailable_items:
        return "it has unavailable required basket items in the simulated assortment."
    if not result.within_max_travel_time:
        return "it is above the selected max travel time, so it remains visible but cannot win."
    if result.product_total_huf > winner.product_total_huf:
        difference = result.product_total_huf - winner.product_total_huf
        return f"its product basket price is {format_huf(difference)} higher than the recommendation."
    if result.net_total_cost_huf > winner.net_total_cost_huf:
        difference = result.net_total_cost_huf - winner.net_total_cost_huf
        return f"its net comparison total is {format_huf(difference)} higher than the recommendation."
    if result.confidence_score < winner.confidence_score:
        return "its confidence score is lower for this basket."
    return "the selected optimization mode ranked the recommendation slightly higher."


def render_calculation_receipt(optimization: PremiumOptimizationResult) -> None:
    """Render auditable calculation receipt."""

    st.subheader("Calculation receipt")
    if optimization.recommended:
        render_calculation_receipt_card(optimization.recommended)
    with st.expander("View store-by-store calculation"):
        st.dataframe(
            pd.DataFrame([premium_result_row(result) for result in optimization.results]),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Net total = product total + estimated travel monetary cost + travel-time opportunity cost. "
            "Travel-time cost is never counted as real spending."
        )


def render_calculation_receipt_card(result: PremiumStoreResult) -> None:
    """Render the required receipt values for one store result."""

    usual_store_net_total = result.net_total_cost_huf + result.savings_vs_usual_store_huf
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="smart-kicker">Auditable calculation</div>
            <h3>{escape(result.store.name)}</h3>
            <div class="metric-grid">
                <div class="mini-metric"><div class="mini-label">Product basket total</div><div class="mini-value">{escape(format_huf(result.product_total_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Travel monetary cost</div><div class="mini-value">{escape(format_huf(result.travel_monetary_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Travel-time opportunity cost</div><div class="mini-value">{escape(format_huf(result.travel_time_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Net comparison total</div><div class="mini-value">{escape(format_huf(result.net_total_cost_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Usual-store net total</div><div class="mini-value">{escape(format_huf(usual_store_net_total))}</div></div>
                <div class="mini-metric"><div class="mini-label">Savings vs usual</div><div class="mini-value">{escape(format_huf(result.savings_vs_usual_store_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Savings vs most expensive</div><div class="mini-value">{escape(format_huf(result.savings_vs_most_expensive_store_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Remaining budget after purchase</div><div class="mini-value">{escape(format_huf(result.remaining_budget_after_purchase_huf))}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_finalization(
    current_basket: Basket,
    optimization: PremiumOptimizationResult | None,
) -> None:
    """Render simulated purchase finalization."""

    st.subheader("Finalize grocery purchase")
    st.caption(
        "Only finalization updates simulated spent so far. Comparison and basket planning do not."
    )
    if optimization is None or optimization.recommended is None or not current_basket.lines:
        st.button("Finalize simulated purchase", disabled=True, use_container_width=True)
        return

    recommendation = optimization.recommended
    store_options = [result.store.id for result in optimization.results]
    selected_store_id = st.selectbox(
        "Store actually visited",
        options=store_options,
        format_func=lambda store_id: next(
            result.store.name for result in optimization.results if result.store.id == store_id
        ),
        index=store_options.index(recommendation.store.id),
    )
    selected_result = result_for_store(optimization, selected_store_id)
    list_name = st.text_input(
        "Simulated list name",
        value=f"{selected_result.store.chain} simulated purchase",
    )
    include_travel = st.checkbox(
        "Count estimated travel monetary cost as real grocery spending for this simulation",
        value=False,
    )
    positive_savings = max(selected_result.savings_vs_usual_store_huf, 0)
    selected_goal_id = "none"
    selected_goal_name = ""
    if positive_savings > 0:
        goals = list_savings_goals()
        goal_options = ["none", *[goal.id for goal in goals]]
        selected_goal_id = st.selectbox(
            "Optional simulated savings goal",
            options=goal_options,
            format_func=lambda goal_id: "Do not move simulated savings"
            if goal_id == "none"
            else next(goal.name for goal in goals if goal.id == goal_id),
        )
        if selected_goal_id != "none":
            selected_goal_name = next(goal.name for goal in goals if goal.id == selected_goal_id)
    else:
        st.caption("No positive estimated saving is available for a simulated goal movement.")

    render_calculation_receipt_card(selected_result)

    if st.button("Finalize simulated purchase", type="primary", use_container_width=True):
        try:
            result = finalize_purchase(
                store_id=selected_result.store.id,
                basket=current_basket,
                travel_monetary_cost_huf=selected_result.travel_monetary_cost_huf,
                travel_time_cost_huf=selected_result.travel_time_cost_huf,
                include_travel_monetary_cost=include_travel,
                route_source=selected_result.route_source,
                list_name=list_name,
            )
            movement_goal_name = ""
            if selected_goal_id != "none" and positive_savings > 0:
                movement = simulate_save_difference_to_goal(
                    selected_goal_id,
                    positive_savings,
                )
                movement_goal_name = movement.goal_name
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["last_success_message"] = result.success_message
            st.session_state["last_finalization_receipt"] = build_finalization_receipt(
                selected_result=selected_result,
                finalization_result=result,
                savings_goal_name=movement_goal_name or selected_goal_name,
            )
            st.session_state["comparison_requested"] = False
            st.rerun()


def result_for_store(
    optimization: PremiumOptimizationResult,
    store_id: str,
) -> PremiumStoreResult:
    """Return one optimizer result by store ID."""

    return next(result for result in optimization.results if result.store.id == store_id)


def build_finalization_receipt(
    selected_result: PremiumStoreResult,
    finalization_result,
    savings_goal_name: str,
) -> dict[str, int | str]:
    """Build serializable simulated verification details."""

    usual_store_estimate = (
        selected_result.net_total_cost_huf
        + selected_result.savings_vs_usual_store_huf
    )
    return {
        "visited_store_name": selected_result.store.name,
        "finalized_basket_total_huf": finalization_result.product_total_huf,
        "usual_store_estimate_huf": usual_store_estimate,
        "estimated_verified_saving_huf": max(
            selected_result.savings_vs_usual_store_huf,
            0,
        ),
        "amount_counted_toward_budget_huf": finalization_result.spent_so_far_increase_huf,
        "remaining_budget_huf": finalization_result.remaining_budget_huf,
        "savings_goal_name": savings_goal_name,
    }


def render_savings_goal_action(optimization: PremiumOptimizationResult | None) -> None:
    """Render simulated save-the-difference action."""

    st.subheader("Simulated save-the-difference")
    goals = list_savings_goals()
    positive_savings = 0
    if optimization and optimization.recommended:
        positive_savings = max(optimization.recommended.savings_vs_usual_store_huf, 0)

    selected_goal_id = st.selectbox(
        "Savings goal",
        options=[goal.id for goal in goals],
        format_func=lambda goal_id: next(goal.name for goal in goals if goal.id == goal_id),
    )
    if st.button(
        "Simulate moving the difference",
        disabled=positive_savings <= 0,
        use_container_width=True,
    ):
        movement = simulate_save_difference_to_goal(selected_goal_id, positive_savings)
        st.success(
            f"Simulated savings movement: {format_huf(movement.amount_huf)} to "
            f"{movement.goal_name}. No real money moved."
        )
        st.rerun()


def render_history_screen(
    current_basket: Basket,
    settings: dict[str, int | str | bool],
) -> None:
    """Render purchases, favorites, insights, and pilot proof tabs."""

    st.subheader("History")
    purchases_tab, favorites_tab, insights_tab, pilot_tab = st.tabs(
        ["Purchases", "Favorites", "Insights", "Pilot proof"]
    )
    with purchases_tab:
        render_previous_lists()
    with favorites_tab:
        render_favorites(current_basket)
    with insights_tab:
        render_spending_insights(settings)
    with pilot_tab:
        render_pilot_proof()


def render_previous_lists() -> None:
    """Render previous grocery lists."""

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
            if cols[0].button("Reload as current basket", key=f"reload_prev_{previous.id}", use_container_width=True):
                reload_previous_list_as_current_basket(previous.id)
                st.session_state["last_success_message"] = (
                    "Previous list reloaded for planning. Spending was not updated."
                )
                st.session_state["comparison_requested"] = False
                st.rerun()
            if cols[1].button("Add to favorites", key=f"fav_prev_{previous.id}", use_container_width=True):
                add_previous_list_to_favorites(previous.id)
                st.session_state["last_success_message"] = "Previous list saved as a simulated favorite."
                st.rerun()


def render_favorites(current_basket: Basket) -> None:
    """Render favorite grocery lists."""

    favorite_name = st.text_input("Favorite name", placeholder="Weekend basics")
    if st.button("Save current basket as favorite", disabled=not current_basket.lines, use_container_width=True):
        try:
            save_current_basket_as_favorite(current_basket, favorite_name)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["last_success_message"] = (
                "Current planning basket saved as simulated favorite. Spending was not updated."
            )
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
            if cols[0].button("Reload favorite", key=f"reload_fav_{favorite.id}", use_container_width=True):
                reload_favorite_as_current_basket(favorite.id)
                st.session_state["last_success_message"] = (
                    "Favorite reloaded for planning. Spending was not updated."
                )
                st.session_state["comparison_requested"] = False
                st.rerun()
            if cols[1].button("Delete favorite", key=f"delete_fav_{favorite.id}", use_container_width=True):
                delete_favorite(favorite.id)
                st.session_state["last_success_message"] = "Favorite deleted. Spending was not updated."
                st.rerun()


def render_spending_insights(settings: dict[str, int | str | bool]) -> None:
    """Render spending insights and dark Plotly charts."""

    prediction = calculate_current_month_track_prediction(
        current_spend_huf=int(settings["already_spent_huf"]),
        monthly_budget_huf=int(settings["monthly_budget_huf"]),
        day_of_month=date.today().day,
    )
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="smart-kicker">Simulated prediction based on current and historical demo data</div>
            <h3>Will I stay on track this month?</h3>
            <p class="smart-subtle">
                Deterministic projection only. No AI is used for this calculation.
            </p>
            <div class="metric-grid">
                <div class="mini-metric"><div class="mini-label">Status</div><div class="mini-value">{escape(prediction.status)}</div></div>
                <div class="mini-metric"><div class="mini-label">Projected month-end</div><div class="mini-value">{escape(format_huf(prediction.projected_spend_huf))}</div></div>
                <div class="mini-metric"><div class="mini-label">Current budget</div><div class="mini-value">{escape(format_huf(int(settings["monthly_budget_huf"])))}</div></div>
                <div class="mini-metric"><div class="mini-label">Projected over/under</div><div class="mini-value">{escape(format_huf(abs(prediction.over_under_budget_huf)))} {'under' if prediction.over_under_budget_huf >= 0 else 'over'}</div></div>
                <div class="mini-metric"><div class="mini-label">On-track likelihood</div><div class="mini-value">{prediction.likelihood_percentage}%</div></div>
                <div class="mini-metric"><div class="mini-label">Severity</div><div class="mini-value">{escape(prediction.severity.title())}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Explanation**")
    for point in prediction.explanation_points:
        st.markdown(f"- {point}")

    historical_months = load_historical_months()
    selected_month = st.selectbox(
        "Selected historical month",
        options=[str(month["month"]) for month in historical_months],
        index=len(historical_months) - 1,
    )
    insights = calculate_spending_insights(selected_month=selected_month)

    cols = st.columns(2)
    cols[0].metric("Average monthly", format_huf(insights.average_monthly_grocery_spending_huf))
    cols[1].metric("Average basket", format_huf(insights.average_basket_value_huf))
    cols = st.columns(2)
    cols[0].metric("Avg trips/month", f"{insights.average_grocery_trips_per_month:.1f}")
    cols[1].metric("Selected month", format_huf(int(insights.selected_month_summary["grocery_spend_huf"])))

    st.caption(
        f"Highest simulated month: {insights.highest_spending_month['month']} "
        f"({format_huf(int(insights.highest_spending_month['grocery_spend_huf']))}). "
        f"Lowest simulated month: {insights.lowest_spending_month['month']} "
        f"({format_huf(int(insights.lowest_spending_month['grocery_spend_huf']))})."
    )

    monthly_fig = px.line(
        pd.DataFrame(insights.monthly_spending_vs_budget_chart_data),
        x="month",
        y=["grocery_spend_huf", "planned_budget_huf"],
        markers=True,
        title="Monthly spending versus budget",
        template="plotly_dark",
    )
    weekly_fig = px.bar(
        pd.DataFrame(insights.weekly_spending_pattern_chart_data),
        x="week",
        y="estimated_spend_huf",
        title="Weekly spending pattern",
        template="plotly_dark",
    )
    store_fig = px.pie(
        pd.DataFrame(insights.store_split_chart_data),
        names="store",
        values="spend_huf",
        title="Store split",
        template="plotly_dark",
    )
    for figure in [monthly_fig, weekly_fig, store_fig]:
        figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f7f8ff",
            margin=dict(l=10, r=10, t=44, b=10),
        )
        st.plotly_chart(figure, width="stretch")


def render_pilot_proof() -> None:
    """Render simulated investor demo KPI proof."""

    st.subheader("Pilot proof")
    st.caption(
        "Simulated pilot metrics for MVP storytelling. Average saving per finalized "
        "shop is calculated from local transactions when available; otherwise it "
        "uses a seeded demo value."
    )
    for metric in calculate_pilot_kpis():
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="smart-kicker">{escape(metric["label"])}</div>
                <h3>{escape(metric["value"])}</h3>
                <p class="smart-subtle">{escape(metric["caption"])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_trust_audit_drawer()


def calculate_pilot_kpis() -> list[dict[str, str]]:
    """Build deterministic simulated pilot KPI values."""

    transaction_count = count_finalized_transactions()
    savings_movement_count = count_savings_movements()
    average_saving_huf = calculate_average_saving_per_finalized_shop()
    adoption_rate = 38 + min(transaction_count * 2, 8)
    repeat_usage = 2.4 + min(transaction_count, 4) * 0.1
    savings_goal_uplift = 19 + min(savings_movement_count * 3, 9)
    variance = 7 if transaction_count == 0 else max(4, 7 - min(transaction_count, 3))

    return [
        {
            "label": "Adoption rate",
            "value": f"{adoption_rate}%",
            "caption": "simulated users who planned at least one basket",
        },
        {
            "label": "Repeat usage",
            "value": f"{repeat_usage:.1f}x",
            "caption": "simulated average weekly planning sessions",
        },
        {
            "label": "Average saving per finalized shop",
            "value": format_huf(average_saving_huf),
            "caption": "calculated from local simulated transactions when available",
        },
        {
            "label": "Savings-goal usage uplift",
            "value": f"{savings_goal_uplift}%",
            "caption": "simulated lift from save-the-difference goal moments",
        },
        {
            "label": "Basket estimate variance",
            "value": f"+/-{variance}%",
            "caption": "simulated variance between basket estimate and finalized shop",
        },
        {
            "label": "Trust/compliance status",
            "value": "Pass",
            "caption": "deterministic calculations; no real banking, payment, or retailer API",
        },
    ]


def count_finalized_transactions() -> int:
    """Return finalized simulated transaction count."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0])


def count_savings_movements() -> int:
    """Return simulated savings movement count."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM savings_movements").fetchone()[0])


def calculate_average_saving_per_finalized_shop() -> int:
    """Calculate average product saving versus usual store or return seeded demo value."""

    ensure_demo_database()
    with connect(DEFAULT_DB_PATH) as connection:
        rows = connection.execute(
            """
            SELECT
                t.id,
                t.product_total_huf,
                SUM(COALESCE(sp.price_huf * li.quantity, li.line_total_huf)) AS usual_total_huf
            FROM transactions t
            JOIN transaction_line_items li ON li.transaction_id = t.id
            JOIN user_profile up ON up.id = 1
            LEFT JOIN store_prices sp
                ON sp.product_id = li.product_id
               AND sp.store_id = up.usual_store_id
               AND sp.is_available = 1
            GROUP BY t.id, t.product_total_huf
            """
        ).fetchall()

    if not rows:
        return 1180

    savings = [
        max(int(row["usual_total_huf"]) - int(row["product_total_huf"]), 0)
        for row in rows
    ]
    return round(sum(savings) / len(savings))


def render_setup_screen(profile: dict[str, int | str]) -> None:
    """Render persistent settings and trust controls."""

    st.subheader("Setup")
    st.caption("Profile settings are persisted locally in the simulated SQLite demo database.")
    store_rows = load_store_rows()
    usual_store_options = [store["id"] for store in store_rows]
    current_store_id = str(profile["usual_store_id"])

    st.markdown('<div class="glass-card"><div class="smart-kicker">Budget and profile</div>', unsafe_allow_html=True)
    monthly_budget_huf = st.number_input(
        "Monthly grocery budget",
        min_value=1,
        value=int(profile["monthly_grocery_budget_huf"]),
        step=5_000,
        format="%d",
    )
    usual_store_id = st.selectbox(
        "Usual store",
        options=usual_store_options,
        format_func=store_name_for_id,
        index=usual_store_options.index(current_store_id),
    )
    origin_address = st.text_input(
        "Origin/address",
        value=str(profile.get("origin_address") or DEFAULT_ORIGIN_ADDRESS),
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card"><div class="smart-kicker">Travel and recommendation</div>', unsafe_allow_html=True)
    max_travel_minutes = st.number_input(
        "Max travel time",
        min_value=1,
        value=int(profile["max_travel_minutes"]),
        step=1,
        format="%d",
    )
    travel_cost_per_km_huf = st.number_input(
        "Estimated travel cost per km",
        min_value=0,
        value=int(profile["travel_cost_per_km_huf"]),
        step=10,
        format="%d",
    )
    st.session_state["value_of_time_huf_per_min"] = st.number_input(
        "Estimated time value per min",
        min_value=0,
        value=int(st.session_state["value_of_time_huf_per_min"]),
        step=5,
        format="%d",
    )
    st.session_state["optimization_mode"] = st.selectbox(
        "Optimization mode",
        options=list(MODE_LABELS),
        format_func=MODE_LABELS.get,
        index=list(MODE_LABELS).index(st.session_state["optimization_mode"]),
    )
    st.session_state["transport_mode"] = st.selectbox(
        "Travel mode",
        options=list(TRANSPORT_LABELS),
        format_func=TRANSPORT_LABELS.get,
        index=list(TRANSPORT_LABELS).index(st.session_state["transport_mode"]),
    )
    st.session_state["consent_enabled"] = st.checkbox(
        "I consent to use simulated supported store, route, price, transaction, savings, and historical data for this local MVP calculation.",
        value=bool(st.session_state["consent_enabled"]),
    )
    st.session_state["use_live_routes"] = st.checkbox(
        "Use live routing via OpenRouteService",
        value=bool(st.session_state["use_live_routes"]),
        help="Uses OpenRouteService for walking and car route estimates when an API key is available. Public transport remains simulated in this MVP.",
    )
    render_route_api_status(str(st.session_state["transport_mode"]))
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Save profile settings", type="primary", use_container_width=True):
        try:
            update_user_profile(
                monthly_grocery_budget_huf=int(monthly_budget_huf),
                usual_store_id=str(usual_store_id),
                max_travel_minutes=int(max_travel_minutes),
                travel_cost_per_km_huf=int(travel_cost_per_km_huf),
                origin_address=str(origin_address),
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["last_success_message"] = "Profile settings saved locally for the simulated MVP."
            st.rerun()

    render_trust_audit_drawer()
    render_reset_demo_data()


def render_trust_audit_drawer() -> None:
    """Render simulation boundaries and formulas."""

    with st.expander("Trust and audit drawer"):
        st.markdown(
            """
            **Data used:** simulated product catalog, simulated store prices,
            Budapest II route estimates that may come from OpenRouteService when
            live routing is enabled and available, local planning basket, local
            profile settings, simulated finalized transactions, simulated savings
            goals, and simulated historical grocery spending.

            **Data not used:** no real banking connection, no real Revolut
            account, no real payment, no receipt OCR, no real retailer API, no
            live card/account data, and no confirmed in-store price feed.

            **Formulas:** net comparison total = product basket total + travel
            monetary cost + travel-time opportunity cost. Remaining budget after
            purchase = monthly budget - spent so far - product basket total.
            Travel monetary cost counts toward spending only when selected at
            finalization. Travel-time opportunity cost never counts as real
            spending.

            **Guardrails:** deterministic calculations only; no AI changes
            rankings or prices. Stores over max travel remain visible but cannot
            win. Unavailable required items block a store from winning. Savings
            movement is simulated only, with no real money movement. The app
            avoids guaranteed-cheapest claims and describes outputs as estimates
            based on supported simulated data.

            **Simulated-data disclaimer:** grocery prices, budgets,
            transactions, savings goals, historical spending, banking behavior,
            and pilot KPI data remain simulated for a local MVP demo. Route
            distance and travel time may be estimated by OpenRouteService for
            walking or car routes when enabled; otherwise they remain simulated.
            """
        )


def render_route_api_status(transport_mode: str) -> None:
    """Show live route availability without exposing credentials."""

    if transport_mode == TRANSPORT_PUBLIC_TRANSPORT:
        st.info("Public transport routes are simulated in this MVP")
        return

    if get_openrouteservice_api_key():
        st.success("Live route API key detected")
    else:
        st.warning("No live route key found — using simulated routes")


def render_reset_demo_data() -> None:
    """Render reset demo data control."""

    with st.expander("Reset simulated demo data"):
        st.caption(
            "Resetting restores simulated prices, profile, goals, historical data, favorites, previous lists, and transactions."
        )
        if st.button("Reset simulated demo data", use_container_width=True):
            reset_demo_data()
            st.session_state["comparison_requested"] = False
            st.session_state["last_success_message"] = "Simulated demo data reset."
            st.rerun()


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
                   usual_store_id, max_travel_minutes, travel_cost_per_km_huf,
                   origin_address
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
            ORDER BY CASE chain
                WHEN 'Lidl' THEN 1
                WHEN 'Aldi' THEN 2
                WHEN 'SPAR' THEN 3
                WHEN 'Tesco' THEN 4
                ELSE 5
            END
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
