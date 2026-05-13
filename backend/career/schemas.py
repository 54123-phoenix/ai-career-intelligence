"""Career schemas — Pydantic models for Career Memory & Evolution Engine (T007).

Covers: CareerEvent, CareerTimeline, BottleneckAnalysis, CareerStrategy,
StrategySimulation, CareerVisualization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# ── Career Event ─────────────────────────────────────────────────────────

class CareerEvent(BaseModel):
    """Standardized career event — output of parser_agent."""

    event_id: str = Field(
        default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}"
    )
    user_id: str = Field(description="Owning user")
    event_type: Literal[
        "job_view", "application_sent", "phone_screen", "interview",
        "technical_test", "offer_received", "offer_accepted", "offer_declined",
        "rejection", "skill_acquired", "promotion", "job_change",
        "resume_updated", "networking_event", "course_completed",
    ] = Field(description="Type of career event")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Job-related fields
    job_id: str | None = None
    job_title: str | None = None
    company: str | None = None
    location: str | None = None
    salary_range: tuple[int, int] | None = None
    # Skill fields
    skills_involved: list[str] = Field(default_factory=list)
    skills_acquired: list[str] = Field(default_factory=list)
    # Outcome
    outcome: Literal["success", "failure", "pending", "neutral"] = "pending"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    # Narrative
    notes: str = Field(default="", description="Free-text context")
    source: str = Field(default="manual", description="manual | system | import")


# ── Skill Trajectory ─────────────────────────────────────────────────────

class SkillSnapshot(BaseModel):
    """Skill state at a point in time."""

    date: str = Field(description="ISO date")
    skills: dict[str, float] = Field(
        default_factory=dict, description="skill_name → proficiency [0,1]"
    )
    new_skills: list[str] = Field(default_factory=list)


# ── Career Timeline ──────────────────────────────────────────────────────

class CareerTimeline(BaseModel):
    """Full career history for one user — output of retrieval_agent."""

    user_id: str = Field(description="User identifier")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Recent events (last 10)
    recent_events: list[CareerEvent] = Field(default_factory=list)
    # Skill trajectory over time
    skill_trajectory: list[SkillSnapshot] = Field(default_factory=list)
    # Interview outcomes
    interview_successes: list[CareerEvent] = Field(default_factory=list)
    interview_failures: list[CareerEvent] = Field(default_factory=list)
    # Behavioral distribution
    application_distribution: dict[str, int] = Field(
        default_factory=dict, description="category → count"
    )
    total_events: int = Field(default=0)
    active_days: int = Field(default=0)
    average_events_per_week: float = Field(default=0.0)


# ── Bottleneck Analysis ──────────────────────────────────────────────────

class BottleneckAnalysis(BaseModel):
    """Career pattern analysis — output of reviewer_agent."""

    user_id: str = Field(description="User identifier")
    analysis_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Primary bottleneck
    dominant_bottleneck: str = Field(
        description="Main failure reason. Examples: skill_gap, interview_skill, "
        "compensation_mismatch, location_mismatch, experience_deficit, "
        "application_volume_low, resume_quality, market_timing, networking_gap"
    )
    bottleneck_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # Secondary issues
    secondary_bottlenecks: list[str] = Field(
        default_factory=list,
        description="Contributing factors (max 3)"
    )
    # Trend
    trend: Literal["improving", "stable", "declining"] = "stable"
    trend_detail: str = Field(default="", description="Evidence for trend assessment")
    # Systemic
    systemic_issue: bool = Field(default=False)
    systemic_reason: str = Field(default="", description="Why this is or isn't systemic")
    # Quantified metrics
    application_to_interview_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    interview_to_offer_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_gap_areas: list[str] = Field(default_factory=list)
    recommended_focus: list[str] = Field(
        default_factory=list, description="Areas needing immediate attention (max 3)"
    )


# ── Career Strategy ──────────────────────────────────────────────────────

class ActionItem(BaseModel):
    """A single executable action in the career plan."""

    day: int = Field(ge=1, le=14, description="Day number in the plan")
    action: str = Field(description="Concrete action description")
    category: Literal["skill", "application", "networking", "interview_prep", "research"] = "skill"
    expected_outcome: str = Field(default="")
    hours_estimate: float = Field(default=1.0, ge=0.5, le=8.0)


class CareerStrategy(BaseModel):
    """Career development strategy — output of architect_agent."""

    user_id: str
    strategy_id: str = Field(
        default_factory=lambda: f"strat-{uuid.uuid4().hex[:8]}"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Core focus
    focus_skill: str = Field(description="Primary skill to break through bottleneck")
    focus_reason: str = Field(default="", description="Why this skill")
    # 7-14 day action plan (max 5 items)
    action_plan: list[ActionItem] = Field(
        default_factory=list, description="Up to 5 concrete actions"
    )
    # Risk analysis
    risk_if_no_adjustment: str = Field(
        default="", description="What happens if current path continues unchanged"
    )
    risk_severity: Literal["low", "medium", "high", "critical"] = "medium"
    # Success expectation
    success_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_timeline_weeks: int = Field(default=4, ge=1, le=52)
    # Context
    based_on_bottleneck: str = Field(default="")
    based_on_trend: str = Field(default="")


# ── Strategy Simulation ──────────────────────────────────────────────────

class StrategySimulation(BaseModel):
    """Simulation outcome for a career strategy — output of simulation_agent."""

    simulation_id: str = Field(
        default_factory=lambda: f"sim-{uuid.uuid4().hex[:8]}"
    )
    strategy_id: str = Field(description="Strategy being simulated")
    # Core output
    success_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    main_failure_risk: str = Field(
        default="", description="Most likely reason for strategy failure"
    )
    expected_outcome: str = Field(
        default="", description="Most likely result if strategy is followed"
    )
    # Adjustment
    adjustment_needed: bool = Field(default=False)
    adjustment_suggestion: str = Field(default="", description="Concrete fix if needed")
    # Confidence
    simulation_confidence: float = Field(default=0.0, ge=0.0, le=1.0,
        description="How confident the simulation is in its prediction")


# ── Career Visualization ─────────────────────────────────────────────────

class CareerVisualization(BaseModel):
    """Structured data for frontend rendering — output of frontend_agent."""

    user_id: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # 1. Timeline
    career_timeline: CareerTimeline | None = None
    # 2. Skill graph data
    skill_graph: dict = Field(
        default_factory=dict,
        description="{dates: [...], skills: {skill_name: [values...]}}"
    )
    # 3. Bottleneck summary
    bottleneck_summary: BottleneckAnalysis | None = None
    # 4. Current strategy
    current_strategy: CareerStrategy | None = None
    # 5. Simulation result
    simulation_result: StrategySimulation | None = None
    # Meta
    data_sources: list[str] = Field(default_factory=list)
    last_updated: str | None = None
