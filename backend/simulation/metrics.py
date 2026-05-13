"""Simulation metrics — decompose a simulation path into quantifiable scores.

Three indicators feed into the final reward:
  offer_probability    — P(offer) estimate from gate scores + outcome
  skill_gap_score      — inverse of skill gap (1.0 = no gaps)
  trajectory_efficiency — path directness (fewer steps, fewer pivots = higher)

Output:
  calculate_reward(state) → float          # weighted sum [0, 1]
  evaluate(result)        → dict[str, float] # full breakdown
"""

from __future__ import annotations

from .state import SimulationResult, SimulationState

# Weights for aggregating into a single reward (sums to 1.0)
W_OFFER = 0.50   # did we get an offer?
W_SKILL = 0.30   # how well do skills match?
W_EFFICIENCY = 0.20  # how direct was the path?


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_reward(state: SimulationState) -> float:
    """Aggregate reward signal from a simulation final state.

    reward = 0.50 × offer_probability
           + 0.30 × skill_gap_score
           + 0.20 × trajectory_efficiency
    """
    return round(
        W_OFFER * offer_probability(state)
        + W_SKILL * skill_gap_score(state)
        + W_EFFICIENCY * trajectory_efficiency(state),
        4,
    )


def evaluate(result: SimulationResult) -> dict[str, float]:
    """Full metric breakdown for a completed simulation."""
    state = result.final_state
    return {
        "offer_probability": round(offer_probability(state), 4),
        "skill_gap_score": round(skill_gap_score(state), 4),
        "trajectory_efficiency": round(trajectory_efficiency(state), 4),
        "total_reward": calculate_reward(state),
        "outcome": 1.0 if result.outcome == "accepted" else 0.0,
        "steps": result.final_state.step_count,
    }


# ---------------------------------------------------------------------------
# Individual metrics
# ---------------------------------------------------------------------------


def offer_probability(state: SimulationState) -> float:
    """Estimate P(offer) from gate scores and final state.

    - accepted           → 1.0
    - rejected/timeout   → computed from hr_screen + interview scores
    - in progress        → projected from current scores
    """
    if state.current_step == "accepted":
        return 1.0

    hr = state.scores.get("hr_screen")
    iv = state.scores.get("interview")

    if hr is not None and iv is not None:
        # Both gates passed → weighted combination
        return round(hr * 0.4 + iv * 0.6, 4)

    if hr is not None:
        # Only HR screen available
        if state.current_step == "rejected" and hr < 0.35:
            return round(hr * 0.3, 4)  # hard fail → very low
        return round(hr * 0.5, 4)

    # Before any gate
    return 0.3


def skill_gap_score(state: SimulationState) -> float:
    """Inverse skill gap: 1.0 = all required skills present, 0.0 = none.

    Uses candidate.skills ∩ job.required_skills from the state snapshots.
    """
    candidate_skills = {s.lower().strip() for s in state.candidate.skills}
    required = state.job.required_skills

    if not required:
        return 1.0

    matched = sum(1 for s in required if s.lower().strip() in candidate_skills)

    # Optional skills add a small bonus
    optional_bonus = 0.0
    if state.job.optional_skills:
        opt_matched = sum(1 for s in state.job.optional_skills if s.lower().strip() in candidate_skills)
        optional_bonus = min(opt_matched * 0.05, 0.1)

    return round(matched / len(required) + optional_bonus, 4)


def trajectory_efficiency(state: SimulationState) -> float:
    """Measure path directness.

    Factors:
      - Direct path (applied→screened→interview→offer→accepted): 1.0
      - Each extra step: -0.1
      - Each pivot action: -0.2
      - Each prepare loop: -0.05
      - Minimum floor: 0.1
    """
    optimal_steps = 4  # applied → screened → interview → offer → accepted
    actual_steps = state.step_count

    # Count actions
    pivot_count = sum(1 for d in state.decisions if d.action == "pivot")
    prepare_count = sum(1 for d in state.decisions if d.action == "prepare")

    base = 1.0
    base -= max(0, actual_steps - optimal_steps) * 0.1
    base -= pivot_count * 0.2
    base -= prepare_count * 0.05

    return round(max(base, 0.1), 4)
