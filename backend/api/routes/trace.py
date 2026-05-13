"""Trace API routes — query InteractionTrace records.

Endpoints:
  GET /api/v1/trace/{trace_id}          — full InteractionTrace by ID
  GET /api/v1/trace/                    — list recent traces
  GET /api/v1/trace/{trace_id}/samples  — training samples for a trace
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.signal_layer.data_signal_layer import DataSignalLayer
from backend.signal_layer.schemas import InteractionTrace
from backend.feedback.schemas import TrainingSample

router = APIRouter()

# Module-level singleton — shared with pipeline route
_layer = DataSignalLayer()


def get_signal_layer() -> DataSignalLayer:
    """Expose the shared DataSignalLayer for use by other route modules."""
    return _layer


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/{trace_id}", response_model=InteractionTrace)
async def get_trace(trace_id: str):
    """Retrieve a complete InteractionTrace by trace_id.

    Returns the full execution record: query, candidates, simulations,
    reviews, and training samples — all linked by this trace_id.
    """
    trace = _layer.get_trace(trace_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace '{trace_id}' not found. It may have expired or never existed.",
        )
    return trace


@router.get("/")
async def list_traces(limit: int = 50):
    """List recent InteractionTrace records, newest first.

    Returns trace_id, mode, query, candidate count, and elapsed_ms
    for each trace — enough to identify runs without full payloads.
    """
    traces = _layer.list_traces(limit=limit)
    return {
        "count": len(traces),
        "traces": [
            {
                "trace_id": t.trace_id,
                "mode": t.mode.value,
                "user_query": t.user_query[:80],
                "candidate_count": len(t.retrieved_candidates),
                "simulation_count": len(t.simulation_results),
                "sample_count": len(t.training_samples),
                "errors": len(t.errors),
                "elapsed_ms": t.elapsed_ms,
            }
            for t in traces
        ],
    }


@router.get("/{trace_id}/samples", response_model=list[TrainingSample])
async def get_trace_samples(trace_id: str):
    """Retrieve only the training samples for a specific trace.

    Useful for downstream training pipelines that only need the
    learning-to-rank dataset from one execution.
    """
    trace = _layer.get_trace(trace_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace '{trace_id}' not found.",
        )
    return trace.training_samples
