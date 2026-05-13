"""Tests for CareerArchitect."""

import pytest
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect


class TestCareerArchitect:
    def _build_strategy(self, events_data: list[dict], user_id: str = "u1"):
        p = CareerParser()
        r = CareerRetriever()
        r.ingest_batch(p.parse_batch(events_data, user_id))
        timeline = r.retrieve(user_id)
        analysis = CareerReviewer().analyze(timeline)
        arch = CareerArchitect()
        return arch.design(timeline, analysis)

    def test_design_produces_strategy(self):
        strategy = self._build_strategy([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert strategy.user_id == "u1"
        assert strategy.focus_skill != ""
        assert len(strategy.action_plan) > 0

    def test_action_plan_max_5_items(self):
        strategy = self._build_strategy([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert len(strategy.action_plan) <= 5

    def test_risk_included(self):
        strategy = self._build_strategy([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert strategy.risk_if_no_adjustment != ""
        assert strategy.risk_severity in ("low", "medium", "high", "critical")

    def test_success_probability_in_range(self):
        strategy = self._build_strategy([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert 0.0 < strategy.success_probability <= 1.0

    def test_action_items_have_days(self):
        strategy = self._build_strategy([
            {"type": "rejection"}, {"type": "rejection"}, {"type": "rejection"},
        ])
        for action in strategy.action_plan:
            assert 1 <= action.day <= 14
            assert action.action != ""

    def test_improving_trend_gives_higher_probability(self):
        s1 = self._build_strategy([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ], "u1")
        s2 = self._build_strategy([
            {"type": "rejection", "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "interview", "outcome": "success", "timestamp": "2026-02-01T00:00:00Z"},
            {"type": "offer_received", "timestamp": "2026-03-01T00:00:00Z"},
        ], "u2")
        # improving trend should have higher probability
        assert s2.success_probability > s1.success_probability
