"""Signal Layer schemas — InteractionTrace links all pipeline stage outputs.

InteractionTrace is the single unified record of one pipeline execution.
Every output from a single run is collected here under one trace_id.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.feedback.schemas import FeedbackAggregate, TrainingSample
from backend.pipeline.modes import ExecutionMode
from backend.shared.types import MatchResult
from backend.simulation.state import SimulationResult


class InteractionTrace(BaseModel):
    """Unified trace of one full pipeline execution.

    Links: query → candidates → simulations → reviews → training samples.
    Every output from a single pipeline run is collected here under one trace_id.

    This is the single source of truth for T006 — all downstream consumers
    (training pipelines, analytics, debugging) read from this record.
    """

    trace_id: str = Field(
        description="Universal trace identifier — same as PipelineContext.execution_id"
    )
    mode: ExecutionMode = Field(description="Execution mode used for this run")

    # Input
    user_query: str = Field(default="", description="Raw user query string")
    filters: dict[str, Any] | None = Field(
        default=None, description="User-provided filters"
    )

    # Stage outputs — collected from PipelineContext after execution
    retrieved_candidates: list[MatchResult] = Field(
        default_factory=list, description="Top-K matched jobs from retrieval stage"
    )
    simulation_results: list[SimulationResult] = Field(
        default_factory=list, description="Per-candidate simulation results"
    )
    reviewer_aggregate: FeedbackAggregate | None = Field(
        default=None, description="Batch review output with bias findings"
    )
    training_samples: list[TrainingSample] = Field(
        default_factory=list,
        description="Learning-to-rank dataset — each sample carries trace_id",
    )

    # Ranking stage outputs (populated in RANKING mode)
    feature_vectors: list = Field(
        default_factory=list, description="Feature vectors from feature_builder_agent"
    )
    reranked_candidates: list = Field(
        default_factory=list, description="Reranked candidates from rerank_engine_agent"
    )
    ranking_pairs: list = Field(
        default_factory=list, description="Pairwise ranking data from pair_builder_agent"
    )
    model_used: dict | None = Field(
        default=None, description="Active ranking model metadata at execution time"
    )
    interaction_history: list | None = Field(
        default=None, description="User behavior logs for ranking pair generation"
    )

    # Session stage outputs (populated in SESSION mode)
    session_id: str | None = Field(default=None, description="Session ID")
    session_actions: list = Field(default_factory=list, description="SessionAction objects")
    session_summary: dict | None = Field(default=None, description="SessionSummary output")
    dynamic_preferences: dict | None = Field(default=None, description="DynamicPreferences output")
    queued_events: list = Field(default_factory=list, description="FeedbackQueueEvent objects")
    drift_score: float = Field(default=0.0, description="Preference shift score")
    session_review: dict | None = Field(default=None, description="SessionReview output")

    # Career stage outputs (populated in CAREER mode — T007)
    career_events: list = Field(default_factory=list, description="CareerEvent objects")
    career_timeline: dict | None = Field(default=None, description="CareerTimeline output")
    bottleneck_analysis: dict | None = Field(default=None, description="BottleneckAnalysis output")
    career_strategy: dict | None = Field(default=None, description="CareerStrategy output")
    strategy_simulation: dict | None = Field(default=None, description="StrategySimulation output")
    career_visualization: dict | None = Field(default=None, description="CareerVisualization output")

    # Metadata
    plan_steps: list[str] = Field(
        default_factory=list,
        description="Which steps actually executed (from ExecutionPlan)",
    )
    errors: list[str] = Field(
        default_factory=list, description="Non-fatal errors encountered during execution"
    )
    started_at: float = Field(default=0.0, description="Pipeline start (perf_counter)")
    elapsed_ms: float = Field(default=0.0, description="Total wall time in ms")
