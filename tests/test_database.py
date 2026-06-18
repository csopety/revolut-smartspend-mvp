import sqlite3
from pathlib import Path

from smartspend.database import (
    DEFAULT_ORIGIN_ADDRESS,
    DEFAULT_ORIGIN_LATITUDE,
    DEFAULT_ORIGIN_LONGITUDE,
    ensure_demo_database,
    initialize_database,
    reset_demo_data,
    update_user_profile,
)

EXPECTED_STORE_COORDINATES = {
    "lidl_huvosvolgyi": (47.54510653574783, 18.962848219071322),
    "tesco_becsi": (47.56307158883334, 19.021628036706577),
    "aldi_mammut": (47.508623779082136, 19.026129496998564),
    "spar_rozsakert": (47.522678948771826, 19.014748181658817),
}


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


def test_historical_monthly_spending_has_enriched_snapshots(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(historical_monthly_spending)"
            ).fetchall()
        }
        row = connection.execute(
            """
            SELECT *
            FROM historical_monthly_spending
            WHERE month = '2026-05'
            """
        ).fetchone()

    assert {
        "week_1_spend_huf",
        "week_2_spend_huf",
        "week_3_spend_huf",
        "week_4_spend_huf",
        "lidl_spend_huf",
        "aldi_spend_huf",
        "spar_spend_huf",
        "tesco_spend_huf",
        "highest_purchase_huf",
        "most_used_store",
    }.issubset(columns)
    assert row["week_1_spend_huf"] > 0
    assert row["lidl_spend_huf"] > 0
    assert row["highest_purchase_huf"] > 0
    assert row["most_used_store"] == "Lidl"


def test_update_user_profile_persists_setup_without_changing_spending(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        original_spent = connection.execute(
            """
            SELECT already_spent_current_month_huf
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()[0]

    update_user_profile(
        monthly_grocery_budget_huf=175000,
        usual_store_id="lidl_huvosvolgyi",
        max_travel_minutes=22,
        travel_cost_per_km_huf=135,
        origin_address="Margit korut 1, Budapest II",
        db_path=db_path,
    )

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT monthly_grocery_budget_huf, usual_store_id,
                   max_travel_minutes, travel_cost_per_km_huf,
                   origin_address, already_spent_current_month_huf
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    assert row["monthly_grocery_budget_huf"] == 175000
    assert row["usual_store_id"] == "lidl_huvosvolgyi"
    assert row["max_travel_minutes"] == 22
    assert row["travel_cost_per_km_huf"] == 135
    assert row["origin_address"] == "Margit korut 1, Budapest II"
    assert row["already_spent_current_month_huf"] == original_spent


def test_user_profile_default_origin_is_seeded(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT origin_address, origin_latitude, origin_longitude
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    assert row["origin_address"] == DEFAULT_ORIGIN_ADDRESS
    assert row["origin_latitude"] == DEFAULT_ORIGIN_LATITUDE
    assert row["origin_longitude"] == DEFAULT_ORIGIN_LONGITUDE


def test_stores_have_seeded_latitude_and_longitude(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(stores)").fetchall()
        }
        rows = connection.execute(
            """
            SELECT id, chain, latitude, longitude
            FROM stores
            ORDER BY id
            """
        ).fetchall()

    assert {"latitude", "longitude"}.issubset(columns)
    assert len(rows) == 4
    assert {row["chain"] for row in rows} == {"Aldi", "Lidl", "SPAR", "Tesco"}
    for row in rows:
        expected_latitude, expected_longitude = EXPECTED_STORE_COORDINATES[row["id"]]
        assert row["latitude"] == expected_latitude
        assert row["longitude"] == expected_longitude


def test_ensure_demo_database_updates_existing_store_coordinates(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE stores
            SET latitude = 47.0,
                longitude = 19.0
            WHERE id = 'lidl_huvosvolgyi'
            """
        )

    ensure_demo_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT latitude, longitude
            FROM stores
            WHERE id = 'lidl_huvosvolgyi'
            """
        ).fetchone()

    assert row["latitude"] == EXPECTED_STORE_COORDINATES["lidl_huvosvolgyi"][0]
    assert row["longitude"] == EXPECTED_STORE_COORDINATES["lidl_huvosvolgyi"][1]


def test_reset_demo_data_preserves_valid_route_coordinates(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"

    reset_demo_data(db_path)
    reset_demo_data(db_path)

    with sqlite3.connect(db_path) as connection:
        invalid_store_coordinates = connection.execute(
            """
            SELECT COUNT(*)
            FROM stores
            WHERE latitude NOT BETWEEN -90 AND 90
               OR longitude NOT BETWEEN -180 AND 180
               OR latitude IS NULL
               OR longitude IS NULL
            """
        ).fetchone()[0]
        profile = connection.execute(
            """
            SELECT origin_latitude, origin_longitude
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    assert invalid_store_coordinates == 0
    assert profile[0] == DEFAULT_ORIGIN_LATITUDE
    assert profile[1] == DEFAULT_ORIGIN_LONGITUDE


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
