"""Session API routes — session tracking, behavior aggregation, preference queries.

Registered at /api/v1/session
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.session.behavior_aggregator import BehaviorAggregator
from backend.session.feedback_queue import FeedbackQueueAgent
from backend.session.preference_updater import PreferenceUpdater
from backend.session.schemas import (
    DynamicPreferences,
    Session,
    SessionAction,
    SessionPipelineOutput,
    SessionSummary,
)
from backend.session.session_tracker import SessionTracker

from pydantic import BaseModel, Field

router = APIRouter()

# Module-level singletons
_tracker = SessionTracker(timeout_minutes=30)
_aggregator = BehaviorAggregator()
_updater = PreferenceUpdater(recent_weight=0.7)
_feedback_queue = FeedbackQueueAgent(max_events=10000)
_preference_store: dict[str, DynamicPreferences] = {}


# ── Request models ───────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    user_id: str = Field(description="User identifier")


class RecordActionRequest(BaseModel):
    session_id: str = Field(description="Target session ID")
    action: SessionAction


class RunSessionRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_query: str = Field(default="", description="Current search query")
    user_embedding: list[float] | None = None
    filters: dict | None = None


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("/start", response_model=dict, tags=["Session"])
async def start_session(body: StartSessionRequest):
    """Start a new session for a user. Auto-ends any existing active session."""
    session = _tracker.start_session(body.user_id)
    return {"session_id": session.session_id, "user_id": session.user_id, "is_active": True}


@router.post("/action", response_model=dict, tags=["Session"])
async def record_action(body: RecordActionRequest):
    """Record a user action within a session."""
    try:
        session = _tracker.record_action(body.session_id, body.action)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    summary = _aggregator.aggregate(session)
    return {
        "session": session.model_dump(),
        "summary": summary.model_dump(),
    }


@router.post("/end", response_model=dict, tags=["Session"])
async def end_session(body: StartSessionRequest):
    """End an active session by user_id."""
    session = _tracker.get_active_session(body.user_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No active session for {body.user_id}")

    ended = _tracker.end_session(session.session_id)
    return ended.model_dump()


@router.get("/active/{user_id}", response_model=dict, tags=["Session"])
async def get_active_session(user_id: str):
    """Get the current active session for a user (auto-creates if none)."""
    session = _tracker.get_active_session(user_id)
    return {
        "session": session.model_dump(),
        "active_count": _tracker.active_count,
    }


@router.get("/{session_id}", response_model=dict, tags=["Session"])
async def get_session(session_id: str):
    """Get a specific session by ID."""
    session = _tracker.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session.model_dump()


@router.get("/user/{user_id}/sessions", response_model=list[dict], tags=["Session"])
async def list_user_sessions(user_id: str, limit: int = 20):
    """List recent sessions for a user."""
    sessions = _tracker.list_user_sessions(user_id, limit=limit)
    return [s.model_dump() for s in sessions]


@router.get("/preferences/{user_id}", response_model=dict, tags=["Session"])
async def get_preferences(user_id: str):
    """Get dynamic preferences for a user."""
    prefs = _preference_store.get(user_id)
    if prefs is None:
        prefs = _updater.create_default(user_id)
        _preference_store[user_id] = prefs
    session = _tracker.get_active_session(user_id)
    summary = _aggregator.aggregate(session) if session else None
    return {
        "preferences": prefs.model_dump(),
        "session_summary": summary.model_dump() if summary else None,
        "session_count": prefs.session_count,
        "shift_score": prefs.preference_shift_score,
    }


@router.post("/run", response_model=SessionPipelineOutput, tags=["Session"])
async def run_session_pipeline(body: RunSessionRequest):
    """Execute the full SESSION pipeline.

    Pipeline: session_track → behavior_aggregate → preference_update
              → retrieval → rerank → review → feedback_queue → feedback
    """
    from backend.api.routes.pipeline import get_signal_layer
    from backend.pipeline.modes import ExecutionMode

    layer = get_signal_layer()

    # Ensure an active session exists
    session = _tracker.get_active_session(body.user_id)
    user_id = body.user_id

    # Extract query text from session if body is empty
    query = body.user_query
    if not query:
        # Use last query from session
        for action in reversed(session.ordered_actions):
            if action.action_type == "query" and action.query_text:
                query = action.query_text
                break
        if not query:
            query = " "

    # Run SESSION pipeline
    from backend.pipeline.orchestrator import PipelineOrchestrator

    # Create orchestrator with shared session state
    orch = layer.orchestrator
    orch._session_tracker = _tracker
    orch._behavior_aggregator = _aggregator
    orch._preference_updater = _updater
    orch._feedback_queue = _feedback_queue
    orch._preference_store = _preference_store

    ctx = await orch.run(
        user_query=query,
        user_embedding=body.user_embedding,
        filters=body.filters,
        force_mode=ExecutionMode.SESSION,
    )
    # Manually set user_id on context
    ctx.user_id = user_id  # type: ignore

    # Build output
    summary_obj = SessionSummary(**ctx.session_summary) if ctx.session_summary else None
    prefs_obj = DynamicPreferences(**ctx.dynamic_preferences) if ctx.dynamic_preferences else None

    return SessionPipelineOutput(
        session_id=ctx.session_id or "",
        trace_id=ctx.execution_id,
        session_summary=summary_obj,
        updated_preferences=prefs_obj,
        queued_events_count=len(ctx.queued_events),
        drift_score=ctx.drift_score,
    )


@router.get("/queue/status", response_model=dict, tags=["Session"])
async def queue_status():
    """Get feedback queue status — pending events count."""
    return {
        "pending_events": _feedback_queue.event_count,
        "max_events": _feedback_queue._max,
    }
