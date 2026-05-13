"""T009 schemas — Career Growth System V2 with RL Optimization.

Extends T008 with:
  - BaselineStrategy: standardized career path templates (cold-start support)
  - IndustryTrend: market trend prediction data for architect
  - DiversityMetric: strategy diversity scoring to prevent overfitting
  - OffPathFlag: anomaly detection for non-typical path strategies
  - DynamicWeights: RL-style weight iteration state
  - PrivacyMask: data anonymization/privacy layer
  - FeedbackLoopState: bidirectional agent feedback state machine
  - T009PipelineOutput: extended unified output envelope
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from backend.career.t008_schemas import (
    CareerData,
    CareerDataEntry,
    CareerPlan,
    JobRecommendation,
    ParserOutput,
    PlanStep,
    RetrievalOutput,
    ReviewerOutput,
    ScoredStrategy,
    SimulationFeedback,
    SimulationRound,
    SkillNode,
    StrategyCandidate,
    T008PipelineOutput,
    TimelineNode,
    UserProfile,
    VisualizationGraph,
)


# ── Baseline Strategy (parser_agent — cold start) ──────────────────────────

class BaselineStrategyTemplate(BaseModel):
    """Standardized career growth path template for a specific role/domain."""

    template_id: str = Field(default_factory=lambda: f"bst-{uuid.uuid4().hex[:8]}")
    domain: str = Field(description="Career domain: engineering, design, product, data, etc.")
    target_role: str = Field(description="Target job title")
    typical_skills: list[str] = Field(default_factory=list, description="Required skills in order of acquisition")
    typical_timeline_months: int = Field(default=24, ge=6, le=60)
    typical_milestones: list[str] = Field(default_factory=list, description="Key progression milestones")
    recommended_strategies: list[str] = Field(
        default_factory=list, description="Strategy names proven effective for this path"
    )
    risk_factors: list[str] = Field(default_factory=list, description="Common pitfalls")
    source: str = Field(default="industry_benchmark", description="Template data source")


class BaselineStrategy(BaseModel):
    """Complete baseline strategy reference set — parser_agent output."""

    baseline_id: str = Field(default_factory=lambda: f"bl-{uuid.uuid4().hex[:8]}")
    templates: list[BaselineStrategyTemplate] = Field(default_factory=list)
    matched_template_id: str | None = Field(
        default=None, description="Best-matching template for current user"
    )
    match_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class OffPathFlag(BaseModel):
    """Anomaly flag for strategies deviating from typical career paths."""

    strategy_id: str
    flag_type: Literal["skill_order_anomaly", "timeline_deviation", "role_skip", "industry_jump", "salary_mismatch"]
    severity: Literal["low", "medium", "high"]
    description: str = ""
    deviation_score: float = Field(default=0.0, ge=0.0, le=1.0, description="0=typical, 1=extreme deviation")
    recommendation: str = Field(default="", description="Suggested correction")


class T009ParserOutput(BaseModel):
    """Extended parser output for T009."""

    user_profile: UserProfile
    career_data: CareerData | None = None
    baseline_strategy: BaselineStrategy | None = None
    off_path_flags: list[OffPathFlag] = Field(default_factory=list)
    new_user_generated: bool = Field(default=False, description="True if profile was auto-generated for cold start")
    warnings: list[str] = Field(default_factory=list)


# ── Industry Trends (architect_agent input) ────────────────────────────────

class IndustryTrend(BaseModel):
    """Market/industry trend prediction."""

    trend_id: str = Field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:8]}")
    domain: str = Field(description="Industry domain")
    trend_name: str = Field(description="Trend label, e.g., 'AI/ML growth', 'remote-first shift'")
    direction: Literal["rising", "stable", "declining"] = "stable"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    affected_skills: list[str] = Field(default_factory=list, description="Skills gaining/losing demand")
    affected_roles: list[str] = Field(default_factory=list, description="Roles impacted by this trend")
    growth_rate_pct: float = Field(default=0.0, description="Estimated annual growth rate %")
    source: str = Field(default="", description="Data source for trend")
    valid_until: str = Field(default="", description="ISO date when trend prediction expires")


class TrendReport(BaseModel):
    """Aggregated industry trends for a domain."""

    report_id: str = Field(default_factory=lambda: f"trr-{uuid.uuid4().hex[:8]}")
    domain: str
    trends: list[IndustryTrend] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: str = Field(default="", description="Executive summary of trend impact")


# ── Diversity & Dynamic Weights (reviewer_agent V2) ────────────────────────

class DiversityMetric(BaseModel):
    """Diversity scoring to prevent strategy overfitting."""

    strategy_diversity: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How different are strategies from each other (0=all same, 1=max diverse)"
    )
    dimension_balance: dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension spread across strategies (success_rate, match_degree, etc.)"
    )
    overfitting_risk: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Risk that strategies have converged to a local optimum"
    )
    recommendation: str = Field(default="")


class DynamicWeights(BaseModel):
    """RL-style iteratively updated scoring weights."""

    iteration: int = Field(default=0, ge=0, description="Weight update iteration count")
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "success_rate": 0.30,
            "match_degree": 0.25,
            "growth_cycle": 0.15,
            "skill_adaptability": 0.15,
            "diversity": 0.15,
        },
        description="Current 5-dimension weights, updated each iteration"
    )
    weight_history: list[dict[str, float]] = Field(
        default_factory=list, description="Previous weight snapshots for convergence tracking"
    )
    convergence_delta: float = Field(
        default=1.0, ge=0.0, description="Max weight change in last iteration (convergence when < 0.01)"
    )
    learning_rate: float = Field(default=0.05, ge=0.001, le=0.5)


class ScoredStrategyV2(BaseModel):
    """Extended scored strategy with diversity contribution and off-path status."""

    strategy: StrategyCandidate
    scores: dict[str, float] = Field(
        default_factory=lambda: {
            "success_rate": 0.0,
            "match_degree": 0.0,
            "growth_cycle": 0.0,
            "skill_adaptability": 0.0,
            "diversity": 0.0,
        }
    )
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""
    rank: int = 0
    off_path: bool = Field(default=False, description="True if strategy deviates from typical path")
    off_path_flags: list[OffPathFlag] = Field(default_factory=list)


class T009ReviewerOutput(BaseModel):
    """Extended reviewer output for T009."""

    strategy_list: list[ScoredStrategyV2] = Field(default_factory=list)
    top_n: int = 3
    diversity_metric: DiversityMetric | None = None
    dynamic_weights: DynamicWeights | None = None
    off_path_warnings: list[str] = Field(default_factory=list)


# ── Privacy Layer (frontend_agent requirement) ─────────────────────────────

class PrivacyMask(BaseModel):
    """Data anonymization/privacy mask configuration."""

    mask_personal_info: bool = Field(default=True, description="Mask name, email, phone")
    mask_company_names: bool = Field(default=False, description="Mask company names in display")
    mask_salary: bool = Field(default=False, description="Hide salary ranges")
    anonymization_level: Literal["none", "basic", "full"] = Field(default="basic")
    masked_fields: list[str] = Field(
        default_factory=list, description="Fields currently masked"
    )


# ── Feedback Loop State (bidirectional agent communication) ────────────────

class FeedbackLoopState(BaseModel):
    """Tracks bidirectional feedback between agents."""

    state_id: str = Field(default_factory=lambda: f"fls-{uuid.uuid4().hex[:8]}")
    # retrieval ↔ reviewer
    retrieval_reviewer_iterations: int = Field(default=0, ge=0)
    reviewer_weight_updates: int = Field(default=0, ge=0)

    # simulation → reviewer
    simulation_feedback_applied: bool = Field(default=False)
    simulation_rounds_run: int = Field(default=0)

    # frontend → parser + reviewer
    user_feedback_received: bool = Field(default=False)
    user_strategy_adopted: str | None = Field(default=None)
    user_behavior_preferences: dict = Field(default_factory=dict)

    # Convergence status
    pipeline_converged: bool = Field(default=False)
    convergence_reason: str = Field(default="")


# ── Frontend Feedback (user → system) ──────────────────────────────────────

class UserFeedback(BaseModel):
    """Structured user feedback collected by frontend."""

    feedback_id: str = Field(default_factory=lambda: f"fb-{uuid.uuid4().hex[:8]}")
    user_id: str
    session_id: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Strategy feedback
    strategy_adopted: str | None = Field(default=None, description="Strategy name the user chose")
    strategy_rating: float = Field(default=0.0, ge=0.0, le=1.0, description="User rating of strategy quality")

    # Path interaction
    nodes_clicked: list[str] = Field(default_factory=list, description="Skill/timeline nodes user clicked")
    time_spent_sections: dict[str, float] = Field(
        default_factory=dict, description="Seconds spent per visualization section"
    )

    # Explicit feedback
    comments: str = Field(default="")
    preferences_updated: dict = Field(default_factory=dict)
    privacy_level: Literal["none", "basic", "full"] = Field(default="basic")


# ── T009 Extended Architect Output ─────────────────────────────────────────

class T009ArchitectOutput(BaseModel):
    """Extended architect output with trend integration and interactive nodes."""

    career_plan: CareerPlan
    visualization_data: VisualizationGraph
    trend_adjustments: list[str] = Field(
        default_factory=list, description="How industry trends modified the plan"
    )
    interactive_nodes: dict[str, dict] = Field(
        default_factory=dict,
        description="node_id → {description, strategy_note, risk_note, click_action}"
    )
    long_term_outlook: str = Field(default="", description="12-24 month career outlook")
    privacy_mask: PrivacyMask | None = None


# ── T009 Simulation Output (RL iteration) ──────────────────────────────────

class T009SimulationFeedback(BaseModel):
    """Extended simulation feedback with RL weight updates."""

    base_feedback: SimulationFeedback
    weight_updates_applied: int = Field(default=0, ge=0)
    updated_weights: DynamicWeights | None = None
    off_path_strategies_detected: list[str] = Field(
        default_factory=list, description="Strategy IDs flagged as off-path"
    )
    rl_iteration: int = Field(default=1, ge=1, description="Current RL iteration number")
    rl_converged: bool = Field(default=False)


# ── T009 Unified Pipeline Output ───────────────────────────────────────────

class T009PipelineOutput(BaseModel):
    """Complete T009 pipeline output with all enhancements."""

    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    status: Literal["success", "partial", "failed"] = "success"
    errors: list[str] = Field(default_factory=list)

    # Stage 1: Parser (extended)
    user_profile: UserProfile | None = None
    career_data: CareerData | None = None
    baseline_strategy: BaselineStrategy | None = None
    off_path_flags: list[OffPathFlag] = Field(default_factory=list)
    new_user_generated: bool = False

    # Stage 2: Retrieval
    job_recommendations: list[JobRecommendation] = Field(default_factory=list)
    strategy_candidates: list[StrategyCandidate] = Field(default_factory=list)

    # Stage 3: Reviewer V2 (with diversity + dynamic weights)
    strategy_list: list[ScoredStrategyV2] = Field(default_factory=list)
    diversity_metric: DiversityMetric | None = None
    dynamic_weights: DynamicWeights | None = None

    # Stage 4: Architect (with trends)
    career_plan: CareerPlan | None = None
    visualization_data: VisualizationGraph | None = None
    trend_adjustments: list[str] = Field(default_factory=list)
    interactive_nodes: dict[str, dict] = Field(default_factory=dict)
    long_term_outlook: str = ""

    # Stage 5: Simulation V2 (RL iteration)
    simulation_feedback: T009SimulationFeedback | None = None
    refined_strategy_list: list[ScoredStrategyV2] | None = None

    # Stage 6: Frontend-ready
    frontend_data: dict = Field(default_factory=dict)
    privacy_mask: PrivacyMask | None = None

    # Feedback loop state
    feedback_loop: FeedbackLoopState | None = None
    user_feedback: UserFeedback | None = None

    # Metadata
    elapsed_ms: float = 0.0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    t009_version: str = Field(default="2.0.0")
