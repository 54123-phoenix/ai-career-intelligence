"""Retrieval API routes — POST /api/v1/retrieval/match.

Pipeline: resume → embedding → vector search → matcher → MatchResult[]
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.retrieval.embedder import embedder
from backend.retrieval.matcher import JobMatcher, _missing_skills
from backend.shared.types import MatchResult, StructuredResume

router = APIRouter()

_matcher = JobMatcher()

# ---------------------------------------------------------------------------
# Request / Response models (inline — no need for separate schemas in MVP)
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume: StructuredResume
    top_k: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class MatchResponse(BaseModel):
    matches: list[MatchResult]
    query_ms: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/match", response_model=MatchResponse)
async def match_resume_to_jobs(body: MatchRequest) -> MatchResponse:
    """Match a resume against all indexed jobs.

    Pipeline:
      1. Encode resume (use pre-computed embedding if present)
      2. Cosine-search JobVectorStore
      3. Compute missing_skills per result
      4. Return top-k MatchResult[]
    """
    import time

    t0 = time.perf_counter()

    resume = body.resume
    matches = _matcher.match_from_store(
        resume=resume,
        top_k=body.top_k,
        score_threshold=body.score_threshold,
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    return MatchResponse(matches=matches, query_ms=elapsed)
