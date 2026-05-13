"""Tests for FeatureBuilderAgent."""

import pytest
from backend.ranking.feature_builder import FeatureBuilderAgent
from backend.ranking.schemas import UserBehaviorLog
from backend.shared.types import MatchResult


def _make_candidate(item_id: str, score: float, payload: dict | None = None) -> MatchResult:
    return MatchResult(
        item_id=item_id,
        score=score,
        payload=payload or {},
        match_type="resume_to_job",
    )


def _make_log(job_id: str, action: str, dwell_ms: int = 0, position: int = 0) -> UserBehaviorLog:
    return UserBehaviorLog(
        trace_id="t1",
        job_id=job_id,
        action=action,
        dwell_time_ms=dwell_ms,
        position=position,
    )


class TestFeatureBuilder:
    def test_all_8_features_computed(self):
        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.85, {"required_skills": ["Python"], "company": "Google"})]
        result = builder.build_features("trace-1", {"skills": ["Python"]}, candidates)
        assert len(result) == 1
        for key in FeatureBuilderAgent.FEATURE_KEYS:
            assert key in result[0].features
            assert 0.0 <= result[0].features[key] <= 1.0

    def test_skill_overlap_perfect_match(self):
        overlap = FeatureBuilderAgent._compute_skill_overlap(
            {"python", "sql"}, {"python", "sql"}
        )
        assert overlap == 1.0

    def test_skill_overlap_no_match(self):
        overlap = FeatureBuilderAgent._compute_skill_overlap(
            {"python"}, {"java", "go"}
        )
        assert overlap == 0.0

    def test_skill_overlap_null_safe(self):
        assert FeatureBuilderAgent._compute_skill_overlap(set(), {"python"}) == 0.0
        assert FeatureBuilderAgent._compute_skill_overlap({"python"}, set()) == 1.0
        # Both empty: no job requirements = full match
        assert FeatureBuilderAgent._compute_skill_overlap(set(), set()) == 1.0

    def test_embedding_similarity_from_match_score(self):
        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.72)]
        result = builder.build_features("t1", {"skills": []}, candidates)
        assert result[0].features["embedding_similarity"] == 0.72

    def test_retrieval_rank_normalized(self):
        assert FeatureBuilderAgent._compute_retrieval_rank(0, 10) == 1.0
        assert FeatureBuilderAgent._compute_retrieval_rank(9, 10) == 0.1
        assert FeatureBuilderAgent._compute_retrieval_rank(0, 1) == 1.0

    def test_historical_features_zero_without_history(self):
        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.5)]
        result = builder.build_features("t1", {"skills": []}, candidates)
        assert result[0].features["historical_ctr"] == 0.0
        assert result[0].features["dwell_time"] == 0.0
        assert result[0].features["save_frequency"] == 0.0

    def test_historical_ctr_with_history(self):
        builder = FeatureBuilderAgent()
        logs = [
            _make_log("j1", "clicked", dwell_ms=5000),
            _make_log("j1", "skipped", dwell_ms=100),
            _make_log("j2", "clicked", dwell_ms=3000),
            _make_log("j2", "clicked", dwell_ms=4000),
        ]
        candidates = [_make_candidate("j1", 0.5), _make_candidate("j2", 0.6)]
        result = builder.build_features("t1", {"skills": []}, candidates, logs)
        assert result[0].features["historical_ctr"] == 0.5  # 1 click / 2 views
        assert result[1].features["historical_ctr"] == 1.0  # 2 clicks / 2 views

    def test_trace_id_on_all_outputs(self):
        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.5), _make_candidate("j2", 0.6)]
        result = builder.build_features("exec-abc", {"skills": []}, candidates)
        for fv in result:
            assert fv.trace_id == "exec-abc"

    def test_feature_key_ordering_consistent(self):
        builder = FeatureBuilderAgent()
        candidates = [_make_candidate("j1", 0.5)]
        result = builder.build_features("t1", {"skills": []}, candidates)
        keys = list(result[0].features.keys())
        assert keys == list(FeatureBuilderAgent.FEATURE_KEYS)

    def test_empty_candidates_returns_empty(self):
        builder = FeatureBuilderAgent()
        result = builder.build_features("t1", {"skills": []}, [])
        assert result == []

    def test_salary_match_score_null_safe(self):
        assert FeatureBuilderAgent._compute_salary_match(None, None) == 0.5
        assert FeatureBuilderAgent._compute_salary_match((100, 200), None) == 0.5
        assert FeatureBuilderAgent._compute_salary_match(None, [100, 200]) == 0.5

    def test_salary_match_perfect(self):
        # User prefers 200-400K, job midpoint is 300K → perfect match
        assert FeatureBuilderAgent._compute_salary_match((200, 400), [250, 350]) == 1.0

    def test_company_quality_known(self):
        assert FeatureBuilderAgent._compute_company_quality("Google") == 1.0
        assert FeatureBuilderAgent._compute_company_quality("Alibaba") == 0.95

    def test_company_quality_unknown(self):
        assert FeatureBuilderAgent._compute_company_quality("UnknownCorp") == 0.50
        assert FeatureBuilderAgent._compute_company_quality("") == 0.50
