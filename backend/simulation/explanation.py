"""Explanation layer — post-hoc analysis of a SimulationResult.

Reads the simulation audit trail and produces human-readable explanations
of what happened, why, and where things went wrong.

Rules:
  - Read-only: consumes SimulationResult, never mutates state
  - No new simulation steps
  - Explains T-003 agents (CandidateAgent + HRAgent) behavior only
"""

from __future__ import annotations

from .metrics import evaluate
from .state import AgentDecision, SimulationResult, SimulationState


def explain(result: SimulationResult) -> dict:
    """Produce a full explanation layer from a completed simulation.

    Returns a dict with 5 sections:
      decision_path      — step-by-step narrative
      hr_reasoning       — why HR passed or rejected
      candidate_actions  — candidate's strategic choices
      failure_points     — breakdown points (empty if accepted)
      confidence_score   — overall explanation confidence
    """
    state = result.final_state
    metrics = evaluate(result)

    return {
        "decision_path": _build_decision_path(result),
        "hr_reasoning": _build_hr_reasoning(state),
        "candidate_actions": _build_candidate_actions(state),
        "failure_points": _build_failure_points(result),
        "confidence_score": _confidence(result, metrics),
    }


# ---------------------------------------------------------------------------
# Section 1: Decision Path — step-by-step narrative
# ---------------------------------------------------------------------------


def _build_decision_path(result: SimulationResult) -> dict:
    steps = []
    for i, d in enumerate(result.final_state.decisions):
        steps.append({
            "order": i + 1,
            "agent": d.agent_name,
            "action": d.action,
            "summary": _narrate(d),
            "reasoning": d.reasoning,
            "confidence": d.confidence,
            "params": _public_params(d),
        })

    return {
        "title": _path_title(result),
        "total_actions": len(steps),
        "steps": steps,
    }


def _narrate(d: AgentDecision) -> str:
    """One-sentence narration of a decision."""
    agent = d.agent_name.capitalize()
    if d.action == "apply":
        return f"{agent} decided to apply for the position."
    if d.action == "prepare":
        focus = d.params.get("focus", "skills")
        return f"{agent} chose to prepare — focusing on {focus}."
    if d.action == "pivot":
        return f"{agent} pivoted strategy — seeking alternative approach."
    if d.action == "screen":
        passed = d.params.get("passed", False)
        score = d.params.get("score", 0)
        if d.params.get("hard_pass"):
            return f"HR performed hard-pass rejection (score: {score:.2f})."
        if passed:
            return f"HR screened and passed the candidate (score: {score:.2f})."
        return f"HR screened and rejected (score: {score:.2f})."
    return f"{agent} performed action '{d.action}'."


def _public_params(d: AgentDecision) -> dict:
    """Filter params to safe-for-explanation keys only."""
    safe_keys = {"score", "passed", "hard_pass", "gap_count", "focus", "match_score"}
    return {k: v for k, v in d.params.items() if k in safe_keys}


def _path_title(result: SimulationResult) -> str:
    outcome = result.outcome
    strategy = result.strategy_name
    if outcome == "accepted":
        return f"Successful '{strategy}' strategy — offer accepted"
    if outcome == "rejected":
        return f"Failed '{strategy}' strategy — rejected at '{result.final_state.current_step}'"
    return f"Inconclusive '{strategy}' strategy — timed out"


# ---------------------------------------------------------------------------
# Section 2: HR Reasoning
# ---------------------------------------------------------------------------


def _build_hr_reasoning(state: SimulationState) -> dict:
    hr_decisions = [d for d in state.decisions if d.agent_name == "hr"]

    if not hr_decisions:
        return {
            "evaluation": "No HR screening occurred — candidate did not reach screening gate.",
            "score": None,
            "verdict": "not_screened",
            "details": [],
        }

    hr = hr_decisions[0]
    score = hr.params.get("score", 0)
    passed = hr.params.get("passed", False)
    hard_pass = hr.params.get("hard_pass", False)
    sub = hr.params.get("sub_scores", {})
    reasons = hr.params.get("rejection_reasons", [])

    details = []
    if sub:
        details.append(f"Skill match: {sub.get('skill', 0):.0%}")
        details.append(f"Experience fit: {sub.get('experience', 0):.0%}")
        details.append(f"Keyword overlap: {sub.get('keyword', 0):.0%}")

    verdict = "passed" if passed else ("hard_pass" if hard_pass else "failed")

    return {
        "evaluation": hr.reasoning,
        "score": round(score, 3),
        "verdict": verdict,
        "details": details,
        "rejection_reasons": reasons,
    }


