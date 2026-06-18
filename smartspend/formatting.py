"""Shared deterministic display formatting helpers."""


def format_huf(amount_huf: int) -> str:
    """Format Hungarian forint amounts without locale dependencies."""

    return f"{amount_huf:,.0f} HUF".replace(",", " ")
