"""FeedbackAgent — convert system outputs into training data for learning-to-rank.

Merges simulation + reviewer + user behavior logs into TrainingSample objects.
Generates learning-to-rank datasets that enable the system improvement loop.

Core capability: feature extraction → label computation → dataset assembly.
"""

from __future__ import annotations

import hashlib

from backend.feedback.schemas import FeedbackAggregate, FeedbackEntry, TrainingSample
from backend.shared.types import MatchResult
from backend.simulation.state import SimulationResult


class FeedbackAgent:
    """Convert system outputs into training data for the closed-loop learning system.

    All improvement comes from feedback_agent output — this is the single source
    of truth for learning signals.

    Usage:
        agent = FeedbackAgent()
        sample = agent.generate_sample(entry, result, match)
        dataset = agent.generate_dataset(aggregate, results, matches)
    """

    def __init__(self):
        self._samples: list[TrainingSample] = []

    # ── Public API ────────────────────────────────────────────────────────

    def generate_sample(
        self,
        entry: FeedbackEntry,
        result: SimulationResult,
        match: MatchResult | None = None,
    ) -> TrainingSample:
        """Generate one TrainingSample from feedback + simulation + retrieval data.

        Args:
            entry: Reviewer-generated FeedbackEntry with all signals
            result: Original SimulationResult
            match: The MatchResult that was simulated (may be None for multi-path)

        Returns:
            TrainingSample with 12-dim feature vector, label, and reward
        """
        features = self._extract_features(result, match)
        label = self._compute_label(entry, result)
        reward = entry.combined_signal
        sample_id = self._make_sample_id(entry)

        sample = TrainingSample(
            features=features,
            label=round(label, 4),
            reward=round(reward, 4),
            sample_id=sample_id,
            source="simulation",
        )
        return sample

    def generate_dataset(
        self,
        aggregate: FeedbackAggregate,
        results: list[SimulationResult],
        matches: list[MatchResult] | None = None,
    ) -> list[TrainingSample]:
        """Generate a learning-to-rank dataset from a batch of results.

        Pairs each SimulationResult with its corresponding MatchResult by position.
        Filters out low-quality samples (label < 0.1 or empty features).
        Sorts by label descending (ranked dataset format).

        Args:
            aggregate: Batch review output from ReviewerAgent.review_batch()
            results: All simulation results in the batch
            matches: Corresponding MatchResult for each simulation (aligned by index)

        Returns:
            Ranked list of TrainingSample (highest label first)
        """
        match_list = matches or []
        samples: list[TrainingSample] = []

        for i, (entry, result) in enumerate(zip(aggregate.entries, results)):
            match = match_list[i] if i < len(match_list) else None
            try:
                sample = self.generate_sample(entry, result, match)
                if sample.label >= 0.1 and sample.features:
                    samples.append(sample)
            except Exception:
                continue

        # Sort by label descending (learning-to-rank format)
        samples.sort(key=lambda s: s.label, reverse=True)

        # Persist for API retrieval
        self._samples = (self._samples + samples)[-5000:]

        return samples

    @property
    def cached_samples(self) -> list[TrainingSample]:
        """Access accumulated samples (for API retrieval)."""
        return list(self._samples)

    def clear_samples(self) -> None:
        """Reset sample cache."""
        self._samples.clear()

    # ── Feature extraction ────────────────────────────────────────────────

    def _extract_features(
        self,
        result: SimulationResult,
        match: MatchResult | None = None,
    ) -> dict:
        """Extract 12-dim feature vector from simulation result.

        Features:
          0. skill_match_ratio: float [0, 1] — candidate skills / required skills
          1. hr_score: float [0, 1] — HR gate score
          2. interview_score: float [0, 1] — interview gate score
          3. success_probability: float [0, 1] — engine estimate
          4. step_count: float [0, 1] — normalized by max_steps
          5. has_skill_gaps: float {0.0, 1.0} — binary flag
          6. gap_count: float [0, 1] — normalized missing skill count
          7. strategy_aggressiveness: float [0, 1] — mapped from strategy_name
          8. experience_years_estimate: float [0, 1] — from resume experience count
          9. location_match: float {0.0, 1.0} — binary flag
          10. salary_above_median: float {0.0, 1.0} — binary flag
          11. retrieval_score: float [0, 1] — cosine similarity from MatchResult
        """
        state = result.final_state
        candidate = state.candidate
        job = state.job

        # 0. Skill match ratio
        candidate_skills = {s.lower().strip() for s in candidate.skills}
        required = job.required_skills
        skill_match_ratio = (
            sum(1 for s in required if s.lower().strip() in candidate_skills) / len(required)
            if required
            else 1.0
        )

        # 1-2. Gate scores
        hr_score = state.scores.get("hr_screen", 0.0)
        interview_score = state.scores.get("interview", 0.0)

        # 3. Success probability (direct from result)
        success_probability = result.success_probability

        # 4. Step count (normalized by max_steps)
        step_count = min(state.step_count / max(state.max_steps, 1), 1.0)

        # 5-6. Skill gaps
        missing = [s for s in required if s.lower().strip() not in candidate_skills]
        has_skill_gaps = 1.0 if missing else 0.0
        gap_count = min(len(missing) / 10.0, 1.0)  # normalize: 10+ gaps = 1.0

        # 7. Strategy aggressiveness
        strategy_map = {
            "aggressive": 0.9,
            "balanced": 0.6,
            "conservative": 0.3,
            "default": 0.5,
        }
        strategy_aggressiveness = strategy_map.get(
            result.strategy_name.lower(), 0.5
        )

        # 8. Experience years estimate (from education earliest year)
        experience_years_estimate = 0.5  # default
        if candidate.experience:
            experience_years_estimate = min(len(candidate.experience) / 5.0, 1.0)

        # 9. Location match
        location_match = 0.0
        if candidate.education and job.location:
            # Best-effort: check if candidate has any context matching job location
            location_match = 0.5  # MVP default — location from resume is unstructured
        if not job.location:
            location_match = 1.0  # remote/no-location jobs always match

        # 10. Salary above median (simplified)
        salary_above_median = 0.5  # default when no salary data
        if job.salary_range:
            mid = (job.salary_range[0] + job.salary_range[1]) / 2
            salary_above_median = 1.0 if mid >= 400 else 0.0  # 400K/yr = 33K/mo

        # 11. Retrieval score
        retrieval_score = match.score if match else 0.5

        return {
            "skill_match_ratio": round(skill_match_ratio, 4),
            "hr_score": round(hr_score, 4),
            "interview_score": round(interview_score, 4),
            "success_probability": round(success_probability, 4),
            "step_count": round(step_count, 4),
            "has_skill_gaps": has_skill_gaps,
            "gap_count": round(gap_count, 4),
            "strategy_aggressiveness": round(strategy_aggressiveness, 4),
            "experience_years_estimate": round(experience_years_estimate, 4),
            "location_match": round(location_match, 4),
            "salary_above_median": salary_above_median,
            "retrieval_score": round(retrieval_score, 4),
        }

    # ── Label computation ──────────────────────────────────────────────────

    def _compute_label(
        self,
        entry: FeedbackEntry,
        result: SimulationResult,
    ) -> float:
        """Compute target relevance label from feedback signals + outcome.

        Label = 0.5 × combined_signal + 0.5 × outcome_binary
        where outcome_binary = 1.0 if accepted else 0.0 if rejected else 0.3 if timeout

        Clamped to [0.0, 1.0].
        """
        outcome_map = {"accepted": 1.0, "rejected": 0.0, "timeout": 0.3}
        outcome_binary = outcome_map.get(result.outcome, 0.0)

        label = 0.5 * entry.combined_signal + 0.5 * outcome_binary
        return max(0.0, min(1.0, label))

    # ── Long-term aggregation (T006 L3) ────────────────────────────────────

    @staticmethod
    def aggregate_long_term(
        session_metrics: list[dict] | None = None,
        retraining_metrics: list[dict] | None = None,
        ranking_performance: list[dict] | None = None,
    ) -> "LongTermReport":
        """Aggregate long-term recommendation performance across sessions.

        Detects degradation when NDCG@10 drops below 80% of peak.
        """
        from backend.session.schemas import LongTermReport
        import statistics
        from datetime import datetime, timezone

        sessions = session_metrics or []
        rankings = ranking_performance or []

        report = LongTermReport(
            period_start=datetime.now(timezone.utc).isoformat(),
            period_end=datetime.now(timezone.utc).isoformat(),
        )

        # Average CTR across sessions
        ctrs = [s.get("session_ctr", 0.0) for s in sessions if isinstance(s, dict)]
        if ctrs:
            report.avg_ctr = round(statistics.mean(ctrs), 4)

        # Average NDCG@10
        ndcg_vals = [r.get("ndcg_10", r.get("train_ndcg_10", 0.0)) for r in rankings if isinstance(r, dict)]
        if ndcg_vals:
            report.avg_ndcg_10 = round(statistics.mean(ndcg_vals), 4)

        # MRR (from reviewer metrics if available)
        mrr_vals = [r.get("mrr", 0.0) for r in rankings if isinstance(r, dict) and r.get("mrr")]
        if mrr_vals:
            report.avg_mrr = round(statistics.mean(mrr_vals), 4)

        # Save / apply rates
        saves = [s.get("save_rate", 0.0) for s in sessions if isinstance(s, dict)]
        applies = [s.get("apply_rate", 0.0) for s in sessions if isinstance(s, dict)]
        if saves:
            report.avg_save_rate = round(statistics.mean(saves), 4)
        if applies:
            report.avg_apply_rate = round(statistics.mean(applies), 4)

        report.total_sessions = len(sessions)

        # Session retention (at least 2 actions per session)
        retained = sum(1 for s in sessions if isinstance(s, dict) and s.get("total_actions", 0) >= 2)
        report.session_retention = round(retained / len(sessions), 4) if sessions else 0.0

        # Degradation detection: NDCG drops below 80% of recent peak
        if ndcg_vals and len(ndcg_vals) >= 3:
            recent_peak = max(ndcg_vals)
            current = ndcg_vals[-1]
            if current < recent_peak * 0.8:
                report.degradation_detected = True
                report.retraining_recommendation = (
                    f"NDCG@10 degraded from peak {recent_peak:.4f} to {current:.4f}. "
                    "Consider incremental retraining with recent session data."
                )
            else:
                report.retraining_recommendation = "Model performance stable. Continue monitoring."

        return report

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _make_sample_id(entry: FeedbackEntry) -> str:
        """Deterministic sample ID: md5(simulation_id + strategy_name)[:12]."""
        raw = f"{entry.simulation_id}:{entry.strategy_name}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
