"""Pipeline API routes — the main T006 entry point.

Endpoints:
  POST /api/v1/pipeline/run      — execute full pipeline, returns InteractionTrace
  GET  /api/v1/pipeline/modes    — list available execution modes
  GET  /api/v1/pipeline/health   — pipeline-specific health check
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.routes.trace import get_signal_layer
from backend.pipeline.modes import ExecutionMode

from pydantic import BaseModel, Field

router = APIRouter()

# Shared DataSignalLayer — same instance as trace route
_layer = get_signal_layer()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class PipelineRequest(BaseModel):
    user_query: str = Field(
        default="", description="Natural language job search query"
    )
    user_embedding: list[float] | None = Field(
        default=None, description="Pre-computed query embedding"
    )
    filters: dict | None = Field(
        default=None, description="E.g. {'location': '北京', 'skill': 'Python'}"
    )
    mode: ExecutionMode | None = Field(
        default=None, description="Force a specific mode; architect decides if omitted"
    )
    interaction_history: list | None = Field(
        default=None, description="User behavior logs for ranking pair generation (RANKING mode)"
    )
    user_id: str | None = Field(
        default=None, description="User identifier (SESSION mode)"
    )
    session_id: str | None = Field(
        default=None, description="Existing session ID (SESSION mode)"
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_pipeline(body: PipelineRequest):
    """Execute the full multi-agent closed-loop pipeline.

    Pipeline modes:
      - FAST: cached retrieval → minimal simulation → review → feedback
      - FULL: retrieval → simulation → review → feedback
      - RANKING: retrieval → feature_build → rerank → review → pair_build
      - FALLBACK: degraded mode, cache or API-only

    Returns an InteractionTrace — the unified trace record linking all stage
    outputs by trace_id. Every TrainingSample in the response carries trace_id.

    Mode selection:
      - Omit 'mode' → ArchitectAgent auto-selects based on system state
      - Set 'mode' → bypass architect and force the specified mode
    """
    try:
        trace = await _layer.execute(
            user_query=body.user_query,
            user_embedding=body.user_embedding,
            filters=body.filters,
            force_mode=body.mode,
        )
        # Inject interaction_history into trace for ranking pair generation
        if body.interaction_history:
            trace.interaction_history = body.interaction_history
        # Inject session fields
        if body.user_id:
            setattr(trace, 'user_id', body.user_id)
        if body.session_id:
            trace.session_id = body.session_id
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Pipeline execution failed: {e}"
        )

    return trace


@router.get("/modes")
async def get_modes() -> dict:
    """List available execution modes and their descriptions."""
    return {
        "modes": {
            "fast": {
                "description": "Cached retrieval, minimal simulation (top 3)",
                "use_when": "Warm cache, simple queries",
            },
            "full": {
                "description": "Complete pipeline: retrieval → simulation → review → feedback",
                "use_when": "Normal operation, complex queries",
            },
            "fallback": {
                "description": "Degraded mode: cached or API-only, no simulation",
                "use_when": "Core services degraded",
            },
            "ranking": {
                "description": "LTR pipeline: retrieval → feature_build → rerank → review → pair_build",
                "use_when": "Trained ranking model available, real user behavior available",
            },
            "session": {
                "description": "Session learning: track → aggregate → update_prefs → retrieval → rerank → review → feedback_queue → feedback",
                "use_when": "User sessions available, dynamic preferences needed, ongoing user engagement",
            },
            "career": {
                "description": "Career evolution: parse → retrieve → review → architect → simulate → frontend",
                "use_when": "Long-term career analysis, bottleneck detection, strategy generation",
            },
        }
    }


@router.get("/health")
async def pipeline_health() -> dict:
    """Pipeline-specific health check."""
    architect = _layer.orchestrator._architect
    health = architect._check_system_health()
    all_ok = all(health.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "services": health,
    }
