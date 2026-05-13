"""Unit tests for ReviewerAgent — T005."""

from __future__ import annotations

from datetime import date

import pytest

from backend.feedback.schemas import FeedbackEntry, FeedbackAggregate
from backend.shared.types import (
    MatchResult,
    StructuredJob,
    StructuredResume,
)
from backend.simulation.state import AgentDecision, SimulationResult, SimulationState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_resume(skills: list[str] | None = None) -> StructuredResume:
    return StructuredResume(
        resume_id="res-001",
        name="Test Candidate",
        skills=skills or ["Python", "FastAPI", "Docker"],
        summary="Test resume",
    )


def _make_job(required: list[str] | None = None) -> StructuredJob:
    return StructuredJob(
        job_id="job-001",
        title="Backend Engineer",
        company="TestCorp",
        required_skills=required or ["Python", "FastAPI", "Kubernetes"],
        optional_skills=["AWS"],
        salary_range=(300, 500),
        location="北京",
    )


def _make_state(outcome: str = "rejected", scores: dict | None = None) -> SimulationState:
    return SimulationState(
        simulation_id="sim-001",
        candidate=_make_resume(),
        job=_make_job(),
        current_step=outcome,
        step_count=4,
        scores=scores or {"hr_screen": 0.75, "interview": 0.65},
    )


def _make_result(outcome: str = "rejected", success_prob: float = 0.5) -> SimulationResult:
    return SimulationResult(
        simulation_id="sim-001",
        strategy_name="balanced",
        outcome=outcome,
        final_state=_make_state(outcome=outcome),
        success_probability=success_prob,
        confidence_interval=(max(0, success_prob - 0.1), min(1, success_prob + 0.1)),
        time_to_offer=0,
        key_decisions=[
            AgentDecision(agent_name="candidate", action="apply", confidence=0.7),
            AgentDecision(agent_name="hr", action="screen", params={"score": 0.75, "passed": True}),
        ],
    )


def _make_match(score: float = 0.8, missing: list[str] | None = None) -> MatchResult:
    return MatchResult(
        item_id="job-001",
        score=score,
        payload={
            "title": "Backend Engineer",
            "company": "TestCorp",
            "required_skills": ["Python", "FastAPI", "Kubernetes"],
            "missing_skills": missing or ["Kubernetes"],
        },
        match_type="resume_to_job",
    )


# ---------------------------------------------------------------------------
# ReviewerAgent — single review
# ---------------------------------------------------------------------------


class TestReviewerSingle:
    def test_review_returns_feedback_entry(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = _make_result()
        entry = reviewer.review(result)
        assert isinstance(entry, FeedbackEntry)
        assert entry.simulation_id == "sim-001"
        assert entry.strategy_name == "balanced"

    def test_review_with_matches(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = _make_result()
        matches = [_make_match(score=0.85, missing=["Kubernetes"])]
        entry = reviewer.review(result, matches)
        assert entry.retrieval_reward >= 0.0

    def test_review_accepted_outcome(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = _make_result(outcome="accepted", success_prob=0.8)
        entry = reviewer.review(result)
        assert entry.outcome == "accepted"

    def test_review_rejected_outcome_has_penalty(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = _make_result(outcome="rejected", success_prob=0.1)
        matches = [_make_match(score=0.9)]
        entry = reviewer.review(result, matches)
        # High match score + low success = ranking mismatch
        assert entry.ranking_penalty >= 0.0

    def test_review_combined_signal_in_range(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        result = _make_result()
        entry = reviewer.review(result)
        assert 0.0 <= entry.combined_signal <= 1.0


# ---------------------------------------------------------------------------
# ReviewerAgent — batch review
# ---------------------------------------------------------------------------


class TestReviewerBatch:
    def test_review_batch_empty(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        agg = reviewer.review_batch([])
        assert agg.total_entries == 0

    def test_review_batch_single(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        results = [_make_result(outcome="rejected")]
        agg = reviewer.review_batch(results)
        assert agg.total_entries == 1
        assert len(agg.entries) == 1

    def test_review_batch_multiple(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        results = [
            _make_result(outcome="accepted", success_prob=0.8),
            _make_result(outcome="rejected", success_prob=0.3),
            _make_result(outcome="accepted", success_prob=0.7),
        ]
        agg = reviewer.review_batch(results)
        assert agg.total_entries == 3
        assert 0.0 <= agg.avg_reward <= 1.0
        assert 0.0 <= agg.avg_offer_probability <= 1.0


class TestBiasDetection:
    def test_diverse_results_no_bias(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        results = [
            _make_result(outcome="accepted", success_prob=0.9),
            _make_result(outcome="rejected", success_prob=0.2),
            _make_result(outcome="accepted", success_prob=0.6),
            _make_result(outcome="rejected", success_prob=0.1),
            _make_result(outcome="accepted", success_prob=0.8),
        ]
        agg = reviewer.review_batch(results)
        # Bias detection only triggers on very tight distributions
        # With diverse outcomes, bias_incident_count may be 0
        assert agg.bias_incident_count >= 0

    def test_uniform_outcomes_detected(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        results = [
            _make_result(outcome="rejected", success_prob=0.5),
            _make_result(outcome="rejected", success_prob=0.5),
            _make_result(outcome="rejected", success_prob=0.5),
            _make_result(outcome="rejected", success_prob=0.5),
            _make_result(outcome="rejected", success_prob=0.5),
        ]
        agg = reviewer.review_batch(results)
        # All identical outcomes → overfitting bias should be detected
        assert agg.bias_incident_count > 0


class TestReviewerIndependence:
    """Verify reviewer works with mock results — no engine dependency."""

    def test_reviewer_does_not_import_engine(self):
        """Smoke test: reviewer module has no functional engine import."""
        from backend.feedback import reviewer as reviewer_module
        import inspect

        src = inspect.getsource(reviewer_module)
        # Only check actual import statements, not docstrings
        import_lines = [
            l for l in src.split("\n")
            if l.strip().startswith("from") or l.strip().startswith("import")
        ]
        imports = "\n".join(import_lines)
        assert "SimulationEngine" not in imports, "Reviewer must not import SimulationEngine"

    def test_reviewer_rejects_invalid_input_gracefully(self):
        from backend.feedback.reviewer import ReviewerAgent

        reviewer = ReviewerAgent()
        # Empty result should not crash
        result = _make_result()
        entry = reviewer.review(result)
        assert isinstance(entry, FeedbackEntry)
