"""RetrievalCache — TTL-based in-memory cache for retrieval results.

Enables fast mode by serving cached MatchResult[] when a query+filter
combination has been recently computed. Default TTL: 300 seconds.
"""

from __future__ import annotations

import hashlib
import json
import time

from backend.shared.types import MatchResult


class RetrievalCache:
    """TTL cache for retrieval results. Enables fast execution mode.

    Stores (timestamp, results) pairs keyed by deterministic cache key.
    Expired entries are treated as cache misses (not auto-evicted).

    Usage:
        cache = RetrievalCache(ttl_seconds=300)
        cache.set(cache.make_key("python backend", {"location": "北京"}), results)
        cached = cache.get("some-key")  # → list[MatchResult] or None
    """

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, list[MatchResult]]] = {}

    def get(self, key: str) -> list[MatchResult] | None:
        """Return cached results if non-expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, results = entry
        if time.time() - ts > self._ttl:
            return None
        return results

    def set(self, key: str, results: list[MatchResult]) -> None:
        """Store results with current timestamp."""
        self._store[key] = (time.time(), results)

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate a specific key, or the entire cache if key is None."""
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)

    def is_valid(self, key: str) -> bool:
        """Check if key exists and is non-expired."""
        return self.get(key) is not None

    @property
    def ttl(self) -> int:
        return self._ttl

    @property
    def entry_count(self) -> int:
        """Number of entries in cache (including expired ones)."""
        return len(self._store)

    @staticmethod
    def make_key(query: str, filters: dict | None = None) -> str:
        """Deterministic cache key from query + optional filters.

        Uses md5 for speed — not security-sensitive.
        """
        raw = query.lower().strip()
        if filters:
            # Sort keys for deterministic ordering
            sorted_filters = json.dumps(filters, sort_keys=True, default=str)
            raw += sorted_filters
        return hashlib.md5(raw.encode()).hexdigest()[:16]
