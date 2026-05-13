"""Simulation API routes — POST /api/v1/simulation/run.

Pipeline: load resume + job → SimulationEngine.run() → SimulationResult
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from backend.shared.types import StructuredJob, StructuredResume, WorkExperience
from backend.simulation.engine import SimulationEngine
from backend.simulation.final_schema import build_envelope
from backend.simulation.state import SimulationResult

from pydantic import BaseModel, Field

router = APIRouter()

_engine = SimulationEngine()

# ---------------------------------------------------------------------------
# In-memory registry — replace with DB lookups in production
# ---------------------------------------------------------------------------

_SAMPLE_RESUMES: dict[str, StructuredResume] = {
    "res-001": StructuredResume(
        resume_id="res-001",
        name="Alice Wang",
        skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Docker", "AWS"],
        summary="Senior backend engineer, 5 years building distributed systems.",
        experience=[
            WorkExperience(
                company="TechCorp", title="Senior Backend Engineer",
                description="Built real-time data pipeline handling 10M events/day.",
                tech_stack=["Python", "Kafka", "Redis", "AWS"],
                start_date=date(2020, 3, 1), end_date=date(2025, 6, 1),
            ),
            WorkExperience(
                company="StartupAI", title="Backend Developer",
                description="Developed REST APIs for AI recruitment platform.",
                tech_stack=["Python", "FastAPI", "PostgreSQL", "Docker"],
                start_date=date(2018, 7, 1), end_date=date(2020, 2, 1),
            ),
        ],
    ),
    "res-002": StructuredResume(
        resume_id="res-002",
        name="Bob Zhang",
        skills=["Python"],
        summary="Junior developer, 1 year experience.",
        experience=[
            WorkExperience(
                company="SmallCo", title="Junior Developer",
                description="Wrote Python scripts for data processing.",
                tech_stack=["Python"],
                start_date=date(2024, 1, 1), end_date=date(2025, 1, 1),
            ),
        ],
    ),
    "res-003": StructuredResume(
        resume_id="res-003",
        name="Carol Li",
        skills=["React", "TypeScript", "CSS", "Next.js", "GraphQL"],
        summary="Frontend engineer, 3 years building SaaS dashboards.",
        experience=[
            WorkExperience(
                company="WebCo", title="Frontend Engineer",
                description="Built customer-facing dashboard with Next.js.",
                tech_stack=["React", "TypeScript", "Next.js", "GraphQL"],
                start_date=date(2022, 1, 1), end_date=date(2025, 1, 1),
            ),
        ],
    ),
}

_SAMPLE_JOBS: dict[str, StructuredJob] = {
    "job-001": StructuredJob(
        job_id="job-001",
        title="Senior Backend Engineer",
        company="ACME Corp",
        location="上海",
        level="高级",
        required_skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
        optional_skills=["AWS", "GraphQL", "Terraform"],
        salary_range=(350, 550),
        description="Build and scale distributed backend systems serving millions of users.",
    ),
    "job-002": StructuredJob(
        job_id="job-002",
        title="ML Engineer",
        company="AILab",
        location="北京",
        level="高级",
        required_skills=["Python", "TensorFlow", "PyTorch", "NLP", "Deep Learning"],
        optional_skills=["Kubernetes", "MLflow"],
        salary_range=(400, 600),
        description="Design and train large-scale NLP models for production.",
    ),
    "job-003": StructuredJob(
        job_id="job-003",
        title="Frontend Developer",
        company="WebCo",
        location="深圳",
        level="中级",
        required_skills=["React", "TypeScript", "CSS"],
        optional_skills=["Next.js", "GraphQL", "Tailwind"],
        salary_range=(200, 350),
        description="Build responsive SaaS dashboards with Next.js and TypeScript.",
    ),
}

# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class SimulationRunRequest(BaseModel):
    resume_id: str = Field(description="StructuredResume ID")
    job_id: str = Field(description="StructuredJob ID")
    strategy: str = Field(default="balanced", description="aggressive | conservative | balanced")


class SimulationRunResponse(BaseModel):
    """Legacy response envelope — kept for backward compatibility."""
    result: SimulationResult
    metrics: dict[str, float]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_simulation(body: SimulationRunRequest) -> dict:
    """Run a single-path career simulation.

    Returns FinalT004Schema: ProductView (UI) + Explanation (analysis) + raw data.
    """
    resume = _SAMPLE_RESUMES.get(body.resume_id)
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume '{body.resume_id}' not found. Available: {list(_SAMPLE_RESUMES.keys())}",
        )

    job = _SAMPLE_JOBS.get(body.job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{body.job_id}' not found. Available: {list(_SAMPLE_JOBS.keys())}",
        )

    result = _engine.run(resume, job, strategy=body.strategy)
    return build_envelope(result)


@router.get("/samples")
async def list_samples() -> dict:
    """List available sample resume and job IDs for testing."""
    return {
        "resumes": {rid: r.name for rid, r in _SAMPLE_RESUMES.items()},
        "jobs": {jid: f"{j.title} @ {j.company}" for jid, j in _SAMPLE_JOBS.items()},
    }
