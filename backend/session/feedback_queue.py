"""FeedbackQueueAgent — convert session behaviors into queued ranking feedback events.

Event weights:
  apply = 1.0  (strongest positive)
  save  = 0.8
  click = 0.5
  skip  = -0.3 (weak negative)
  dwell = normalized [0, 1]

Events are queued in-memory for nightly batch retraining.
Deduplication by (session_id, job_id, event_type).
"""

from __future__ import annotations

from collections import OrderedDict

from backend.session.schemas import (
    FeedbackQueueEvent,
    Session,
    SessionAction,
    SessionSummary,
)


class FeedbackQueueAgent:
    """Convert session behavior into queued ranking training events.

    Accumulates events in-memory. Events are drained for nightly training.

    Usage:
        queue = FeedbackQueueAgent(max_events=10000)
        events = queue.enqueue_session(session, summary, trace_id, model_version=3)
        pending = queue.drain_events(500)
    """

    def __init__(self, max_events: int = 10000):
        self._max = max_events
        self._queue: OrderedDict[str, FeedbackQueueEvent] = OrderedDict()

    # ── Public API ────────────────────────────────────────────────────────

    def enqueue_session(
        self,
        session: Session,
        summary: SessionSummary,
        trace_id: str,
        model_version: int = 0,
    ) -> list[FeedbackQueueEvent]:
        """Convert all actions in a session into queued feedback events.

        Args:
            session: Completed session with ordered_actions
            summary: Behavioral summary (for context)
            trace_id: Pipeline execution ID
            model_version: Current active ranking model version

        Returns:
            List of newly enqueued FeedbackQueueEvent objects
        """
        events: list[FeedbackQueueEvent] = []

        for action in session.ordered_actions:
            if not action.job_id:
                continue

            event_type = self._map_action_type(action.action_type)
            if event_type is None:
                continue  # skip 'query' actions

            weight = self._compute_weight(action)
            key = f"{session.session_id}:{action.job_id}:{event_type}"

            # Dedup: update existing event if already queued
            if key in self._queue:
                existing = self._queue[key]
                existing.weight = max(existing.weight, weight) if weight > 0 else min(existing.weight, weight)
                existing.timestamp = action.timestamp
                continue

            event = FeedbackQueueEvent(
                session_id=session.session_id,
                trace_id=trace_id,
                model_version=model_version,
                event_type=event_type,
                job_id=action.job_id,
                weight=weight,
                timestamp=action.timestamp,
            )

            # Evict oldest if at capacity
            if len(self._queue) >= self._max:
                self._queue.popitem(last=False)

            self._queue[key] = event
            events.append(event)

        return events

    def get_pending_events(self) -> list[FeedbackQueueEvent]:
        """Return all pending events without draining."""
        return list(self._queue.values())

    def drain_events(self, count: int | None = None) -> list[FeedbackQueueEvent]:
        """Consume and return events from the front of the queue.

        Args:
            count: Max events to drain. None = drain all.

        Returns:
            List of consumed FeedbackQueueEvent objects
        """
        if count is None or count >= len(self._queue):
            events = list(self._queue.values())
            self._queue.clear()
            return events

        events: list[FeedbackQueueEvent] = []
        for _ in range(count):
            if not self._queue:
                break
            _, event = self._queue.popitem(last=False)
            events.append(event)
        return events

    @property
    def event_count(self) -> int:
        """Number of pending events in the queue."""
        return len(self._queue)

    def clear(self) -> None:
        """Remove all queued events."""
        self._queue.clear()

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _map_action_type(action_type: str) -> str | None:
        """Map SessionAction.action_type to FeedbackQueueEvent.event_type."""
        mapping = {
            "click": "click",
            "save": "save",
            "apply": "apply",
            "skip": "skip",
            "dwell": "dwell",
        }
        return mapping.get(action_type)

    @staticmethod
    def _compute_weight(action: SessionAction) -> float:
        """Compute training weight for an action.

        apply = 1.0, save = 0.8, click = 0.5, skip = -0.3, dwell = [0,1]
        """
        base_weights = {
            "click": 0.5,
            "save": 0.8,
            "apply": 1.0,
            "skip": -0.3,
            "dwell": 0.2,
        }
        base = base_weights.get(action.action_type, 0.0)

        if action.action_type == "dwell" and action.dwell_time_ms > 0:
            dwell_norm = min(action.dwell_time_ms / 30_000.0, 1.0)
            return round(dwell_norm, 4)

        return base
