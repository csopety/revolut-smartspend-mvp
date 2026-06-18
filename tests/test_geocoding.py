import pytest
import requests

from smartspend.geocoding import (
    NOMINATIM_SEARCH_URL,
    NOMINATIM_SOURCE,
    NOMINATIM_USER_AGENT,
    geocode_origin_address,
)


class FakeGeocodingResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_successful_geocoding_with_mocked_response() -> None:
    def successful_request(*args: object, **kwargs: object) -> FakeGeocodingResponse:
        assert args[0] == NOMINATIM_SEARCH_URL
        assert kwargs["params"] == {
            "q": "Margit korut 2, Budapest II",
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "hu",
            "addressdetails": 1,
        }
        assert kwargs["headers"] == {"User-Agent": NOMINATIM_USER_AGENT}
        assert kwargs["timeout"] == 8
        return FakeGeocodingResponse(
            [
                {
                    "lat": "47.5112",
                    "lon": "19.0345",
                    "display_name": "Margit korut 2, Budapest, Hungary",
                }
            ]
        )

    result = geocode_origin_address(
        "Margit korut 2, Budapest II",
        request_get=successful_request,
    )

    assert result.address == "Margit korut 2, Budapest II"
    assert result.display_name == "Margit korut 2, Budapest, Hungary"
    assert result.latitude == 47.5112
    assert result.longitude == 19.0345
    assert result.source == NOMINATIM_SOURCE


def test_empty_address_raises_value_error() -> None:
    with pytest.raises(ValueError, match="empty"):
        geocode_origin_address("  ")


def test_no_result_raises_safe_value_error() -> None:
    def no_result_request(*args: object, **kwargs: object) -> FakeGeocodingResponse:
        return FakeGeocodingResponse([])

    with pytest.raises(ValueError, match="No origin coordinates"):
        geocode_origin_address("Unknown address", request_get=no_result_request)


def test_invalid_lat_lon_raises_safe_value_error() -> None:
    def invalid_request(*args: object, **kwargs: object) -> FakeGeocodingResponse:
        return FakeGeocodingResponse(
            [
                {
                    "lat": "not-a-latitude",
                    "lon": "19.0345",
                    "display_name": "Bad coordinate",
                }
            ]
        )

    with pytest.raises(ValueError, match="invalid coordinates"):
        geocode_origin_address("Bad coordinate", request_get=invalid_request)


def test_request_error_raises_safe_value_error() -> None:
    def failing_request(*args: object, **kwargs: object) -> object:
        raise requests.RequestException("network unavailable")

    with pytest.raises(ValueError, match="Origin geocoding failed"):
        geocode_origin_address("Margit korut 2, Budapest II", request_get=failing_request)
