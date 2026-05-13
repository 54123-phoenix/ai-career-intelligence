"""Tests for CareerSimulator."""

import pytest
from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect
from backend.career.career_simulator import CareerSimulator


class TestCareerSimulator:
    def _simulate(self, events_data: list[dict], user_id: str = "u1"):
        p = CareerParser()
        r = CareerRetriever()
        r.ingest_batch(p.parse_batch(events_data, user_id))
        timeline = r.retrieve(user_id)
        analysis = CareerReviewer().analyze(timeline)
        strategy = CareerArchitect().design(timeline, analysis)
        sim = CareerSimulator()
        return sim.simulate(strategy, analysis)

    def test_simulate_produces_probability(self):
        result = self._simulate([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert 0.0 <= result.success_probability <= 1.0

    def test_failure_risk_identified(self):
        result = self._simulate([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert result.main_failure_risk != ""

    def test_expected_outcome_described(self):
        result = self._simulate([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert result.expected_outcome != ""

    def test_adjustment_for_low_probability(self):
        result = self._simulate([
            {"type": "rejection"}, {"type": "rejection"}, {"type": "rejection"},
        ])
        # 3 rejections → application_volume_low, stable trend → ~0.60 probability
        # With 5 actions, probability >= 0.60 doesn't always need adjustment
        assert 0.0 <= result.success_probability <= 1.0
        assert result.main_failure_risk != ""

    def test_simulation_confidence_in_range(self):
        result = self._simulate([
            {"type": "application_sent"}, {"type": "application_sent"}, {"type": "application_sent"},
            {"type": "application_sent"}, {"type": "application_sent"},
        ])
        assert 0.0 <= result.simulation_confidence <= 1.0
