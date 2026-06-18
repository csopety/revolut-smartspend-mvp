"""Side-effect-free basket logic for SmartSpend planning."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class BasketLine:
    """One product and quantity inside a planned basket."""

    product_id: str
    quantity: int


@dataclass(frozen=True)
class Basket:
    """A planned basket that does not affect spending until checkout."""

    lines: tuple[BasketLine, ...] = ()
    spending_impact_huf: int = 0


def add_product(basket: Basket, product_id: str, quantity: int = 1) -> Basket:
    """Add a product, increasing quantity when it already exists."""

    if quantity <= 0:
        raise ValueError("Quantity to add must be positive.")

    existing_line = find_line(basket, product_id)
    if existing_line is None:
        return replace(
            basket,
            lines=(*basket.lines, BasketLine(product_id=product_id, quantity=quantity)),
        )

    return edit_quantity(
        basket=basket,
        product_id=product_id,
        quantity=existing_line.quantity + quantity,
    )


def edit_quantity(basket: Basket, product_id: str, quantity: int) -> Basket:
    """Set a basket line quantity, removing the product when quantity is zero."""

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    if quantity == 0:
        return remove_product(basket, product_id)

    updated_lines = []
    found_product = False
    for line in basket.lines:
        if line.product_id == product_id:
            updated_lines.append(BasketLine(product_id=product_id, quantity=quantity))
            found_product = True
        else:
            updated_lines.append(line)

    if not found_product:
        updated_lines.append(BasketLine(product_id=product_id, quantity=quantity))

    return replace(basket, lines=tuple(updated_lines))


def remove_product(basket: Basket, product_id: str) -> Basket:
    """Remove one product from the planned basket."""

    return replace(
        basket,
        lines=tuple(line for line in basket.lines if line.product_id != product_id),
    )


def clear_basket(basket: Basket) -> Basket:
    """Remove every product from the planned basket."""

    return replace(basket, lines=())


def reload_basket(lines: list[dict[str, int | str]] | tuple[BasketLine, ...]) -> Basket:
    """Reload saved basket contents without changing spending."""

    if isinstance(lines, tuple) and all(isinstance(line, BasketLine) for line in lines):
        return Basket(lines=lines, spending_impact_huf=0)

    basket = Basket()
    for line in lines:
        product_id = str(line["product_id"])
        quantity = int(line["quantity"])
        basket = edit_quantity(basket, product_id, quantity)

    return basket


def find_line(basket: Basket, product_id: str) -> BasketLine | None:
    """Return one basket line by product ID."""

    return next((line for line in basket.lines if line.product_id == product_id), None)
