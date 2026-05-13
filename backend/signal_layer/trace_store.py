"""TraceStore — in-memory persistence for InteractionTrace records.

Provides put/get/list with TTL-based retention and a configurable cap.
"""

from __future__ import annotations

import time

from backend.signal_layer.schemas import InteractionTrace


class TraceStore:
    """In-memory store of InteractionTrace records.

    Evicts oldest entries when max_traces is exceeded.
    Supports optional TTL-based expiration.

    Usage:
        store = TraceStore(max_traces=500)
        store.put(trace)
        t = store.get("exec-a1b2c3d4")
        recent = store.list(limit=20)
    """

    def __init__(self, max_traces: int = 1000, ttl_seconds: int = 3600):
        self._max = max_traces
        self._ttl = ttl_seconds
        self._store: dict[str, InteractionTrace] = {}
        self._timestamps: dict[str, float] = {}

    def put(self, trace: InteractionTrace) -> None:
        """Store a trace. Evicts oldest if at capacity."""
        if len(self._store) >= self._max:
            self._evict_one()
        self._store[trace.trace_id] = trace
        self._timestamps[trace.trace_id] = time.time()

    def get(self, trace_id: str) -> InteractionTrace | None:
        """Retrieve a trace by ID. Returns None if missing or expired."""
        trace = self._store.get(trace_id)
        if trace is None:
            return None
        ts = self._timestamps.get(trace_id, 0)
        if self._ttl > 0 and (time.time() - ts) > self._ttl:
            self._store.pop(trace_id, None)
            self._timestamps.pop(trace_id, None)
            return None
        return trace

    def list(self, limit: int = 50) -> list[InteractionTrace]:
        """Return the most recent traces, newest first."""
        traces = list(self._store.values())
        traces.sort(key=lambda t: t.started_at, reverse=True)
        return traces[:limit]

    def clear(self) -> None:
        """Remove all traces."""
        self._store.clear()
        self._timestamps.clear()

    @property
    def count(self) -> int:
        """Current number of stored traces."""
        return len(self._store)

    def _evict_one(self) -> None:
        """Remove the oldest trace by timestamp."""
        if not self._timestamps:
            return
        oldest_id = min(self._timestamps, key=lambda k: self._timestamps[k])
        self._store.pop(oldest_id, None)
        self._timestamps.pop(oldest_id, None)
