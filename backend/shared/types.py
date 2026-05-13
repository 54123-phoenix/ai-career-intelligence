"""
Shared types for AI Career Intelligence System.

WARNING: This file is maintained by @architect_agent.
Any module-specific types should live in their own module (e.g., backend/parser/schemas.py).

Version: 1.0.0
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# L1: Understanding Layer Types
# ---------------------------------------------------------------------------

class Project(BaseModel):
    """项目经历"""
    name: str = Field(description="项目名称")
    description: str = Field(default="", description="项目描述")
    tech_stack: list[str] = Field(default_factory=list, description="技术栈")
    start_date: date | None = None
    end_date: date | None = None


class Education(BaseModel):
    """教育背景"""
    school: str
    degree: Literal["本科", "硕士", "博士", "其他"] = "其他"
    major: str
    graduation_year: int | None = None


class WorkExperience(BaseModel):
    """工作经历"""
    company: str
    title: str
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None


class StructuredResume(BaseModel):
    """结构化简历 —— Parser 输出，Simulation / Retrieval 输入"""
    resume_id: str = Field(description="全局唯一标识")
    name: str
    email: str | None = None
    phone: str | None = None
    summary: str = ""
    skills: list[str] = Field(default_factory=list, description="标准化后的技能标签")
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    experience: list[WorkExperience] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    skill_embedding: list[float] | None = None


class StructuredJob(BaseModel):
    """结构化岗位 v1.0.0 —— Parser 输出，Simulation / Retrieval 输入"""

    job_id: str
    title: str
    company: str
    location: str = ""
    level: str = ""
    description: str = ""

    # Skills
    required_skills: list[str] = Field(default_factory=list)
    optional_skills: list[str] = Field(default_factory=list)

    # Compensation
    salary_range: tuple[int, int] | None = None  # (min, max) K/年

    # Metadata
    posted_date: date | None = None
    job_embedding: list[float] | None = None


# ---------------------------------------------------------------------------
# Retrieval Layer Types
# ---------------------------------------------------------------------------

class MatchResult(BaseModel):
    """检索匹配结果"""
    item_id: str
    score: float = Field(ge=0.0, le=1.0, description="匹配分数")
    payload: dict = Field(default_factory=dict)
    match_type: Literal["resume_to_job", "job_to_resume", "skill_to_skill"]


# ---------------------------------------------------------------------------
# L2: Simulation Layer Types
#    Canonical definitions moved to backend.simulation.state (v2.0.0).
#    Import from there for the authoritative versions:
#        from backend.simulation.state import AgentDecision, SimulationState, SimulationResult
#    The types below are kept for backward compatibility during migration.
# ---------------------------------------------------------------------------


class AgentDecision(BaseModel):
    """Agent 决策输出 (legacy v1 — prefer backend.simulation.state)"""
    action: str
    params: dict = Field(default_factory=dict)
    reasoning: str = Field(description="决策理由，用于可解释性")


class SimulationState(BaseModel):
    """模拟全局状态 (legacy v1 — prefer backend.simulation.state)"""
    simulation_id: str
    candidate: StructuredResume
    job: StructuredJob
    current_step: Literal["applied", "screened", "interview", "offer", "rejected", "end"] = "applied"
    decisions: list[AgentDecision] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    market_adjustment: float = Field(default=1.0, description="市场供需修正系数")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO 格式时间戳")


class SimulationResult(BaseModel):
    """模拟结果 (legacy v1 — prefer backend.simulation.state)"""
    simulation_id: str
    strategy_name: str = "default"
    final_state: SimulationState
    success_probability: float = Field(ge=0.0, le=1.0)
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    key_decisions: list[AgentDecision] = Field(default_factory=list)
    time_to_offer: int = Field(ge=0, description="模拟天数")
    path_history: list[SimulationState] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# L3: Evolution Layer Types
# ---------------------------------------------------------------------------

class RewardSignal(BaseModel):
    """反馈信号 —— 用于策略优化"""
    simulation_id: str
    match_improvement: float = 0.0
    success_rate: float = 0.0
    path_efficiency: float = 0.0
    novelty_bonus: float = 0.0
    total_reward: float = 0.0
