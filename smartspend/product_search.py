"""Product search for the SmartSpend V2 catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from smartspend.database import DEFAULT_DB_PATH, connect, ensure_demo_database


@dataclass(frozen=True)
class ProductSearchResult:
    """One ranked product search result."""

    product_id: str
    display_name: str
    english_name: str
    hungarian_name: str
    category: str
    unit: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    match_type: str
    rank_score: int


def search_products(
    query: str,
    limit: int = 10,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[ProductSearchResult]:
    """Search products by names, aliases, prefixes, partials, and tags."""

    normalized_query = normalize_text(query)
    if not normalized_query:
        return []

    ensure_demo_database(db_path)
    results = []

    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, english_name, hungarian_name, category, unit, aliases
            FROM products
            ORDER BY english_name
            """
        ).fetchall()

    for row in rows:
        result = score_product(row, normalized_query)
        if result is not None:
            results.append(result)

    results.sort(
        key=lambda result: (
            result.rank_score,
            result.display_name.lower() != normalized_query,
            len(result.display_name),
            result.display_name.lower(),
            result.product_id,
        )
    )
    return results[:limit]


def score_product(row: object, query: str) -> ProductSearchResult | None:
    """Score a product row against one normalized query."""

    english_name = row["english_name"]
    hungarian_name = row["hungarian_name"]
    display_name = english_name
    aliases = tuple(normalize_text(row["aliases"]).split())
    tags = build_tags(row)

    names = {
        normalize_text(english_name),
        normalize_text(hungarian_name),
        normalize_text(display_name),
    }
    name_tokens = set().union(*(name.split() for name in names))

    if query in names:
        match_type = "exact"
        rank_score = 1
    elif any(name.startswith(query) for name in names) or any(
        token.startswith(query) for token in name_tokens
    ):
        match_type = "prefix"
        rank_score = 2
    elif query in aliases:
        match_type = "alias"
        rank_score = 3
    elif any(alias.startswith(query) for alias in aliases):
        match_type = "alias"
        rank_score = 3
    elif any(query in name for name in names) or any(query in alias for alias in aliases):
        match_type = "partial"
        rank_score = 4
    elif query in tags or any(tag.startswith(query) for tag in tags):
        match_type = "tag"
        rank_score = 5
    else:
        return None

    return ProductSearchResult(
        product_id=row["id"],
        display_name=display_name,
        english_name=english_name,
        hungarian_name=hungarian_name,
        category=row["category"],
        unit=row["unit"],
        aliases=aliases,
        tags=tags,
        match_type=match_type,
        rank_score=rank_score,
    )


def build_tags(row: object) -> tuple[str, ...]:
    """Build deterministic searchable tags from catalog fields."""

    tag_text = " ".join(
        [
            row["category"],
            row["unit"],
            row["english_name"],
            row["hungarian_name"],
            row["aliases"],
        ]
    )
    return tuple(sorted(set(normalize_text(tag_text).split())))


def normalize_text(value: str) -> str:
    """Normalize user-entered text for deterministic search."""

    return " ".join(value.lower().strip().split())
