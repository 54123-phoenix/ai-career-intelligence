"""Career API — recommendation & feedback facade routes.

Routes at /api/v1/career:
  POST /recommendations — job recommendations
  POST /match-score     — skill match scoring
  POST /feedback        — user feedback
"""

from __future__ import annotations

from fastapi import APIRouter

from ._career_state import _t010

from pydantic import BaseModel, Field

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────

class RecommendationsRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")


class MatchScoreRequest(BaseModel):
    user_input: str = Field(description="用户职业目标、技能与经验描述")
    job_title: str = Field(description="目标岗位名称")
    required_skills: list[str] = Field(default_factory=list, description="岗位所需技能")


class CareerFeedbackRequest(BaseModel):
    analysis_id: str
    rating: float = Field(ge=0, le=5)
    comments: str = ""
    adopted_strategy: str | None = None


# ── Routes ───────────────────────────────────────────────────────────────

@router.post("/recommendations", response_model=dict, tags=["Career Facade"])
async def career_recommendations(body: RecommendationsRequest):
    """业务 facade：获取岗位推荐列表."""
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
    """业务 facade：查询用户与特定岗位的匹配评分."""
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
    experience_fit = min(experience_years / 3.0, 1.0)

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
