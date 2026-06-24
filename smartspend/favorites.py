"""Favorite grocery list persistence for SmartSpend V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from smartspend.basket import Basket, BasketLine
from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database
from smartspend.transactions import (
    get_previous_list_items,
    save_current_basket,
    validate_basket_quantities,
)


@dataclass(frozen=True)
class FavoriteListSummary:
    """One saved favorite grocery list."""

    id: int
    name: str
    created_at: str


def save_current_basket_as_favorite(
    basket: Basket,
    name: str,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> FavoriteListSummary:
    """Save a planned basket as a favorite without changing spending."""

    validate_favorite_name(name)
    validate_basket_quantities(basket)
    if not basket.lines:
        raise ValueError("Cannot save an empty basket as a favorite.")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO favorite_lists (name, created_at)
            VALUES (?, ?)
            """,
            (name.strip(), created_at),
        )
        favorite_id = cursor.lastrowid
        connection.executemany(
            """
            INSERT INTO favorite_list_items (favorite_list_id, product_id, quantity)
            VALUES (?, ?, ?)
            """,
            [(favorite_id, line.product_id, line.quantity) for line in basket.lines],
        )

    return FavoriteListSummary(id=favorite_id, name=name.strip(), created_at=created_at)


def add_previous_list_to_favorites(
    previous_list_id: int,
    name: str | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> FavoriteListSummary:
    """Copy a finalized previous list into favorites without changing spending."""

    lines = get_previous_list_items(previous_list_id, db_path)
    if not lines:
        raise ValueError(f"No previous list found with id '{previous_list_id}'.")

    favorite_name = name or f"Favorite from previous list #{previous_list_id}"
    return save_current_basket_as_favorite(
        basket=Basket(lines=lines),
        name=favorite_name,
        db_path=db_path,
    )


def list_favorites(
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[FavoriteListSummary]:
    """Return saved favorite grocery lists."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, created_at
            FROM favorite_lists
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        FavoriteListSummary(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def get_favorite_items(
    favorite_list_id: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> tuple[BasketLine, ...]:
    """Return items in one favorite grocery list."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT product_id, quantity
            FROM favorite_list_items
            WHERE favorite_list_id = ?
            ORDER BY id
            """,
            (favorite_list_id,),
        ).fetchall()

    return tuple(
        BasketLine(product_id=row["product_id"], quantity=row["quantity"])
        for row in rows
    )


def reload_favorite_as_current_basket(
    favorite_list_id: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> Basket:
    """Reload a favorite list for planning without changing spending."""

    lines = get_favorite_items(favorite_list_id, db_path)
    if not lines:
        raise ValueError(f"No favorite list found with id '{favorite_list_id}'.")

    return save_current_basket(Basket(lines=lines), db_path)


def delete_favorite(
    favorite_list_id: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> None:
    """Delete a favorite list without changing spending."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        connection.execute(
            "DELETE FROM favorite_lists WHERE id = ?",
            (favorite_list_id,),
        )


def validate_favorite_name(name: str) -> None:
    """Validate a user-provided favorite name."""

    if not name.strip():
        raise ValueError("Favorite name cannot be empty.")
