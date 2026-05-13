"""Career API — path, resume & trends facade routes.

Routes at /api/v1/career:
  POST /path     — career path graph data
  POST /resume   — resume upload & parse (placeholder)
  GET  /trends   — market trend data
"""

from __future__ import annotations

from fastapi import APIRouter

from ._career_state import _t010

from pydantic import BaseModel, Field

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────

class CareerPathRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("/path", response_model=dict, tags=["Career Facade"])
async def career_path(body: CareerPathRequest):
    """业务 facade：获取职业路径图数据."""
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

    plan = output.career_plan
    if plan:
        return {
            "primary_path": plan.selected_strategy.strategy.strategy_name if plan.selected_strategy else [],
            "skill_nodes": [],
            "timeline_nodes": [],
            "skill_edges": [],
        }

    return {"primary_path": [], "skill_nodes": [], "timeline_nodes": [], "skill_edges": []}


@router.post("/resume", response_model=dict, tags=["Career Facade"])
async def career_upload_resume():
    """业务 facade：简历上传与解析. MVP: placeholder."""
    return {
        "resume_id": "res-facade-001",
        "parsed": {"skills": [], "experience": []},
        "message": "Resume upload endpoint ready — integrate with parser",
    }


@router.get("/trends", response_model=dict, tags=["Career Facade"])
async def career_trends(user_id: str = "default-user"):
    """业务 facade：获取长期趋势分析."""
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
