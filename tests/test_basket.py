import pytest

from smartspend.basket import (
    Basket,
    add_product,
    clear_basket,
    edit_quantity,
    find_line,
    reload_basket,
    remove_product,
)


def test_add_product_creates_basket_line() -> None:
    basket = add_product(Basket(), "milk", quantity=2)

    assert len(basket.lines) == 1
    assert basket.lines[0].product_id == "milk"
    assert basket.lines[0].quantity == 2
    assert basket.spending_impact_huf == 0


def test_adding_same_product_increases_quantity_without_duplicates() -> None:
    basket = add_product(Basket(), "milk", quantity=1)
    basket = add_product(basket, "milk", quantity=2)

    assert len(basket.lines) == 1
    assert find_line(basket, "milk").quantity == 3


def test_edit_quantity_updates_existing_line() -> None:
    basket = add_product(Basket(), "milk", quantity=1)
    basket = edit_quantity(basket, "milk", quantity=4)

    assert find_line(basket, "milk").quantity == 4


def test_edit_quantity_to_zero_removes_product() -> None:
    basket = add_product(Basket(), "milk", quantity=1)
    basket = edit_quantity(basket, "milk", quantity=0)

    assert basket.lines == ()


def test_remove_product_deletes_only_that_product() -> None:
    basket = add_product(Basket(), "milk")
    basket = add_product(basket, "bread_loaf")
    basket = remove_product(basket, "milk")

    assert find_line(basket, "milk") is None
    assert find_line(basket, "bread_loaf").quantity == 1


def test_clear_basket_removes_all_lines() -> None:
    basket = add_product(Basket(), "milk")
    basket = add_product(basket, "bread_loaf")

    assert clear_basket(basket).lines == ()


def test_reload_basket_does_not_affect_spending() -> None:
    basket = reload_basket(
        [
            {"product_id": "milk", "quantity": 2},
            {"product_id": "bread_loaf", "quantity": 1},
        ]
    )

    assert len(basket.lines) == 2
    assert basket.spending_impact_huf == 0


def test_rejects_invalid_quantities() -> None:
    with pytest.raises(ValueError, match="positive"):
        add_product(Basket(), "milk", quantity=0)

    with pytest.raises(ValueError, match="negative"):
        edit_quantity(Basket(), "milk", quantity=-1)
