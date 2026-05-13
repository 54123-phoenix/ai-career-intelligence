"""Career API routes — Career Memory & Evolution Engine (T007).

Registered at /api/v1/career
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect
from backend.career.career_simulator import CareerSimulator
from backend.career.career_frontend import CareerFrontend
from backend.career.schemas import (
    BottleneckAnalysis,
    CareerEvent,
    CareerStrategy,
    CareerTimeline,
    CareerVisualization,
    StrategySimulation,
)

from pydantic import BaseModel, Field

router = APIRouter()

# Module-level singletons (shared across requests)
_parser = CareerParser()
_retriever = CareerRetriever()
_reviewer = CareerReviewer()
_architect = CareerArchitect()
_simulator = CareerSimulator()
_frontend = CareerFrontend()


# ── Request models ───────────────────────────────────────────────────────

class EventRequest(BaseModel):
    user_id: str = Field(default="default-user")
    raw_events: list[dict] = Field(default_factory=list, description="Raw behavior data")
    single_event: dict | None = Field(default=None, description="Single raw event (alternative to list)")


class AnalyzeRequest(BaseModel):
    user_id: str = Field(description="User to analyze")


class StrategyRequest(BaseModel):
    user_id: str = Field(description="User identifier")


class SimulateRequest(BaseModel):
    user_id: str = Field(description="User identifier")


class RunCareerRequest(BaseModel):
    user_id: str = Field(default="default-user")
    raw_events: list[dict] = Field(default_factory=list)


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


@router.post("/analyze", response_model=dict, tags=["Career"])
async def analyze_career(body: AnalyzeRequest):
    """Step 3: Analyze career patterns (bottlenecks + trends)."""
    timeline = _retriever.retrieve(body.user_id)
    if timeline.total_events == 0:
        raise HTTPException(status_code=404, detail=f"No events found for {body.user_id}")

    analysis = _reviewer.analyze(timeline)
    return analysis.model_dump()


@router.post("/strategy", response_model=dict, tags=["Career"])
async def design_strategy(body: StrategyRequest):
    """Step 4: Design career development strategy."""
    timeline = _retriever.retrieve(body.user_id)
    if timeline.total_events == 0:
        raise HTTPException(status_code=404, detail=f"No events found for {body.user_id}")

    analysis = _reviewer.analyze(timeline)
    strategy = _architect.design(timeline, analysis)
    return strategy.model_dump()


@router.post("/simulate", response_model=dict, tags=["Career"])
async def simulate_strategy(body: SimulateRequest):
    """Step 5: Simulate career strategy execution."""
    timeline = _retriever.retrieve(body.user_id)
    if timeline.total_events == 0:
        raise HTTPException(status_code=404, detail=f"No events found for {body.user_id}")

    analysis = _reviewer.analyze(timeline)
    strategy = _architect.design(timeline, analysis)
    simulation = _simulator.simulate(strategy, analysis)
    return simulation.model_dump()


@router.get("/visualize/{user_id}", response_model=dict, tags=["Career"])
async def visualize(user_id: str):
    """Step 6: Build complete career visualization JSON for frontend."""
    timeline = _retriever.retrieve(user_id)
    analysis = _reviewer.analyze(timeline) if timeline.total_events > 0 else None
    strategy = _architect.design(timeline, analysis) if analysis else None
    simulation = _simulator.simulate(strategy, analysis) if strategy and analysis else None

    viz = _frontend.build(
        user_id=user_id,
        timeline=timeline,
        bottleneck=analysis,
        strategy=strategy,
        simulation=simulation,
    )
    return viz.model_dump()


@router.post("/run", response_model=dict, tags=["Career"])
async def run_career_pipeline(body: RunCareerRequest):
    """Execute the full T007 career evolution pipeline.

    Pipeline: parse → retrieve → review → architect → simulate → frontend
    """
    from backend.api.routes.pipeline import get_signal_layer
    from backend.pipeline.modes import ExecutionMode

    layer = get_signal_layer()

    # Inject career module singletons into orchestrator
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

    # Manually parse and inject events
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
# T008: Career Growth System Convergence & Strategy Optimization
# ═══════════════════════════════════════════════════════════════════════════

from backend.career.t008_pipeline import T008Pipeline
from backend.career.t008_schemas import (
    ParserOutput,
    RetrievalOutput,
    ReviewerOutput,
    ArchitectOutput,
    SimulationFeedback,
    T008PipelineOutput,
)

_t008 = T008Pipeline(simulation_rounds=10)


class T008RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="", description="User career goals, skills, experience")
    career_dataset: list[dict] | None = Field(
        default=None, description="Recruitment info / career path dataset entries"
    )


class T008ParseRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="", description="User career goals, skills, experience")
    career_dataset: list[dict] | None = None


@router.post("/t008/run", response_model=dict, tags=["T008 Career Growth"])
async def t008_run(body: T008RunRequest):
    """Execute the full T008 6-agent career growth convergence pipeline.

    Pipeline: parse → retrieve → review → architect → simulate → review(re-rank) → frontend
    """
    output = _t008.run(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    return output.model_dump()


@router.post("/t008/parse", response_model=dict, tags=["T008 Career Growth"])
async def t008_parse(body: T008ParseRequest):
    """Stage 1: Parse user profile and career dataset."""
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    return parser_output.model_dump()


@router.post("/t008/retrieve", response_model=dict, tags=["T008 Career Growth"])
async def t008_retrieve(body: T008ParseRequest):
    """Stage 2: Retrieve matching jobs and strategy candidates."""
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    return retrieval_output.model_dump()


@router.post("/t008/review", response_model=dict, tags=["T008 Career Growth"])
async def t008_review(body: T008ParseRequest):
    """Stage 3: Score and rank strategies across 4 dimensions."""
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    reviewer_output = _t008._stage_review(retrieval_output)
    return reviewer_output.model_dump()


@router.post("/t008/architect", response_model=dict, tags=["T008 Career Growth"])
async def t008_architect(body: T008ParseRequest):
    """Stage 4: Generate career plan + visualization data."""
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    reviewer_output = _t008._stage_review(retrieval_output)
    architect_output = _t008._stage_architect(parser_output, reviewer_output)
    return architect_output.model_dump()


@router.post("/t008/simulate", response_model=dict, tags=["T008 Career Growth"])
async def t008_simulate(body: T008ParseRequest):
    """Stage 5: Multi-round simulation with feedback generation."""
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    reviewer_output = _t008._stage_review(retrieval_output)
    architect_output = _t008._stage_architect(parser_output, reviewer_output)

    if architect_output.career_plan is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Career plan generation failed")

    sim_feedback = _t008._stage_simulate(architect_output.career_plan)
    return sim_feedback.model_dump()


@router.get("/t008/frontend/{user_id}", response_model=dict, tags=["T008 Career Growth"])
async def t008_frontend(user_id: str):
    """Stage 6: Get frontend-ready visualization data for a user."""
    from backend.career.t008_schemas import T008PipelineOutput
    output = T008PipelineOutput(user_profile=None)
    frontend_data = _t008._stage_frontend(output)
    return {"user_id": user_id, "frontend_data": frontend_data}


# ═══════════════════════════════════════════════════════════════════════════
# T009: Career Growth V2 — RL Optimization & Feedback Loop
# ═══════════════════════════════════════════════════════════════════════════

from backend.career.t009_pipeline import T009Pipeline
from backend.career.t009_schemas import UserFeedback

_t009 = T009Pipeline(simulation_rounds=10, rl_iterations=3)


class T009RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="", description="User career goals, skills, experience")
    career_dataset: list[dict] | None = None
    industry_trends: list[dict] | None = None
    privacy_level: str = Field(default="basic", description="none | basic | full")
    previous_feedback: dict | None = Field(
        default=None, description="Serialized UserFeedback from previous session"
    )


class T009FeedbackRequest(BaseModel):
    """User feedback submitted from frontend."""
    user_id: str
    session_id: str = ""
    strategy_adopted: str | None = None
    strategy_rating: float = Field(default=0.0, ge=0.0, le=1.0)
    nodes_clicked: list[str] = Field(default_factory=list)
    time_spent_sections: dict[str, float] = Field(default_factory=dict)
    comments: str = ""
    preferences_updated: dict = Field(default_factory=dict)
    privacy_level: str = Field(default="basic")


@router.post("/t009/run", response_model=dict, tags=["T009 Career Growth V2"])
async def t009_run(body: T009RunRequest):
    """Execute the T009 pipeline with RL optimization and feedback loop.

    Enhancements: baseline strategies, diversity scoring, dynamic weights,
    off-path detection, industry trends, privacy masking.
    """
    # Deserialize previous feedback if provided
    prev_feedback = None
    if body.previous_feedback:
        try:
            prev_feedback = UserFeedback(**body.previous_feedback)
        except Exception:
            pass

    output = _t009.run(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
        industry_trends=body.industry_trends,
        user_feedback=prev_feedback,
        privacy_level=body.privacy_level,
    )
    return output.model_dump()


@router.post("/t009/feedback", response_model=dict, tags=["T009 Career Growth V2"])
async def t009_submit_feedback(body: T009FeedbackRequest):
    """Submit user feedback for回流 to parser and reviewer agents.

    Feedback is used to update strategy weights and preference signals.
    """
    feedback = UserFeedback(
        user_id=body.user_id,
        session_id=body.session_id,
        strategy_adopted=body.strategy_adopted,
        strategy_rating=body.strategy_rating,
        nodes_clicked=body.nodes_clicked,
        time_spent_sections=body.time_spent_sections,
        comments=body.comments,
        preferences_updated=body.preferences_updated,
        privacy_level=body.privacy_level,
    )
    loop_state = _t009.handle_user_feedback(feedback)
    return {
        "received": True,
        "feedback_id": feedback.feedback_id,
        "feedback_loop": loop_state.model_dump(),
    }


@router.get("/t009/baselines", response_model=dict, tags=["T009 Career Growth V2"])
async def t009_list_baselines():
    """List available baseline career path templates."""
    templates = _t009._baseline_templates
    return {
        "count": len(templates),
        "templates": [t.model_dump() for t in templates],
    }


@router.post("/t009/trends", response_model=dict, tags=["T009 Career Growth V2"])
async def t009_analyze_trends(body: T009RunRequest):
    """Analyze industry trends for a user profile."""
    parser_output = _t009._stage_parse_v2(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    trends = _t009._parse_trends(body.industry_trends or [])
    trend_report = _t009._build_trend_report(trends, parser_output.user_profile)
    return trend_report.model_dump() if trend_report else {"trends": [], "summary": "No trend data provided"}


# ═══════════════════════════════════════════════════════════════════════════
# T010: Lightweight Career Growth — Core Layer with Upgrade Interfaces
# ═══════════════════════════════════════════════════════════════════════════

from backend.career.t010_pipeline import T010Pipeline

_t010 = T010Pipeline()


class T010RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="", description="Single user career goals, skills, experience")
    career_dataset: list[dict] | None = None
    industry_trends: list[dict] | None = None
    privacy_level: str = Field(default="basic", description="none | basic | full")
    previous_feedback: dict | None = None


@router.post("/t010/run", response_model=dict, tags=["T010 Lightweight"])
async def t010_run(body: T010RunRequest):
    """Execute lightweight T010 pipeline — core layer, single-user, upgrade-ready.

    Strict constraints: 3-5 strategy candidates, ≤10 simulation rounds,
    short-term focus, every agent output includes upgrade_interface metadata.
    """
    prev_feedback = None
    if body.previous_feedback:
        try:
            prev_feedback = UserFeedback(**body.previous_feedback)
        except Exception:
            pass

    output = _t010.run(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
        industry_trends=body.industry_trends,
        user_feedback=prev_feedback,
        privacy_level=body.privacy_level,
    )
    return output.model_dump()


@router.get("/t010/upgrade-interfaces", response_model=dict, tags=["T010 Lightweight"])
async def t010_list_upgrade_interfaces():
    """List all upgrade interfaces with their hooks and implementation notes.

    Each entry documents what the core layer does and what can be extended.
    """
    interfaces = {
        "parser": T010ParserOutput().upgrade.model_dump(),
        "retrieval": T010RetrievalOutput().upgrade.model_dump(),
        "reviewer": T010ReviewerOutput().upgrade.model_dump(),
        "architect": T010ArchitectOutput(
            career_plan=CareerPlan(user_id=""),
            visualization_data=VisualizationGraph(),
        ).upgrade.model_dump(),
        "simulation": T010SimulationOutput().upgrade.model_dump(),
        "frontend": T010FrontendData().upgrade.model_dump(),
    }
    return {
        "version": "core-1.0",
        "description": "Each agent has documented upgrade hooks for future expansion",
        "agents": interfaces,
    }
