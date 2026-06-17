"""Simulated grocery data for the SmartSpend MVP.

All values are invented for demonstration purposes. The data is intentionally
small so beginners can read it and understand how the later optimizer works.
"""

from smartspend.models import BasketItem, GroceryDataset, Product, Store


def get_product_categories() -> list[str]:
    """Return the three grocery categories used in the MVP."""

    return ["Bakery", "Dairy", "Produce"]


def get_products() -> list[Product]:
    """Return simulated products across three basic grocery categories."""

    return [
        Product(
            id="bread_loaf",
            name="White bread loaf",
            category="Bakery",
            unit="1 loaf",
        ),
        Product(
            id="rolls",
            name="Breakfast rolls",
            category="Bakery",
            unit="6 pieces",
        ),
        Product(
            id="milk",
            name="Milk",
            category="Dairy",
            unit="1 liter",
        ),
        Product(
            id="yogurt",
            name="Plain yogurt",
            category="Dairy",
            unit="500 g",
        ),
        Product(
            id="apples",
            name="Apples",
            category="Produce",
            unit="1 kg",
        ),
        Product(
            id="tomatoes",
            name="Tomatoes",
            category="Produce",
            unit="1 kg",
        ),
    ]


def get_stores() -> list[Store]:
    """Return four simulated Budapest II grocery chains with product prices."""

    return [
        Store(
            id="aldi_mammut",
            name="Aldi Mammut",
            chain="Aldi",
            neighborhood="Szell Kalman ter",
            travel_minutes=9,
            travel_cost_huf=0,
            prices_huf={
                "bread_loaf": 549,
                "rolls": 499,
                "milk": 399,
                "yogurt": 429,
                "apples": 699,
                "tomatoes": 899,
            },
        ),
        Store(
            id="lidl_huvosvolgyi",
            name="Lidl Huvosvolgyi ut",
            chain="Lidl",
            neighborhood="Huvosvolgy",
            travel_minutes=14,
            travel_cost_huf=450,
            prices_huf={
                "bread_loaf": 529,
                "rolls": 479,
                "milk": 389,
                "yogurt": 399,
                "apples": 649,
                "tomatoes": 849,
            },
        ),
        Store(
            id="spar_rozsakert",
            name="SPAR Rozsakert",
            chain="SPAR",
            neighborhood="Torokvesz",
            travel_minutes=7,
            travel_cost_huf=0,
            prices_huf={
                "bread_loaf": 599,
                "rolls": 549,
                "milk": 429,
                "yogurt": 459,
                "apples": 729,
                "tomatoes": 949,
            },
        ),
        Store(
            id="tesco_becsi",
            name="Tesco Becsi ut",
            chain="Tesco",
            neighborhood="Ujlak",
            travel_minutes=18,
            travel_cost_huf=450,
            prices_huf={
                "bread_loaf": 579,
                "rolls": 519,
                "milk": 419,
                "yogurt": 449,
                "apples": 679,
                "tomatoes": 879,
            },
        ),
    ]


def get_default_basket() -> list[BasketItem]:
    """Return a small starter basket for demos and tests."""

    return [
        BasketItem(product_id="bread_loaf", quantity=1),
        BasketItem(product_id="milk", quantity=2),
        BasketItem(product_id="apples", quantity=1),
    ]


def get_grocery_dataset() -> GroceryDataset:
    """Return the complete simulated dataset for the MVP."""

    return GroceryDataset(
        products=get_products(),
        stores=get_stores(),
        default_basket=get_default_basket(),
    )
