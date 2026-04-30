"""Simple in-memory cache for query responses."""

from datetime import datetime, timedelta, timezone


class QueryCache:
    """TTL cache used for query response retrieval by query_id."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """Initialize cache storage."""

        self._ttl = timedelta(seconds=ttl_seconds)
        self._data: dict[str, tuple[datetime, object]] = {}

    def set(self, key: str, value: object) -> None:
        """Store a value in the cache."""

        self._data[key] = (datetime.now(timezone.utc), value)

    def get(self, key: str) -> object | None:
        """Read a value if present and not expired."""

        entry = self._data.get(key)
        if not entry:
            return None
        created_at, value = entry
        if datetime.now(timezone.utc) - created_at > self._ttl:
            self._data.pop(key, None)
            return None
        return value


query_cache = QueryCache()
