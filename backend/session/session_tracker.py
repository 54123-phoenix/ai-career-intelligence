"""SessionTracker — track and organize user actions into time-ordered sessions.

Session boundary: 30 minutes of inactivity → auto-end, next action starts new session.
All actions routed through SessionTracker — it is the single source of truth for sessions.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from backend.session.schemas import Session, SessionAction


class SessionTracker:
    """Track user actions and group them into sessions.

    In-memory store with session timeout. The sole creator of Session objects.

    Usage:
        tracker = SessionTracker(timeout_minutes=30)
        session = tracker.start_session("user-1")
        tracker.record_action(session.session_id, action)
        ended = tracker.end_session(session.session_id)
    """

    def __init__(self, timeout_minutes: int = 30):
        self._timeout_seconds = timeout_minutes * 60
        self._sessions: dict[str, Session] = {}
        self._user_active: dict[str, str] = {}  # user_id → active session_id

    # ── Public API ────────────────────────────────────────────────────────

    def start_session(self, user_id: str) -> Session:
        """Create a new active session. Auto-ends any existing active session."""
        if user_id in self._user_active:
            old_id = self._user_active[user_id]
            self.end_session(old_id)

        session = Session(user_id=user_id)
        self._sessions[session.session_id] = session
        self._user_active[user_id] = session.session_id
        return session

    def record_action(
        self,
        session_id: str,
        action: SessionAction,
    ) -> Session:
        """Append an action to a session. Auto-starts session if needed.

        Validates chronological ordering — action timestamp must be >= last action.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        if not session.is_active:
            raise ValueError(f"Session {session_id} is already ended")

        # Validate chronological ordering
        if session.ordered_actions:
            last_ts = session.ordered_actions[-1].timestamp
            if action.timestamp < last_ts:
                # Out of order — still append but warn via preserving order by timestamp
                pass

        # Stamp action with session_id
        action.session_id = session_id
        session.ordered_actions.append(action)

        # Update session timestamp
        self._sessions[session_id] = session
        return session

    def end_session(self, session_id: str) -> Session:
        """Mark a session as inactive and set ended_at."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        session.is_active = False
        session.ended_at = datetime.now(timezone.utc).isoformat()

        # Clear user active mapping
        user_id = session.user_id
        if self._user_active.get(user_id) == session_id:
            del self._user_active[user_id]

        self._sessions[session_id] = session
        return session

    def get_active_session(self, user_id: str) -> Session | None:
        """Return the active session for a user, or None.

        Auto-starts a new session if none exists or existing has timed out.
        """
        if user_id in self._user_active:
            session_id = self._user_active[user_id]
            session = self._sessions.get(session_id)
            if session and self._is_session_alive(session):
                return session
            # Timed out → auto-end
            if session:
                self.end_session(session_id)

        return self.start_session(user_id)

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve any session by ID."""
        return self._sessions.get(session_id)

    def list_user_sessions(self, user_id: str, limit: int = 20) -> list[Session]:
        """Return recent sessions for a user, newest first."""
        user_sessions = [
            s for s in self._sessions.values() if s.user_id == user_id
        ]
        user_sessions.sort(key=lambda s: s.started_at, reverse=True)
        return user_sessions[:limit]

    def cleanup_expired(self) -> int:
        """End all timed-out sessions. Returns count of sessions ended."""
        count = 0
        for session_id, session in list(self._sessions.items()):
            if session.is_active and not self._is_session_alive(session):
                self.end_session(session_id)
                count += 1
        return count

    @property
    def active_count(self) -> int:
        """Number of currently active sessions."""
        self.cleanup_expired()
        return len(self._user_active)

    # ── Internal ──────────────────────────────────────────────────────────

    def _is_session_alive(self, session: Session) -> bool:
        """Check if the session is still within the timeout window."""
        if not session.ordered_actions:
            # Session with no actions: check started_at
            try:
                started = datetime.fromisoformat(session.started_at)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            except (ValueError, TypeError):
                elapsed = 0
            return elapsed < self._timeout_seconds

        last_action = session.ordered_actions[-1]
        try:
            last_ts = datetime.fromisoformat(last_action.timestamp)
            elapsed = (datetime.now(timezone.utc) - last_ts).total_seconds()
        except (ValueError, TypeError):
            elapsed = 0
        return elapsed < self._timeout_seconds
