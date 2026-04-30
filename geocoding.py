import requests
from cache import cache

GEOCODING_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


def geocode_address(address: str):

    normalized = " ".join(address.strip().lower().split())
    cache_key = f"geocode:{normalized}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        print(f" Geocode cache HIT: {address}")
        return cached_result

    print(f" Geocode cache MISS: {address}")

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "store-locator-app"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()

    if not data:
        # cache negative result to avoid repeated calls
        cache.set(cache_key, None, 60 * 60)
        return None

    result = {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"])
    }

    cache.set(cache_key, result, GEOCODING_CACHE_TTL_SECONDS)

    return result