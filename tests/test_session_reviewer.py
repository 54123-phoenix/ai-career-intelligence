"""Tests for session-level review in ReviewerAgent."""

import pytest
from backend.feedback.reviewer import ReviewerAgent
from backend.session.schemas import SessionSummary


class TestSessionReviewer:
    @pytest.fixture
    def reviewer(self):
        return ReviewerAgent()

    def test_review_session_basic(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            click_through_rate=0.5,
            engagement_score=0.6,
            total_actions=10,
        )
        result = reviewer.review_session(summary)
        assert result.session_id == "s1"
        assert result.session_ctr == 0.5
        assert result.detected_issues == []

    def test_detect_high_drift(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            engagement_score=0.5,
            total_actions=5,
        )
        result = reviewer.review_session(summary, drift_score=0.55)
        assert any("unstable_preferences" in i for i in result.detected_issues)

    def test_detect_overreaction(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            engagement_score=0.3,
            total_actions=3,
        )
        result = reviewer.review_session(summary, drift_score=0.85)
        assert any("overreaction" in i for i in result.detected_issues)

    def test_detect_engagement_degradation(self, reviewer):
        summary = SessionSummary(
            session_id="s3",
            user_id="u1",
            engagement_score=0.05,
            total_actions=5,
        )
        result = reviewer.review_session(summary, engagement_history=[0.6, 0.7, 0.5])
        # 0.05 < 0.6 * 0.5 = 0.3
        assert any("ranking_degradation" in i for i in result.detected_issues)

    def test_low_engagement_warning(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            engagement_score=0.05,
            total_actions=3,
        )
        result = reviewer.review_session(summary)
        assert any("low_engagement" in i for i in result.detected_issues)

    def test_zero_ctr_with_many_actions(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            click_through_rate=0.0,
            engagement_score=0.0,
            total_actions=15,
        )
        result = reviewer.review_session(summary)
        assert any("zero_ctr_with_actions" in i for i in result.detected_issues)

    def test_healthy_session_no_issues(self, reviewer):
        summary = SessionSummary(
            session_id="s1",
            user_id="u1",
            click_through_rate=0.4,
            engagement_score=0.65,
            total_actions=20,
        )
        result = reviewer.review_session(summary, drift_score=0.1)
        assert result.detected_issues == []
