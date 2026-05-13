"""Tests for PairBuilderAgent."""

import pytest
from backend.ranking.pair_builder import PairBuilderAgent
from backend.ranking.schemas import UserBehaviorLog


def _log(job_id: str, action: str, position: int = 0, dwell_ms: int = 0) -> UserBehaviorLog:
    return UserBehaviorLog(
        trace_id="t1",
        job_id=job_id,
        action=action,
        dwell_time_ms=dwell_ms,
        position=position,
    )


class TestPairBuilder:
    def test_clicked_vs_skipped_pairs(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "clicked"), _log("j2", "skipped")]
        pairs = builder.build_pairs("t1", logs)
        assert len(pairs) == 1
        assert pairs[0].positive_job_id == "j1"
        assert pairs[0].negative_job_id == "j2"
        assert pairs[0].relation == "clicked_gt_skipped"

    def test_saved_vs_clicked_pairs(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "saved"), _log("j2", "clicked")]
        pairs = builder.build_pairs("t1", logs)
        assert len(pairs) == 1
        assert pairs[0].positive_job_id == "j1"
        assert pairs[0].negative_job_id == "j2"
        assert pairs[0].relation == "saved_gt_clicked"

    def test_no_self_pairs(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "clicked"), _log("j1", "skipped")]
        pairs = builder.build_pairs("t1", logs)
        assert len(pairs) == 0

    def test_empty_logs_returns_empty(self):
        builder = PairBuilderAgent()
        assert builder.build_pairs("t1", []) == []

    def test_single_action_type_no_pairs(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "clicked"), _log("j2", "clicked")]
        pairs = builder.build_pairs("t1", logs)
        assert pairs == []

    def test_pair_id_deterministic(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "clicked"), _log("j2", "skipped")]
        pairs1 = builder.build_pairs("t1", logs)
        pairs2 = builder.build_pairs("t1", logs)
        assert pairs1[0].pair_id == pairs2[0].pair_id

    def test_pair_id_unique_for_different_relations(self):
        id1 = PairBuilderAgent._make_pair_id("j1", "j2", "clicked_gt_skipped")
        id2 = PairBuilderAgent._make_pair_id("j1", "j2", "saved_gt_clicked")
        assert id1 != id2

    def test_trace_id_on_all_pairs(self):
        builder = PairBuilderAgent()
        logs = [_log("j1", "clicked"), _log("j2", "skipped")]
        pairs = builder.build_pairs("exec-001", logs)
        for p in pairs:
            assert p.trace_id == "exec-001"

    def test_saved_not_paired_with_saved_clicked_job(self):
        """A job that is both saved and clicked should not appear as negative in saved>clicked pairs."""
        builder = PairBuilderAgent()
        logs = [_log("j1", "saved"), _log("j1", "clicked"), _log("j2", "clicked")]
        pairs = builder.build_pairs("t1", logs)
        # Only j1(saved) > j2(clicked, not saved), no self-pair j1 > j1
        for p in pairs:
            assert p.negative_job_id != "j1"

    def test_multiple_clicked_vs_multiple_skipped(self):
        builder = PairBuilderAgent()
        logs = [
            _log("j1", "clicked"),
            _log("j2", "clicked"),
            _log("j3", "skipped"),
            _log("j4", "skipped"),
        ]
        pairs = builder.build_pairs("t1", logs)
        # 2 clicked × 2 skipped = 4 pairs
        assert len(pairs) == 4
