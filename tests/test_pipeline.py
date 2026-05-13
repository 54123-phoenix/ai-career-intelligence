"""Unit tests for Pipeline Orchestration — T005."""

from __future__ import annotations

import pytest

from backend.pipeline.modes import ExecutionMode, ExecutionPlan, PipelineContext


# ---------------------------------------------------------------------------
# ArchitectAgent
# ---------------------------------------------------------------------------


class TestArchitectAgent:
    def test_determine_plan_force_mode(self):
        from backend.pipeline.architect import ArchitectAgent

        architect = ArchitectAgent()
        plan = architect.determine_plan(
            "test query", force_mode=ExecutionMode.FULL
        )
        assert plan.mode == ExecutionMode.FULL
        assert "User-forced" in plan.reason

    def test_determine_plan_full_mode_default(self):
        from backend.pipeline.architect import ArchitectAgent

        architect = ArchitectAgent()
        plan = architect.determine_plan("Python 后端 北京")
        # Without cache, should default to FULL
        assert plan.mode == ExecutionMode.FULL

    def test_determine_plan_with_cache_miss(self):
        from backend.pipeline.architect import ArchitectAgent
        from backend.pipeline.cache import RetrievalCache

        cache = RetrievalCache(ttl_seconds=300)
        architect = ArchitectAgent(cache=cache)
        plan = architect.determine_plan("Python 后端 北京")
        assert plan.mode == ExecutionMode.FULL
        assert not plan.cache_used

    def test_query_complexity_simple(self):
        from backend.pipeline.architect import ArchitectAgent

        complexity = ArchitectAgent._assess_query_complexity("Python")
        assert complexity < 0.3

    def test_query_complexity_complex(self):
        from backend.pipeline.architect import ArchitectAgent

        complexity = ArchitectAgent._assess_query_complexity(
            "高级 Python 后端 北京 5年经验 Kafka Flink 微服务架构"
        )
        assert complexity > 0.3

    def test_should_simulate_no_matches(self):
        from backend.pipeline.architect import ArchitectAgent

        assert not ArchitectAgent._should_simulate(0, 0.5)

    def test_should_simulate_simple_query(self):
        from backend.pipeline.architect import ArchitectAgent

        assert not ArchitectAgent._should_simulate(10, 0.1)

    def test_should_simulate_normal(self):
        from backend.pipeline.architect import ArchitectAgent

        assert ArchitectAgent._should_simulate(10, 0.5)

    def test_system_health_check(self):
        from backend.pipeline.architect import ArchitectAgent

        architect = ArchitectAgent()
        health = architect._check_system_health()
        assert "qdrant" in health
        assert "embedder" in health
        assert "simulation_engine" in health


# ---------------------------------------------------------------------------
# RetrievalCache
# ---------------------------------------------------------------------------


class TestRetrievalCache:
    def test_set_and_get(self):
        from backend.pipeline.cache import RetrievalCache
        from backend.shared.types import MatchResult

        cache = RetrievalCache(ttl_seconds=300)
        results = [MatchResult(item_id="j1", score=0.9, payload={}, match_type="resume_to_job")]
        cache.set("key1", results)
        cached = cache.get("key1")
        assert cached is not None
        assert cached[0].item_id == "j1"

    def test_cache_miss(self):
        from backend.pipeline.cache import RetrievalCache

        cache = RetrievalCache(ttl_seconds=300)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        from backend.pipeline.cache import RetrievalCache
        from backend.shared.types import MatchResult
        import time

        cache = RetrievalCache(ttl_seconds=0)  # immediate expiry
        results = [MatchResult(item_id="j1", score=0.9, payload={}, match_type="resume_to_job")]
        cache.set("key1", results)
        time.sleep(0.01)  # let TTL expire (0s TTL + any time > 0)
        assert cache.get("key1") is None

    def test_is_valid(self):
        from backend.pipeline.cache import RetrievalCache
        from backend.shared.types import MatchResult

        cache = RetrievalCache(ttl_seconds=3600)
        results = [MatchResult(item_id="j1", score=0.9, payload={}, match_type="resume_to_job")]
        cache.set("key1", results)
        assert cache.is_valid("key1")

    def test_invalidate_key(self):
        from backend.pipeline.cache import RetrievalCache
        from backend.shared.types import MatchResult

        cache = RetrievalCache(ttl_seconds=3600)
        results = [MatchResult(item_id="j1", score=0.9, payload={}, match_type="resume_to_job")]
        cache.set("key1", results)
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_invalidate_all(self):
        from backend.pipeline.cache import RetrievalCache
        from backend.shared.types import MatchResult

        cache = RetrievalCache(ttl_seconds=3600)
        results = [MatchResult(item_id="j1", score=0.9, payload={}, match_type="resume_to_job")]
        cache.set("k1", results)
        cache.set("k2", results)
        cache.invalidate(None)
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_make_key_deterministic(self):
        from backend.pipeline.cache import RetrievalCache

        k1 = RetrievalCache.make_key("Python 北京", {"location": "北京"})
        k2 = RetrievalCache.make_key("Python 北京", {"location": "北京"})
        assert k1 == k2

    def test_make_key_different_for_different_input(self):
        from backend.pipeline.cache import RetrievalCache

        k1 = RetrievalCache.make_key("Python 北京", {"location": "北京"})
        k2 = RetrievalCache.make_key("Python 上海", {"location": "上海"})
        assert k1 != k2


# ---------------------------------------------------------------------------
# PipelineContext
# ---------------------------------------------------------------------------


class TestPipelineContext:
    def test_default_values(self):
        ctx = PipelineContext()
        assert ctx.execution_id.startswith("exec-")
        assert ctx.mode == ExecutionMode.FULL
        assert ctx.retrieved_candidates == []
        assert ctx.simulation_results == []
        assert ctx.training_samples == []
        assert ctx.errors == []

    def test_field_assignment(self):
        ctx = PipelineContext(user_query="test", mode=ExecutionMode.FAST)
        assert ctx.user_query == "test"
        assert ctx.mode == ExecutionMode.FAST


# ---------------------------------------------------------------------------
# ExecutionPlan
# ---------------------------------------------------------------------------


class TestExecutionPlan:
    def test_default_plan(self):
        plan = ExecutionPlan(mode=ExecutionMode.FULL)
        assert plan.mode == ExecutionMode.FULL
        assert plan.steps == []
        assert plan.simulation_needed is True
        assert plan.retrieval_top_k == 20

    def test_fast_plan(self):
        plan = ExecutionPlan(
            mode=ExecutionMode.FAST,
            steps=["cache_lookup", "simulation_top3"],
            reason="Cache hit",
            cache_used=True,
            simulation_needed=True,
            retrieval_top_k=3,
        )
        assert plan.retrieval_top_k == 3
        assert plan.cache_used is True
