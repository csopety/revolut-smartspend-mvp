from inspect import signature
from pathlib import Path

import pytest
import requests

from smartspend.database import DEFAULT_ORIGIN_ADDRESS, reset_demo_data
from smartspend.route_service import (
    ROUTE_SOURCE_OPENROUTESERVICE,
    get_openrouteservice_route,
    get_route,
)


class FakeRouteResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def successful_ors_payload(
    distance_meters: int = 4200,
    duration_seconds: int = 960,
) -> dict[str, object]:
    return {
        "routes": [
            {
                "summary": {
                    "distance": distance_meters,
                    "duration": duration_seconds,
                }
            }
        ]
    }


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


def test_route_falls_back_to_simulated_when_no_openrouteservice_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENROUTESERVICE_API_KEY", raising=False)
    monkeypatch.delenv("ORS_API_KEY", raising=False)

    def unexpected_request(*args: object, **kwargs: object) -> object:
        raise AssertionError("Route API should not be called without a key.")

    route = get_route(
        "lidl_huvosvolgyi",
        use_openrouteservice=True,
        api_key=None,
        db_path=str(db_path),
        request_get=unexpected_request,
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 3.5
    assert route.travel_minutes == 14


def test_walking_route_can_use_openrouteservice_when_response_works(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def successful_request(*args: object, **kwargs: object) -> FakeRouteResponse:
        url = str(args[0])
        assert url.endswith("/foot-walking/json")
        assert kwargs["headers"]["Authorization"] == "demo-token"
        assert kwargs["headers"]["Content-Type"] == "application/json; charset=utf-8"
        assert kwargs["headers"]["Accept"] == "application/json"
        assert kwargs["json"]["coordinates"][0] == [19.0244, 47.5071]
        assert kwargs["json"]["coordinates"][1] == [
            19.021628036706577,
            47.56307158883334,
        ]
        assert kwargs["timeout"] == 8
        return FakeRouteResponse(successful_ors_payload())

    route = get_route(
        "tesco_becsi",
        use_openrouteservice=True,
        transport_mode="walking",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=successful_request,
    )

    assert route.route_source == ROUTE_SOURCE_OPENROUTESERVICE
    assert route.distance_km == 4.2
    assert route.travel_minutes == 16


def test_car_route_can_use_openrouteservice_with_live_route_flag(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def successful_request(*args: object, **kwargs: object) -> FakeRouteResponse:
        assert str(args[0]).endswith("/driving-car/json")
        assert kwargs["json"]["coordinates"][0] == [19.0244, 47.5071]
        assert kwargs["json"]["coordinates"][1] == [
            18.962848219071322,
            47.54510653574783,
        ]
        return FakeRouteResponse(successful_ors_payload(3500, 780))

    route = get_route(
        "lidl_huvosvolgyi",
        use_live_routes=True,
        transport_mode="car",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=successful_request,
    )

    assert route.route_source == ROUTE_SOURCE_OPENROUTESERVICE
    assert route.distance_km == 3.5
    assert route.travel_minutes == 13


def test_public_transport_falls_back_to_simulated(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def unexpected_request(*args: object, **kwargs: object) -> object:
        raise AssertionError("Public transport should not call OpenRouteService.")

    route = get_route(
        "spar_rozsakert",
        use_openrouteservice=True,
        transport_mode="public_transport",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=unexpected_request,
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 1.8
    assert route.travel_minutes == 7


def test_route_falls_back_to_simulated_on_openrouteservice_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def failing_request(*args: object, **kwargs: object) -> object:
        raise requests.RequestException("network unavailable")

    route = get_route(
        "aldi_mammut",
        use_openrouteservice=True,
        transport_mode="walking",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=failing_request,
    )

    assert route.route_source == "Simulated"
    assert route.distance_km == 2.2
    assert route.travel_minutes == 9


def test_route_falls_back_to_simulated_on_bad_openrouteservice_payload(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    def bad_payload_request(*args: object, **kwargs: object) -> FakeRouteResponse:
        return FakeRouteResponse({"routes": []})

    route = get_route(
        "aldi_mammut",
        use_openrouteservice=True,
        transport_mode="car",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=bad_payload_request,
    )

    assert route.route_source == "Simulated"


def test_openrouteservice_exception_message_does_not_include_secret(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    token_value = "sentinel-token-value"

    def failing_request(*args: object, **kwargs: object) -> object:
        raise RuntimeError(f"upstream rejected {token_value}")

    with pytest.raises(ValueError) as error:
        get_openrouteservice_route(
            "tesco_becsi",
            origin=DEFAULT_ORIGIN_ADDRESS,
            transport_mode="walking",
            api_key=token_value,
            db_path=str(db_path),
            request_get=failing_request,
        )

    assert token_value not in str(error.value)


def test_openrouteservice_route_results_are_cached(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)
    call_count = 0

    def successful_request(*args: object, **kwargs: object) -> FakeRouteResponse:
        nonlocal call_count
        call_count += 1
        return FakeRouteResponse(successful_ors_payload())

    first_route = get_route(
        "tesco_becsi",
        use_openrouteservice=True,
        transport_mode="walking",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=successful_request,
    )
    second_route = get_route(
        "tesco_becsi",
        use_openrouteservice=True,
        transport_mode="walking",
        api_key="demo-token",
        db_path=str(db_path),
        request_get=successful_request,
    )

    assert first_route == second_route
    assert call_count == 1


def test_route_rejects_unknown_store(tmp_path: Path) -> None:
    db_path = tmp_path / "smartspend_demo.db"
    reset_demo_data(db_path)

    with pytest.raises(ValueError, match="No store found"):
        get_route("missing_store", db_path=str(db_path))
