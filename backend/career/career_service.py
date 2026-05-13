"""CareerService — unified facade over the T010 lightweight pipeline.

Frontend calls /api/career/analyze → CareerService.analyze() → T010Pipeline.run().
All T008/T009/T010 internals are hidden from the caller.
"""

from __future__ import annotations

from backend.career.t010_pipeline import T010Pipeline


class CareerService:
    """Single public entry point: analyze(user_input, ...) -> dict.

    Internally delegates to T010Pipeline (the lightweight core wrapper
    over T009→T008→T007). The response format matches the canonical
    facade /analyze response — no T008/T009/T010 keys leak.
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
