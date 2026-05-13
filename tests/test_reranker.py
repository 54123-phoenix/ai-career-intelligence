"""Tests for RerankEngineAgent."""

import pytest
from backend.ranking.feature_builder import FeatureBuilderAgent
from backend.ranking.model_store import ModelStore
from backend.ranking.reranker import RerankEngineAgent
from backend.ranking.schemas import FeatureVector


def _make_fv(candidate_id: str, features: dict | None = None) -> FeatureVector:
    defaults = {
        "skill_overlap_score": 0.8,
        "embedding_similarity": 0.9,
        "salary_match_score": 0.7,
        "company_quality_score": 0.6,
        "retrieval_rank": 0.5,
        "historical_ctr": 0.1,
        "dwell_time": 0.2,
        "save_frequency": 0.05,
    }
    return FeatureVector(
        candidate_id=candidate_id,
        trace_id="t1",
        features=features or defaults,
    )


class TestReranker:
    def test_no_model_identity_fallback(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1", {"embedding_similarity": 0.9}), _make_fv("j2", {"embedding_similarity": 0.5})]
        result = engine.rerank("t1", fvs)
        assert result[0].candidate_id == "j1"
        assert result[1].candidate_id == "j2"
        assert result[0].ranking_score == 0.9

    def test_rank_assigned_1_indexed(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1", {"embedding_similarity": 0.3}), _make_fv("j2", {"embedding_similarity": 0.9})]
        result = engine.rerank("t1", fvs)
        assert result[0].candidate_id == "j2"
        assert result[0].final_rank == 1
        assert result[1].candidate_id == "j1"
        assert result[1].final_rank == 2

    def test_original_score_preserved(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1", {"embedding_similarity": 0.75})]
        result = engine.rerank("t1", fvs)
        assert result[0].original_score == 0.75

    def test_trace_id_on_outputs(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1")]
        result = engine.rerank("exec-xyz", fvs)
        for rc in result:
            assert rc.trace_id == "exec-xyz"

    def test_candidate_pool_not_modified(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1"), _make_fv("j2")]
        original_ids = [fv.candidate_id for fv in fvs]
        engine.rerank("t1", fvs)
        assert [fv.candidate_id for fv in fvs] == original_ids

    def test_has_active_model_false_initially(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        assert not engine.has_active_model()

    def test_rerank_identity_explicit(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [_make_fv("j1", {"embedding_similarity": 0.8})]
        result = engine.rerank_identity("t1", fvs)
        assert result[0].ranking_score == 0.8
        assert result[0].original_score == 0.8

    def test_sorted_by_ranking_score_desc(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        fvs = [
            _make_fv("j1", {"embedding_similarity": 0.2}),
            _make_fv("j2", {"embedding_similarity": 0.9}),
            _make_fv("j3", {"embedding_similarity": 0.5}),
        ]
        result = engine.rerank("t1", fvs)
        assert result[0].candidate_id == "j2"
        assert result[1].candidate_id == "j3"
        assert result[2].candidate_id == "j1"

    def test_empty_feature_vectors(self):
        engine = RerankEngineAgent(model_store=ModelStore())
        assert engine.rerank("t1", []) == []
        assert engine.rerank_identity("t1", []) == []
