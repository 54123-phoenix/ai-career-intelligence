"""Data Ingestion schemas — T005 v1.0.0.

UnifiedJob is the canonical job representation across all data sources.
All RawJobPosting variants normalize into this single schema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Source descriptor
# ---------------------------------------------------------------------------


class DataSource(BaseModel):
    """Metadata about a data origin."""

    name: str = Field(description="Source identifier: boss | lagou | liepin | github")
    url: str = Field(default="", description="Base URL or endpoint")
    last_fetched: int = Field(default=0, description="Epoch seconds of last successful fetch")
    item_count: int = Field(default=0, description="Items ingested in last batch")


# ---------------------------------------------------------------------------
# Raw input (before normalization)
# ---------------------------------------------------------------------------


class RawJobPosting(BaseModel):
    """Unprocessed job posting from any source. Fields vary by source."""

    source: str = Field(description="Source identifier")
    raw_id: str = Field(description="Original ID from source")
    title: str = ""
    company: str = ""
    location: str = ""
    salary_text: str = ""  # "30K-50K" or "面议" or "$80k-$120k"
    skills_text: str = ""  # comma-separated or free-text
    description: str = ""
    level: str = ""  # "初级" | "中级" | "高级" — may be empty
    raw_json: dict = Field(default_factory=dict, description="Original payload for debugging")
    fetched_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


# ---------------------------------------------------------------------------
# Unified output (after normalization)
# ---------------------------------------------------------------------------


class UnifiedJob(BaseModel):
    """Canonical job representation — the single schema consumed downstream.

    All fields are guaranteed non-null after normalization.
    """

    job_id: str = Field(description="Deterministic ID: md5(source + raw_id)")
    title: str
    company: str
    salary_range: str = Field(default="", description="Normalized string: '300K-500K/年'")
    location: str = ""
    skills: list[str] = Field(default_factory=list, description="Merged required + optional, normalized")
    source: str = Field(description="Source identifier")
    timestamp: int = Field(default=0, description="Epoch seconds")


# ---------------------------------------------------------------------------
# Ingestion batch result
# ---------------------------------------------------------------------------


class IngestionResult(BaseModel):
    """Outcome of one ingestion run."""

    source: str
    fetched: int = Field(default=0, description="Raw postings retrieved")
    normalized: int = Field(default=0, description="Successfully converted to UnifiedJob")
    duplicates_skipped: int = Field(default=0)
    errors: int = Field(default=0)
    jobs: list[UnifiedJob] = Field(default_factory=list)
    elapsed_ms: float = Field(default=0.0)
