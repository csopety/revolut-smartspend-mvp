from inspect import signature
from pathlib import Path

import pytest
import requests

from smartspend.database import DEFAULT_ORIGIN_ADDRESS, reset_demo_data
from smartspend.route_service import get_route


class FakeGoogleResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_route_uses_simulated_route_by_default(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    route = get_route("aldi_mammut", db_path=str(db_path))

    assert route.route_source == "Simulated"
    assert route.distance_km == 2.2
    assert route.travel_minutes == 9


def test_route_default_origin_is_budapest_ii_landmark() -> None:
    default_origin = signature(get_route).parameters["origin"].default

    assert default_origin == DEFAULT_ORIGIN_ADDRESS


def test_route_falls_back_to_simulated_when_no_google_key(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    route = get_route(
        "lidl_huvosvolgyi",
        use_google_maps=True,
        api_key=None,
        db_path=str(db_path),
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 3.5
    assert route.travel_minutes == 14


def test_route_falls_back_to_simulated_on_google_failure(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def failing_request(*args: object, **kwargs: object) -> object:
        raise requests.RequestException("network unavailable")

    route = get_route(
        "spar_rozsakert",
        use_google_maps=True,
        api_key="fake-key",
        db_path=str(db_path),
        request_get=failing_request,
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 1.8
    assert route.travel_minutes == 7


def test_route_falls_back_to_simulated_on_google_error_status(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def error_status_request(*args: object, **kwargs: object) -> FakeGoogleResponse:
        return FakeGoogleResponse({"status": "REQUEST_DENIED", "routes": []})

    route = get_route(
        "aldi_mammut",
        use_google_maps=True,
        api_key="fake-key",
        db_path=str(db_path),
        request_get=error_status_request,
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 2.2
    assert route.travel_minutes == 9


def test_route_can_use_google_maps_when_key_and_response_work(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def successful_request(*args: object, **kwargs: object) -> FakeGoogleResponse:
        return FakeGoogleResponse(
            {
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "distance": {"value": 4200},
                                "duration": {"value": 960},
                            }
                        ]
                    }
                ],
            }
        )

    route = get_route(
        "tesco_becsi",
        use_google_maps=True,
        api_key="fake-key",
        db_path=str(db_path),
        request_get=successful_request,
    )

    assert route.route_source == "Google Maps"
    assert route.distance_km == 4.2
    assert route.travel_minutes == 16


def test_route_rejects_unknown_store(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    with pytest.raises(ValueError, match="No store found"):
        get_route("missing_store", db_path=str(db_path))
