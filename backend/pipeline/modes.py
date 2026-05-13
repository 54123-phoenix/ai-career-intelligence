"""Pipeline mode types — ExecutionMode enum, ExecutionPlan, PipelineContext.

PipelineContext is the single state object that flows through all pipeline stages.
Every agent reads from / writes to this context — no implicit globals.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.feedback.schemas import FeedbackAggregate, TrainingSample
from backend.shared.types import MatchResult
from backend.simulation.state import SimulationResult


class ExecutionMode(str, Enum):
    """Pipeline execution mode selected by ArchitectAgent."""

    FAST = "fast"       # Cached retrieval, minimal or no simulation
    FULL = "full"       # Full pipeline: retrieval → simulation → review → feedback
    FALLBACK = "fallback"  # Degraded mode: cached or API-only, no simulation
    RANKING = "ranking"  # LTR pipeline: retrieval → feature_build → rerank → review → pair_build
    SESSION = "session"  # Session learning: track → aggregate → update_prefs → retrieval → rerank → review → feedback_queue → feedback
    CAREER = "career"  # Career evolution: parser → retrieval → reviewer → architect → simulation → frontend


class ExecutionPlan(BaseModel):
    """ArchitectAgent output — dictates which steps run and how.

    Generated once per pipeline invocation by ArchitectAgent.determine_plan().
    """

    mode: ExecutionMode = Field(description="Selected execution mode")
    steps: list[str] = Field(
        default_factory=list, description="Ordered agent call sequence"
    )
    reason: str = Field(default="", description="Why this mode was selected")
    cache_used: bool = Field(default=False, description="Whether cached results were found")
    simulation_needed: bool = Field(default=True, description="Whether to run simulation")
    rerank_needed: bool = Field(default=False, description="Whether to apply ranking model")
    retrieval_top_k: int = Field(default=20, ge=1, le=100)
    session_id: str | None = Field(default=None, description="Session ID for SESSION mode")
    dynamic_preferences_needed: bool = Field(default=False, description="Whether to update dynamic preferences")


class PipelineContext(BaseModel):
    """State carried through the full pipeline execution.

    Created at pipeline start, mutated by each stage, returned at pipeline end.
    All agent outputs are accumulated here — no hidden state anywhere.
    """

    execution_id: str = Field(
        default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}",
        description="Unique identifier for this pipeline run",
    )
    mode: ExecutionMode = Field(default=ExecutionMode.FULL, description="Active execution mode")
    plan: ExecutionPlan | None = Field(default=None, description="Architect-generated plan")

    # Input
    user_query: str = Field(default="", description="Raw user query string")
    user_embedding: list[float] | None = Field(default=None, description="Query embedding vector")
    filters: dict[str, Any] | None = Field(default=None, description="User-provided filters")
    user_id: str | None = Field(default=None, description="User identifier for session tracking")

    # Stage outputs — populated sequentially
    retrieved_candidates: list[MatchResult] = Field(
        default_factory=list, description="Top-K matched jobs from retrieval"
    )
    simulation_results: list[SimulationResult] = Field(
        default_factory=list, description="Simulation results for top matches"
    )
    reviewer_aggregate: FeedbackAggregate | None = Field(
        default=None, description="Batch review output"
    )
    training_samples: list[TrainingSample] = Field(
        default_factory=list, description="Generated learning-to-rank dataset"
    )

    # Interaction history — user behavior logs injected for ranking pair generation
    interaction_history: list | None = Field(
        default=None, description="User behavior logs for ranking pair generation (RANKING mode)"
    )

    # Ranking stage outputs (populated in RANKING mode)
    feature_vectors: list = Field(
        default_factory=list, description="Feature vectors from feature_builder_agent"
    )
    reranked_candidates: list = Field(
        default_factory=list, description="Reranked candidates from rerank_engine_agent"
    )
    ranking_pairs: list = Field(
        default_factory=list, description="Pairwise training data from pair_builder_agent"
    )
    model_used: dict | None = Field(
        default=None, description="Active ranking model metadata at execution time"
    )

    # Session stage outputs (populated in SESSION mode)
    session_id: str | None = Field(
        default=None, description="Active session ID"
    )
    session_actions: list = Field(
        default_factory=list, description="SessionAction objects from session tracker"
    )
    session_summary: dict | None = Field(
        default=None, description="SessionSummary from behavior_aggregator (serialized)"
    )
    dynamic_preferences: dict | None = Field(
        default=None, description="DynamicPreferences from preference_updater (serialized)"
    )
    queued_events: list = Field(
        default_factory=list, description="FeedbackQueueEvent objects for nightly training"
    )
    drift_score: float = Field(
        default=0.0, description="Preference drift score from preference_updater"
    )
    session_review: dict | None = Field(
        default=None, description="SessionReview from reviewer (serialized)"
    )

    # Career stage outputs (populated in CAREER mode — T007)
    career_events: list = Field(
        default_factory=list, description="Parsed CareerEvent objects"
    )
    career_timeline: dict | None = Field(
        default=None, description="CareerTimeline from career_retriever"
    )
    bottleneck_analysis: dict | None = Field(
        default=None, description="BottleneckAnalysis from career_reviewer"
    )
    career_strategy: dict | None = Field(
        default=None, description="CareerStrategy from career_architect"
    )
    strategy_simulation: dict | None = Field(
        default=None, description="StrategySimulation from career_simulator"
    )
    career_visualization: dict | None = Field(
        default=None, description="CareerVisualization from career_frontend"
    )

    # Metadata
    errors: list[str] = Field(
        default_factory=list, description="Non-fatal errors encountered during execution"
    )
    started_at: float = Field(
        default_factory=time.perf_counter, description="Pipeline start (perf_counter)"
    )
    elapsed_ms: float = Field(default=0.0, description="Total pipeline wall time in ms")
