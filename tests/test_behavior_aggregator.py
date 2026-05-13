"""Tests for BehaviorAggregator."""

import pytest
from backend.session.behavior_aggregator import BehaviorAggregator
from backend.session.schemas import Session, SessionAction


def _action(action_type: str, job_id: str | None = None, dwell_ms: int = 0, payload: dict | None = None) -> SessionAction:
    return SessionAction(
        session_id="s1",
        action_type=action_type,
        job_id=job_id,
        dwell_time_ms=dwell_ms,
        job_payload=payload,
    )


def _session(actions: list[SessionAction]) -> Session:
    return Session(
        session_id="s1",
        user_id="u1",
        ordered_actions=actions,
    )


class TestBehaviorAggregator:
    def test_aggregate_computes_rates(self):
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1"),
            _action("click", "j2"),
            _action("skip", "j3"),
            _action("save", "j1"),
        ])
        summary = agg.aggregate(s)
        assert summary.total_actions == 4
        assert summary.click_through_rate == 0.5  # 2/4
        assert summary.save_rate == 0.25  # 1/4
        assert summary.apply_rate == 0.0

    def test_engagement_score_computed(self):
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1", dwell_ms=15000),
            _action("save", "j1"),
            _action("apply", "j1"),
        ])
        summary = agg.aggregate(s)
        assert 0.0 < summary.engagement_score <= 1.0

    def test_empty_session(self):
        agg = BehaviorAggregator()
        s = _session([])
        summary = agg.aggregate(s)
        assert summary.total_actions == 0
        assert summary.engagement_score == 0.0
        assert summary.click_through_rate == 0.0

    def test_categories_extracted(self):
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1", payload={"required_skills": ["Python"], "level": "Senior", "location": "Beijing"}),
            _action("skip", "j2", payload={"required_skills": ["Java"], "level": "Junior"}),
        ])
        summary = agg.aggregate(s)
        assert "python" in summary.clicked_categories
        assert "senior" in summary.clicked_categories
        assert "beijing" in summary.clicked_categories
        assert "java" in summary.skipped_categories

    def test_dwell_time_averaged(self):
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1", dwell_ms=10000),
            _action("click", "j2", dwell_ms=5000),
        ])
        summary = agg.aggregate(s)
        assert summary.average_dwell_time_ms == 7500.0

    def test_top_skills_extracted(self):
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1", payload={"required_skills": ["Python"], "company": "Google"}),
            _action("click", "j2", payload={"required_skills": ["Python"], "company": "MS"}),
            _action("click", "j3", payload={"required_skills": ["Java"], "company": "Oracle"}),
        ])
        summary = agg.aggregate(s)
        assert summary.top_clicked_skills[0] == "Python"  # 2 clicks
        assert "Java" in summary.top_clicked_skills

    def test_only_real_actions_counted(self):
        """Verify only actual actions contribute, not inferred data."""
        agg = BehaviorAggregator()
        s = _session([
            _action("click", "j1"),
            _action("click", "j2"),
        ])
        summary = agg.aggregate(s)
        assert summary.click_through_rate == 1.0
        assert summary.save_rate == 0.0  # no saves in session
        assert summary.apply_rate == 0.0  # no applies in session
