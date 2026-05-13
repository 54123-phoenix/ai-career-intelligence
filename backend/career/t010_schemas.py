"""T010 schemas — Lightweight Career Growth with explicit upgrade interfaces.

Design: core layer (single-user, lightweight) + upgrade_interface hooks for:
  - Multi-user cohort analysis
  - Multi-industry data sources
  - Multi-scenario long-term simulation
  - Cross-user strategy library
  - Group pattern scoring / multi-dim metrics
  - Trend overlay on career paths
  - Group comparison views

Each agent output carries upgrade_interface markers documenting what can be extended.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from backend.career.t008_schemas import (
    CareerData, CareerDataEntry, CareerPlan, JobRecommendation,
    RetrievalOutput, SkillNode, StrategyCandidate, UserProfile,
    VisualizationGraph,
)
from backend.career.t009_schemas import (
    BaselineStrategy, BaselineStrategyTemplate, DiversityMetric,
    DynamicWeights, FeedbackLoopState, OffPathFlag, PrivacyMask,
    ScoredStrategyV2, T009ParserOutput, T009SimulationFeedback,
    TrendReport, UserFeedback,
)


# ── Upgrade Interface — metadata attached to every agent's output ──────────

class UpgradeInterface(BaseModel):
    """Documents what can be upgraded in a future version of this agent's output.

    Every agent output carries this — makes the upgrade path explicit in the data,
    not just in code comments.
    """

    agent: str = Field(description="Agent name: parser, retrieval, reviewer, architect, simulation, frontend")
    core_capability: str = Field(description="What the core layer does today")
    upgrade_hooks: list[str] = Field(
        default_factory=list, description="Named extension points for future versions"
    )
    upgrade_notes: str = Field(default="", description="Implementation guidance for each hook")
    version: str = Field(default="core-1.0", description="Current layer version")


# ── T010 Agent Outputs — thin wrappers with upgrade interfaces ─────────────

class T010ParserOutput(BaseModel):
    """Parser output: core = single-user profile + baseline match."""

    user_profile: UserProfile
    career_data: CareerData | None = None
    baseline_strategy: BaselineStrategy | None = None
    off_path_flags: list[OffPathFlag] = Field(default_factory=list)
    new_user_generated: bool = False
    warnings: list[str] = Field(default_factory=list)
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="parser",
            core_capability="Single-user profile normalization, single-source career data parsing, baseline template matching",
            upgrade_hooks=[
                "multi_user_ingest",
                "multi_source_aggregation",
                "cross_domain_mapping",
            ],
            upgrade_notes=(
                "multi_user_ingest: accept list[user_input] → list[UserProfile]. "
                "multi_source_aggregation: register SourceAdapter per industry. "
                "cross_domain_mapping: map skills across domains via ontology."
            ),
        )
    )


class T010RetrievalOutput(BaseModel):
    """Retrieval output: core = 3-5 candidates, single-user job matching."""

    job_recommendations: list[JobRecommendation] = Field(default_factory=list)
    strategy_candidates: list[StrategyCandidate] = Field(
        default_factory=list, max_length=5, description="Strictly 3-5 candidates for lightweight mode"
    )
    total_matches: int = 0
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="retrieval",
            core_capability="Single-user semantic job matching, 3-5 strategy candidates from baseline+history",
            upgrade_hooks=[
                "cross_user_strategy_library",
                "multi_industry_retrieval",
                "strategy_graph_search",
            ],
            upgrade_notes=(
                "cross_user_strategy_library: query strategy embeddings from cohort. "
                "multi_industry_retrieval: federated search across industry-specific indices. "
                "strategy_graph_search: traverse strategy→skill→job graph for multi-hop matches."
            ),
        )
    )


class T010ReviewerOutput(BaseModel):
    """Reviewer output: core = single-user 5-dim scoring, dynamic weight update."""

    strategy_list: list[ScoredStrategyV2] = Field(default_factory=list)
    top_n: int = 3
    diversity_metric: DiversityMetric | None = None
    dynamic_weights: DynamicWeights | None = None
    off_path_warnings: list[str] = Field(default_factory=list)
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="reviewer",
            core_capability="Single-user 5-dimension scoring, RL dynamic weight update, off-path detection",
            upgrade_hooks=[
                "group_pattern_scoring",
                "multi_dim_metric_expansion",
                "cohort_benchmark_comparison",
            ],
            upgrade_notes=(
                "group_pattern_scoring: score strategies against cohort success patterns. "
                "multi_dim_metric_expansion: add dimensions (market_timing, networking_score, etc.). "
                "cohort_benchmark_comparison: percentile rank within similar-profile users."
            ),
        )
    )


class T010ArchitectOutput(BaseModel):
    """Architect output: core = single-user career plan + path graph."""

    career_plan: CareerPlan
    visualization_data: VisualizationGraph
    trend_adjustments: list[str] = Field(default_factory=list)
    interactive_nodes: dict[str, dict] = Field(default_factory=dict)
    long_term_outlook: str = ""
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="architect",
            core_capability="Single-user career plan generation, skill-path graph, optional trend overlay",
            upgrade_hooks=[
                "multi_scenario_simulation",
                "long_term_trend_overlay",
                "group_strategy_overlay",
            ],
            upgrade_notes=(
                "multi_scenario_simulation: generate A/B/C plans for different market conditions. "
                "long_term_trend_overlay: project skill demand curves over 5 years onto path graph. "
                "group_strategy_overlay: show where user's path intersects with cohort paths."
            ),
        )
    )


class T010SimulationOutput(BaseModel):
    """Simulation output: core = short-term, high-confidence, single-user."""

    base_feedback: T009SimulationFeedback | None = None
    weight_updates_applied: int = 0
    updated_weights: DynamicWeights | None = None
    off_path_strategies_detected: list[str] = Field(default_factory=list)
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="simulation",
            core_capability="Short-term strategy simulation (≤10 rounds), high-confidence priority, single-user",
            upgrade_hooks=[
                "multi_scenario_long_term",
                "multi_user_cohort_sim",
                "market_shock_scenario",
            ],
            upgrade_notes=(
                "multi_scenario_long_term: simulate 12-24 month trajectories with macro factors. "
                "multi_user_cohort_sim: batch-simulate all users sharing a template. "
                "market_shock_scenario: inject recession/boom events into simulation."
            ),
        )
    )


class T010FrontendData(BaseModel):
    """Frontend-ready data with privacy and upgrade metadata."""

    summary: dict = Field(default_factory=dict)
    career_path_graph: dict = Field(default_factory=dict)
    strategy_comparison: dict = Field(default_factory=dict)
    action_timeline: list[dict] = Field(default_factory=list)
    simulation_chart: dict = Field(default_factory=dict)
    recommendations: list[dict] = Field(default_factory=list)
    interactive_nodes: dict[str, dict] = Field(default_factory=dict)
    privacy_mask: PrivacyMask | None = None
    upgrade: UpgradeInterface = Field(
        default_factory=lambda: UpgradeInterface(
            agent="frontend",
            core_capability="Single-user path graph, strategy cards, risk annotations, privacy masking",
            upgrade_hooks=[
                "multi_user_view",
                "cohort_comparison",
                "trend_overlay_view",
            ],
            upgrade_notes=(
                "multi_user_view: toggle between user profiles in same dashboard. "
                "cohort_comparison: percentile charts against similar users. "
                "trend_overlay_view: animated trend lines over career path graph."
            ),
        )
    )


# ── T010 Unified Pipeline Output ───────────────────────────────────────────

class T010PipelineOutput(BaseModel):
    """Lightweight T010 pipeline output — core layer only, upgrade-ready."""

    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    status: Literal["success", "partial", "failed"] = "success"
    errors: list[str] = Field(default_factory=list)

    # Stage 1: Parser (core)
    user_profile: UserProfile | None = None
    career_data: CareerData | None = None
    baseline_strategy: BaselineStrategy | None = None
    off_path_flags: list[OffPathFlag] = Field(default_factory=list)

    # Stage 2: Retrieval (core, 3-5 candidates)
    job_recommendations: list[JobRecommendation] = Field(default_factory=list)
    strategy_candidates: list[StrategyCandidate] = Field(default_factory=list)

    # Stage 3: Reviewer (core, 5-dim + dynamic weights)
    strategy_list: list[ScoredStrategyV2] = Field(default_factory=list)
    diversity_metric: DiversityMetric | None = None
    dynamic_weights: DynamicWeights | None = None

    # Stage 4: Architect (core, single-user plan)
    career_plan: CareerPlan | None = None
    visualization_data: VisualizationGraph | None = None
    interactive_nodes: dict[str, dict] = Field(default_factory=dict)

    # Stage 5: Simulation (core, short-term)
    simulation_feedback: T009SimulationFeedback | None = None
    refined_strategy_list: list[ScoredStrategyV2] | None = None

    # Stage 6: Frontend data (core, privacy-masked)
    frontend_data: dict = Field(default_factory=dict)
    privacy_mask: PrivacyMask | None = None

    # Feedback loop state
    feedback_loop: FeedbackLoopState | None = None

    # ── Upgrade interfaces — one per agent ──
    upgrade_interfaces: dict[str, UpgradeInterface] = Field(
        default_factory=dict,
        description="Keyed by agent name. Documents every extension point.",
    )

    # Metadata
    elapsed_ms: float = 0.0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = Field(default="core-1.0", description="T010 lightweight core version")
