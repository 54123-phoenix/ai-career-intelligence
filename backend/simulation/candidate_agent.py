"""CandidateAgent — the job-seeker's decision-making logic.

Input:  SimulationState
Output: AgentDecision {action: apply | prepare | pivot, params, reasoning, confidence}

Pure rule-based logic. No LLM calls. Strategy-driven thresholds determine behavior.
"""

from __future__ import annotations

from datetime import datetime

from backend.shared.types import StructuredJob, StructuredResume

from .state import AgentDecision, SimulationState

# ---------------------------------------------------------------------------
# Strategy profiles — confidence + thresholds
# ---------------------------------------------------------------------------

STRATEGY_PROFILES: dict[str, dict] = {
    "aggressive": {
        "confidence": 0.9,
        "apply_threshold": 0.4,   # apply even with 40% skill match
        "prepare_threshold": 0.3,  # only prepare when below this
    },
    "conservative": {
        "confidence": 0.4,
        "apply_threshold": 0.8,    # only apply at 80%+ match
        "prepare_threshold": 0.6,
    },
    "balanced": {
        "confidence": 0.65,
        "apply_threshold": 0.6,
        "prepare_threshold": 0.4,
    },
    # fallback
    "default": {
        "confidence": 0.5,
        "apply_threshold": 0.5,
        "prepare_threshold": 0.5,
    },
}


