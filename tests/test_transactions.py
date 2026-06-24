import sqlite3
from pathlib import Path

import pytest

from smartspend.basket import Basket, BasketLine, add_product
from smartspend.database import reset_demo_data
from smartspend.models import BasketItem, Store
from smartspend.optimizer import optimize_premium_basket
from smartspend.route_service import RouteResult
from smartspend.transactions import (
    clear_current_basket,
    count_transactions,
    finalize_purchase,
    get_previous_list_items,
    get_remaining_budget,
    get_spent_so_far,
    list_previous_lists,
    load_current_basket,
    reload_previous_list_as_current_basket,
    save_current_basket,
)


def count_rows(db_path: Path, table_name: str) -> int:
    with sqlite3.connect(db_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def test_building_and_saving_current_basket_does_not_update_spending(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    starting_spent = get_spent_so_far(db_path)

    basket = add_product(Basket(), "bread_loaf", quantity=2)
    save_current_basket(basket, db_path)

    assert get_spent_so_far(db_path) == starting_spent
    assert load_current_basket(db_path).lines == basket.lines


def test_running_recommendation_does_not_update_spending(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    starting_spent = get_spent_so_far(db_path)

    stores = [
        Store("usual", "Usual", "Usual", "Home", 5, 0, {"bread": 500}),
        Store("better", "Better", "Better", "Near", 6, 0, {"bread": 400}),
    ]
    routes = {
        "usual": RouteResult("usual", 1.0, 5, "Simulated"),
        "better": RouteResult("better", 1.2, 6, "Simulated"),
    }
    optimize_premium_basket(
        stores=stores,
        basket=[BasketItem("bread", 2)],
        monthly_budget_huf=100_000,
        already_spent_huf=starting_spent,
        max_travel_minutes=10,
        usual_store_id="usual",
        routes_by_store_id=routes,
    )

    assert get_spent_so_far(db_path) == starting_spent


def test_finalizing_purchase_updates_spending_and_saves_records(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(
        lines=(
            BasketLine("bread_loaf", 1),
            BasketLine("milk", 2),
        )
    )
    save_current_basket(basket, db_path)
    starting_spent = get_spent_so_far(db_path)

    result = finalize_purchase(
        store_id="lidl_huvosvolgyi",
        basket=basket,
        travel_monetary_cost_huf=500,
        travel_time_cost_huf=900,
        include_travel_monetary_cost=True,
        route_source="Simulated",
        list_name="Weekly basics",
        db_path=db_path,
    )

    assert result.spent_so_far_increase_huf == result.product_total_huf + 500
    assert result.travel_time_cost_huf == 900
    assert get_spent_so_far(db_path) == starting_spent + result.spent_so_far_increase_huf
    assert result.remaining_budget_huf == get_remaining_budget(db_path)
    assert "Purchase finalized. Spent so far increased by" in result.success_message
    assert count_rows(db_path, "transactions") == 1
    assert count_rows(db_path, "transaction_line_items") == 2
    assert count_rows(db_path, "previous_lists") == 1
    assert count_rows(db_path, "previous_list_items") == 2
    assert load_current_basket(db_path).lines == ()
    assert result.current_basket.lines == ()


def test_travel_monetary_cost_counts_only_when_selected(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1),))
    starting_spent = get_spent_so_far(db_path)

    result = finalize_purchase(
        store_id="aldi_mammut",
        basket=basket,
        travel_monetary_cost_huf=700,
        travel_time_cost_huf=9999,
        include_travel_monetary_cost=False,
        db_path=db_path,
    )

    assert result.spent_so_far_increase_huf == result.product_total_huf
    assert result.travel_cost_counted_huf == 0
    assert get_spent_so_far(db_path) == starting_spent + result.product_total_huf


def test_finalization_accepts_openrouteservice_route_source(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1),))

    result = finalize_purchase(
        store_id="aldi_mammut",
        basket=basket,
        route_source="OpenRouteService",
        db_path=db_path,
    )

    assert result.transaction_id == 1
    assert count_rows(db_path, "transactions") == 1


def test_finalization_validates_product_availability(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("fresh_salmon", 1),))

    with pytest.raises(ValueError, match="unavailable"):
        finalize_purchase("aldi_mammut", basket, db_path=db_path)


def test_previous_lists_can_be_viewed_and_reloaded_without_budget_side_effects(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1), BasketLine("milk", 1)))
    result = finalize_purchase("spar_rozsakert", basket, db_path=db_path)
    spent_after_finalization = get_spent_so_far(db_path)
    transaction_count = count_transactions(db_path)

    previous_lists = list_previous_lists(db_path)
    previous_items = get_previous_list_items(result.previous_list_id, db_path)
    reloaded = reload_previous_list_as_current_basket(result.previous_list_id, db_path)

    assert previous_lists[0].id == result.previous_list_id
    assert previous_items == basket.lines
    assert reloaded.lines == basket.lines
    assert get_spent_so_far(db_path) == spent_after_finalization
    assert count_transactions(db_path) == transaction_count


def test_clear_current_basket_does_not_update_spending(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1),))
    save_current_basket(basket, db_path)
    starting_spent = get_spent_so_far(db_path)

    cleared = clear_current_basket(db_path)

    assert cleared.lines == ()
    assert load_current_basket(db_path).lines == ()
    assert get_spent_so_far(db_path) == starting_spent
