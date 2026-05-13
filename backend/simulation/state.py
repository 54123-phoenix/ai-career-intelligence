"""Simulation Layer — Pydantic schema definitions ONLY.

No implementation. No agent logic. No engine code.
Defined here, re-exported by backend.shared.types for cross-module consumption.

Version: 2.0.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.shared.types import StructuredJob, StructuredResume


# ---------------------------------------------------------------------------
# Agent Decision
# ---------------------------------------------------------------------------


class AgentDecision(BaseModel):
    """Single action taken by one agent at one simulation step.

    Every decision is traceable: who did what, why, with what confidence.
    """

    agent_name: str = Field(description="candidate | hr | market | interview")
    action: str = Field(description="Action verb: apply | screen | adjust | assess | accept | reject")
    params: dict = Field(default_factory=dict, description="Action-specific parameters")
    reasoning: str = Field(default="", description="Explainable rationale — required for audit")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Agent's own confidence in this decision")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO-8601 timestamp",
    )


# ---------------------------------------------------------------------------
# Simulation State
# ---------------------------------------------------------------------------


class SimulationState(BaseModel):
    """Global simulation state — the single source of truth at each step.

    This is the LangGraph StateGraph schema. Every agent reads from / writes to
    this state. No agent may hold private state outside of this object.
    """

    simulation_id: str
    strategy_name: str = Field(default="default", description="A | B | C strategy label")

    # Immutable entities (set at sim start, never mutated)
    candidate: StructuredResume
    job: StructuredJob

    # Position in the hiring pipeline
    current_step: Literal[
        "applied", "screened", "interview", "offer", "accepted", "rejected", "end"
    ] = Field(default="applied")
    step_count: int = Field(default=0, ge=0, description="How many agent actions have occurred")
    max_steps: int = Field(default=20, ge=1, le=100, description="Safety ceiling — timeout → rejected")

    # Decision history — append-only audit trail
    decisions: list[AgentDecision] = Field(default_factory=list)

    # Gate scores — populated by agents at each phase
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="e.g. {'hr_screen': 0.8, 'interview': 0.65, 'final': 0.72}",
    )

    # Market context — updated by MarketAgent
    market_adjustment: float = Field(
        default=1.0, ge=0.5, le=1.5,
        description="Supply/demand modifier: <1 = more competition, >1 = less",
    )
    competition_intensity: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="0 = no competition, 1 = maximum competition",
    )

    # Metadata
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Last-updated ISO-8601 timestamp",
    )


# ---------------------------------------------------------------------------
# Simulation Result
# ---------------------------------------------------------------------------


class SimulationResult(BaseModel):
    """Final output of one simulation path — consumed by Frontend and L3 Evolution."""

    simulation_id: str
    strategy_name: str = Field(default="default")
    outcome: Literal["accepted", "rejected", "timeout"] = Field(default="timeout")

    # Final snapshot
    final_state: SimulationState

    # Probability analysis
    success_probability: float = Field(ge=0.0, le=1.0, description="Estimated P(offer)")
    confidence_interval: tuple[float, float] = Field(
        default=(0.0, 0.0),
        description="(lower_bound, upper_bound)",
    )

    # Key moments
    key_decisions: list[AgentDecision] = Field(
        default_factory=list,
        description="Pivotal decisions that changed the outcome",
    )
    time_to_offer: int = Field(ge=0, description="Steps from applied → offer (0 if never offered)")

    # Full trace
    path_history: list[SimulationState] = Field(
        default_factory=list,
        description="State snapshot at every step — for Frontend timeline rendering",
    )

    # Human-readable recommendation
    recommendation: str = Field(default="", description="Generated strategy advice")
