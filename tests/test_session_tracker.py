"""Tests for SessionTracker."""

import time
import pytest
from backend.session.session_tracker import SessionTracker
from backend.session.schemas import SessionAction


def _action(action_type: str, job_id: str | None = None, dwell_ms: int = 0) -> SessionAction:
    return SessionAction(
        action_type=action_type,
        job_id=job_id,
        dwell_time_ms=dwell_ms,
    )


class TestSessionTracker:
    @pytest.fixture
    def tracker(self):
        return SessionTracker(timeout_minutes=30)

    def test_start_session_creates_active(self, tracker):
        s = tracker.start_session("u1")
        assert s.is_active
        assert s.user_id == "u1"

    def test_end_session_marks_inactive(self, tracker):
        s = tracker.start_session("u1")
        ended = tracker.end_session(s.session_id)
        assert not ended.is_active
        assert ended.ended_at is not None

    def test_record_action_appends_in_order(self, tracker):
        s = tracker.start_session("u1")
        a1 = _action("click", "j1")
        a2 = _action("skip", "j2")
        tracker.record_action(s.session_id, a1)
        tracker.record_action(s.session_id, a2)
        session = tracker.get_session(s.session_id)
        assert len(session.ordered_actions) == 2
        assert session.ordered_actions[0].action_type == "click"
        assert session.ordered_actions[1].action_type == "skip"

    def test_get_active_session_auto_creates(self, tracker):
        s = tracker.get_active_session("u1")
        assert s is not None
        assert s.user_id == "u1"
        assert s.is_active

    def test_get_active_session_returns_existing(self, tracker):
        s1 = tracker.start_session("u1")
        s2 = tracker.get_active_session("u1")
        assert s1.session_id == s2.session_id

    def test_record_action_on_ended_session_raises(self, tracker):
        s = tracker.start_session("u1")
        tracker.end_session(s.session_id)
        with pytest.raises(ValueError, match="already ended"):
            tracker.record_action(s.session_id, _action("click", "j1"))

    def test_record_action_missing_session_raises(self, tracker):
        with pytest.raises(KeyError):
            tracker.record_action("nonexistent", _action("click", "j1"))

    def test_start_session_auto_ends_previous(self, tracker):
        s1 = tracker.start_session("u1")
        s2 = tracker.start_session("u1")
        s1_ended = tracker.get_session(s1.session_id)
        assert not s1_ended.is_active
        assert s2.is_active

    def test_list_user_sessions(self, tracker):
        s1 = tracker.start_session("u1")
        tracker.end_session(s1.session_id)
        s2 = tracker.start_session("u1")
        sessions = tracker.list_user_sessions("u1")
        assert len(sessions) == 2  # s1 ended + s2 active

    def test_active_count(self, tracker):
        tracker.start_session("u1")
        tracker.start_session("u2")
        assert tracker.active_count == 2

    def test_cleanup_expired(self, tracker):
        t = SessionTracker(timeout_minutes=0)  # immediate timeout
        t.start_session("u1")
        count = t.cleanup_expired()
        assert count == 1

    def test_all_action_types_supported(self, tracker):
        s = tracker.start_session("u1")
        for at in ["query", "click", "skip", "save", "apply", "dwell"]:
            a = _action(at, "j1")
            tracker.record_action(s.session_id, a)
        session = tracker.get_session(s.session_id)
        types = {a.action_type for a in session.ordered_actions}
        assert types == {"query", "click", "skip", "save", "apply", "dwell"}
