from datetime import datetime, timedelta


class InMemoryCache:
    def __init__(self):
        self.store = {}

    def get(self, key: str):
        item = self.store.get(key)

        if not item:
            return None

        value, expires_at = item

        if datetime.now() > expires_at:
            del self.store[key]
            return None

        return value

    def set(self, key: str, value, ttl_seconds: int):
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.store[key] = (value, expires_at)


cache = InMemoryCache()