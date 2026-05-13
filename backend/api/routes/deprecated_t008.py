"""DEPRECATED: T008 Career Growth routes.

These routes exposed internal 6-agent pipeline details and are NOT registered in main.py.
Kept for reference only — frontend should use /api/v1/career/analyze (business facade).
Deprecation: true, Sunset: 2026-12-31
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.career.t008_pipeline import T008Pipeline
from backend.career.t008_schemas import (
    T008PipelineOutput,
)

from pydantic import BaseModel, Field

router = APIRouter()
_t008 = T008Pipeline(simulation_rounds=10)


class T008RunRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="")
    career_dataset: list[dict] | None = None


class T008ParseRequest(BaseModel):
    user_id: str = Field(default="default-user")
    user_input: dict | str = Field(default="")
    career_dataset: list[dict] | None = None


@router.post("/t008/run", response_model=dict, tags=["T008 Career Growth"])
async def t008_run(body: T008RunRequest):
    output = _t008.run(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    return output.model_dump()


@router.post("/t008/parse", response_model=dict, tags=["T008 Career Growth"])
async def t008_parse(body: T008ParseRequest):
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    return parser_output.model_dump()


@router.post("/t008/retrieve", response_model=dict, tags=["T008 Career Growth"])
async def t008_retrieve(body: T008ParseRequest):
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    return retrieval_output.model_dump()


@router.post("/t008/review", response_model=dict, tags=["T008 Career Growth"])
async def t008_review(body: T008ParseRequest):
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
    parser_output = _t008._stage_parse(
        user_input=body.user_input,
        career_dataset=body.career_dataset,
        user_id=body.user_id,
    )
    retrieval_output = _t008._stage_retrieve(parser_output)
    reviewer_output = _t008._stage_review(retrieval_output)
    architect_output = _t008._stage_architect(parser_output, reviewer_output)

    if architect_output.career_plan is None:
        raise HTTPException(status_code=400, detail="Career plan generation failed")

    sim_feedback = _t008._stage_simulate(architect_output.career_plan)
    return sim_feedback.model_dump()


@router.get("/t008/frontend/{user_id}", response_model=dict, tags=["T008 Career Growth"])
async def t008_frontend(user_id: str):
    output = T008PipelineOutput(user_profile=None)
    frontend_data = _t008._stage_frontend(output)
    return {"user_id": user_id, "frontend_data": frontend_data}
