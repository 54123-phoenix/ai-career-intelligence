"""Session schemas — Pydantic models for session feedback learning loop (T006 v1.0.0).

All models carry session_id and trace_id where applicable (Constraint 6).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# ── Session Action ───────────────────────────────────────────────────────

class SessionAction(BaseModel):
    """A single user action within a session."""

    action_id: str = Field(
        default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}"
    )
    session_id: str = Field(default="", description="Owning session ID")
    trace_id: str = Field(default="", description="Pipeline execution ID")
    action_type: Literal["query", "click", "skip", "save", "apply", "dwell"] = Field(
        description="Type of user action"
    )
    job_id: str | None = Field(default=None, description="Job ID if applicable")
    job_payload: dict | None = Field(
        default=None, description="Job metadata (skills, company, location, level)"
    )
    dwell_time_ms: int = Field(default=0, ge=0)
    position: int = Field(default=0, ge=0)
    query_text: str | None = Field(default=None, description="Query text if action_type=query")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Session ──────────────────────────────────────────────────────────────

class Session(BaseModel):
    """Time-ordered sequence of user actions, bounded by 30-min inactivity."""

    session_id: str = Field(
        default_factory=lambda: f"sess-{uuid.uuid4().hex[:8]}"
    )
    user_id: str = Field(description="User this session belongs to")
    ordered_actions: list[SessionAction] = Field(
        default_factory=list, description="Actions in chronological order"
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    ended_at: str | None = Field(default=None, description="When session ended (auto or manual)")
    is_active: bool = Field(default=True)


# ── Session Summary ──────────────────────────────────────────────────────

class SessionSummary(BaseModel):
    """Aggregated behavioral statistics from one session."""

    session_id: str = Field(description="Source session ID")
    user_id: str = Field(default="")
    trace_id: str = Field(default="", description="Pipeline execution ID")
    clicked_categories: list[str] = Field(
        default_factory=list, description="Categories of clicked jobs (skills/levels/locations)"
    )
    skipped_categories: list[str] = Field(
        default_factory=list, description="Categories of skipped jobs"
    )
    clicked_job_ids: list[str] = Field(default_factory=list)
    saved_job_ids: list[str] = Field(default_factory=list)
    applied_job_ids: list[str] = Field(default_factory=list)
    skipped_job_ids: list[str] = Field(default_factory=list)
    average_dwell_time_ms: float = Field(default=0.0, ge=0.0)
    save_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    apply_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    click_through_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    total_actions: int = Field(default=0, ge=0)
    top_clicked_skills: list[str] = Field(default_factory=list)
    top_clicked_companies: list[str] = Field(default_factory=list)


# ── Dynamic Preferences ──────────────────────────────────────────────────

class DynamicPreferences(BaseModel):
    """User preferences that evolve across sessions via EMA blending."""

    user_id: str = Field(description="User these preferences belong to")
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    skill_weights: dict[str, float] = Field(
        default_factory=dict, description="Skill → weight [0,1]"
    )
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_companies: list[str] = Field(default_factory=list)
    preferred_levels: list[str] = Field(default_factory=list)
    salary_preference: tuple[int, int] | None = Field(
        default=None, description="(min, max) in K/year"
    )
    preferred_categories: list[str] = Field(default_factory=list)
    preference_shift_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="How much preferences shifted in last update"
    )
    session_count: int = Field(default=0, ge=0, description="Number of sessions aggregated")


# ── Feedback Queue Event ─────────────────────────────────────────────────

class FeedbackQueueEvent(BaseModel):
    """A queued training event generated from session behavior."""

    event_id: str = Field(
        default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}"
    )
    session_id: str = Field(description="Source session ID")
    trace_id: str = Field(description="Pipeline execution ID")
    model_version: int = Field(default=0, ge=0, description="Ranking model version at event time")
    event_type: Literal["click", "save", "apply", "skip", "dwell"] = Field(
        description="Training signal type"
    )
    job_id: str = Field(description="Job this event relates to")
    weight: float = Field(default=0.0, description="Training weight: positive=boost, negative=suppress")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Session Review ───────────────────────────────────────────────────────

class SessionReview(BaseModel):
    """Reviewer output for a single session."""

    session_id: str
    trace_id: str = Field(default="")
    session_ctr: float = Field(default=0.0, ge=0.0, le=1.0)
    ndcg_score: float | None = Field(default=None)
    drift_score: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    detected_issues: list[str] = Field(default_factory=list)


# ── Long-Term Report ─────────────────────────────────────────────────────

class LongTermReport(BaseModel):
    """Aggregated long-term recommendation performance statistics."""

    report_id: str = Field(
        default_factory=lambda: f"ltr-{uuid.uuid4().hex[:8]}"
    )
    period_start: str = Field(default="")
    period_end: str = Field(default="")
    avg_ctr: float = Field(default=0.0)
    avg_ndcg_10: float | None = Field(default=None)
    avg_mrr: float | None = Field(default=None)
    avg_save_rate: float = Field(default=0.0)
    avg_apply_rate: float = Field(default=0.0)
    session_retention: float = Field(default=0.0)
    total_sessions: int = Field(default=0)
    degradation_detected: bool = Field(default=False)
    retraining_recommendation: str = Field(default="")


# ── Pipeline Output ──────────────────────────────────────────────────────

class SessionPipelineOutput(BaseModel):
    """Aggregate output of one SESSION-mode pipeline execution."""

    session_id: str = Field(description="Session ID")
    trace_id: str = Field(description="Pipeline trace ID")
    session_summary: SessionSummary | None = None
    updated_preferences: DynamicPreferences | None = None
    session_review: SessionReview | None = None
    queued_events_count: int = Field(default=0)
    drift_score: float = Field(default=0.0)
    long_term_report: LongTermReport | None = None
