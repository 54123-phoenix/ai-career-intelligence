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


# ═══════════════════════════════════════════════════════════════════════════
# Business Facade — 业务语义 API（前端应调用这些端点，而非 T008/T009/T010）
# ═══════════════════════════════════════════════════════════════════════════

class CareerAnalyzeRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")
    resume_data: dict | None = Field(default=None)
    depth: str = Field(default="standard", description="quick | standard | deep")


class CareerFeedbackRequest(BaseModel):
    analysis_id: str
    rating: float = Field(ge=0, le=5)
    comments: str = ""
    adopted_strategy: str | None = None


@router.post("/analyze", response_model=dict, tags=["Career Facade"])
async def career_analyze(body: CareerAnalyzeRequest):
    """业务 facade：职业综合分析（解析 + 推荐 + 策略 + 模拟）.

    内部调用 T010 pipeline，对外隐藏实现细节。
    """
    output = _t010.run(
        user_input=body.user_input,
        user_id="facade-user",
        privacy_level="basic",
    )
    return {
        "id": output.execution_id,
        "status": output.status,
        "user_profile": output.user_profile.model_dump() if output.user_profile else None,
        "recommendations": [j.model_dump() for j in output.job_recommendations],
        "strategies": [s.model_dump() for s in output.strategy_list],
        "plan": output.career_plan.model_dump() if output.career_plan else None,
        "simulation": output.simulation_feedback.model_dump() if output.simulation_feedback else None,
        "frontend_data": output.frontend_data,
        "generated_at": output.generated_at,
        "career_data": None,
        "errors": output.errors,
    }


@router.post("/resume", response_model=dict, tags=["Career Facade"])
async def career_upload_resume():
    """业务 facade：简历上传与解析.

    内部调用 T001 parser，对外隐藏实现细节。
    """
    # MVP: return placeholder — integrate with parser agent
    return {
        "resume_id": "res-facade-001",
        "parsed": {"skills": [], "experience": []},
        "message": "Resume upload endpoint ready — integrate with parser",
    }


class RecommendationsRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")


class MatchScoreRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")
    job_title: str = Field(description="目标岗位名称")
    required_skills: list[str] = Field(default_factory=list, description="岗位所需技能")


class CareerPathRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")


@router.post("/recommendations", response_model=dict, tags=["Career Facade"])
async def career_recommendations(body: RecommendationsRequest):
    """业务 facade：获取岗位推荐列表.

    内部调用 T010 pipeline 提取 job_recommendations。
    """
    output = _t010.run(
        user_input=body.user_input,
        user_id="facade-user",
        privacy_level="basic",
    )
    return {
        "recommendations": [j.model_dump() for j in output.job_recommendations],
        "total_matches": output.total_matches,
    }


@router.post("/match-score", response_model=dict, tags=["Career Facade"])
async def career_match_score(body: MatchScoreRequest):
    """业务 facade：查询用户与特定岗位的匹配评分.

    内部调用 T010 pipeline 解析用户画像，再与岗位技能计算 Jaccard 相似度。
    """
    output = _t010.run(
        user_input=body.user_input,
        user_id="facade-user",
        privacy_level="basic",
    )

    user_skills = set(output.user_profile.skills) if output.user_profile else set()
    job_skills = set(body.required_skills)

    intersection = user_skills & job_skills
    union = user_skills | job_skills
    skill_match = len(intersection) / len(union) if union else 0.0

    experience_years = output.user_profile.experience_years if output.user_profile else 0
    # Simple heuristic: 3+ years = full fit, less = proportional
    experience_fit = min(experience_years / 3.0, 1.0)

    # Keyword overlap: user career goals vs job title
    goals = " ".join(output.user_profile.career_goals).lower() if output.user_profile else ""
    keyword_overlap = 1.0 if body.job_title.lower() in goals else 0.5

    overall = (skill_match * 0.5) + (experience_fit * 0.3) + (keyword_overlap * 0.2)

    return {
        "job_title": body.job_title,
        "score": round(overall, 2),
        "breakdown": {
            "skill_match": round(skill_match, 2),
            "experience_fit": round(experience_fit, 2),
            "keyword_overlap": round(keyword_overlap, 2),
        },
        "matched_skills": list(intersection),
        "missing_skills": list(job_skills - user_skills),
    }


@router.post("/feedback", response_model=dict, tags=["Career Facade"])
async def career_feedback(body: CareerFeedbackRequest):
    """业务 facade：提交用户反馈."""
    return {"received": True, "feedback_id": f"fb-{body.analysis_id}"}


@router.post("/path", response_model=dict, tags=["Career Facade"])
async def career_path(body: CareerPathRequest):
    """业务 facade：获取职业路径图数据.

    内部调用 T010 pipeline 提取 visualization_data。
    """
    output = _t010.run(
        user_input=body.user_input,
        user_id="facade-user",
        privacy_level="basic",
    )

    viz = output.visualization_data
    if viz:
        return {
            "primary_path": viz.primary_path,
            "skill_nodes": [n.model_dump() for n in viz.skill_nodes],
            "timeline_nodes": [n.model_dump() for n in viz.timeline_nodes],
            "skill_edges": viz.skill_edges,
        }

    # Fallback: derive from career_plan
    plan = output.career_plan
    if plan:
        return {
            "primary_path": plan.selected_strategy.strategy.strategy_name if plan.selected_strategy else [],
            "skill_nodes": [],
            "timeline_nodes": [],
            "skill_edges": [],
        }

    return {"primary_path": [], "skill_nodes": [], "timeline_nodes": [], "skill_edges": []}


@router.get("/trends", response_model=dict, tags=["Career Facade"])
async def career_trends(user_id: str = "default-user"):
    """业务 facade：获取长期趋势分析.

    MVP: 返回基于行业基准的 mock 趋势数据。
    """
    # In production, integrate with external labor market data APIs
    mock_trends = [
        {"domain": "互联网", "trend_name": "云原生架构师需求增长", "direction": "up", "growth_rate_pct": 35},
        {"domain": "人工智能", "trend_name": "大模型应用开发", "direction": "up", "growth_rate_pct": 58},
        {"domain": "后端开发", "trend_name": "Go / Rust 高性能服务", "direction": "up", "growth_rate_pct": 22},
        {"domain": "数据工程", "trend_name": "实时数据管道", "direction": "up", "growth_rate_pct": 18},
        {"domain": "前端开发", "trend_name": "全栈型前端", "direction": "stable", "growth_rate_pct": 8},
    ]
    return {
        "user_id": user_id,
        "trends": mock_trends,
        "updated_at": "2026-05-13",
    }


# ── Deprecation headers ────────────────────────────────────────────────────
# Handled globally by middleware in main.py (deprecation_middleware).
# All /career/t008/*, /career/t009/*, /career/t010/* responses include:
#   Deprecation: true
#   Sunset: 2026-12-31
