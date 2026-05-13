"""Tests for FeedbackQueueAgent."""

import pytest
from backend.session.feedback_queue import FeedbackQueueAgent
from backend.session.schemas import Session, SessionAction, SessionSummary


def _action(action_type: str, job_id: str, dwell_ms: int = 0) -> SessionAction:
    return SessionAction(
        session_id="s1",
        action_type=action_type,
        job_id=job_id,
        dwell_time_ms=dwell_ms,
    )


def _session(actions: list[SessionAction]) -> Session:
    return Session(session_id="s1", user_id="u1", ordered_actions=actions)


class TestFeedbackQueue:
    def test_enqueue_session_produces_events(self):
        queue = FeedbackQueueAgent(max_events=100)
        s = _session([
            _action("click", "j1"),
            _action("save", "j2"),
            _action("apply", "j3"),
        ])
        summary = SessionSummary(session_id="s1", user_id="u1")
        events = queue.enqueue_session(s, summary, "t1", model_version=1)
        assert len(events) == 3

    def test_event_weights_correct(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("apply", "j1")])
        events = queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        assert events[0].weight == 1.0

        s2 = _session([_action("save", "j2")])
        events2 = queue.enqueue_session(s2, SessionSummary(session_id="s2", user_id="u1"), "t2")
        assert events2[0].weight == 0.8

        s3 = _session([_action("click", "j3")])
        events3 = queue.enqueue_session(s3, SessionSummary(session_id="s3", user_id="u1"), "t3")
        assert events3[0].weight == 0.5

        s4 = _session([_action("skip", "j4")])
        events4 = queue.enqueue_session(s4, SessionSummary(session_id="s4", user_id="u1"), "t4")
        assert events4[0].weight == -0.3

    def test_dwell_weight_normalized(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("dwell", "j1", dwell_ms=15000)])  # 15s = 0.5 normalized
        events = queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        assert events[0].weight == 0.5

    def test_dedup_same_job_event_type(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("click", "j1"), _action("click", "j1")])
        events = queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        assert len(events) == 1  # deduped
        assert queue.event_count == 1

    def test_drain_events_consumes(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("click", "j1"), _action("save", "j2")])
        queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        assert queue.event_count == 2
        drained = queue.drain_events(1)
        assert len(drained) == 1
        assert queue.event_count == 1

    def test_drain_all(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("click", "j1"), _action("save", "j2")])
        queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        drained = queue.drain_events()
        assert len(drained) == 2
        assert queue.event_count == 0

    def test_event_properties_preserved(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("click", "j1")])
        events = queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1", model_version=3)
        assert events[0].session_id == "s1"
        assert events[0].trace_id == "t1"
        assert events[0].model_version == 3
        assert events[0].event_type == "click"
        assert events[0].job_id == "j1"

    def test_clear_removes_all(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("click", "j1")])
        queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        queue.clear()
        assert queue.event_count == 0

    def test_query_actions_skipped(self):
        queue = FeedbackQueueAgent()
        s = _session([_action("query", None)])
        events = queue.enqueue_session(s, SessionSummary(session_id="s1", user_id="u1"), "t1")
        assert len(events) == 0  # query has no job_id, skipped
