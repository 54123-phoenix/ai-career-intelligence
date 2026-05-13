"""Ranking schemas — Pydantic models for the LTR pipeline (T006 v1.0.0).

Every output type carries trace_id (Constraint 1).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """Numeric feature vector for one candidate — input to ranking model."""

    candidate_id: str = Field(description="Job ID from MatchResult.item_id")
    trace_id: str = Field(description="Pipeline execution ID")
    features: dict[str, float] = Field(
        default_factory=dict,
        description="8-dim feature dict: skill_overlap_score, embedding_similarity, "
        "salary_match_score, company_quality_score, retrieval_rank, "
        "historical_ctr, dwell_time, save_frequency",
    )


class RerankedCandidate(BaseModel):
    """Candidate after ranking model application — output of rerank_engine."""

    candidate_id: str = Field(description="Job ID from MatchResult.item_id")
    trace_id: str = Field(description="Pipeline execution ID")
    original_score: float = Field(ge=0.0, le=1.0, description="Semantic retrieval score (auxiliary only)")
    ranking_score: float = Field(ge=0.0, le=1.0, description="Score from ranking model")
    final_rank: int = Field(ge=1, description="1-indexed rank after sorting by ranking_score")
    features: dict[str, float] = Field(default_factory=dict, description="Feature vector used for scoring")


class UserBehaviorLog(BaseModel):
    """A single user interaction event — raw signal for pair generation."""

    trace_id: str = Field(description="Pipeline execution ID")
    job_id: str = Field(description="Job that was interacted with")
    action: Literal["clicked", "saved", "skipped", "applied"] = Field(
        description="User action on this job"
    )
    dwell_time_ms: int = Field(default=0, ge=0, description="Time spent viewing (ms)")
    position: int = Field(default=0, ge=0, description="Display position (0-indexed)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp",
    )


class RankingPair(BaseModel):
    """Pairwise ranking sample — clicked > skipped, saved > clicked."""

    pair_id: str = Field(description="Deterministic ID: md5(pos+neg+rel)[:12]")
    trace_id: str = Field(description="Pipeline execution ID")
    positive_job_id: str = Field(description="Preferred job (clicked or saved)")
    negative_job_id: str = Field(description="Less preferred job (skipped or clicked)")
    positive_features: dict[str, float] = Field(
        default_factory=dict, description="Features for positive job"
    )
    negative_features: dict[str, float] = Field(
        default_factory=dict, description="Features for negative job"
    )
    relation: Literal["clicked_gt_skipped", "saved_gt_clicked"] = Field(
        description="Preference relation type"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp",
    )


class TrainedRankerModel(BaseModel):
    """Metadata for a versioned ranking model stored on disk."""

    model_id: str = Field(
        default_factory=lambda: f"ranker-{uuid.uuid4().hex[:8]}",
        description="Unique model identifier",
    )
    model_version: int = Field(default=0, ge=0, description="Auto-incremented version number (0 = not yet saved)")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 creation timestamp",
    )
    training_samples_count: int = Field(ge=0, description="Number of pairs used for training")
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Training metrics: ndcg_1, ndcg_3, ndcg_5, ndcg_10, pairwise_accuracy, validation_loss",
    )
    model_path: str = Field(default="", description="Path to LightGBM model file on disk")
    feature_names: list[str] = Field(
        default_factory=list,
        description="Ordered feature names this model expects",
    )
    is_active: bool = Field(default=False, description="Whether this model is currently used for reranking")
    parent_model_version: int | None = Field(default=None, description="Parent model version for incremental training lineage")


class RankingPipelineOutput(BaseModel):
    """Aggregate output of one RANKING-mode pipeline execution."""

    trace_id: str = Field(description="Pipeline execution ID")
    feature_vectors: list[FeatureVector] = Field(default_factory=list)
    reranked_candidates: list[RerankedCandidate] = Field(default_factory=list)
    ranking_pairs: list[RankingPair] = Field(default_factory=list)
    model_used: TrainedRankerModel | None = Field(default=None, description="Active model at execution time")


# API request/response models (used by backend.api.routes.ranking) -------------


class RerankRequest(BaseModel):
    """Request body for POST /api/v1/ranking/rerank."""

    trace_id: str = Field(
        default_factory=lambda: f"rerank-{uuid.uuid4().hex[:8]}"
    )
    candidates: list[dict] = Field(default_factory=list, description="List of {item_id, score, payload} dicts")
    user_profile: dict = Field(default_factory=dict, description="{skills: [...], query: str}")
    interaction_history: list[UserBehaviorLog] | None = None


class PairRequest(BaseModel):
    """Request body for POST /api/v1/ranking/pairs."""

    trace_id: str = Field(
        default_factory=lambda: f"pairs-{uuid.uuid4().hex[:8]}"
    )
    behavior_logs: list[UserBehaviorLog] = Field(default_factory=list)


class TrainRequest(BaseModel):
    """Request body for POST /api/v1/ranking/train."""

    pairs: list[RankingPair] | None = None
    from_recent_traces: bool = False
    days: int = Field(default=7, ge=1, le=90)
    validation_split: float = Field(default=0.2, ge=0.1, le=0.5)
