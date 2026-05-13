"""Integration tests: full session pipeline flow."""

import pytest
from backend.session.session_tracker import SessionTracker
from backend.session.behavior_aggregator import BehaviorAggregator
from backend.session.preference_updater import PreferenceUpdater
from backend.session.feedback_queue import FeedbackQueueAgent
from backend.session.schemas import SessionAction, SessionSummary


def _action(action_type: str, job_id: str | None = None, dwell_ms: int = 0, payload: dict | None = None) -> SessionAction:
    return SessionAction(
        action_type=action_type,
        job_id=job_id,
        dwell_time_ms=dwell_ms,
        job_payload=payload,
    )


class TestSessionPipeline:
    def test_full_pipeline_track_to_summary(self):
        """Session tracking → behavior aggregation."""
        tracker = SessionTracker(timeout_minutes=30)
        agg = BehaviorAggregator()

        session = tracker.start_session("u1")
        for a in [
            _action("query"),
            _action("click", "j1", dwell_ms=10000, payload={"required_skills": ["Python"], "company": "Google"}),
            _action("click", "j2", dwell_ms=5000, payload={"required_skills": ["Python"], "company": "Meta"}),
            _action("skip", "j3", dwell_ms=200, payload={"required_skills": ["Java"]}),
            _action("save", "j1"),
        ]:
            tracker.record_action(session.session_id, a)

        summary = agg.aggregate(session)
        assert summary.total_actions == 5
        assert summary.click_through_rate == 0.4
        assert summary.save_rate == 0.2
        assert "python" in summary.clicked_categories
        assert summary.top_clicked_skills[0] == "Python"

    def test_full_pipeline_summary_to_preferences(self):
        """Behavior aggregation → preference updating."""
        agg = BehaviorAggregator()
        updater = PreferenceUpdater(recent_weight=0.7)

        session = SessionTracker().start_session("u1")
        summary = SessionSummary(
            session_id=session.session_id,
            user_id="u1",
            clicked_categories=["python", "senior", "beijing"],
            top_clicked_skills=["Python", "SQL"],
            top_clicked_companies=["Google", "Meta"],
            click_through_rate=0.5,
            engagement_score=0.7,
            total_actions=10,
        )

        updated = updater.update(None, summary)
        assert updated.user_id == "u1"
        assert updated.session_count == 1
        assert len(updated.skill_weights) > 0

    def test_full_pipeline_preferences_to_queue(self):
        """Preference update → feedback queue."""
        tracker = SessionTracker(timeout_minutes=30)
        agg = BehaviorAggregator()
        updater = PreferenceUpdater()
        queue = FeedbackQueueAgent()

        session = tracker.start_session("u1")
        for a in [
            _action("click", "j1"),
            _action("save", "j2"),
            _action("apply", "j3"),
            _action("skip", "j4"),
        ]:
            tracker.record_action(session.session_id, a)

        summary = agg.aggregate(session, trace_id="t1")
        prefs = updater.update(None, summary)
        events = queue.enqueue_session(session, summary, "t1", model_version=1)

        assert summary.total_actions == 4
        assert prefs.session_count == 1
        assert len(events) == 4

    def test_trace_id_flows_through_pipeline(self):
        """trace_id propagates through all session stages."""
        trace_id = "exec-session-001"
        tracker = SessionTracker()
        agg = BehaviorAggregator()

        session = tracker.start_session("u1")
        tracker.record_action(session.session_id, _action("click", "j1"))
        tracker.record_action(session.session_id, _action("save", "j2"))

        summary = agg.aggregate(session, trace_id=trace_id)
        assert summary.trace_id == trace_id

    def test_preference_persistence_across_sessions(self):
        """Dynamic preferences accumulate across multiple sessions."""
        updater = PreferenceUpdater(recent_weight=0.7)

        # Session 1: Python focus
        prefs = updater.update(None, SessionSummary(
            session_id="s1", user_id="u1",
            top_clicked_skills=["Python"],
            clicked_categories=["python"],
        ))
        assert prefs.session_count == 1

        # Session 2: SQL focus
        prefs = updater.update(prefs, SessionSummary(
            session_id="s2", user_id="u1",
            top_clicked_skills=["SQL", "Go"],
            clicked_categories=["sql", "go"],
        ))
        assert prefs.session_count == 2
        # Should still retain Python from session 1 (via historical weight)
        assert len(prefs.skill_weights) >= 2

    def test_queue_dedup_across_sessions(self):
        """Feedback queue deduplicates same event from different actions."""
        queue = FeedbackQueueAgent()
        s1 = SessionTracker().start_session("u1")
        tracker = SessionTracker()
        session = tracker.get_active_session("u1")

        # Overwrite with our session
        tracker._sessions[s1.session_id] = s1
        tracker.record_action(s1.session_id, _action("click", "j1"))
        tracker.record_action(s1.session_id, _action("click", "j1"))

        summary = SessionSummary(session_id=s1.session_id, user_id="u1")
        queue.enqueue_session(s1, summary, "t1")
        assert queue.event_count == 1  # deduped
