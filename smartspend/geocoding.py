"""OpenStreetMap Nominatim geocoding for explicit origin lookups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import requests

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_SOURCE = "OpenStreetMap Nominatim"
NOMINATIM_USER_AGENT = "SmartSpendMVP/1.0 educational-demo"
NOMINATIM_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class GeocodingResult:
    """A safely parsed Nominatim result for a route origin."""

    address: str
    display_name: str
    latitude: float
    longitude: float
    source: str = NOMINATIM_SOURCE


def geocode_origin_address(
    address: str,
    request_get: Callable[..., object] = requests.get,
) -> GeocodingResult:
    """Geocode an explicitly submitted origin address with Nominatim."""

    normalized_address = address.strip()
    if not normalized_address:
        raise ValueError("Origin address cannot be empty.")

    try:
        response = request_get(
            NOMINATIM_SEARCH_URL,
            params={
                "q": normalized_address,
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "hu",
                "addressdetails": 1,
            },
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=NOMINATIM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        raise ValueError("Origin geocoding failed. Please try another address.") from None

    if not isinstance(payload, list) or not payload:
        raise ValueError("No origin coordinates found for that address.")

    first_result = payload[0]
    try:
        latitude = float(first_result["lat"])
        longitude = float(first_result["lon"])
        display_name = str(first_result["display_name"]).strip()
    except (KeyError, TypeError, ValueError):
        raise ValueError("Origin geocoding returned invalid coordinates.") from None

    if not display_name:
        raise ValueError("Origin geocoding returned an invalid display name.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Origin geocoding returned invalid coordinates.")

    return GeocodingResult(
        address=normalized_address,
        display_name=display_name,
        latitude=latitude,
        longitude=longitude,
    )
