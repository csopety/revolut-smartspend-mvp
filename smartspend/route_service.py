"""Route lookup service with safe simulated fallback."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

import requests

from smartspend.database import (
    DEFAULT_DB_PATH,
    DEFAULT_ORIGIN_ADDRESS,
    connect,
    ensure_demo_database,
)

GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


@dataclass(frozen=True)
class RouteResult:
    """Route details used by the optimizer UI."""

    store_id: str
    distance_km: float
    travel_minutes: int
    route_source: str


def get_route(
    store_id: str,
    origin: str = DEFAULT_ORIGIN_ADDRESS,
    use_google_maps: bool = False,
    api_key: str | None = None,
    db_path: str = str(DEFAULT_DB_PATH),
    request_get: Callable[..., object] = requests.get,
) -> RouteResult:
    """Return route details from Google Maps when possible, otherwise simulated."""

    if use_google_maps:
        key = api_key or get_google_maps_api_key()
        if key:
            try:
                return get_google_maps_route(
                    store_id=store_id,
                    origin=origin,
                    api_key=key,
                    db_path=db_path,
                    request_get=request_get,
                )
            except (KeyError, TypeError, ValueError, requests.RequestException):
                pass

    return get_simulated_route(store_id=store_id, db_path=db_path)


def get_simulated_route(
    store_id: str,
    db_path: str = str(DEFAULT_DB_PATH),
) -> RouteResult:
    """Return deterministic route details from local SQLite store data."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, distance_km, travel_minutes
            FROM stores
            WHERE id = ?
            """,
            (store_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No store found with id '{store_id}'.")

    return RouteResult(
        store_id=row["id"],
        distance_km=float(row["distance_km"]),
        travel_minutes=int(row["travel_minutes"]),
        route_source="Simulated",
    )


def get_google_maps_route(
    store_id: str,
    origin: str,
    api_key: str,
    db_path: str = str(DEFAULT_DB_PATH),
    request_get: Callable[..., object] = requests.get,
) -> RouteResult:
    """Request Google Maps route distance/time for a store."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, name, neighborhood
            FROM stores
            WHERE id = ?
            """,
            (store_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No store found with id '{store_id}'.")

    response = request_get(
        GOOGLE_DIRECTIONS_URL,
        params={
            "origin": origin,
            "destination": f"{row['name']}, {row['neighborhood']}, Budapest",
            "mode": "driving",
            "key": api_key,
        },
        timeout=5,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "OK":
        raise ValueError("Google Maps route lookup failed.")

    leg = payload["routes"][0]["legs"][0]
    distance_meters = int(leg["distance"]["value"])
    duration_seconds = int(leg["duration"]["value"])

    return RouteResult(
        store_id=row["id"],
        distance_km=round(distance_meters / 1000, 1),
        travel_minutes=max(1, round(duration_seconds / 60)),
        route_source="Google Maps",
    )


def get_google_maps_api_key() -> str | None:
    """Read Google Maps API key from environment or Streamlit secrets."""

    environment_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if environment_key:
        return environment_key

    try:
        import streamlit as st

        secret_value = st.secrets.get("GOOGLE_MAPS_API_KEY")
    except Exception:
        return None

    return str(secret_value) if secret_value else None
