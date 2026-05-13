"""Feedback API routes.

Endpoints:
  POST /api/v1/feedback/review              — review single simulation
  POST /api/v1/feedback/review/batch        — review batch of simulations
  POST /api/v1/feedback/training-samples    — generate training dataset
  GET  /api/v1/feedback/samples             — get accumulated training samples
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.feedback.feedback_agent import FeedbackAgent
from backend.feedback.reviewer import ReviewerAgent
from backend.feedback.schemas import FeedbackAggregate, FeedbackEntry, TrainingSample
from backend.shared.types import MatchResult
from backend.simulation.state import SimulationResult

from pydantic import BaseModel, Field

router = APIRouter()

_reviewer = ReviewerAgent()
_feedback = FeedbackAgent()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ReviewRequest(BaseModel):
    simulation_result: SimulationResult
    retrieval_matches: list[MatchResult] | None = None


class ReviewBatchRequest(BaseModel):
    results: list[SimulationResult]
    retrieval_matches: list[MatchResult] | None = None


class GenerateSamplesRequest(BaseModel):
    aggregate: FeedbackAggregate
    results: list[SimulationResult]
    matches: list[MatchResult] | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/review", response_model=FeedbackEntry)
async def review_simulation(body: ReviewRequest):
    """Review a single simulation result.

    Produces a FeedbackEntry with retrieval_reward, ranking_penalty,
    bias_flags, and combined_signal.
    """
    try:
        return _reviewer.review(body.simulation_result, body.retrieval_matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")


@router.post("/review/batch", response_model=FeedbackAggregate)
async def review_batch(body: ReviewBatchRequest):
    """Review a batch of simulation results.

    Returns FeedbackAggregate with per-entry reviews and batch-level
    bias detection findings.
    """
    if not body.results:
        raise HTTPException(status_code=400, detail="At least one result required")

    retrieval_ctx: dict[str, list[MatchResult]] | None = None
    if body.retrieval_matches:
        retrieval_ctx = {r.simulation_id: body.retrieval_matches for r in body.results}

    try:
        return _reviewer.review_batch(body.results, retrieval_ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch review failed: {e}")


@router.post("/training-samples", response_model=list[TrainingSample])
async def generate_samples(body: GenerateSamplesRequest):
    """Generate a learning-to-rank dataset from review + simulation outputs.

    Filters out low-quality samples (label < 0.1 or empty features).
    Returns samples sorted by label descending (ranked format).
    """
    if not body.results:
        raise HTTPException(status_code=400, detail="At least one result required")

    try:
        return _feedback.generate_dataset(body.aggregate, body.results, body.matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample generation failed: {e}")


@router.get("/samples", response_model=list[TrainingSample])
async def get_samples(limit: int = 50):
    """Get accumulated training samples from this session."""
    return _feedback.cached_samples[:limit]
