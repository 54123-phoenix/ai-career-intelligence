"""T008 schemas — Career Growth System Convergence & Strategy Optimization.

Extends T007 Career schemas with T008-specific data models:
  - UserProfile: parsed user career goals, skills, experience
  - CareerDataset: parsed recruitment/career path datasets
  - JobRecommendation: job matched to user profile
  - StrategyCandidate: strategy with match score from retrieval
  - ScoredStrategy: strategy scored across 4 dimensions by reviewer
  - CareerPlan: architect output with timeline, skill nodes, steps
  - VisualizationGraph: frontend-renderable career path graph
  - SimulationRound: single round simulation result
  - SimulationFeedback: multi-round simulation output for reviewer re-rank
  - T008PipelineOutput: unified pipeline output envelope
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from backend.career.schemas import (
    ActionItem,
    BottleneckAnalysis,
    CareerStrategy,
    CareerTimeline,
    CareerVisualization,
    StrategySimulation,
)


# ── Parser Agent Output ────────────────────────────────────────────────────

class UserProfile(BaseModel):
    """Standardized user career profile — parser_agent output."""

    user_id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    career_goals: list[str] = Field(
        default_factory=list, description="Target roles, industries, or career objectives"
    )
    skills: list[str] = Field(
        default_factory=list, description="Current skill inventory, normalized"
    )
    experience_years: float = Field(default=0.0, ge=0.0, description="Total years of experience")
    education_level: str = Field(default="", description="Highest education level")
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    salary_expectation: tuple[int, int] | None = None  # (min, max) K/年
    raw_text: str = Field(default="", description="Original user input text")


class CareerDataEntry(BaseModel):
    """Single entry in a career dataset — parsed from recruitment/path data."""

    job_title: str
    required_skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)
    growth_path: list[str] = Field(
        default_factory=list, description="Typical career progression titles"
    )
    level: str = ""  # 初级/中级/高级/专家
    salary_range: tuple[int, int] | None = None
    location: str = ""
    industry: str = ""
    source: str = Field(default="", description="Dataset origin identifier")


class CareerData(BaseModel):
    """Parsed career dataset — parser_agent output."""

    dataset_id: str = Field(default_factory=lambda: f"ds-{uuid.uuid4().hex[:8]}")
    entries: list[CareerDataEntry] = Field(default_factory=list)
    total_entries: int = Field(default=0)
    processed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ParserOutput(BaseModel):
    """Complete parser_agent output for T008."""

    user_profile: UserProfile
    career_data: CareerData | None = None
    warnings: list[str] = Field(default_factory=list)


# ── Retrieval Agent Output ─────────────────────────────────────────────────

class JobRecommendation(BaseModel):
    """A job matched to the user profile."""

    job_id: str
    title: str
    company: str = ""
    location: str = ""
    level: str = ""
    required_skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)
    salary_range: tuple[int, int] | None = None
    match_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Semantic match score")
    match_details: dict = Field(
        default_factory=dict,
        description="Skill overlap, level match, location match breakdown",
    )


class StrategyCandidate(BaseModel):
    """A strategy matched to the user from historical data."""

    strategy_id: str
    strategy_name: str = ""
    description: str = ""
    match_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Match to user profile")
    historical_success_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Success rate in T007 simulations"
    )
    source: str = Field(default="history", description="Where strategy was retrieved from")


class RetrievalOutput(BaseModel):
    """Complete retrieval_agent output for T008."""

    job_recommendations: list[JobRecommendation] = Field(default_factory=list)
    strategy_candidates: list[StrategyCandidate] = Field(default_factory=list)
    total_matches: int = Field(default=0)


# ── Reviewer Agent Output ──────────────────────────────────────────────────

class ScoredStrategy(BaseModel):
    """A strategy scored across 4 dimensions by the reviewer."""

    strategy: StrategyCandidate
    scores: dict[str, float] = Field(
        default_factory=lambda: {
            "success_rate": 0.0,
            "match_degree": 0.0,
            "growth_cycle": 0.0,
            "skill_adaptability": 0.0,
        },
        description="4-dimension scores: success_rate, match_degree, growth_cycle, skill_adaptability",
    )
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = Field(default="", description="Why this strategy was scored this way")
    rank: int = Field(default=0, ge=0)


class ReviewerOutput(BaseModel):
    """Complete reviewer_agent output for T008."""

    strategy_list: list[ScoredStrategy] = Field(
        default_factory=list, description="Ranked strategies (TOP N)"
    )
    top_n: int = Field(default=3)
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "success_rate": 0.35,
            "match_degree": 0.30,
            "growth_cycle": 0.20,
            "skill_adaptability": 0.15,
        }
    )


# ── Architect Agent Output ─────────────────────────────────────────────────

class PlanStep(BaseModel):
    """A single step in the career growth plan."""

    step_number: int = Field(ge=1)
    phase: Literal["preparation", "application", "interview", "negotiation", "onboarding"] = "preparation"
    title: str = ""
    description: str = ""
    duration_days: int = Field(default=7, ge=1, le=90)
    skills_required: list[str] = Field(default_factory=list)
    skills_acquired: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)


class SkillNode(BaseModel):
    """A skill node in the career path graph."""

    skill_name: str
    level: Literal["beginner", "intermediate", "advanced", "expert"] = "intermediate"
    dependencies: list[str] = Field(
        default_factory=list, description="Skills that must be acquired first"
    )
    estimated_hours: float = Field(default=40.0, ge=1.0)


class TimelineNode(BaseModel):
    """A time node on the career path."""

    week: int = Field(ge=0)
    label: str = ""
    event_type: Literal["skill_acquisition", "application", "interview", "offer", "milestone"] = "milestone"
    details: str = ""


class CareerPlan(BaseModel):
    """Complete career growth plan — architect_agent output."""

    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    user_id: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Strategy selection
    selected_strategy: ScoredStrategy | None = None
    alternative_strategies: list[ScoredStrategy] = Field(default_factory=list)

    # Execution plan
    steps: list[PlanStep] = Field(default_factory=list)
    total_duration_days: int = Field(default=0)
    estimated_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Risk assessment
    risk_points: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)

    # Recommendation
    recommendation: str = ""


class VisualizationGraph(BaseModel):
    """Frontend-renderable career path graph data."""

    # Skill tree
    skill_nodes: list[SkillNode] = Field(default_factory=list)
    skill_edges: list[tuple[str, str]] = Field(
        default_factory=list, description="(from_skill, to_skill) dependency edges"
    )

    # Timeline
    timeline_nodes: list[TimelineNode] = Field(default_factory=list)

    # Path options
    primary_path: list[str] = Field(
        default_factory=list, description="Ordered list of skill nodes for primary path"
    )
    alternative_paths: list[list[str]] = Field(
        default_factory=list, description="Alternative skill paths"
    )

    # Strategy comparison data
    strategy_comparison: dict = Field(
        default_factory=dict,
        description="{strategy_name: {success_rate, growth_cycle, skill_match}}",
    )

    # Metadata
    render_hints: dict = Field(
        default_factory=dict,
        description="Frontend rendering hints: colors, layout, zoom level",
    )


class ArchitectOutput(BaseModel):
    """Complete architect_agent output for T008."""

    career_plan: CareerPlan
    visualization_data: VisualizationGraph


# ── Simulation Agent Output ────────────────────────────────────────────────

class SimulationRound(BaseModel):
    """Result of a single simulation round."""

    round_id: int = Field(ge=1)
    success: bool = False
    success_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_triggered: list[str] = Field(default_factory=list)
    skill_gaps_exposed: list[str] = Field(default_factory=list)
    steps_to_outcome: int = Field(default=0, ge=0)
    notes: str = ""


class SimulationFeedback(BaseModel):
    """Multi-round simulation feedback for reviewer re-ranking."""

    simulation_id: str = Field(default_factory=lambda: f"sim-{uuid.uuid4().hex[:8]}")
    career_plan_id: str
    total_rounds: int = Field(default=0, ge=0)
    successful_rounds: int = Field(default=0, ge=0)
    average_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    rounds: list[SimulationRound] = Field(default_factory=list)
    aggregated_risks: dict[str, int] = Field(
        default_factory=dict, description="Risk → occurrence count"
    )
    aggregated_skill_gaps: dict[str, int] = Field(
        default_factory=dict, description="Skill gap → occurrence count"
    )
    recommendation: str = Field(
        default="", description="Feedback for reviewer to re-rank strategies"
    )


# ── T008 Pipeline Output ───────────────────────────────────────────────────

class T008PipelineOutput(BaseModel):
    """Unified T008 pipeline output — consumed by frontend."""

    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    status: Literal["success", "partial", "failed"] = "success"
    errors: list[str] = Field(default_factory=list)

    # Stage 1: Parser
    user_profile: UserProfile | None = None
    career_data: CareerData | None = None

    # Stage 2: Retrieval
    job_recommendations: list[JobRecommendation] = Field(default_factory=list)
    strategy_candidates: list[StrategyCandidate] = Field(default_factory=list)

    # Stage 3: Reviewer
    strategy_list: list[ScoredStrategy] = Field(default_factory=list)

    # Stage 4: Architect
    career_plan: CareerPlan | None = None
    visualization_data: VisualizationGraph | None = None

    # Stage 5: Simulation (feedback loop)
    simulation_feedback: SimulationFeedback | None = None

    # Stage 3-revisit: Re-ranked strategies after simulation feedback
    refined_strategy_list: list[ScoredStrategy] | None = None

    # Stage 6: Frontend-ready
    frontend_data: dict = Field(default_factory=dict)

    # Metadata
    elapsed_ms: float = Field(default=0.0)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
