"""Career API — analysis & event routes.

Routes at /api/v1/career:
  POST /event       — ingest career events
  GET  /timeline/{id} — retrieve career timeline
  POST /run         — full T007 pipeline
  GET  /events/{id} — list raw events
  POST /analyze     — business facade: comprehensive analysis
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.career.schemas import (
    CareerTimeline,
)
from ._career_state import (
    _parser,
    _retriever,
    _reviewer,
    _architect,
    _simulator,
    _frontend,
)

from pydantic import BaseModel, Field

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────

class EventRequest(BaseModel):
    user_id: str = Field(default="default-user")
    raw_events: list[dict] = Field(default_factory=list)
    single_event: dict | None = Field(default=None)


class AnalyzeRequest(BaseModel):
    user_id: str = Field(description="User to analyze")


class RunCareerRequest(BaseModel):
    user_id: str = Field(default="default-user")
    raw_events: list[dict] = Field(default_factory=list)


class CareerAnalyzeRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")
    resume_data: dict | None = Field(default=None)
    depth: str = Field(default="standard", description="quick | standard | deep")


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("/event", response_model=dict, tags=["Career"])
async def ingest_event(body: EventRequest):
    """Step 1: Parse and ingest raw career events."""
    user_id = body.user_id
    raw = body.raw_events or ([body.single_event] if body.single_event else [])

    if not raw:
        raise HTTPException(status_code=400, detail="No events provided")

    events = _parser.parse_batch(raw, user_id)
    _retriever.ingest_batch(events)

    return {
        "user_id": user_id,
        "events_parsed": len(events),
        "events": [e.model_dump() for e in events],
    }


@router.get("/timeline/{user_id}", response_model=dict, tags=["Career"])
async def get_timeline(user_id: str):
    """Step 2: Retrieve career timeline for a user."""
    timeline = _retriever.retrieve(user_id)
    return timeline.model_dump()


@router.post("/run", response_model=dict, tags=["Career"])
async def run_career_pipeline(body: RunCareerRequest):
    """Execute the full T007 career evolution pipeline."""
    from backend.api.routes.pipeline import get_signal_layer
    from backend.pipeline.modes import ExecutionMode

    layer = get_signal_layer()
    orch = layer.orchestrator
    orch._career_parser = _parser
    orch._career_retriever = _retriever
    orch._career_reviewer = _reviewer
    orch._career_architect = _architect
    orch._career_simulator = _simulator
    orch._career_frontend = _frontend

    ctx = await orch.run(
        user_query="career analysis",
        force_mode=ExecutionMode.CAREER,
    )
    ctx.user_id = body.user_id  # type: ignore

    if body.raw_events:
        events = _parser.parse_batch(body.raw_events, body.user_id)
        _retriever.ingest_batch(events)
        ctx.career_events = [e.model_dump() for e in events]

        timeline = _retriever.retrieve(body.user_id)
        ctx.career_timeline = timeline.model_dump()

        analysis = _reviewer.analyze(timeline)
        ctx.bottleneck_analysis = analysis.model_dump()

        strategy = _architect.design(timeline, analysis)
        ctx.career_strategy = strategy.model_dump()

        sim = _simulator.simulate(strategy, analysis)
        ctx.strategy_simulation = sim.model_dump()

        viz = _frontend.build(
            user_id=body.user_id,
            timeline=timeline,
            bottleneck=analysis,
            strategy=strategy,
            simulation=sim,
        )
        ctx.career_visualization = viz.model_dump()

    return {
        "user_id": body.user_id,
        "timeline": ctx.career_timeline,
        "bottleneck_analysis": ctx.bottleneck_analysis,
        "career_strategy": ctx.career_strategy,
        "strategy_simulation": ctx.strategy_simulation,
        "visualization": ctx.career_visualization,
    }


@router.get("/events/{user_id}", response_model=list[dict], tags=["Career"])
async def list_events(user_id: str, limit: int = 50):
    """List raw career events for a user."""
    events = _retriever.get_events(user_id, limit=limit)
    return [e.model_dump() for e in events]


# ═══════════════════════════════════════════════════════════════════════════
# Business Facade — /api/career/analyze
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/analyze", response_model=dict, tags=["Career Facade"])
async def career_analyze(body: CareerAnalyzeRequest):
    """业务 facade：职业综合分析（解析 + 推荐 + 策略 + 模拟）.

    内部通过 CareerService 调用 T010 pipeline，对外隐藏实现细节。
    """
    from backend.career.career_service import CareerService

    service = CareerService()
    return service.analyze(
        user_input=body.user_input,
        resume_data=body.resume_data,
        depth=body.depth,
    )
