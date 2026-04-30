"""Simple in-process store for query history and watchlist entries.

This store provides a working persistence layer when Postgres is not yet
provisioned. Production deployments should switch to the SQLAlchemy models
in ``app.models`` while keeping the same interface.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from threading import RLock
from typing import Iterable
from uuid import uuid4

from app.schemas.post import HistoryEntry, QueryResponse, WatchlistEntry


class HistoryStore:
    """Bounded ordered store for completed query results."""

    def __init__(self, max_entries: int = 200) -> None:
        """Initialize the history store.

        Args:
            max_entries: Hard cap on retained entries.
        """

        self._entries: "OrderedDict[str, QueryResponse]" = OrderedDict()
        self._max_entries = int(max_entries)
        self._lock = RLock()

    def add(self, response: QueryResponse) -> None:
        """Insert or refresh a completed query response."""

        with self._lock:
            self._entries[response.query_id] = response
            self._entries.move_to_end(response.query_id)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def get(self, query_id: str) -> QueryResponse | None:
        """Return a stored query response by ID."""

        with self._lock:
            return self._entries.get(query_id)

    def list(self, limit: int = 20) -> list[HistoryEntry]:
        """List the most recent queries, newest first."""

        with self._lock:
            entries = list(self._entries.values())[-limit:][::-1]
        return [
            HistoryEntry(
                id=entry.query_id,
                topic=entry.topic,
                sources=entry.sources,
                window_hours=entry.window_hours,
                raw_score=entry.weighted_result.raw_score,
                weighted_score=entry.weighted_result.weighted_score,
                divergence=entry.weighted_result.divergence,
                divergence_flag=entry.weighted_result.divergence_flag,
                post_count=entry.weighted_result.total_posts,
                queried_at=entry.queried_at,
                runtime_ms=entry.runtime_ms,
            )
            for entry in entries
        ]


class WatchlistStore:
    """Thread-safe in-memory watchlist store with refresh metadata."""

    def __init__(self) -> None:
        """Initialize an empty watchlist store."""

        self._entries: dict[str, WatchlistEntry] = {}
        self._lock = RLock()

    def add(
        self,
        topic: str,
        sources: list[str],
        window_hours: int,
        refresh_interval_minutes: int,
    ) -> WatchlistEntry:
        """Add a watchlist entry and return it."""

        with self._lock:
            entry_id = str(uuid4())
            entry = WatchlistEntry(
                id=entry_id,
                topic=topic,
                sources=list(sources),
                window_hours=window_hours,
                refresh_interval_minutes=refresh_interval_minutes,
                last_refreshed_at=None,
                last_weighted_score=None,
                delta_since_last=None,
                created_at=datetime.now(timezone.utc),
            )
            self._entries[entry_id] = entry
            return entry

    def remove(self, entry_id: str) -> bool:
        """Remove a watchlist entry."""

        with self._lock:
            return self._entries.pop(entry_id, None) is not None

    def list(self) -> list[WatchlistEntry]:
        """Return all watchlist entries sorted by creation time."""

        with self._lock:
            return sorted(self._entries.values(), key=lambda item: item.created_at)

    def update_after_refresh(
        self, entry_id: str, weighted_score: float
    ) -> WatchlistEntry | None:
        """Record a refresh outcome and compute delta vs prior score."""

        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            previous = entry.last_weighted_score or 0.0
            updated = entry.model_copy(
                update={
                    "last_weighted_score": weighted_score,
                    "delta_since_last": weighted_score - previous,
                    "last_refreshed_at": datetime.now(timezone.utc),
                }
            )
            self._entries[entry_id] = updated
            return updated

    def due_for_refresh(self) -> Iterable[WatchlistEntry]:
        """Iterate over entries whose refresh interval has elapsed."""

        now = datetime.now(timezone.utc)
        with self._lock:
            for entry in list(self._entries.values()):
                if entry.last_refreshed_at is None:
                    yield entry
                    continue
                elapsed = (now - entry.last_refreshed_at).total_seconds() / 60.0
                if elapsed >= entry.refresh_interval_minutes:
                    yield entry


history_store = HistoryStore()
watchlist_store = WatchlistStore()


__all__: list[str] = [
    "HistoryStore",
    "WatchlistStore",
    "history_store",
    "watchlist_store",
]
