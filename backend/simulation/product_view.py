"""ProductView transformer — SimulationResult → UI-ready JSON.

Pure data mapping. No inference logic. Every output field is directly renderable.
"""

from __future__ import annotations

from .metrics import evaluate
from .state import SimulationResult


def to_product_view(result: SimulationResult) -> dict:
    """Transform a SimulationResult into a render-ready ProductView dict.

    Returns a dict matching the TypeScript ProductView interface
    defined in frontend/types/simulation.ts.
    """
    state = result.final_state
    metrics = evaluate(result)
    candidate = state.candidate
    job = state.job

    return {
        "simulation_id": result.simulation_id,
        "strategy_name": result.strategy_name,
        "outcome": result.outcome,

        "summary": _build_summary(result, metrics, candidate, job),
        "match_score": _build_match_score(state, metrics),
        "timeline": _build_timeline(result),
        "skill_gap_chart": _build_skill_gap(state),
        "recommendation_cards": _build_cards(result, state, metrics),
    }


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_summary(result, metrics, candidate, job) -> dict:
    outcome = result.outcome
    if outcome == "accepted":
        headline = f"Offer accepted after {result.final_state.step_count} steps"
        badge = "success"
    elif outcome == "timeout":
        headline = "Simulation timed out — consider a different strategy"
        badge = "warning"
    else:
        headline = f"Rejected at '{result.final_state.current_step}' stage"
        badge = "failure"

    return {
        "headline": headline,
        "candidate_name": candidate.name,
        "job_title": job.title,
        "company": job.company,
        "badge": badge,
        "stats": {
            "success_probability": round(result.success_probability, 3),
            "time_to_offer_steps": result.time_to_offer,
            "total_reward": metrics["total_reward"],
        },
    }


def _build_match_score(state, metrics) -> dict:
    overall = min(round(metrics["skill_gap_score"] * 100), 100)
    hr_score = state.scores.get("hr_screen")
    iv_score = state.scores.get("interview")

    if overall >= 70:
        color, label = "green", "Strong"
    elif overall >= 40:
        color, label = "yellow", "Moderate"
    else:
        color, label = "red", "Weak"

    return {
        "overall": overall,
        "breakdown": {
            "skill_match": round(metrics["skill_gap_score"] * 100),
            "experience_fit": round((hr_score or 0) * 100),
            "keyword_overlap": round((iv_score or metrics["skill_gap_score"]) * 100),
        },
        "gauge": {
            "value": overall,
            "color": color,
            "label": label,
        },
    }


def _build_timeline(result) -> dict:
    state = result.final_state
    path = result.path_history
    events = []
    for i, d in enumerate(state.decisions):
        actor = _map_actor(d.agent_name)
        phase = path[i].current_step if i < len(path) else state.current_step

        score = None
        if d.agent_name == "hr" and "score" in d.params:
            score = d.params["score"]

        events.append({
            "step": i,
            "phase": phase,
            "actor": actor,
            "action_label": _action_label(d.action, d.params),
            "reasoning": d.reasoning,
            "score": score,
            "confidence": d.confidence,
            "timestamp": d.timestamp,
        })

    return {
        "events": events,
        "total_steps": state.step_count,
    }


def _build_skill_gap(state) -> dict:
    candidate_skills = {s.lower().strip() for s in state.candidate.skills}
    required = state.job.required_skills
    optional = state.job.optional_skills

    matched = []
    missing = []

    for s in required:
        entry = {"name": s, "value": 100, "category": "required"}
        if s.lower().strip() in candidate_skills:
            matched.append(entry)
        else:
            missing.append(entry)

    for s in optional:
        entry = {"name": s, "value": 60, "category": "optional"}
        if s.lower().strip() in candidate_skills:
            matched.append(entry)
        else:
            missing.append({**entry, "value": 40})

    match_ratio = len(matched) / max(len(matched) + len(missing), 1)

    return {
        "matched": matched,
        "missing": missing,
        "title": f"Skill Match: {round(match_ratio * 100)}%",
        "match_ratio": round(match_ratio, 3),
    }


def _build_cards(result, state, metrics) -> list[dict]:
    cards = []
    outcome = result.outcome
    strategy = result.strategy_name
    gap_skills = _collect_gap_skills(state)

    # Primary action card
    if outcome == "rejected" and gap_skills:
        cards.append({
            "priority": 1,
            "type": "action",
            "title": "Upskill Recommended",
            "description": f"Close skill gaps to improve match: {', '.join(gap_skills[:3])}.",
            "action_label": f"Learn {gap_skills[0]}",
        })
    elif outcome == "accepted":
        cards.append({
            "priority": 1,
            "type": "success",
            "title": "Proceed with Application",
            "description": f"The '{strategy}' strategy led to an offer. Confidence is high.",
            "action_label": "Apply now",
        })
    else:
        cards.append({
            "priority": 1,
            "type": "warning",
            "title": "Strategy Inconclusive",
            "description": "Simulation timed out. Try a different strategy or check market conditions.",
            "action_label": "Try aggressive",
        })

    # Strategy comparison hint
    alternatives = [s for s in ("aggressive", "balanced", "conservative") if s != strategy]
    cards.append({
        "priority": 2,
        "type": "info",
        "title": "Compare Strategies",
        "description": f"Run multi-path comparison with {alternatives[0]} and {alternatives[1]} strategies.",
        "action_label": "Run comparison",
    })

    # Skill gap detail
    if gap_skills:
        cards.append({
            "priority": 3,
            "type": "info",
            "title": f"Skill Gaps ({len(gap_skills)})",
            "description": f"Missing skills: {', '.join(gap_skills)}. Consider a learning roadmap.",
            "action_label": "View roadmap",
        })

    # Reward context
    reward = metrics["total_reward"]
    if reward < 0.4:
        cards.append({
            "priority": 4,
            "type": "warning",
            "title": "Low Reward Signal",
            "description": f"Reward={reward:.2f}. This strategy-path combination is unlikely to succeed.",
        })

    return cards[:5]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _map_actor(agent_name: str) -> str:
    return {
        "candidate": "candidate",
        "hr": "hr",
        "market": "system",
        "interview": "interview",
    }.get(agent_name, "system")


def _action_label(action: str, params: dict) -> str:
    labels = {
        "apply": "Applied to position",
        "prepare": f"Prepared — focus: {params.get('focus', 'skills')}",
        "pivot": "Pivoted strategy",
        "screen": f"HR screened (score: {params.get('score', 'N/A')})",
        "assess": "Interview assessed",
        "accept": "Accepted offer",
        "reject": "Rejected",
    }
    return labels.get(action, action)


def _collect_gap_skills(state) -> list[str]:
    """Collect gap skills from candidate decisions in the state."""
    for d in state.decisions:
        if "gap_skills" in d.params and d.params["gap_skills"]:
            return d.params["gap_skills"]
    return []
