"""DEPRECATED: T009 Career Growth V2 — RL Optimization routes.

These routes exposed internal RL iteration details and are NOT registered in main.py.
Kept for reference only — frontend should use /api/v1/career/analyze (business facade).
Deprecation: true, Sunset: 2026-12-31
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.career.t009_pipeline import T009Pipeline
from backend.career.t009_schemas import UserFeedback

from pydantic import BaseModel, Field

router = APIRouter()
_t009 = T009Pipeline(simulation_rounds=10, rl_iterations=3)


class T009RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="")
    career_dataset: list[dict] | None = None
    industry_trends: list[dict] | None = None
    privacy_level: str = Field(default="basic")
    previous_feedback: dict | None = None


class T009FeedbackRequest(BaseModel):
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
    templates = _t009._baseline_templates
    return {
        "count": len(templates),
        "templates": [t.model_dump() for t in templates],
    }


@router.post("/t009/trends", response_model=dict, tags=["T009 Career Growth V2"])
async def t009_analyze_trends(body: T009RunRequest):
    parser_output = _t009._stage_parse_v2(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    trends = _t009._parse_trends(body.industry_trends or [])
    trend_report = _t009._build_trend_report(trends, parser_output.user_profile)
    return trend_report.model_dump() if trend_report else {"trends": [], "summary": "No trend data provided"}
