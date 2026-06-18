from pathlib import Path

from smartspend.basket import Basket, BasketLine
from smartspend.database import reset_demo_data
from smartspend.favorites import (
    add_previous_list_to_favorites,
    delete_favorite,
    get_favorite_items,
    list_favorites,
    reload_favorite_as_current_basket,
    save_current_basket_as_favorite,
)
from smartspend.transactions import finalize_purchase, get_spent_so_far


def test_save_current_basket_as_favorite_with_custom_name_has_no_spending_effect(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    starting_spent = get_spent_so_far(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1), BasketLine("milk", 2)))

    favorite = save_current_basket_as_favorite(
        basket=basket,
        name="My breakfast basket",
        db_path=db_path,
    )

    assert favorite.name == "My breakfast basket"
    assert get_spent_so_far(db_path) == starting_spent


def test_view_favorite_lists_and_items(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1), BasketLine("milk", 2)))
    favorite = save_current_basket_as_favorite(basket, "Basics", db_path)

    favorites = list_favorites(db_path)
    items = get_favorite_items(favorite.id, db_path)

    assert favorites[0].id == favorite.id
    assert favorites[0].name == "Basics"
    assert items == basket.lines


def test_reload_favorite_as_current_basket_has_no_budget_or_transaction_effect(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1), BasketLine("milk", 2)))
    favorite = save_current_basket_as_favorite(basket, "Basics", db_path)
    starting_spent = get_spent_so_far(db_path)

    reloaded = reload_favorite_as_current_basket(favorite.id, db_path)

    assert reloaded.lines == basket.lines
    assert get_spent_so_far(db_path) == starting_spent


def test_delete_favorite_has_no_spending_effect(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1),))
    favorite = save_current_basket_as_favorite(basket, "Temporary", db_path)
    starting_spent = get_spent_so_far(db_path)

    delete_favorite(favorite.id, db_path)

    assert list_favorites(db_path) == []
    assert get_spent_so_far(db_path) == starting_spent


def test_add_previous_list_to_favorites_has_no_extra_spending_effect(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    basket = Basket(lines=(BasketLine("bread_loaf", 1), BasketLine("milk", 1)))
    finalized = finalize_purchase("spar_rozsakert", basket, db_path=db_path)
    spent_after_finalization = get_spent_so_far(db_path)

    favorite = add_previous_list_to_favorites(
        previous_list_id=finalized.previous_list_id,
        name="Repeat weekly list",
        db_path=db_path,
    )

    assert favorite.name == "Repeat weekly list"
    assert get_favorite_items(favorite.id, db_path) == basket.lines
    assert get_spent_so_far(db_path) == spent_after_finalization
