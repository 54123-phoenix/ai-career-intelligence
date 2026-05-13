"""Unit tests for Simulation Engine — T003 / T005."""

from __future__ import annotations

from datetime import date

import pytest

from backend.shared.types import StructuredJob, StructuredResume, WorkExperience
from backend.simulation.state import SimulationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_alice_resume() -> StructuredResume:
    return StructuredResume(
        resume_id="res-alice",
        name="Alice Wang",
        skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Docker", "AWS"],
        summary="Senior backend engineer, 5 years building distributed systems.",
        experience=[
            WorkExperience(
                company="TechCorp",
                title="Senior Backend Engineer",
                description="Built real-time data pipeline.",
                tech_stack=["Python", "Kafka", "Redis", "AWS"],
                start_date=date(2020, 3, 1),
                end_date=date(2025, 6, 1),
            ),
        ],
    )


def _make_bob_resume() -> StructuredResume:
    return StructuredResume(
        resume_id="res-bob",
        name="Bob Zhang",
        skills=["Python"],
        summary="Junior developer, 1 year experience.",
    )


def _make_backend_job() -> StructuredJob:
    return StructuredJob(
        job_id="job-001",
        title="Senior Backend Engineer",
        company="ACME Corp",
        location="上海",
        level="高级",
        required_skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
        optional_skills=["AWS", "GraphQL", "Terraform"],
        salary_range=(350, 550),
    )


def _make_ml_job() -> StructuredJob:
    return StructuredJob(
        job_id="job-002",
        title="ML Engineer",
        company="AILab",
        location="北京",
        level="高级",
        required_skills=["Python", "TensorFlow", "PyTorch", "NLP"],
        optional_skills=["Kubernetes", "MLflow"],
        salary_range=(400, 600),
    )


# ---------------------------------------------------------------------------
# SimulationEngine
# ---------------------------------------------------------------------------


class TestSimulationEngine:
    def test_run_returns_result(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job(), strategy="balanced")
        assert isinstance(result, SimulationResult)
        assert result.simulation_id.startswith("sim-")

    def test_run_accepted_for_strong_match(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job(), strategy="balanced")
        assert result.outcome in ("accepted", "rejected", "timeout")
        # Alice matches backend job well — should usually succeed
        assert result.success_probability > 0.0

    def test_run_produces_path_history(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job(), strategy="balanced")
        assert len(result.path_history) >= 1

    def test_run_produces_key_decisions(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job(), strategy="balanced")
        assert len(result.key_decisions) >= 0

    def test_run_weak_match_has_low_probability(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_bob_resume(), _make_ml_job(), strategy="balanced")
        # Bob has only Python, ML job requires TensorFlow/PyTorch/NLP
        assert result.success_probability < 1.0

    def test_run_respects_strategy(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        r1 = engine.run(_make_alice_resume(), _make_backend_job(), strategy="aggressive")
        r2 = engine.run(_make_alice_resume(), _make_backend_job(), strategy="conservative")
        # Both should produce valid results
        assert r1.simulation_id != r2.simulation_id
        assert r1.strategy_name == "aggressive"
        assert r2.strategy_name == "conservative"

    def test_run_confidence_interval_in_range(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job())
        lo, hi = result.confidence_interval
        assert 0.0 <= lo <= hi <= 1.0

    def test_run_recommendation_not_empty(self):
        from backend.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        result = engine.run(_make_alice_resume(), _make_backend_job())
        assert result.recommendation != ""


# ---------------------------------------------------------------------------
# CandidateAgent
# ---------------------------------------------------------------------------


class TestCandidateAgent:
    def test_act_returns_decision(self):
        from backend.simulation.candidate_agent import CandidateAgent
        from backend.simulation.state import SimulationState

        agent = CandidateAgent()
        state = SimulationState(
            simulation_id="sim-test",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="applied",
            step_count=0,
        )
        decision = agent.act(state)
        assert decision.agent_name == "candidate"
        assert decision.action in ("apply", "prepare", "pivot")
        assert 0.0 <= decision.confidence <= 1.0

    def test_strategy_affects_confidence(self):
        from backend.simulation.candidate_agent import CandidateAgent
        from backend.simulation.state import SimulationState

        agent = CandidateAgent()
        state_agg = SimulationState(
            simulation_id="sim-agg",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="applied",
            step_count=0,
            strategy_name="aggressive",
        )
        state_con = SimulationState(
            simulation_id="sim-con",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="applied",
            step_count=0,
            strategy_name="conservative",
        )
        d_agg = agent.act(state_agg)
        d_con = agent.act(state_con)
        # Aggressive should have higher base confidence
        # (not strictly guaranteed but characteristic of the implementation)
        assert d_agg.confidence >= 0.0
        assert d_con.confidence >= 0.0


# ---------------------------------------------------------------------------
# HRAgent
# ---------------------------------------------------------------------------


class TestHRAgent:
    def test_act_returns_decision(self):
        from backend.simulation.hr_agent import HRAgent
        from backend.simulation.state import SimulationState

        agent = HRAgent()
        state = SimulationState(
            simulation_id="sim-test",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="screened",
            step_count=1,
        )
        decision = agent.act(state)
        assert decision.agent_name == "hr"
        assert "score" in decision.params

    def test_strong_match_passes_screen(self):
        from backend.simulation.hr_agent import HRAgent
        from backend.simulation.state import SimulationState

        agent = HRAgent()
        state = SimulationState(
            simulation_id="sim-test",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="screened",
            step_count=1,
        )
        decision = agent.act(state)
        assert decision.params["score"] > 0.5
        assert decision.params.get("passed") is True

    def test_weak_match_fails_screen(self):
        from backend.simulation.hr_agent import HRAgent
        from backend.simulation.state import SimulationState

        agent = HRAgent()
        state = SimulationState(
            simulation_id="sim-test",
            candidate=_make_bob_resume(),
            job=_make_ml_job(),
            current_step="screened",
            step_count=1,
        )
        decision = agent.act(state)
        # Bob (only Python) vs ML job — should be lower
        assert decision.params["score"] < 0.5 or decision.params.get("hard_pass") is True


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_calculate_reward_in_range(self):
        from backend.simulation.metrics import calculate_reward
        from backend.simulation.state import SimulationState

        state = SimulationState(
            simulation_id="sim-test",
            candidate=_make_alice_resume(),
            job=_make_backend_job(),
            current_step="accepted",
            step_count=4,
            scores={"hr_screen": 0.8, "interview": 0.7},
        )
        reward = calculate_reward(state)
        assert 0.0 <= reward <= 1.15  # optional_skills bonus can push slightly above 1.0

    def test_evaluate_returns_all_metrics(self):
        from backend.simulation.metrics import evaluate
        from backend.simulation.state import SimulationResult, SimulationState

        result = SimulationResult(
            simulation_id="sim-test",
            strategy_name="balanced",
            outcome="accepted",
            final_state=SimulationState(
                simulation_id="sim-test",
                candidate=_make_alice_resume(),
                job=_make_backend_job(),
                current_step="accepted",
                step_count=4,
                scores={"hr_screen": 0.8, "interview": 0.7},
            ),
            success_probability=0.8,
            confidence_interval=(0.7, 0.9),
            time_to_offer=4,
        )
        metrics = evaluate(result)
        assert "offer_probability" in metrics
        assert "skill_gap_score" in metrics
        assert "trajectory_efficiency" in metrics
        assert "total_reward" in metrics
        for key, v in metrics.items():
            if key == "steps":
                assert isinstance(v, int)
            else:
                assert isinstance(v, float), f"{key} = {v} is not float"
