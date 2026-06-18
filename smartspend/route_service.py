"""Route lookup service with safe simulated fallback."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

import requests
from dotenv import find_dotenv, load_dotenv

from smartspend.database import (
    DEFAULT_DB_PATH,
    DEFAULT_ORIGIN_ADDRESS,
    DEFAULT_ORIGIN_LATITUDE,
    DEFAULT_ORIGIN_LONGITUDE,
    connect,
    ensure_demo_database,
)

OPENROUTESERVICE_DIRECTIONS_URL = (
    "https://api.openrouteservice.org/v2/directions/{profile}/json"
)
ROUTE_TIMEOUT_SECONDS = 8
ROUTE_SOURCE_SIMULATED = "Simulated"
ROUTE_SOURCE_OPENROUTESERVICE = "OpenRouteService"
TRANSPORT_WALKING = "walking"
TRANSPORT_CAR = "car"
TRANSPORT_PUBLIC_TRANSPORT = "public_transport"

_OPENROUTESERVICE_ROUTE_CACHE: dict[tuple[object, ...], "RouteResult"] = {}


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
    use_openrouteservice: bool = False,
    use_live_routes: bool = False,
    transport_mode: str = TRANSPORT_CAR,
    api_key: str | None = None,
    db_path: str = str(DEFAULT_DB_PATH),
    request_get: Callable[..., object] = requests.post,
) -> RouteResult:
    """Return live OpenRouteService route details when possible, otherwise simulated."""

    if use_openrouteservice or use_live_routes:
        key = api_key or get_openrouteservice_api_key()
        if key:
            try:
                return get_openrouteservice_route(
                    store_id=store_id,
                    origin=origin,
                    transport_mode=transport_mode,
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
        route_source=ROUTE_SOURCE_SIMULATED,
    )


def get_openrouteservice_route(
    store_id: str,
    origin: str,
    transport_mode: str,
    api_key: str,
    db_path: str = str(DEFAULT_DB_PATH),
    request_get: Callable[..., object] = requests.post,
) -> RouteResult:
    """Request OpenRouteService distance/time for a supported transport mode."""

    profile = get_openrouteservice_profile(transport_mode)
    if profile is None:
        raise ValueError("OpenRouteService does not support this transport mode.")

    origin_coordinates = get_origin_coordinates(origin=origin, db_path=db_path)
    store_coordinates = get_store_coordinates(store_id=store_id, db_path=db_path)
    cache_key = (
        str(db_path),
        store_id,
        origin_coordinates,
        store_coordinates,
        profile,
        id(request_get),
    )
    if cache_key in _OPENROUTESERVICE_ROUTE_CACHE:
        return _OPENROUTESERVICE_ROUTE_CACHE[cache_key]

    try:
        response = request_get(
            OPENROUTESERVICE_DIRECTIONS_URL.format(profile=profile),
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
            json={"coordinates": [list(origin_coordinates), list(store_coordinates)]},
            timeout=ROUTE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        summary = payload["routes"][0]["summary"]
        distance_meters = float(summary["distance"])
        duration_seconds = float(summary["duration"])
    except Exception:
        raise ValueError("OpenRouteService route lookup failed.") from None

    result = RouteResult(
        store_id=store_id,
        distance_km=round(distance_meters / 1000, 1),
        travel_minutes=max(1, round(duration_seconds / 60)),
        route_source=ROUTE_SOURCE_OPENROUTESERVICE,
    )
    _OPENROUTESERVICE_ROUTE_CACHE[cache_key] = result
    return result


def get_openrouteservice_profile(transport_mode: str) -> str | None:
    """Map app travel modes to OpenRouteService profiles."""

    normalized_mode = transport_mode.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_mode in {TRANSPORT_WALKING, "foot_walking"}:
        return "foot-walking"
    if normalized_mode in {TRANSPORT_CAR, "driving_car", "driving"}:
        return "driving-car"
    if normalized_mode in {TRANSPORT_PUBLIC_TRANSPORT, "public_transport"}:
        return None
    return None


def get_origin_coordinates(
    origin: str = DEFAULT_ORIGIN_ADDRESS,
    db_path: str = str(DEFAULT_DB_PATH),
) -> tuple[float, float]:
    """Return origin coordinates in OpenRouteService longitude/latitude order."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT origin_address, origin_latitude, origin_longitude
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return (DEFAULT_ORIGIN_LONGITUDE, DEFAULT_ORIGIN_LATITUDE)

    origin_text = origin.strip().lower()
    saved_origin_text = str(row["origin_address"]).strip().lower()
    if origin_text in {"", saved_origin_text, DEFAULT_ORIGIN_ADDRESS.lower()}:
        return (float(row["origin_longitude"]), float(row["origin_latitude"]))

    return (DEFAULT_ORIGIN_LONGITUDE, DEFAULT_ORIGIN_LATITUDE)


def get_store_coordinates(
    store_id: str,
    db_path: str = str(DEFAULT_DB_PATH),
) -> tuple[float, float]:
    """Return store coordinates in OpenRouteService longitude/latitude order."""

    ensure_demo_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, latitude, longitude
            FROM stores
            WHERE id = ?
            """,
            (store_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No store found with id '{store_id}'.")
    if row["latitude"] is None or row["longitude"] is None:
        raise ValueError("Store coordinates are unavailable.")

    return (float(row["longitude"]), float(row["latitude"]))


def get_openrouteservice_api_key() -> str | None:
    """Read OpenRouteService API key from environment or Streamlit secrets."""

    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path)
    environment_key = os.getenv("OPENROUTESERVICE_API_KEY") or os.getenv("ORS_API_KEY")
    if environment_key:
        return environment_key

    try:
        import streamlit as st

        secret_value = st.secrets.get("OPENROUTESERVICE_API_KEY") or st.secrets.get(
            "ORS_API_KEY"
        )
    except Exception:
        return None

    return str(secret_value) if secret_value else None
