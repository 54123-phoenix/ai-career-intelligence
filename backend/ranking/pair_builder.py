"""PairBuilderAgent — generate pairwise ranking samples from real user behavior.

Ordering rules:
  1. clicked > skipped  — for each clicked job, pair with skipped jobs at lower/equal position
  2. saved > clicked    — for each saved job, pair with clicked-but-not-saved jobs
  3. Never self-pair (positive_job_id != negative_job_id)
  4. Only uses real UserBehaviorLog (never simulation output)

Pair IDs are deterministic: md5(positive_job_id + negative_job_id + relation)[:12]
"""

from __future__ import annotations

import hashlib
from collections import defaultdict

from backend.ranking.schemas import RankingPair, UserBehaviorLog


class PairBuilderAgent:
    """Generate pairwise ranking training samples from real user behavior logs.

    Usage:
        builder = PairBuilderAgent()
        pairs = builder.build_pairs(trace_id="exec-001", behavior_logs=logs)
    """

    def build_pairs(
        self,
        trace_id: str,
        behavior_logs: list[UserBehaviorLog],
    ) -> list[RankingPair]:
        """Generate pairwise ranking samples from a set of behavior logs.

        Args:
            trace_id: Pipeline execution ID
            behavior_logs: Real user interaction events (must NOT be simulation data)

        Returns:
            list[RankingPair] sorted by timestamp descending
        """
        if not behavior_logs:
            return []

        # Group logs by action, deduplicating by job_id (keep latest action per job)
        by_action = self._group_by_action(behavior_logs)

        clicked = by_action.get("clicked", [])
        skipped = by_action.get("skipped", [])
        saved = by_action.get("saved", [])

        pairs: list[RankingPair] = []

        # Rule 1: clicked > skipped
        pairs.extend(self._generate_clicked_vs_skipped(trace_id, clicked, skipped))

        # Rule 2: saved > clicked
        pairs.extend(self._generate_saved_vs_clicked(trace_id, saved, clicked, behavior_logs))

        # Sort by timestamp descending (most recent first)
        pairs.sort(key=lambda p: p.timestamp, reverse=True)
        return pairs

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _group_by_action(
        logs: list[UserBehaviorLog],
    ) -> dict[str, list[UserBehaviorLog]]:
        """Group logs by action type. Deduplicate: keep latest log per job_id per action."""
        by_action: dict[str, dict[str, UserBehaviorLog]] = defaultdict(dict)
        for log in logs:
            existing = by_action[log.action].get(log.job_id)
            if existing is None or log.timestamp > existing.timestamp:
                by_action[log.action][log.job_id] = log
        return {
            action: list(job_map.values())
            for action, job_map in by_action.items()
        }

    def _generate_clicked_vs_skipped(
        self,
        trace_id: str,
        clicked: list[UserBehaviorLog],
        skipped: list[UserBehaviorLog],
    ) -> list[RankingPair]:
        """For each clicked job, pair with every skipped job. No self-pairs."""
        pairs: list[RankingPair] = []
        skipped_ids = {s.job_id for s in skipped}

        for click in clicked:
            for skip in skipped:
                if click.job_id == skip.job_id:
                    continue  # Rule 3: no self-pairs
                pair = self._make_pair(
                    trace_id=trace_id,
                    positive_job_id=click.job_id,
                    negative_job_id=skip.job_id,
                    relation="clicked_gt_skipped",
                    timestamp=click.timestamp,
                )
                pairs.append(pair)
        return pairs

    def _generate_saved_vs_clicked(
        self,
        trace_id: str,
        saved: list[UserBehaviorLog],
        clicked: list[UserBehaviorLog],
        all_logs: list[UserBehaviorLog],
    ) -> list[RankingPair]:
        """For each saved job, pair with clicked-but-not-saved jobs.

        A job that is both saved and clicked by the same user should not be
        paired against itself. Jobs that were saved should only be paired
        against jobs that were clicked but NOT saved.
        """
        saved_ids = {s.job_id for s in saved}

        # Filter clicked to exclude jobs that were also saved
        clicked_not_saved = [c for c in clicked if c.job_id not in saved_ids]

        pairs: list[RankingPair] = []
        for save in saved:
            for click in clicked_not_saved:
                if save.job_id == click.job_id:
                    continue
                pair = self._make_pair(
                    trace_id=trace_id,
                    positive_job_id=save.job_id,
                    negative_job_id=click.job_id,
                    relation="saved_gt_clicked",
                    timestamp=save.timestamp,
                )
                pairs.append(pair)
        return pairs

    @staticmethod
    def _make_pair(
        trace_id: str,
        positive_job_id: str,
        negative_job_id: str,
        relation: str,
        timestamp: str,
    ) -> RankingPair:
        """Create a RankingPair with deterministic pair_id."""
        pair_id = PairBuilderAgent._make_pair_id(
            positive_job_id, negative_job_id, relation
        )
        return RankingPair(
            pair_id=pair_id,
            trace_id=trace_id,
            positive_job_id=positive_job_id,
            negative_job_id=negative_job_id,
            relation=relation,
            timestamp=timestamp,
        )

    @staticmethod
    def _make_pair_id(pos_job_id: str, neg_job_id: str, relation: str) -> str:
        """Deterministic pair ID: md5(pos + neg + relation)[:12]."""
        raw = f"{pos_job_id}:{neg_job_id}:{relation}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
