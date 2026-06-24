"""Transaction and previous-list persistence for SmartSpend V2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from smartspend.basket import Basket, BasketLine, reload_basket
from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database

SIMULATED_TRANSACTION_NOTICE = (
    "Simulated grocery purchase for the local SmartSpend MVP. No external account "
    "or payment rail was touched."
)


@dataclass(frozen=True)
class FinalizationResult:
    """Values needed after finalizing a simulated purchase."""

    transaction_id: int
    previous_list_id: int
    spent_so_far_increase_huf: int
    remaining_budget_huf: int
    product_total_huf: int
    travel_cost_counted_huf: int
    travel_time_cost_huf: int
    current_basket: Basket
    success_message: str


@dataclass(frozen=True)
class PreviousListSummary:
    """One finalized grocery list saved from a transaction."""

    id: int
    transaction_id: int
    name: str
    store_id: str
    created_at: str


def get_spent_so_far(db_path: Path | str = DEFAULT_DB_PATH) -> int:
    """Return current simulated grocery spending from the user profile."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        return connection.execute(
            "SELECT already_spent_current_month_huf FROM user_profile WHERE id = 1"
        ).fetchone()[0]


def get_remaining_budget(db_path: Path | str = DEFAULT_DB_PATH) -> int:
    """Return current simulated remaining grocery budget."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT monthly_grocery_budget_huf, already_spent_current_month_huf
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    return row["monthly_grocery_budget_huf"] - row["already_spent_current_month_huf"]


def save_current_basket(
    basket: Basket,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> Basket:
    """Persist the current planning basket without changing spending."""

    ensure_demo_database(db_path)
    validate_basket_quantities(basket)

    with connect(db_path) as connection:
        connection.execute("DELETE FROM current_basket_items")
        connection.executemany(
            """
            INSERT INTO current_basket_items (product_id, quantity)
            VALUES (?, ?)
            """,
            [(line.product_id, line.quantity) for line in basket.lines],
        )

    return Basket(lines=basket.lines, spending_impact_huf=0)


def load_current_basket(db_path: Path | str = DEFAULT_DB_PATH) -> Basket:
    """Load the current planning basket without changing spending."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT product_id, quantity
            FROM current_basket_items
            ORDER BY product_id
            """
        ).fetchall()

    return reload_basket(
        [
            {"product_id": row["product_id"], "quantity": row["quantity"]}
            for row in rows
        ]
    )


def clear_current_basket(db_path: Path | str = DEFAULT_DB_PATH) -> Basket:
    """Clear the persisted current basket without changing spending."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        connection.execute("DELETE FROM current_basket_items")

    return Basket()


