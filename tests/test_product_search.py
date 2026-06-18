from pathlib import Path

from smartspend.database import reset_demo_data
from smartspend.product_search import search_products


def test_empty_query_returns_no_results(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    assert search_products("", db_path=db_path) == []
    assert search_products("   ", db_path=db_path) == []


def test_cucu_returns_cucumber_first(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("cucu", db_path=db_path)

    assert results[0].product_id == "cucumber"
    assert results[0].display_name == "Cucumber"


def test_ubi_returns_cucumber_first(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("ubi", db_path=db_path)

    assert results[0].product_id == "cucumber"
    assert results[0].display_name == "Cucumber"


def test_tej_returns_milk_first(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("tej", db_path=db_path)

    assert results[0].product_id == "milk"
    assert results[0].display_name == "Milk"


def test_csir_returns_chicken_products(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("csir", db_path=db_path)

    assert results
    assert all("chicken" in result.english_name.lower() for result in results[:4])


def test_trap_returns_trappista_cheese_first(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("trap", db_path=db_path)

    assert results[0].product_id == "trappista_cheese"
    assert results[0].display_name == "Trappista cheese"


def test_prefix_and_partial_search_are_supported(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    prefix_results = search_products("tom", db_path=db_path)
    partial_results = search_products("berry", db_path=db_path)

    assert prefix_results[0].product_id == "tomatoes"
    assert any(result.product_id == "strawberries" for result in partial_results)


def test_exact_display_name_match_has_top_ranking(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("Milk", db_path=db_path)

    assert results[0].product_id == "milk"
    assert results[0].match_type == "exact"
    assert results[0].rank_score == 1


def test_search_limit_is_respected(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    results = search_products("tej", limit=2, db_path=db_path)

    assert len(results) == 2
