import time
from cache import InMemoryCache


def test_cache_set_and_get():
    cache = InMemoryCache()

    cache.set("key1", {"lat": 1.0, "lon": 2.0}, ttl_seconds=10)

    assert cache.get("key1") == {"lat": 1.0, "lon": 2.0}


def test_cache_missing_key():
    cache = InMemoryCache()

    assert cache.get("missing") is None


def test_cache_expired_key():
    cache = InMemoryCache()

    cache.set("key1", "value1", ttl_seconds=0)

    time.sleep(0.01)

    assert cache.get("key1") is None