def finalize_purchase(
    store_id: str,
    basket: Basket,
    travel_monetary_cost_huf: int = 0,
    travel_time_cost_huf: int = 0,
    include_travel_monetary_cost: bool = False,
    route_source: str = "Simulated",
    list_name: str | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> FinalizationResult:
    """Finalize a simulated purchase and update spending exactly once."""

    ensure_demo_database(db_path)
    validate_basket_quantities(basket)
    if not basket.lines:
        raise ValueError("Cannot finalize an empty basket.")
    if travel_monetary_cost_huf < 0:
        raise ValueError("Travel monetary cost cannot be negative.")
    if travel_time_cost_huf < 0:
        raise ValueError("Travel-time cost cannot be negative.")
    valid_route_sources = {"Simulated", "OpenRouteService"}
    if route_source not in valid_route_sources:
        raise ValueError(
            "Route source must be 'Simulated' or 'OpenRouteService'."
        )

    finalized_at = datetime.now(UTC).isoformat(timespec="seconds")

    with connect(db_path) as connection:
        price_rows = get_available_prices(connection, store_id, basket.lines)
        product_total_huf = sum(
            price_rows[line.product_id] * line.quantity for line in basket.lines
        )
        travel_cost_counted_huf = (
            travel_monetary_cost_huf if include_travel_monetary_cost else 0
        )
        spending_increase_huf = product_total_huf + travel_cost_counted_huf

        profile = connection.execute(
            """
            SELECT monthly_grocery_budget_huf, already_spent_current_month_huf
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()
        new_spent_huf = (
            profile["already_spent_current_month_huf"] + spending_increase_huf
        )
        remaining_budget_huf = profile["monthly_grocery_budget_huf"] - new_spent_huf

        cursor = connection.execute(
            """
            INSERT INTO transactions (
                store_id,
                finalized_at,
                product_total_huf,
                travel_monetary_cost_huf,
                travel_cost_counted_huf,
                travel_time_cost_huf,
                spending_increase_huf,
                remaining_budget_huf,
                route_source,
                simulated_notice
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                store_id,
                finalized_at,
                product_total_huf,
                travel_monetary_cost_huf,
                travel_cost_counted_huf,
                travel_time_cost_huf,
                spending_increase_huf,
                remaining_budget_huf,
                route_source,
                SIMULATED_TRANSACTION_NOTICE,
            ),
        )
        transaction_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO transaction_line_items (
                transaction_id, product_id, quantity, unit_price_huf, line_total_huf
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    transaction_id,
                    line.product_id,
                    line.quantity,
                    price_rows[line.product_id],
                    price_rows[line.product_id] * line.quantity,
                )
                for line in basket.lines
            ],
        )
        connection.execute(
            """
            UPDATE user_profile
            SET already_spent_current_month_huf = ?
            WHERE id = 1
            """,
            (new_spent_huf,),
        )

        previous_cursor = connection.execute(
            """
            INSERT INTO previous_lists (transaction_id, name, store_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                transaction_id,
                list_name or f"Purchase #{transaction_id}",
                store_id,
                finalized_at,
            ),
        )
        previous_list_id = previous_cursor.lastrowid
        connection.executemany(
            """
            INSERT INTO previous_list_items (
                previous_list_id, product_id, quantity
            )
            VALUES (?, ?, ?)
            """,
            [
                (previous_list_id, line.product_id, line.quantity)
                for line in basket.lines
            ],
        )
        connection.execute("DELETE FROM current_basket_items")

    success_message = (
        "Purchase finalized. Spent so far increased by "
        f"{spending_increase_huf} HUF. Remaining budget is now "
        f"{remaining_budget_huf} HUF."
    )

    return FinalizationResult(
        transaction_id=transaction_id,
        previous_list_id=previous_list_id,
        spent_so_far_increase_huf=spending_increase_huf,
        remaining_budget_huf=remaining_budget_huf,
        product_total_huf=product_total_huf,
        travel_cost_counted_huf=travel_cost_counted_huf,
        travel_time_cost_huf=travel_time_cost_huf,
        current_basket=Basket(),
        success_message=success_message,
    )


def list_previous_lists(
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[PreviousListSummary]:
    """Return finalized grocery lists."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, transaction_id, name, store_id, created_at
            FROM previous_lists
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        PreviousListSummary(
            id=row["id"],
            transaction_id=row["transaction_id"],
            name=row["name"],
            store_id=row["store_id"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def get_previous_list_items(
    previous_list_id: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> tuple[BasketLine, ...]:
    """Return line items for a finalized grocery list."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT product_id, quantity
            FROM previous_list_items
            WHERE previous_list_id = ?
            ORDER BY id
            """,
            (previous_list_id,),
        ).fetchall()

    return tuple(
        BasketLine(product_id=row["product_id"], quantity=row["quantity"])
        for row in rows
    )


def reload_previous_list_as_current_basket(
    previous_list_id: int,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> Basket:
    """Reload a previous list for planning without updating spending."""

    basket = Basket(lines=get_previous_list_items(previous_list_id, db_path))
    return save_current_basket(basket, db_path)


def count_transactions(db_path: Path | str = DEFAULT_DB_PATH) -> int:
    """Return the number of simulated finalized purchases."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        return connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


def validate_basket_quantities(basket: Basket) -> None:
    """Validate basket quantities before persistence or finalization."""

    for line in basket.lines:
        if line.quantity <= 0:
            raise ValueError("Basket quantities must be positive.")


def get_available_prices(
    connection,
    store_id: str,
    lines: tuple[BasketLine, ...],
) -> dict[str, int]:
    """Validate product availability and return unit prices."""

    prices: dict[str, int] = {}
    for line in lines:
        row = connection.execute(
            """
            SELECT price_huf, is_available
            FROM store_prices
            WHERE store_id = ? AND product_id = ?
            """,
            (store_id, line.product_id),
        ).fetchone()
        if row is None:
            raise ValueError(
                f"Product '{line.product_id}' has no price row for store '{store_id}'."
            )
        if row["is_available"] != 1 or row["price_huf"] is None:
            raise ValueError(
                f"Product '{line.product_id}' is unavailable at store '{store_id}'."
            )
        prices[line.product_id] = row["price_huf"]

    return prices
