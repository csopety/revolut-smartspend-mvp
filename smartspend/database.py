"""SQLite persistence for the SmartSpend V2 demo data foundation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from smartspend.models import BasketItem, Product, Store

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "smartspend_demo.db"

STORE_SEEDS = [
    {
        "id": "lidl_huvosvolgyi",
        "name": "Lidl Huvosvolgyi ut",
        "chain": "Lidl",
        "neighborhood": "Huvosvolgy",
        "travel_minutes": 14,
        "distance_km": 3.5,
    },
    {
        "id": "aldi_mammut",
        "name": "Aldi Mammut",
        "chain": "Aldi",
        "neighborhood": "Szell Kalman ter",
        "travel_minutes": 9,
        "distance_km": 2.2,
    },
    {
        "id": "spar_rozsakert",
        "name": "SPAR Rozsakert",
        "chain": "SPAR",
        "neighborhood": "Torokvesz",
        "travel_minutes": 7,
        "distance_km": 1.8,
    },
    {
        "id": "tesco_becsi",
        "name": "Tesco Becsi ut",
        "chain": "Tesco",
        "neighborhood": "Ujlak",
        "travel_minutes": 18,
        "distance_km": 4.5,
    },
]

PRODUCT_SEEDS = [
    ("bread_loaf", "White bread loaf", "Feher kenyer", "Bakery", "1 loaf", 599, "kenyer bread loaf"),
    ("whole_wheat_bread", "Whole wheat bread", "Teljes kiorlesu kenyer", "Bakery", "1 loaf", 749, "barna kenyer wholegrain"),
    ("rolls", "Breakfast rolls", "Zsemle", "Bakery", "6 pieces", 529, "zsemle roll rolls"),
    ("kifli", "Crescent roll", "Kifli", "Bakery", "6 pieces", 489, "kifli crescent"),
    ("baguette", "Baguette", "Bagett", "Bakery", "1 piece", 399, "bagett baguette"),
    ("croissant", "Butter croissant", "Vajas croissant", "Bakery", "2 pieces", 579, "croissant vajas"),
    ("toast_bread", "Toast bread", "Toast kenyer", "Bakery", "500 g", 699, "toast sandwich"),
    ("pita", "Pita bread", "Pita", "Bakery", "4 pieces", 649, "pita flatbread"),
    ("cocoa_swirl", "Cocoa swirl", "Kakaos csiga", "Bakery", "2 pieces", 699, "kakaos csiga pastry"),
    ("brioche", "Sweet brioche", "Kalacs", "Bakery", "400 g", 899, "kalacs brioche"),
    ("milk", "Milk", "Tej", "Dairy", "1 liter", 419, "tej milk 2.8"),
    ("uht_milk", "UHT milk", "Tartos tej", "Dairy", "1 liter", 449, "tej tartos uht"),
    ("lactose_free_milk", "Lactose-free milk", "Laktozmentes tej", "Dairy", "1 liter", 699, "tej laktozmentes lactose free"),
    ("yogurt", "Plain yogurt", "Natur joghurt", "Dairy", "500 g", 499, "joghurt yogurt plain"),
    ("greek_yogurt", "Greek yogurt", "Gorog joghurt", "Dairy", "400 g", 799, "joghurt greek gorog"),
    ("sour_cream", "Sour cream", "Tejfol", "Dairy", "330 g", 549, "tejfol sour cream"),
    ("butter", "Butter", "Vaj", "Dairy", "200 g", 899, "vaj butter"),
    ("trappista_cheese", "Trappista cheese", "Trappista sajt", "Dairy", "250 g", 1199, "trap trappista sajt cheese"),
    ("cottage_cheese", "Cottage cheese", "Turo", "Dairy", "250 g", 699, "turo cottage cheese"),
    ("kefir", "Kefir", "Kefir", "Dairy", "450 g", 399, "kefir dairy"),
    ("mozzarella", "Mozzarella", "Mozzarella", "Dairy", "125 g", 599, "mozzarella sajt"),
    ("cream", "Cooking cream", "Fozotejszin", "Dairy", "200 ml", 499, "tejszin cream cooking"),
    ("eggs_10", "Eggs", "Tojas", "Dairy", "10 pieces", 1099, "tojas eggs"),
    ("apples", "Apples", "Alma", "Produce", "1 kg", 699, "alma apple apples"),
    ("bananas", "Bananas", "Banan", "Produce", "1 kg", 799, "banan banana bananas"),
    ("oranges", "Oranges", "Narancs", "Produce", "1 kg", 899, "narancs orange"),
    ("lemons", "Lemons", "Citrom", "Produce", "500 g", 599, "citrom lemon"),
    ("tomatoes", "Tomatoes", "Paradicsom", "Produce", "1 kg", 999, "paradicsom tomato tomatoes"),
    ("cucumber", "Cucumber", "Uborka", "Produce", "1 piece", 349, "cucu ubi uborka cucumber"),
    ("bell_pepper", "Bell pepper", "Paprika", "Produce", "500 g", 749, "paprika pepper"),
    ("potatoes", "Potatoes", "Burgonya", "Produce", "1 kg", 399, "krumpli burgonya potato"),
    ("onions", "Onions", "Voroshagyma", "Produce", "1 kg", 379, "hagyma onion"),
    ("garlic", "Garlic", "Fokhagyma", "Produce", "1 head", 199, "fokhagyma garlic"),
    ("carrots", "Carrots", "Sargarepa", "Produce", "1 kg", 449, "repa carrot"),
    ("lettuce", "Lettuce", "Salata", "Produce", "1 head", 499, "salata lettuce"),
    ("zucchini", "Zucchini", "Cukkini", "Produce", "1 kg", 799, "cukkini zucchini"),
    ("mushrooms", "Mushrooms", "Gomba", "Produce", "500 g", 899, "gomba mushroom"),
    ("strawberries", "Strawberries", "Eper", "Produce", "500 g", 1299, "eper strawberry"),
    ("chicken_breast", "Chicken breast", "Csirkemell", "Meat", "500 g", 1599, "csir csirke chicken breast"),
    ("chicken_thighs", "Chicken thighs", "Csirkecomb", "Meat", "500 g", 1199, "csir csirke thigh comb"),
    ("chicken_wings", "Chicken wings", "Csirkeszarny", "Meat", "500 g", 999, "csir csirke wings szarny"),
    ("chicken_mince", "Chicken mince", "Daralt csirke", "Meat", "500 g", 1399, "csir csirke daralt mince"),
    ("pork_loin", "Pork loin", "Serteskaraj", "Meat", "500 g", 1499, "sertes pork karaj"),
    ("minced_beef", "Minced beef", "Daralt marha", "Meat", "500 g", 1899, "marha beef mince"),
    ("turkey_breast", "Turkey breast", "Pulykamell", "Meat", "500 g", 1699, "pulyka turkey breast"),
    ("ham", "Sliced ham", "Sonka", "Meat", "150 g", 799, "sonka ham"),
    ("salami", "Winter salami", "Teli szalami", "Meat", "100 g", 999, "szalami salami"),
    ("bacon", "Bacon", "Szalonna", "Meat", "200 g", 1099, "bacon szalonna"),
    ("sausages", "Frankfurters", "Virsli", "Meat", "350 g", 999, "virsli sausage"),
    ("rice", "Rice", "Rizs", "Pantry", "1 kg", 699, "rizs rice"),
    ("pasta", "Pasta", "Teszta", "Pantry", "500 g", 449, "teszta pasta"),
    ("flour", "Wheat flour", "Buzaliszt", "Pantry", "1 kg", 399, "liszt flour"),
    ("sugar", "Sugar", "Cukor", "Pantry", "1 kg", 499, "cukor sugar"),
    ("cooking_oil", "Sunflower oil", "Napraforgo etolaj", "Pantry", "1 liter", 899, "olaj etolaj oil"),
    ("salt", "Salt", "So", "Pantry", "1 kg", 199, "so salt"),
    ("black_pepper", "Black pepper", "Fekete bors", "Pantry", "50 g", 449, "bors pepper"),
    ("paprika_powder", "Paprika powder", "Fuszerpaprika", "Pantry", "100 g", 699, "paprika powder fuszer"),
    ("tomato_sauce", "Tomato sauce", "Paradicsomszosz", "Pantry", "500 g", 599, "paradicsom szosz sauce"),
    ("canned_beans", "Canned beans", "Konzerv bab", "Pantry", "400 g", 499, "bab beans konzerv"),
    ("lentils", "Lentils", "Lencse", "Pantry", "500 g", 699, "lencse lentils"),
    ("oats", "Oats", "Zabpehely", "Pantry", "500 g", 599, "zab zabpehely oats"),
    ("cereal", "Breakfast cereal", "Reggeli pehely", "Pantry", "500 g", 1199, "cereal pehely"),
    ("muesli", "Muesli", "Muzli", "Pantry", "500 g", 1099, "muzli muesli"),
    ("honey", "Honey", "Mez", "Pantry", "500 g", 1599, "mez honey"),
    ("jam", "Strawberry jam", "Eperlekvar", "Pantry", "350 g", 899, "lekvar jam eper"),
    ("coffee", "Ground coffee", "Orolt kave", "Pantry", "250 g", 1499, "kave coffee"),
    ("tea", "Black tea", "Fekete tea", "Pantry", "20 bags", 699, "tea black"),
    ("sparkling_water", "Sparkling water", "Szensavas viz", "Drinks", "1.5 liter", 189, "viz water sparkling"),
    ("still_water", "Still water", "Szensavmentes viz", "Drinks", "1.5 liter", 169, "viz water still"),
    ("orange_juice", "Orange juice", "Narancsle", "Drinks", "1 liter", 699, "narancsle juice"),
    ("apple_juice", "Apple juice", "Almale", "Drinks", "1 liter", 599, "almale juice"),
    ("cola", "Cola", "Kola", "Drinks", "1.75 liter", 699, "kola cola"),
    ("dish_soap", "Dish soap", "Mosogatoszer", "Household", "500 ml", 699, "mosogatoszer dish soap"),
    ("laundry_detergent", "Laundry detergent", "Mosopor", "Household", "1.5 liter", 2499, "mososzer mosopor detergent"),
    ("paper_towels", "Paper towels", "Papirtorlo", "Household", "2 rolls", 899, "papirtorlo towels"),
    ("toilet_paper", "Toilet paper", "WC papir", "Household", "8 rolls", 1699, "wc papir toilet paper"),
    ("toothpaste", "Toothpaste", "Fogkrem", "Household", "75 ml", 799, "fogkrem toothpaste"),
    ("frozen_peas", "Frozen peas", "Fagyasztott borso", "Frozen", "450 g", 699, "borso frozen peas"),
    ("frozen_pizza", "Frozen pizza", "Fagyasztott pizza", "Frozen", "1 piece", 1299, "pizza frozen"),
    ("ice_cream", "Ice cream", "Jegkrem", "Frozen", "900 ml", 1699, "jegkrem ice cream"),
    ("sushi_rice", "Sushi rice", "Sushi rizs", "Pantry", "500 g", 1199, "sushi rizs rice"),
    ("fresh_salmon", "Fresh salmon fillet", "Lazacfile", "Meat", "250 g", 3299, "lazac salmon fish"),
]

UNAVAILABLE_PRICE_MARKERS = {
    ("fresh_salmon", "aldi_mammut"),
    ("fresh_salmon", "lidl_huvosvolgyi"),
    ("sushi_rice", "spar_rozsakert"),
    ("ice_cream", "aldi_mammut"),
}

STORE_PRICE_MULTIPLIERS = {
    "lidl_huvosvolgyi": 0.96,
    "aldi_mammut": 0.98,
    "spar_rozsakert": 1.08,
    "tesco_becsi": 1.03,
}


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the local SQLite database and required tables if missing."""

    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                chain TEXT NOT NULL UNIQUE,
                neighborhood TEXT NOT NULL,
                travel_minutes INTEGER NOT NULL CHECK (travel_minutes >= 0),
                distance_km REAL NOT NULL CHECK (distance_km >= 0)
            );

            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                display_name TEXT NOT NULL,
                district TEXT NOT NULL,
                monthly_grocery_budget_huf INTEGER NOT NULL CHECK (
                    monthly_grocery_budget_huf >= 0
                ),
                already_spent_current_month_huf INTEGER NOT NULL CHECK (
                    already_spent_current_month_huf >= 0
                ),
                usual_store_id TEXT NOT NULL REFERENCES stores(id),
                max_travel_minutes INTEGER NOT NULL CHECK (max_travel_minutes >= 0),
                travel_cost_per_km_huf INTEGER NOT NULL CHECK (
                    travel_cost_per_km_huf >= 0
                ),
                include_travel_cost_in_spending INTEGER NOT NULL CHECK (
                    include_travel_cost_in_spending IN (0, 1)
                )
            );

            CREATE TABLE IF NOT EXISTS savings_goals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_amount_huf INTEGER NOT NULL CHECK (target_amount_huf > 0),
                current_amount_huf INTEGER NOT NULL CHECK (current_amount_huf >= 0),
                monthly_contribution_huf INTEGER NOT NULL CHECK (
                    monthly_contribution_huf >= 0
                ),
                priority INTEGER NOT NULL CHECK (priority >= 1)
            );

            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                english_name TEXT NOT NULL,
                hungarian_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                aliases TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS store_prices (
                product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                store_id TEXT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
                price_huf INTEGER CHECK (price_huf IS NULL OR price_huf > 0),
                is_available INTEGER NOT NULL CHECK (is_available IN (0, 1)),
                is_promotion INTEGER NOT NULL CHECK (is_promotion IN (0, 1)),
                unavailable_reason TEXT,
                PRIMARY KEY (product_id, store_id),
                CHECK (
                    (is_available = 1 AND price_huf IS NOT NULL)
                    OR (is_available = 0 AND price_huf IS NULL)
                )
            );

            CREATE TABLE IF NOT EXISTS historical_monthly_spending (
                month TEXT PRIMARY KEY,
                grocery_spend_huf INTEGER NOT NULL CHECK (grocery_spend_huf >= 0),
                planned_budget_huf INTEGER NOT NULL CHECK (planned_budget_huf >= 0),
                transaction_count INTEGER NOT NULL CHECK (transaction_count >= 0),
                notes TEXT NOT NULL
            );
            """
        )


def seed_default_data(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Insert deterministic simulated V2 demo data if it is missing."""

    initialize_database(db_path)

    with connect(db_path) as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO stores (
                id, name, chain, neighborhood, travel_minutes, distance_km
            )
            VALUES (:id, :name, :chain, :neighborhood, :travel_minutes, :distance_km)
            """,
            STORE_SEEDS,
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO user_profile (
                id,
                display_name,
                district,
                monthly_grocery_budget_huf,
                already_spent_current_month_huf,
                usual_store_id,
                max_travel_minutes,
                travel_cost_per_km_huf,
                include_travel_cost_in_spending
            )
            VALUES (1, 'Demo User', 'Budapest II', 150000, 62000,
                    'spar_rozsakert', 18, 120, 0)
            """
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO savings_goals (
                id, name, target_amount_huf, current_amount_huf,
                monthly_contribution_huf, priority
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("rainy_day", "Rainy day buffer", 300000, 85000, 25000, 1),
                ("weekend_trip", "Weekend trip", 180000, 42000, 15000, 2),
                ("holiday_food", "Holiday grocery cushion", 90000, 18000, 8000, 3),
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO products (
                id, english_name, hungarian_name, category, unit, aliases
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            _product_rows(),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO store_prices (
                product_id, store_id, price_huf, is_available,
                is_promotion, unavailable_reason
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            _store_price_rows(),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO historical_monthly_spending (
                month, grocery_spend_huf, planned_budget_huf,
                transaction_count, notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("2025-12", 132400, 145000, 17, "Holiday cooking, still under plan"),
                ("2026-01", 124800, 145000, 15, "Lower spend after holidays"),
                ("2026-02", 138200, 145000, 16, "More home cooking"),
                ("2026-03", 149600, 150000, 18, "Near budget limit"),
                ("2026-04", 142300, 150000, 17, "Produce prices slightly lower"),
                ("2026-05", 156900, 155000, 19, "One larger pantry stock-up"),
            ],
        )


def reset_demo_data(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Delete and recreate the deterministic local demo database."""

    path = Path(db_path)
    if path.exists():
        path.unlink()

    initialize_database(path)
    seed_default_data(path)


def ensure_demo_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Initialize and seed the demo database when it has no product data."""

    initialize_database(db_path)
    with connect(db_path) as connection:
        product_count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        store_count = connection.execute("SELECT COUNT(*) FROM stores").fetchone()[0]
        price_count = connection.execute("SELECT COUNT(*) FROM store_prices").fetchone()[0]
        history_count = connection.execute(
            "SELECT COUNT(*) FROM historical_monthly_spending"
        ).fetchone()[0]

    expected_price_count = product_count * store_count
    if (
        product_count == 0
        or store_count == 0
        or price_count < expected_price_count
        or history_count < 6
    ):
        seed_default_data(db_path)


def load_products_for_optimizer(
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[Product]:
    """Load products that are available in every simulated store."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT p.*
            FROM products p
            JOIN store_prices sp ON sp.product_id = p.id
            GROUP BY p.id
            HAVING COUNT(*) = (SELECT COUNT(*) FROM stores)
               AND SUM(sp.is_available) = (SELECT COUNT(*) FROM stores)
            ORDER BY p.category, p.english_name
            """
        ).fetchall()

    return [
        Product(
            id=row["id"],
            name=row["english_name"],
            category=row["category"],
            unit=row["unit"],
            aliases=tuple(row["aliases"].split()),
        )
        for row in rows
    ]


def load_stores_for_optimizer(
    product_ids: Iterable[str] | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[Store]:
    """Load store records with available prices for optimizer-compatible products."""

    ensure_demo_database(db_path)
    selected_product_ids = set(product_ids or [])

    with connect(db_path) as connection:
        store_rows = connection.execute(
            """
            SELECT id, name, chain, neighborhood, travel_minutes
            FROM stores
            ORDER BY CASE chain
                WHEN 'Lidl' THEN 1
                WHEN 'Aldi' THEN 2
                WHEN 'SPAR' THEN 3
                WHEN 'Tesco' THEN 4
                ELSE 5
            END
            """
        ).fetchall()
        price_rows = connection.execute(
            """
            SELECT store_id, product_id, price_huf
            FROM store_prices
            WHERE is_available = 1
            """
        ).fetchall()

    prices_by_store: dict[str, dict[str, int]] = {row["id"]: {} for row in store_rows}
    for row in price_rows:
        if selected_product_ids and row["product_id"] not in selected_product_ids:
            continue
        prices_by_store[row["store_id"]][row["product_id"]] = row["price_huf"]

    return [
        Store(
            id=row["id"],
            name=row["name"],
            chain=row["chain"],
            neighborhood=row["neighborhood"],
            travel_minutes=row["travel_minutes"],
            travel_cost_huf=0,
            prices_huf=prices_by_store[row["id"]],
        )
        for row in store_rows
    ]


def load_default_basket(db_path: Path | str = DEFAULT_DB_PATH) -> list[BasketItem]:
    """Return the deterministic starter basket used by the current UI."""

    ensure_demo_database(db_path)
    return [
        BasketItem(product_id="bread_loaf", quantity=1),
        BasketItem(product_id="milk", quantity=2),
        BasketItem(product_id="apples", quantity=1),
        BasketItem(product_id="cucumber", quantity=1),
    ]


def _product_rows() -> list[tuple[str, str, str, str, str, str]]:
    return [
        (
            product_id,
            english_name,
            hungarian_name,
            category,
            unit,
            " ".join([product_id, english_name, hungarian_name, aliases]).lower(),
        )
        for product_id, english_name, hungarian_name, category, unit, _, aliases in PRODUCT_SEEDS
    ]


def _store_price_rows() -> list[tuple[str, str, int | None, int, int, str | None]]:
    rows = []
    for product_index, product_seed in enumerate(PRODUCT_SEEDS):
        product_id = product_seed[0]
        base_price_huf = product_seed[5]
        for store_index, store in enumerate(STORE_SEEDS):
            store_id = store["id"]
            if (product_id, store_id) in UNAVAILABLE_PRICE_MARKERS:
                rows.append(
                    (
                        product_id,
                        store_id,
                        None,
                        0,
                        0,
                        "Not included in this store's simulated assortment",
                    )
                )
                continue

            is_promotion = (product_index + store_index) % 13 == 0
            multiplier = STORE_PRICE_MULTIPLIERS[store_id]
            promotion_multiplier = 0.9 if is_promotion else 1.0
            price_huf = _round_price(base_price_huf * multiplier * promotion_multiplier)
            rows.append((product_id, store_id, price_huf, 1, int(is_promotion), None))

    return rows


def _round_price(raw_price_huf: float) -> int:
    rounded = round(raw_price_huf / 10) * 10 - 1
    return max(99, int(rounded))
