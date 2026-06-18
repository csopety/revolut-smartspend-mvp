import sqlite3
from pathlib import Path

from smartspend.database import initialize_database, reset_demo_data


def count_rows(db_path: Path, table_name: str) -> int:
    with sqlite3.connect(db_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def test_database_initializes_required_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    initialize_database(db_path)

    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }

    assert {
        "user_profile",
        "savings_goals",
        "products",
        "stores",
        "store_prices",
        "historical_monthly_spending",
        "transactions",
        "transaction_line_items",
        "previous_lists",
        "previous_list_items",
        "favorite_lists",
        "favorite_list_items",
        "current_basket_items",
        "savings_movements",
    }.issubset(table_names)


def test_seeded_demo_database_has_required_product_and_store_counts(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    assert count_rows(db_path, "products") >= 75
    assert count_rows(db_path, "stores") == 4


def test_every_product_has_a_price_or_unavailable_marker_for_every_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    product_count = count_rows(db_path, "products")
    store_count = count_rows(db_path, "stores")
    price_row_count = count_rows(db_path, "store_prices")

    with sqlite3.connect(db_path) as connection:
        invalid_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM store_prices
            WHERE (is_available = 1 AND price_huf IS NULL)
               OR (is_available = 0 AND price_huf IS NOT NULL)
            """
        ).fetchone()[0]

    assert price_row_count == product_count * store_count
    assert invalid_rows == 0


def test_seeded_demo_database_has_at_least_six_historical_months(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    assert count_rows(db_path, "historical_monthly_spending") >= 6


def test_product_aliases_include_required_search_terms(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        aliases = "\n".join(
            row[0]
            for row in connection.execute(
                "SELECT aliases FROM products ORDER BY id"
            ).fetchall()
        )

    for term in ["cucu", "ubi", "tej", "csir", "trap"]:
        assert term in aliases
