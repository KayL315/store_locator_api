import pytest
from pydantic import ValidationError

from schemas import StoreSearchRequest


def test_search_request_with_coordinates():
    request = StoreSearchRequest(
        lat=42.3601,
        lon=-71.0589,
        radius_miles=10
    )

    assert request.lat == 42.3601
    assert request.lon == -71.0589


def test_search_request_with_address():
    request = StoreSearchRequest(
        address="Boston, MA",
        radius_miles=10
    )

    assert request.address == "Boston, MA"


def test_search_request_without_location_fails():
    with pytest.raises(ValidationError):
        StoreSearchRequest(radius_miles=10)


def test_search_request_lat_without_lon_fails():
    with pytest.raises(ValidationError):
        StoreSearchRequest(lat=42.3601)


def test_search_request_radius_over_100_fails():
    with pytest.raises(ValidationError):
        StoreSearchRequest(
            lat=42.3601,
            lon=-71.0589,
            radius_miles=101
        )