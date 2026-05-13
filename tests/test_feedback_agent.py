"""Unit tests for FeedbackAgent — T005."""

from __future__ import annotations

import pytest

from backend.feedback.schemas import FeedbackAggregate, FeedbackEntry, TrainingSample
from backend.shared.types import AgentDecision, MatchResult, StructuredJob, StructuredResume
from backend.simulation.state import SimulationResult, SimulationState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_resume(skills: list[str] | None = None) -> StructuredResume:
    return StructuredResume(
        resume_id="res-001",
        name="Test Candidate",
        skills=skills or ["Python", "FastAPI", "Docker", "AWS"],
        summary="Senior backend engineer",
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


def _make_result(
    sim_id: str = "sim-001",
    outcome: str = "accepted",
    success_prob: float = 0.7,
    strategy: str = "balanced",
) -> SimulationResult:
    return SimulationResult(
        simulation_id=sim_id,
        strategy_name=strategy,
        outcome=outcome,
        final_state=SimulationState(
            simulation_id=sim_id,
            candidate=_make_resume(),
            job=_make_job(),
            current_step=outcome,
            step_count=4,
            scores={"hr_screen": 0.8, "interview": 0.7, "final": 0.75},
        ),
        success_probability=success_prob,
        confidence_interval=(max(0, success_prob - 0.1), min(1, success_prob + 0.1)),
        time_to_offer=0,
    )


def _make_entry(
    sim_id: str = "sim-001",
    outcome: str = "accepted",
    combined: float = 0.7,
) -> FeedbackEntry:
    return FeedbackEntry(
        simulation_id=sim_id,
        strategy_name="balanced",
        outcome=outcome,
        total_reward=0.6,
        offer_probability=0.7,
        skill_gap_score=0.75,
        retrieval_reward=0.8,
        ranking_penalty=0.0,
        combined_signal=combined,
    )


def _make_match(score: float = 0.8) -> MatchResult:
    return MatchResult(
        item_id="job-001",
        score=score,
        payload={
            "title": "Backend Engineer",
            "company": "TestCorp",
            "required_skills": ["Python", "FastAPI", "Kubernetes"],
            "missing_skills": ["Kubernetes"],
        },
        match_type="resume_to_job",
    )


# ---------------------------------------------------------------------------
# TrainingSample generation
# ---------------------------------------------------------------------------


class TestTrainingSampleGeneration:
    def test_generate_sample_returns_training_sample(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        sample = agent.generate_sample(_make_entry(), _make_result(), _make_match())
        assert isinstance(sample, TrainingSample)
        assert sample.sample_id != ""
        assert len(sample.sample_id) == 12

    def test_sample_label_in_range(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        sample = agent.generate_sample(_make_entry(), _make_result())
        assert 0.0 <= sample.label <= 1.0

    def test_sample_has_features(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        sample = agent.generate_sample(_make_entry(), _make_result(), _make_match())
        assert isinstance(sample.features, dict)
        assert len(sample.features) > 0

    def test_accepted_outcome_gives_higher_label(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        accepted = agent.generate_sample(
            _make_entry(outcome="accepted", combined=0.7), _make_result(outcome="accepted")
        )
        rejected = agent.generate_sample(
            _make_entry(outcome="rejected", combined=0.7), _make_result(outcome="rejected", success_prob=0.2)
        )
        assert accepted.label > rejected.label

    def test_sample_id_deterministic(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        s1 = agent.generate_sample(_make_entry(sim_id="sim-001"), _make_result(sim_id="sim-001"))
        s2 = agent.generate_sample(_make_entry(sim_id="sim-001"), _make_result(sim_id="sim-001"))
        assert s1.sample_id == s2.sample_id

    def test_sample_id_different_for_different_inputs(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        s1 = agent.generate_sample(_make_entry(sim_id="sim-001"), _make_result(sim_id="sim-001"))
        s2 = agent.generate_sample(_make_entry(sim_id="sim-002"), _make_result(sim_id="sim-002"))
        assert s1.sample_id != s2.sample_id


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


class TestFeatureExtraction:
    def test_features_has_12_keys(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        features = agent._extract_features(_make_result(), _make_match())
        assert len(features) == 12

    def test_all_feature_values_in_range(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        features = agent._extract_features(_make_result(), _make_match())
        for key, val in features.items():
            assert 0.0 <= val <= 1.0, f"{key} = {val} out of [0, 1]"

    def test_skill_match_ratio_no_gaps(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        resume = _make_resume(skills=["Python", "FastAPI", "Kubernetes"])
        job = _make_job(required=["Python", "FastAPI", "Kubernetes"])
        result = SimulationResult(
            simulation_id="sim-full",
            strategy_name="balanced",
            outcome="accepted",
            final_state=SimulationState(
                simulation_id="sim-full",
                candidate=resume,
                job=job,
                current_step="accepted",
                step_count=3,
                scores={"hr_screen": 0.9, "interview": 0.85},
            ),
            success_probability=0.9,
            confidence_interval=(0.8, 1.0),
            time_to_offer=3,
        )
        features = agent._extract_features(result)
        assert features["skill_match_ratio"] == 1.0
        assert features["has_skill_gaps"] == 0.0

    def test_skill_match_ratio_with_gaps(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        features = agent._extract_features(_make_result())
        # resume has Python, FastAPI, Docker, AWS; job requires Python, FastAPI, Kubernetes
        # 2/3 matched = 0.6667
        assert features["skill_match_ratio"] < 1.0


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------


class TestDatasetGeneration:
    def test_generate_dataset_returns_list(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [_make_entry(sim_id="sim-001"), _make_entry(sim_id="sim-002")]
        results = [_make_result(sim_id="sim-001"), _make_result(sim_id="sim-002")]
        agg = FeedbackAggregate(
            total_entries=2,
            avg_reward=0.6,
            avg_offer_probability=0.7,
            avg_retrieval_reward=0.8,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        dataset = agent.generate_dataset(agg, results)
        assert isinstance(dataset, list)
        assert len(dataset) == 2

    def test_dataset_sorted_by_label_descending(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [
            _make_entry(sim_id="sim-001", combined=0.3),
            _make_entry(sim_id="sim-002", combined=0.9),
        ]
        results = [
            _make_result(sim_id="sim-001", outcome="rejected", success_prob=0.2),
            _make_result(sim_id="sim-002", outcome="accepted", success_prob=0.9),
        ]
        agg = FeedbackAggregate(
            total_entries=2,
            avg_reward=0.6,
            avg_offer_probability=0.55,
            avg_retrieval_reward=0.8,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        dataset = agent.generate_dataset(agg, results)
        assert dataset[0].label >= dataset[-1].label

    def test_low_quality_samples_filtered(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [_make_entry(sim_id="sim-001", combined=0.05)]
        results = [_make_result(sim_id="sim-001", outcome="rejected", success_prob=0.05)]
        agg = FeedbackAggregate(
            total_entries=1,
            avg_reward=0.05,
            avg_offer_probability=0.05,
            avg_retrieval_reward=0.05,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        dataset = agent.generate_dataset(agg, results)
        # Low label (<0.1) should be filtered
        assert len(dataset) == 0

    def test_cached_samples_accumulate(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [_make_entry(sim_id="sim-001")]
        results = [_make_result(sim_id="sim-001")]
        agg = FeedbackAggregate(
            total_entries=1,
            avg_reward=0.6,
            avg_offer_probability=0.7,
            avg_retrieval_reward=0.8,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        agent.generate_dataset(agg, results)
        cached = agent.cached_samples
        assert len(cached) > 0

    def test_clear_samples(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [_make_entry()]
        results = [_make_result()]
        agg = FeedbackAggregate(
            total_entries=1,
            avg_reward=0.6,
            avg_offer_probability=0.7,
            avg_retrieval_reward=0.8,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        agent.generate_dataset(agg, results)
        agent.clear_samples()
        assert agent.cached_samples == []


class TestDedup:
    def test_dataset_no_duplicate_sample_ids(self):
        from backend.feedback.feedback_agent import FeedbackAgent

        agent = FeedbackAgent()
        entries = [
            _make_entry(sim_id="sim-001"),
            _make_entry(sim_id="sim-002"),
            _make_entry(sim_id="sim-003"),
        ]
        results = [
            _make_result(sim_id="sim-001"),
            _make_result(sim_id="sim-002"),
            _make_result(sim_id="sim-003"),
        ]
        agg = FeedbackAggregate(
            total_entries=3,
            avg_reward=0.6,
            avg_offer_probability=0.7,
            avg_retrieval_reward=0.8,
            total_ranking_penalty=0.0,
            entries=entries,
        )
        dataset = agent.generate_dataset(agg, results)
        ids = [s.sample_id for s in dataset]
        assert len(ids) == len(set(ids))
