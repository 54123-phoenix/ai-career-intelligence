"""Tests for CareerReviewer."""

import pytest
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer


class TestCareerReviewer:
    def _make_timeline(self, events_data: list[dict], user_id: str = "u1"):
        p = CareerParser()
        r = CareerRetriever()
        r.ingest_batch(p.parse_batch(events_data, user_id))
        return r.retrieve(user_id)

    def test_analyze_empty_returns_insufficient_data(self):
        r = CareerRetriever()
        reviewer = CareerReviewer()
        timeline = r.retrieve("u1")
        analysis = reviewer.analyze(timeline)
        assert analysis.dominant_bottleneck == "insufficient_data"

    def test_detect_skill_gap(self):
        timeline = self._make_timeline([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.dominant_bottleneck == "skill_gap"

    def test_detect_interview_skill_issue(self):
        timeline = self._make_timeline([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "interview", "outcome": "failure"},
            {"type": "interview", "outcome": "failure"},
            {"type": "interview", "outcome": "failure"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.dominant_bottleneck in ("interview_skill", "skill_gap")

    def test_trend_improving(self):
        timeline = self._make_timeline([
            {"type": "rejection", "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "interview", "outcome": "success", "timestamp": "2026-02-01T00:00:00Z"},
            {"type": "offer_received", "timestamp": "2026-03-01T00:00:00Z"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.trend == "improving"

    def test_systemic_detection(self):
        timeline = self._make_timeline([
            {"type": "interview", "outcome": "failure"},
            {"type": "interview", "outcome": "failure"},
            {"type": "interview", "outcome": "failure"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.systemic_issue

    def test_metrics_computed(self):
        timeline = self._make_timeline([
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "interview", "outcome": "success"},
            {"type": "offer_received"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert analysis.application_to_interview_rate > 0.0
        assert analysis.interview_to_offer_rate == 1.0

    def test_recommended_focus_not_empty(self):
        timeline = self._make_timeline([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        reviewer = CareerReviewer()
        analysis = reviewer.analyze(timeline)
        assert len(analysis.recommended_focus) > 0
