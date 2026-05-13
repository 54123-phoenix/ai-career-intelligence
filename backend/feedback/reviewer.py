"""ReviewerAgent — evaluates simulation quality, detects bias, generates correction signals.

Independent from simulation engine internals. Only consumes public result types:
- SimulationResult (from backend.simulation.state)
- MatchResult (from backend.shared.types)

Acts as "teacher signal generator" for the closed-loop learning system.
"""

from __future__ import annotations

import statistics
from collections import Counter

from backend.feedback.schemas import BiasFinding, FeedbackAggregate, FeedbackEntry
from backend.shared.types import MatchResult
from backend.simulation.state import SimulationResult


class ReviewerAgent:
    """Evaluate simulation quality and detect systematic bias.

    Independence from simulation engine is enforced by design:
    - Does NOT import from backend.simulation.engine or any agent modules
    - Only consumes SimulationResult, MatchResult (public types)
    - Generates correction signals consumed by FeedbackAgent

    Usage:
        reviewer = ReviewerAgent()
        entry = reviewer.review(result, matches)
        aggregate = reviewer.review_batch(results, retrieval_context)
    """

    # Weights for combining signals into FeedbackEntry.combined_signal
    W_SIM_REWARD = 0.40
    W_RETRIEVAL = 0.35
    W_PENALTY = 0.25

    def review(
        self,
        result: SimulationResult,
        retrieval_matches: list[MatchResult] | None = None,
    ) -> FeedbackEntry:
        """Review a single simulation result. Produces a FeedbackEntry with all signals.

        Args:
            result: Completed simulation result from SimulationEngine.run()
            retrieval_matches: The MatchResult list that fed into this simulation

        Returns:
            FeedbackEntry with computed signals ready for FeedbackAgent consumption
        """
        total_reward = self._sim_reward(result)
        retrieval_reward = self._compute_retrieval_reward(result, retrieval_matches)
        ranking_penalty = self._compute_ranking_penalty(result, retrieval_matches)
        bias_flags = self._flag_issues(result)
        combined = self._combine_signals(
            total_reward, retrieval_reward, ranking_penalty, bias_flags
        )

        return FeedbackEntry(
            simulation_id=result.simulation_id,
            strategy_name=result.strategy_name,
            outcome=result.outcome,
            total_reward=round(total_reward, 4),
            offer_probability=result.success_probability,
            skill_gap_score=self._skill_gap_from_result(result),
            retrieval_reward=round(retrieval_reward, 4),
            ranking_penalty=round(ranking_penalty, 4),
            bias_flags=bias_flags,
            combined_signal=round(combined, 4),
            timestamp=0,  # filled by caller if needed
        )

    def review_batch(
        self,
        results: list[SimulationResult],
        retrieval_context: dict[str, list[MatchResult]] | None = None,
    ) -> FeedbackAggregate:
        """Review multiple simulation results. Detects batch-level bias patterns.

        Args:
            results: List of completed simulation results
            retrieval_context: {simulation_id: [MatchResult]} mapping

        Returns:
            FeedbackAggregate with per-entry reviews + batch-level bias findings
        """
        ctx = retrieval_context or {}
        entries: list[FeedbackEntry] = []
        for r in results:
            matches = ctx.get(r.simulation_id)
            entry = self.review(r, matches)
            entries.append(entry)

        bias_findings = self._detect_bias(results, entries)

        if not entries:
            return FeedbackAggregate(
                total_entries=0,
                avg_reward=0.0,
                avg_offer_probability=0.0,
                avg_retrieval_reward=0.0,
                total_ranking_penalty=0.0,
                bias_incident_count=len(bias_findings),
                entries=[],
            )

        return FeedbackAggregate(
            total_entries=len(entries),
            avg_reward=round(statistics.mean(e.total_reward for e in entries), 4),
            avg_offer_probability=round(
                statistics.mean(e.offer_probability for e in entries), 4
            ),
            avg_retrieval_reward=round(
                statistics.mean(e.retrieval_reward for e in entries), 4
            ),
            total_ranking_penalty=round(sum(e.ranking_penalty for e in entries), 4),
            bias_incident_count=len(bias_findings),
            entries=entries,
        )

    # ------------------------------------------------------------------
    # Session-level review (T006 L3)
    # ------------------------------------------------------------------

    def review_session(
        self,
        session_summary,
        reranked_results: list | None = None,
        drift_score: float = 0.0,
        engagement_history: list[float] | None = None,
    ):
        """Review session-level recommendation quality and detect drift anomalies.

        Args:
            session_summary: SessionSummary from behavior_aggregator
            reranked_results: Reranked candidates or retrieved candidates
            drift_score: Preference shift score from preference_updater
            engagement_history: Previous session engagement scores for trend detection

        Returns:
            SessionReview with computed metrics and detected issues
        """
        from backend.session.schemas import SessionReview

        # Compute CTR from session summary
        session_ctr = getattr(session_summary, 'click_through_rate', 0.0)
        engagement = getattr(session_summary, 'engagement_score', 0.0)
        session_id = getattr(session_summary, 'session_id', '')

        issues: list[str] = []

        # Drift detection: high shift score indicates unstable preferences
        if drift_score > 0.4:
            issues.append(
                f"unstable_preferences: shift_score={drift_score:.3f} exceeds threshold 0.4"
            )

        # Overreaction detection: if a single session dominates preferences
        if drift_score > 0.7:
            issues.append(
                f"overreaction_risk: single-session shift dominates preferences ({drift_score:.3f})"
            )

        # Engagement degradation: compare with previous sessions
        if engagement_history:
            recent_avg = sum(engagement_history) / len(engagement_history) if engagement_history else 0.0
            if recent_avg > 0 and engagement < recent_avg * 0.5:
                issues.append(
                    f"ranking_degradation: engagement dropped {engagement:.3f} vs avg {recent_avg:.3f}"
                )

        # Low engagement warning
        if engagement < 0.1:
            issues.append(f"low_engagement: {engagement:.3f}")

        # Check if CTR is suspiciously zero with many actions
        total_actions = getattr(session_summary, 'total_actions', 0)
        if session_ctr == 0.0 and total_actions > 10:
            issues.append("zero_ctr_with_actions: possible tracking issue")

        return SessionReview(
            session_id=session_id,
            session_ctr=round(session_ctr, 4),
            engagement_score=round(engagement, 4),
            drift_score=round(drift_score, 4),
            detected_issues=issues,
        )

    # ------------------------------------------------------------------
    # Internal signal computation
    # ------------------------------------------------------------------

    def _detect_bias(
        self,
        results: list[SimulationResult],
        entries: list[FeedbackEntry],
    ) -> list[BiasFinding]:
        """Scan for systematic bias across multiple simulation results.

        Checks:
          - Ranking bias: scores clustered in a narrow range (std < 0.05)
          - Skill bias: certain skills consistently over-weighted in outcomes
          - Confidence bias: all success_probability near a single value
          - Overfitting: identical strategy producing near-identical outputs
        """
        findings: list[BiasFinding] = []

        if len(results) < 3:
            return findings

        scores = [e.total_reward for e in entries]

        # 1. Ranking bias — low variance across results suggests undifferentiated output
        if len(scores) >= 5 and statistics.stdev(scores) < 0.05:
            findings.append(
                BiasFinding(
                    severity="medium",
                    category="ranking_bias",
                    description=f"Scores clustered in narrow range (σ={statistics.stdev(scores):.4f})",
                    affected_simulation_ids=[r.simulation_id for r in results],
                    correction_signal=-0.1,
                    recommendation="Increase candidate diversity or add deliberate exploration noise",
                )
            )

        # 2. Confidence bias — success_probability distribution suspiciously tight
        probs = [r.success_probability for r in results]
        if len(probs) >= 5 and statistics.stdev(probs) < 0.03:
            findings.append(
                BiasFinding(
                    severity="low",
                    category="confidence_bias",
                    description=f"Success probabilities nearly uniform (σ={statistics.stdev(probs):.4f})",
                    affected_simulation_ids=[r.simulation_id for r in results],
                    correction_signal=-0.05,
                    recommendation="Calibrate confidence intervals in simulation engine",
                )
            )

        # 3. Overfitting — same strategy producing identical outcomes
        outcome_counter = Counter(r.outcome for r in results)
        if len(results) >= 5:
            dominant = max(outcome_counter.values())
            if dominant == len(results):
                findings.append(
                    BiasFinding(
                        severity="high",
                        category="overfitting",
                        description=f"All {len(results)} simulations produced identical outcome: "
                        f"'{results[0].outcome}'",
                        affected_simulation_ids=[r.simulation_id for r in results],
                        correction_signal=-0.2,
                        recommendation="Strategy parameters may be too narrow; introduce exploration noise",
                    )
                )

        return findings

    def _compute_retrieval_reward(
        self,
        result: SimulationResult,
        matches: list[MatchResult] | None = None,
    ) -> float:
        """How well did retrieval serve this simulation?

        Based on: average match score, missing skills count, salary alignment.
        Without match data, falls back to skill_gap_score from the result.
        """
        if not matches:
            return self._skill_gap_from_result(result)

        avg_score = statistics.mean(m.score for m in matches) if matches else 0.0

        # Count missing skills across all matches
        total_missing = 0
        for m in matches:
            total_missing += len(m.payload.get("missing_skills", []))
        avg_missing = total_missing / len(matches) if matches else 999

        # High avg score + low missing = good retrieval
        missing_penalty = min(avg_missing * 0.1, 0.5)
        return round(max(avg_score - missing_penalty, 0.0), 4)

    def _compute_ranking_penalty(
        self,
        result: SimulationResult,
        matches: list[MatchResult] | None = None,
    ) -> float:
        """Penalty for poor ranking.

        High penalty when success_probability is low but top match score was high
        (indicates retrieval ranked a poor-fit job highly, wasting simulation cycles).
        """
        if not matches or not matches[0].score:
            return 0.0

        top_score = matches[0].score
        success = result.success_probability

        # If top match was high-confidence (>0.7) but simulation failed (<0.3), that's a ranking error
        if top_score > 0.7 and success < 0.3:
            return round((top_score - success) * 0.5, 4)

        # Mild penalty for moderate mismatch
        if top_score > 0.5 and success < 0.2:
            return round((top_score - success) * 0.3, 4)

        return 0.0

    def _flag_issues(self, result: SimulationResult) -> list[str]:
        """Flag individual result-level issues."""
        flags: list[str] = []
        if result.success_probability < 0.1:
            flags.append("very_low_success_probability")
        if result.outcome == "timeout":
            flags.append("simulation_timeout")
        if len(result.key_decisions) == 0:
            flags.append("no_key_decisions")
        if result.final_state.step_count <= 1:
            flags.append("premature_termination")
        return flags

    def _combine_signals(
        self,
        sim_reward: float,
        retrieval_reward: float,
        ranking_penalty: float,
        bias_flags: list[str],
    ) -> float:
        """Weighted combination: W_SIM*sim + W_RETRIEVAL*retrieval - W_PENALTY*penalty.

        Each bias_flag reduces the combined signal by 0.05.
        """
        base = (
            self.W_SIM_REWARD * sim_reward
            + self.W_RETRIEVAL * retrieval_reward
            - self.W_PENALTY * ranking_penalty
        )
        bias_discount = len(bias_flags) * 0.05
        return round(max(base - bias_discount, 0.0), 4)

    @staticmethod
    def _sim_reward(result: SimulationResult) -> float:
        """Extract total reward from simulation metrics when available, else estimate."""
        scores = result.final_state.scores
        final = scores.get("final", 0.0)
        hr = scores.get("hr_screen", 0.0)
        iv = scores.get("interview", 0.0)
        if final > 0:
            return final
        if hr > 0 and iv > 0:
            return round(hr * 0.4 + iv * 0.6, 4)
        if hr > 0:
            return round(hr * 0.5, 4)
        return result.success_probability

    @staticmethod
    def _skill_gap_from_result(result: SimulationResult) -> float:
        """Compute skill gap score from simulation state."""
        candidate_skills = {s.lower().strip() for s in result.final_state.candidate.skills}
        required = result.final_state.job.required_skills
        if not required:
            return 1.0
        matched = sum(1 for s in required if s.lower().strip() in candidate_skills)
        return round(matched / len(required), 4)
