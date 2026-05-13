"""Tests for RankingTrainerAgent."""

import tempfile
from pathlib import Path

import pytest

from backend.ranking.model_store import ModelStore
from backend.ranking.schemas import RankingPair
from backend.ranking.trainer import RankingTrainerAgent

try:
    import lightgbm  # noqa: F401
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False

lgb_required = pytest.mark.skipif(not LGB_AVAILABLE, reason="lightgbm not installed")


def _make_pair(
    pos_id: str,
    neg_id: str,
    pos_features: dict | None = None,
    neg_features: dict | None = None,
    relation: str = "clicked_gt_skipped",
    trace_id: str = "t1",
) -> RankingPair:
    return RankingPair(
        pair_id=f"{pos_id}_{neg_id}",
        trace_id=trace_id,
        positive_job_id=pos_id,
        negative_job_id=neg_id,
        positive_features=pos_features or {
            "skill_overlap_score": 0.8,
            "embedding_similarity": 0.7,
            "salary_match_score": 0.6,
            "company_quality_score": 0.5,
            "retrieval_rank": 0.5,
            "historical_ctr": 0.3,
            "dwell_time": 0.4,
            "save_frequency": 0.2,
        },
        negative_features=neg_features or {
            "skill_overlap_score": 0.2,
            "embedding_similarity": 0.3,
            "salary_match_score": 0.1,
            "company_quality_score": 0.4,
            "retrieval_rank": 0.1,
            "historical_ctr": 0.0,
            "dwell_time": 0.0,
            "save_frequency": 0.0,
        },
        relation=relation,
    )


def _gen_pairs(n: int = 20) -> list[RankingPair]:
    """Generate synthetic pairs with feature variance across queries."""
    pairs = []
    for i in range(n):
        trace_id = f"trace-{i // 5}"
        pos_f = {
            "f1": 0.7 + (i % 3) * 0.05,
            "f2": 0.6 + (i % 4) * 0.03,
        }
        neg_f = {
            "f1": 0.2 + (i % 3) * 0.05,
            "f2": 0.1 + (i % 4) * 0.02,
        }
        pairs.append(_make_pair(f"pos-{i}", f"neg-{i}", pos_f, neg_f, trace_id=trace_id))
    return pairs


class TestRankingTrainer:
    @pytest.fixture
    def store_and_trainer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ModelStore(storage_dir=tmpdir)
            trainer = RankingTrainerAgent(model_store=store)
            yield store, trainer

    @lgb_required
    def test_train_with_synthetic_pairs(self, store_and_trainer):
        store, trainer = store_and_trainer
        pairs = _gen_pairs(30)
        booster, meta = trainer.train(pairs, validation_split=0.3)
        assert meta.model_version == 1
        assert meta.training_samples_count == 30
        assert meta.is_active
        assert Path(meta.model_path).exists()

    @lgb_required
    def test_metrics_computed(self, store_and_trainer):
        store, trainer = store_and_trainer
        pairs = _gen_pairs(30)
        _, meta = trainer.train(pairs, validation_split=0.3)
        assert "pairwise_accuracy" in meta.metrics
        assert meta.metrics["pairwise_accuracy"] > 0.0

    @lgb_required
    def test_model_save_and_load(self, store_and_trainer):
        store, trainer = store_and_trainer
        pairs = _gen_pairs(20)
        booster, meta = trainer.train(pairs, validation_split=0.2)

        loaded = store.load(1)
        assert loaded is not None
        assert loaded[1].model_version == 1

    @lgb_required
    def test_version_increments(self, store_and_trainer):
        store, trainer = store_and_trainer
        pairs = _gen_pairs(30)
        _, m1 = trainer.train(pairs)
        _, m2 = trainer.train(pairs)
        assert m1.model_version == 1
        assert m2.model_version == 2

    def test_empty_pairs_raises(self, store_and_trainer):
        store, trainer = store_and_trainer
        with pytest.raises(ValueError, match="empty pairs"):
            trainer.train([])

    @lgb_required
    def test_evaluate_returns_metrics(self, store_and_trainer):
        store, trainer = store_and_trainer
        pairs = _gen_pairs(30)
        booster, _ = trainer.train(pairs, validation_split=0.3)
        metrics = trainer.evaluate(booster, pairs)
        assert "pairwise_accuracy" in metrics
        assert 0.0 <= metrics["pairwise_accuracy"] <= 1.0

    def test_infer_feature_names(self):
        pairs = [_make_pair("a", "b", {"x": 1.0, "y": 0.5}, {"x": 0.2, "y": 0.1})]
        names = RankingTrainerAgent._infer_feature_names(pairs)
        assert names == ["x", "y"]

    def test_infer_feature_names_empty(self):
        assert RankingTrainerAgent._infer_feature_names([]) == []
