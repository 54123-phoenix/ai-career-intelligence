"""FinalT004Schema — unified Simulation response envelope.

Merges ProductView (renderable UI sections) + Explanation (interpretable analysis)
into a single response contract for POST /api/v1/simulation/run.

Version: 1.0.0 — backward compatible with existing SimulationRunResponse.
"""

from __future__ import annotations

from .explanation import explain
from .metrics import evaluate
from .product_view import to_product_view
from .state import SimulationResult


def build_envelope(result: SimulationResult) -> dict:
    """Merge ProductView + Explanation → FinalT004Schema.

    The returned dict is the canonical response format for simulation endpoints.
    Existing SimulationRunResponse fields (result, metrics) are preserved for
    backward compatibility.
    """
    product = to_product_view(result)
    explanation = explain(result)
    metrics = evaluate(result)

    return {
        # ── Top-level identity ──────────────────────────────────────
        "simulation_id": result.simulation_id,
        "strategy_name": result.strategy_name,
        "outcome": result.outcome,

        # ── ProductView sections (UI rendering) ─────────────────────
        "summary": product["summary"],
        "match_score": product["match_score"],
        "timeline": product["timeline"],
        "skill_gap_chart": product["skill_gap_chart"],
        "recommendation_cards": product["recommendation_cards"],

        # ── Explanation sections (interpretability) ──────────────────
        "decision_path": explanation["decision_path"],
        "hr_reasoning": explanation["hr_reasoning"],
        "candidate_actions": explanation["candidate_actions"],
        "failure_points": explanation["failure_points"],
        "confidence_score": explanation["confidence_score"],

        # ── Backward-compatible raw data ────────────────────────────
        "result": result.model_dump(mode="json"),
        "metrics": metrics,
    }
