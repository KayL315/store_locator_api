from geocoding import geocode_address
from cache import cache


class MockResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


def test_geocode_address_success(monkeypatch):
    cache.store.clear()

    def mock_get(*args, **kwargs):
        return MockResponse(
            200,
            [
                {
                    "lat": "42.3601",
                    "lon": "-71.0589"
                }
            ]
        )

    monkeypatch.setattr("geocoding.requests.get", mock_get)

    result = geocode_address("Boston, MA")

    assert result == {"lat": 42.3601, "lon": -71.0589}


def test_geocode_address_no_result(monkeypatch):
    cache.store.clear()

    def mock_get(*args, **kwargs):
        return MockResponse(200, [])

    monkeypatch.setattr("geocoding.requests.get", mock_get)

    result = geocode_address("Unknown Place")

    assert result is None


def test_geocode_address_api_error(monkeypatch):
    cache.store.clear()

    def mock_get(*args, **kwargs):
        return MockResponse(500, [])

    monkeypatch.setattr("geocoding.requests.get", mock_get)

    result = geocode_address("Boston, MA")

    assert result is None


def test_geocode_address_cache_hit():
    cache.store.clear()

    cache.set(
        "geocode:boston, ma",
        {"lat": 42.3601, "lon": -71.0589},
        ttl_seconds=100
    )

    result = geocode_address("Boston, MA")

    assert result == {"lat": 42.3601, "lon": -71.0589}