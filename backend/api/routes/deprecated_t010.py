"""DEPRECATED: T010 Lightweight Career Growth routes.

These routes exposed internal upgrade interfaces and are NOT registered in main.py.
Kept for reference only — frontend should use /api/v1/career/analyze (business facade).
Deprecation: true, Sunset: 2026-12-31
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.career.t010_pipeline import T010Pipeline
from backend.career.t010_schemas import (
    T010ParserOutput,
    T010RetrievalOutput,
    T010ReviewerOutput,
    T010ArchitectOutput,
    T010SimulationOutput,
    T010FrontendData,
)
from backend.career.t008_schemas import CareerPlan, VisualizationGraph
from backend.career.t009_schemas import UserFeedback

from pydantic import BaseModel, Field

router = APIRouter()
_t010 = T010Pipeline()


class T010RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="")
    career_dataset: list[dict] | None = None
    industry_trends: list[dict] | None = None
    privacy_level: str = Field(default="basic")
    previous_feedback: dict | None = None


@router.post("/t010/run", response_model=dict, tags=["T010 Lightweight"])
async def t010_run(body: T010RunRequest):
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