class CandidateAgent:
    """Simulates a job candidate's strategic decision-making.

    Reads the current SimulationState and returns an AgentDecision based on
    the candidate's strategy profile and skill match against the target job.
    """

    def __init__(self, strategy: str | None = None):
        self._strategy_override = strategy

    # ---- public API ---------------------------------------------------------

    def act(self, state: SimulationState) -> AgentDecision:
        """Produce one decision given the current simulation state."""
        strategy = self._strategy_override or state.strategy_name
        profile = STRATEGY_PROFILES.get(strategy, STRATEGY_PROFILES["default"])

        step = state.current_step
        match_score = self._compute_match(state.candidate, state.job)
        gap_skills = self._gap_skills(state.candidate, state.job)
        gap_count = len(gap_skills)

        if step == "applied":
            return self._decide_initial(state, match_score, gap_count, gap_skills, profile)
        elif step == "screened":
            return self._decide_after_screen(state, match_score, gap_count, gap_skills, profile)
        elif step == "interview":
            return self._decide_at_interview(state, profile)
        elif step == "offer":
            return self._decide_offer(state, match_score, profile)
        elif step in ("accepted", "rejected", "end"):
            return self._terminal(state)
        else:
            return self._decide_initial(state, match_score, gap_count, gap_skills, profile)

    # ---- decision methods (one per pipeline phase) --------------------------

    def _decide_initial(
        self,
        state: SimulationState,
        match_score: float,
        gap_count: int,
        gap_skills: list[str],
        profile: dict,
    ) -> AgentDecision:
        threshold = profile["apply_threshold"]
        prep_threshold = profile["prepare_threshold"]

        if match_score >= threshold:
            return AgentDecision(
                agent_name="candidate",
                action="apply",
                params={"match_score": round(match_score, 3)},
                reasoning=(
                    f"Skill match {match_score:.0%} exceeds threshold {threshold:.0%}. "
                    f"Ready to apply."
                ),
                confidence=profile["confidence"],
                timestamp=datetime.now().isoformat(),
            )
        elif match_score >= prep_threshold:
            return AgentDecision(
                agent_name="candidate",
                action="prepare",
                params={
                    "match_score": round(match_score, 3),
                    "gap_count": gap_count,
                    "gap_skills": gap_skills[:5],
                },
                reasoning=(
                    f"Match {match_score:.0%} below apply threshold. "
                    f"Preparing — targeting {gap_count} gap skill(s): {', '.join(gap_skills[:3])}."
                ),
                confidence=round(profile["confidence"] * 0.7, 2),
                timestamp=datetime.now().isoformat(),
            )
        else:
            return AgentDecision(
                agent_name="candidate",
                action="pivot",
                params={
                    "match_score": round(match_score, 3),
                    "gap_count": gap_count,
                    "gap_skills": gap_skills[:5],
                    "suggested_focus": gap_skills[:3],
                },
                reasoning=(
                    f"Match {match_score:.0%} is critically low. "
                    f"Pivoting — suggest focusing on: {', '.join(gap_skills[:3])} "
                    f"before targeting this role."
                ),
                confidence=round(profile["confidence"] * 0.5, 2),
                timestamp=datetime.now().isoformat(),
            )

    def _decide_after_screen(
        self,
        state: SimulationState,
        match_score: float,
        gap_count: int,
        gap_skills: list[str],
        profile: dict,
    ) -> AgentDecision:
        hr_score = state.scores.get("hr_screen", 0.0)

        if hr_score >= 0.7:
            return AgentDecision(
                agent_name="candidate",
                action="prepare",
                params={"focus": "interview", "hr_score": hr_score},
                reasoning=f"Passed HR screen (score={hr_score:.2f}). Preparing for interview.",
                confidence=round(profile["confidence"] * 0.8, 2),
                timestamp=datetime.now().isoformat(),
            )
        elif gap_count > 0:
            return AgentDecision(
                agent_name="candidate",
                action="prepare",
                params={"focus": "skills", "gap_skills": gap_skills[:3]},
                reasoning=(
                    f"HR score {hr_score:.2f} is borderline. "
                    f"Strengthening skills: {', '.join(gap_skills[:3])}."
                ),
                confidence=profile["confidence"],
                timestamp=datetime.now().isoformat(),
            )
        else:
            return AgentDecision(
                agent_name="candidate",
                action="apply",
                params={"hr_score": hr_score},
                reasoning="HR screen passed, no skill gaps. Proceeding.",
                confidence=profile["confidence"],
                timestamp=datetime.now().isoformat(),
            )

    def _decide_at_interview(self, state: SimulationState, profile: dict) -> AgentDecision:
        interview_score = state.scores.get("interview", 0.5)
        return AgentDecision(
            agent_name="candidate",
            action="prepare",
            params={"focus": "negotiation", "interview_score": interview_score},
            reasoning=f"Post-interview (score={interview_score:.2f}). Preparing for offer negotiation.",
            confidence=profile["confidence"],
            timestamp=datetime.now().isoformat(),
        )

    def _decide_offer(self, state: SimulationState, match_score: float, profile: dict) -> AgentDecision:
        final_score = state.scores.get("final", match_score)
        if final_score >= 0.5:
            return AgentDecision(
                agent_name="candidate",
                action="apply",  # "apply" here means "accept" in offer context
                params={"final_score": final_score, "action": "accept"},
                reasoning=f"Offer received (score={final_score:.2f}). Accepting — meets expectations.",
                confidence=profile["confidence"],
                timestamp=datetime.now().isoformat(),
            )
        else:
            return AgentDecision(
                agent_name="candidate",
                action="pivot",
                params={"final_score": final_score, "action": "reject"},
                reasoning=f"Offer below threshold (score={final_score:.2f}). Rejecting — seeking better match.",
                confidence=round(profile["confidence"] * 0.6, 2),
                timestamp=datetime.now().isoformat(),
            )

    def _terminal(self, state: SimulationState) -> AgentDecision:
        return AgentDecision(
            agent_name="candidate",
            action="apply",
            params={"step": state.current_step},
            reasoning=f"Simulation ended at step '{state.current_step}'. No further action.",
            confidence=1.0,
            timestamp=datetime.now().isoformat(),
        )

    # ---- helpers -------------------------------------------------------------

    def _compute_match(self, candidate: StructuredResume, job: StructuredJob) -> float:
        """Skill match score: |candidate ∩ required| / |required|."""
        if not job.required_skills:
            return 1.0
        c_set = {s.lower().strip() for s in candidate.skills}
        matched = sum(1 for s in job.required_skills if s.lower().strip() in c_set)
        return matched / len(job.required_skills)

    def _gap_skills(self, candidate: StructuredResume, job: StructuredJob) -> list[str]:
        """Skills the job requires but the candidate does not have."""
        c_set = {s.lower().strip() for s in candidate.skills}
        return [s for s in job.required_skills if s.lower().strip() not in c_set]