# ---------------------------------------------------------------------------
# Section 3: Candidate Actions
# ---------------------------------------------------------------------------


def _build_candidate_actions(state: SimulationState) -> dict:
    c_decisions = [d for d in state.decisions if d.agent_name == "candidate"]

    actions = []
    for d in c_decisions:
        actions.append({
            "action": d.action,
            "confidence": d.confidence,
            "reasoning": d.reasoning,
            "gap_skills": d.params.get("gap_skills", [])[:5],
            "match_score": d.params.get("match_score"),
        })

    strategy = state.strategy_name
    strategy_explanation = {
        "aggressive": "Candidate applied aggressively — prioritizing speed over preparation.",
        "conservative": "Candidate took a conservative approach — preparing thoroughly before applying.",
        "balanced": "Candidate balanced preparation with timely applications.",
    }.get(strategy, f"Unknown strategy: {strategy}")

    return {
        "strategy": strategy,
        "strategy_explanation": strategy_explanation,
        "total_actions": len(actions),
        "actions": actions,
    }


# ---------------------------------------------------------------------------
# Section 4: Failure Points — where things went wrong
# ---------------------------------------------------------------------------


def _build_failure_points(result: SimulationResult) -> list[dict]:
    if result.outcome == "accepted":
        return []

    state = result.final_state
    points = []

    # Check HR gate
    hr_decisions = [d for d in state.decisions if d.agent_name == "hr"]
    for hr in hr_decisions:
        if hr.params.get("hard_pass"):
            points.append({
                "stage": "hr_screen",
                "severity": "critical",
                "cause": "Hard pass — fundamental skill or experience gap.",
                "detail": hr.reasoning,
                "remediation": (
                    "Acquire missing required skills and gain relevant experience "
                    "before reapplying to similar roles."
                ),
            })
        elif not hr.params.get("passed"):
            points.append({
                "stage": "hr_screen",
                "severity": "high",
                "cause": f"HR score ({hr.params.get('score', 0):.2f}) below pass threshold.",
                "detail": hr.reasoning,
                "remediation": "Improve skill match ratio and experience relevance.",
            })

    # Check interview gate
    iv_score = state.scores.get("interview")
    if iv_score is not None and iv_score < 0.45:
        points.append({
            "stage": "interview",
            "severity": "medium",
            "cause": f"Interview score ({iv_score:.2f}) below threshold.",
            "detail": "Candidate did not meet the interview bar.",
            "remediation": "Strengthen interview preparation and domain knowledge.",
        })

    # Check for pivot actions (strategy failures)
    pivots = [d for d in state.decisions if d.action == "pivot"]
    for p in pivots:
        points.append({
            "stage": p.params.get("step", "unknown"),
            "severity": "medium",
            "cause": "Candidate pivoted away from the target role.",
            "detail": p.reasoning,
            "remediation": "Reassess target role alignment with current skill set.",
        })

    # Timeout
    if result.outcome == "timeout":
        points.append({
            "stage": "simulation",
            "severity": "high",
            "cause": f"Simulation exceeded max steps ({state.max_steps}).",
            "detail": "Strategy did not converge to a terminal outcome.",
            "remediation": "Switch to a more decisive strategy (e.g., aggressive).",
        })

    return points


# ---------------------------------------------------------------------------
# Section 5: Confidence Score
# ---------------------------------------------------------------------------


def _confidence(result: SimulationResult, metrics: dict) -> dict:
    """Overall confidence in the explanation quality.

    Based on:
      - Decision count (more decisions = richer explanation)
      - Gate score availability
      - Outcome clarity
    """
    state = result.final_state
    n_decisions = len(state.decisions)

    # More data points → higher confidence
    data_factor = min(n_decisions / 4, 1.0)

    # Gate scores → higher confidence
    gate_factor = 0.0
    if state.scores.get("hr_screen") is not None:
        gate_factor += 0.4
    if state.scores.get("interview") is not None:
        gate_factor += 0.3
    if state.scores.get("final") is not None:
        gate_factor += 0.3

    # Outcome clarity
    outcome_factor = 1.0 if result.outcome != "timeout" else 0.5

    overall = round((data_factor * 0.3 + gate_factor * 0.4 + outcome_factor * 0.3), 3)

    return {
        "overall": overall,
        "factors": {
            "data_richness": round(data_factor, 2),
            "gate_coverage": round(gate_factor, 2),
            "outcome_clarity": round(outcome_factor, 2),
        },
        "interpretation": _confidence_label(overall),
    }


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return "High — explanation is well-supported by simulation data."
    if score >= 0.5:
        return "Moderate — explanation covers key events but may miss nuance."
    return "Low — limited data; explanation should be treated as indicative."
