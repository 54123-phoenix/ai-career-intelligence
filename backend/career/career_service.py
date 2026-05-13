"""CareerService — unified facade over the T010 lightweight pipeline.

Frontend calls /api/career/analyze → CareerService.analyze() → T010Pipeline.run().
All T008/T009/T010 internals are hidden from the caller.
"""

from __future__ import annotations

from backend.career.t010_pipeline import T010Pipeline
from backend.shared.types import StructuredJob, StructuredResume


class CareerService:
    """Single public entry point: analyze(user_input, ...) -> dict.

    Internally delegates to T010Pipeline (the lightweight core wrapper
    over T009→T008→T007) and enriches results with SimulationEngine
    outputs. No T008/T009/T010 keys leak to the response.
    """

    def __init__(self):
        self._pipeline = T010Pipeline()

    def analyze(
        self,
        user_input: str,
        *,
        resume_data: dict | None = None,
        depth: str = "standard",
        user_id: str = "facade-user",
    ) -> dict:
        """Run full career analysis and return frontend-ready dict."""
        output = self._pipeline.run(
            user_input=user_input,
            user_id=user_id,
            privacy_level="basic",
        )

        response = {
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

        # Enrich with SimulationEngine results for top job recommendations
        if output.user_profile and output.job_recommendations:
            response["simulations"] = self._run_simulations(
                output.user_profile, output.job_recommendations[:3]
            )
        else:
            response["simulations"] = []

        return response

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _profile_to_resume(profile) -> StructuredResume:
        """Convert T008 UserProfile → StructuredResume for SimulationEngine."""
        from backend.career.t008_schemas import UserProfile

        return StructuredResume(
            resume_id=f"res-{profile.user_id}",
            name=profile.user_id,
            skills=profile.skills,
            summary=", ".join(profile.career_goals) if profile.career_goals else "",
        )

    @staticmethod
    def _run_simulations(profile, job_recommendations) -> list[dict]:
        """Run SimulationEngine for top job matches, return envelopes."""
        from backend.simulation.engine import SimulationEngine
        from backend.simulation.final_schema import build_envelope

        resume = CareerService._profile_to_resume(profile)
        engine = SimulationEngine()
        envelopes: list[dict] = []

        for job_rec in job_recommendations:
            job = StructuredJob(
                job_id=f"sim-{job_rec.job_id}",
                title=job_rec.title,
                company=job_rec.company or "",
                location=job_rec.location or "",
                level=job_rec.level or "",
                required_skills=job_rec.required_skills,
                optional_skills=job_rec.optional_skills,
            )
            try:
                result = engine.run(resume, job, strategy="balanced")
                envelopes.append(build_envelope(result))
            except Exception:
                from backend.shared.fallback import fallback_simulation_dialog

                dialog = fallback_simulation_dialog()
                dialog["simulation_id"] = job.job_id
                dialog["summary"]["headline"] = f"Estimated path for {job.title}"
                envelopes.append(dialog)

        return envelopes
