"""Career API — strategy & simulation routes.

Routes at /api/v1/career:
  POST /strategy      — design career development strategy
  POST /simulate      — simulate strategy execution
  GET  /visualize/{id} — full career visualization JSON
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ._career_state import (
    _retriever,
    _reviewer,
    _architect,
    _simulator,
    _frontend,
)

from pydantic import BaseModel, Field

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────

class StrategyRequest(BaseModel):
    user_id: str = Field(description="User identifier")


class SimulateRequest(BaseModel):
    user_id: str = Field(description="User identifier")


# ── Routes ───────────────────────────────────────────────────────────────

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
