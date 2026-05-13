"""PipelineConfig — tunable parameters for the multi-agent pipeline.

All timing values in milliseconds, all ratios in [0, 1].
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    """Configuration for the multi-agent T005 pipeline.

    Tunable parameters affecting execution mode selection, caching,
    simulation depth, and feedback retention.
    """

    # Cache
    cache_ttl_seconds: int = Field(
        default=300, ge=0, description="TTL for retrieval cache; 0 disables caching"
    )

    # Retrieval
    default_top_k: int = Field(
        default=20, ge=1, le=100, description="Default retrieval top-K in full mode"
    )
    fast_mode_top_k: int = Field(
        default=3, ge=1, le=10, description="Top candidates to simulate in fast mode"
    )

    # Architect thresholds
    fast_mode_confidence_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum confidence for fast mode cache hit"
    )
    fallback_degraded_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="If fewer than this fraction of services are healthy, force fallback",
    )

    # Simulation
    max_simulation_paths: int = Field(
        default=5, ge=1, le=20, description="Maximum simulations per pipeline run"
    )
    simulation_strategy: str = Field(
        default="balanced",
        description="Default strategy: aggressive | conservative | balanced",
    )

    # Feedback
    feedback_retention_count: int = Field(
        default=5000, ge=0, description="Maximum training samples retained in memory"
    )
    min_sample_label: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Minimum label for a valid training sample"
    )

    # Ranking (T006 LTR)
    ranking_enabled: bool = Field(
        default=False, description="Enable the LTR ranking pipeline"
    )
    ranking_model_dir: str = Field(
        default="backend/ranking/models", description="Directory for versioned ranking models"
    )
    ranking_min_training_pairs: int = Field(
        default=100, ge=10, description="Minimum pairs required to trigger training"
    )
    ranking_retraining_interval_hours: int = Field(
        default=24, ge=1, description="Hours between automatic retraining checks"
    )
    ranking_validation_split: float = Field(
        default=0.2, ge=0.1, le=0.5, description="Fraction of pairs reserved for validation"
    )

    # Career (T007 — Career Memory & Evolution Engine)
    career_max_events_per_user: int = Field(
        default=500, ge=10, description="Max career events stored per user"
    )
    career_trajectory_months: int = Field(
        default=24, ge=6, le=60, description="Months of history for skill trajectory"
    )

    # Session (T006 L3 — Session Feedback Loop)
    session_timeout_minutes: int = Field(
        default=30, ge=5, le=120, description="Minutes of inactivity before session auto-ends"
    )
    session_preference_recent_weight: float = Field(
        default=0.7, ge=0.5, le=0.9, description="Weight of recent session in preference blending"
    )
    session_engagement_decay_days: int = Field(
        default=14, ge=1, le=90, description="Days over which engagement scores decay"
    )
    session_max_events_per_batch: int = Field(
        default=500, ge=10, le=5000, description="Max feedback events drained per training batch"
    )
    session_feedback_queue_max: int = Field(
        default=10000, ge=100, le=100000, description="Max events in feedback queue"
    )

    # Health
    health_check_timeout_ms: int = Field(
        default=2000, ge=100, description="Timeout for individual health check"
    )


# Module-level default config
config = PipelineConfig()
