"""Compatibility loaders for the SmartSpend demo dataset.

V2 stores the simulated data in SQLite. These functions keep the existing UI
and tests working while the richer persistence layer is introduced.
"""

from smartspend.database import (
    load_default_basket,
    load_products_for_optimizer,
    load_stores_for_optimizer,
)
from smartspend.models import BasketItem, GroceryDataset, Product, Store


def get_product_categories() -> list[str]:
    """Return product categories from the persisted demo catalog."""

    return sorted({product.category for product in get_products()})


def get_products() -> list[Product]:
    """Return optimizer-compatible products from the SQLite demo catalog."""

    return load_products_for_optimizer()


def get_stores() -> list[Store]:
    """Return persisted stores with prices for currently visible products."""

    products = get_products()
    return load_stores_for_optimizer(product.id for product in products)


def get_default_basket() -> list[BasketItem]:
    """Return the deterministic starter basket for demos and tests."""

    return load_default_basket()


def get_grocery_dataset() -> GroceryDataset:
    """Return the complete UI-compatible dataset for the MVP."""

    products = get_products()
    return GroceryDataset(
        products=products,
        stores=load_stores_for_optimizer(product.id for product in products),
        default_basket=get_default_basket(),
    )
