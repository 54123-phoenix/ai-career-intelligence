"""Integration tests: full ranking pipeline flow."""

import pytest
from backend.ranking.feature_builder import FeatureBuilderAgent
from backend.ranking.model_store import ModelStore
from backend.ranking.pair_builder import PairBuilderAgent
from backend.ranking.reranker import RerankEngineAgent
from backend.ranking.schemas import FeatureVector, UserBehaviorLog
from backend.shared.types import MatchResult


def _make_candidate(item_id: str, score: float, payload: dict | None = None) -> MatchResult:
    return MatchResult(
        item_id=item_id,
        score=score,
        payload=payload or {"required_skills": ["Python"], "company": "Google"},
        match_type="resume_to_job",
    )


def _make_log(job_id: str, action: str, dwell_ms: int = 0) -> UserBehaviorLog:
    return UserBehaviorLog(
        trace_id="t1",
        job_id=job_id,
        action=action,
        dwell_time_ms=dwell_ms,
        position=0,
    )


class TestRankingPipeline:
    def test_full_pipeline_feature_to_rerank(self):
        """Feature building → reranking (identity fallback)."""
        builder = FeatureBuilderAgent()
        engine = RerankEngineAgent(model_store=ModelStore())

        candidates = [
            _make_candidate("j1", 0.9, {"required_skills": ["Python"], "company": "Google"}),
            _make_candidate("j2", 0.5, {"required_skills": ["Java"], "company": "Startup"}),
        ]

        fvs = builder.build_features("trace-001", {"skills": ["Python"]}, candidates)
        assert len(fvs) == 2

        reranked = engine.rerank("trace-001", fvs)
        assert reranked[0].candidate_id == "j1"  # higher embedding_similarity
        assert reranked[0].final_rank == 1
        assert reranked[1].final_rank == 2

    def test_trace_id_flows_through_all_stages(self):
        """trace_id propagates from features → reranked → pairs."""
        trace_id = "exec-full-001"

        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.8)]
        fvs = builder.build_features(trace_id, {"skills": ["Python"]}, candidates)
        assert all(fv.trace_id == trace_id for fv in fvs)

        engine = RerankEngineAgent(model_store=ModelStore())
        reranked = engine.rerank(trace_id, fvs)
        assert all(rc.trace_id == trace_id for rc in reranked)

        pair_builder = PairBuilderAgent()
        logs = [_make_log("j1", "clicked"), _make_log("j2", "skipped")]
        pairs = pair_builder.build_pairs(trace_id, logs)
        assert all(p.trace_id == trace_id for p in pairs)

    def test_identity_rerank_when_no_model(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [
            FeatureVector(
                candidate_id="j1",
                trace_id="t1",
                features={"embedding_similarity": 0.3},
            ),
            FeatureVector(
                candidate_id="j2",
                trace_id="t1",
                features={"embedding_similarity": 0.9},
            ),
        ]
        result = engine.rerank("t1", fvs)
        assert result[0].candidate_id == "j2"
        assert result[0].ranking_score == 0.9

    def test_pairs_generated_from_behavior(self):
        builder = PairBuilderAgent()
        logs = [
            _make_log("j1", "clicked", dwell_ms=5000),
            _make_log("j2", "skipped", dwell_ms=200),
            _make_log("j3", "clicked", dwell_ms=3000),
        ]
        pairs = builder.build_pairs("t1", logs)
        # j1 clicked vs j2 skipped, j3 clicked vs j2 skipped = 2 pairs
        assert len(pairs) == 2
        relations = {p.relation for p in pairs}
        assert relations == {"clicked_gt_skipped"}

    def test_ranking_pipeline_with_features_then_pairs(self):
        """End-to-end: candidates → features → rerank → behavior → pairs."""
        trace_id = "e2e-001"

        # 1. Feature building
        builder = FeatureBuilderAgent()
        candidates = [
            _make_candidate("j1", 0.9),
            _make_candidate("j2", 0.4),
            _make_candidate("j3", 0.7),
        ]
        fvs = builder.build_features(trace_id, {"skills": ["Python", "SQL"]}, candidates)
        assert len(fvs) == 3

        # 2. Rerank
        engine = RerankEngineAgent(model_store=ModelStore())
        reranked = engine.rerank(trace_id, fvs)
        assert reranked[0].candidate_id == "j1"
        assert reranked[2].candidate_id == "j2"

        # 3. Pair building from simulated user behavior
        logs = [
            _make_log("j1", "clicked", dwell_ms=8000),
            _make_log("j2", "skipped", dwell_ms=100),
            _make_log("j3", "clicked", dwell_ms=5000),
        ]
        pair_builder = PairBuilderAgent()
        pairs = pair_builder.build_pairs(trace_id, logs)
        assert len(pairs) >= 2  # j1>j2, j3>j2
