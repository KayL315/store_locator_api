import requests
from cache import cache

GEOCODING_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

def geocode_address(address: str):
    """
    Use Nominatim (OpenStreetMap) to convert address to lat/lon
    """
    cache_key = f"geocode:{address.strip().lower()}"

    cached_result = cache.get(cache_key)

    if cached_result:

        print(f"Cache hit for: {address}")

        return cached_result

    print(f"Cache miss. Calling geocoding API for: {address}")

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "store-locator-app"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        return None

    data = response.json()

    if not data:
        return None

    result = {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"])
    }

    cache.set(cache_key, result, GEOCODING_CACHE_TTL_SECONDS)

    return result