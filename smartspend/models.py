"""Core data models for the SmartSpend MVP.

The app uses simulated grocery data only. These models keep that data explicit
and easy to inspect before any optimization logic is applied.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    """A grocery product available in the simulated Budapest II demo."""

    id: str
    name: str
    category: str
    unit: str


@dataclass(frozen=True)
class Store:
    """A simulated grocery store option near Budapest II."""

    id: str
    name: str
    chain: str
    neighborhood: str
    travel_minutes: int
    travel_cost_huf: int
    prices_huf: dict[str, int]


@dataclass(frozen=True)
class BasketItem:
    """A selected product and quantity for a grocery basket."""

    product_id: str
    quantity: int


@dataclass(frozen=True)
class GroceryDataset:
    """All simulated data needed by the MVP data layer."""

    products: list[Product]
    stores: list[Store]
    default_basket: list[BasketItem]
